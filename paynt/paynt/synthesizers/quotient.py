import stormpy
import stormpy.synthesis
import stormpy.pomdp

import math
import re
import itertools

from .statistic import Statistic

from ..sketch.jani import JaniUnfolder
from ..sketch.holes import Hole,Holes,DesignSpace

from ..profiler import Profiler

from .models import MarkovChain,MDP,DTMC

import logging
logger = logging.getLogger(__name__)


class QuotientContainer:

    # holes with avg choice value difference below this threshold will be considered consistent
    inconsistency_threshold = 0
    # whether choice values will be weighted by expected number of visits
    compute_expected_visits = True

    def __init__(self, sketch):

        # model origin
        self.sketch = sketch
        
        # qoutient MDP for the super-family
        self.quotient_mdp = None

        # for each choice of the quotient MDP contains a set of hole-option labelings
        self.action_to_hole_options = None
        # bitvector of quotient MDP choices not labeled by any hole
        self.default_actions = None
        # for each state of the quotient MDP, a set of holes associated with the actions in this state
        self.state_to_holes = None

        # builder options
        self.subsystem_builder_options = stormpy.SubsystemBuilderOptions()
        self.subsystem_builder_options.build_state_mapping = True
        self.subsystem_builder_options.build_action_mapping = True

        # (optional) counter of discarded assignments
        self.discarded = None

    
    def compute_default_actions(self):
        self.default_actions = stormpy.BitVector(self.quotient_mdp.nr_choices, False)
        for choice in range(self.quotient_mdp.nr_choices):
            if not self.action_to_hole_options[choice]:
                self.default_actions.set(choice)

    
    def compute_state_to_holes(self):
        tm = self.quotient_mdp.transition_matrix
        self.state_to_holes = []
        for state in range(self.quotient_mdp.nr_states):
            relevant_holes = set()
            for action in range(tm.get_row_group_start(state),tm.get_row_group_end(state)):
                relevant_holes.update(set(self.action_to_hole_options[action].keys()))
            self.state_to_holes.append(relevant_holes)


    def select_actions(self, family):
        ''' Select non-default actions relevant in the provided design space. '''
        Profiler.start("quotient::select_actions")

        if family.parent_info is None:
            # select from the super-quotient
            selected_actions = []
            for action in range(self.quotient_mdp.nr_choices):
                if self.default_actions[action]:
                    continue
                hole_options = self.action_to_hole_options[action]
                if family.includes(hole_options):
                    selected_actions.append(action)
        else:
            # filter each action in the parent wrt newly restricted design space
            parent_actions = family.parent_info.selected_actions
            selected_actions = []
            for action in parent_actions:
                hole_options = self.action_to_hole_options[action]
                # if family.includes(hole_options):
                if family.parent_info.splitter not in hole_options or family.includes(hole_options):
                    selected_actions.append(action)

        # construct bitvector of selected actions
        selected_actions_bv = stormpy.synthesis.construct_selection(self.default_actions, selected_actions)
        
        Profiler.resume()
        return None,selected_actions,selected_actions_bv

    def restrict_mdp(self, mdp, selected_actions_bv):
        '''
        Restrict the quotient MDP to the selected actions.
        :param selected_actions_bv a bitvector of selected actions
        :return (1) the restricted model
        :return (2) sub- to full state mapping
        :return (3) sub- to full action mapping
        '''
        Profiler.start("quotient::restrict_mdp")
        
        keep_unreachable_states = False # TODO investigate this
        all_states = stormpy.BitVector(mdp.nr_states, True)
        submodel_construction = stormpy.construct_submodel(
            mdp, all_states, selected_actions_bv, keep_unreachable_states, self.subsystem_builder_options
        )
        
        model = submodel_construction.model
        state_map = list(submodel_construction.new_to_old_state_mapping)
        choice_map = list(submodel_construction.new_to_old_action_mapping)

        Profiler.resume()
        return model,state_map,choice_map



    def restrict_quotient(self, selected_actions_bv):
        return self.restrict_mdp(self.quotient_mdp, selected_actions_bv)        

    
    def build(self, family):
        ''' Construct the quotient MDP for the family. '''

        # select actions compatible with the family and restrict the quotient
        hole_selected_actions,selected_actions,selected_actions_bv = self.select_actions(family)
        model,state_map,choice_map = self.restrict_quotient(selected_actions_bv)

        # cash restriction information
        family.hole_selected_actions = hole_selected_actions
        family.selected_actions = selected_actions

        # encapsulate MDP
        family.mdp = MDP(model, self, state_map, choice_map, family)
        family.mdp.analysis_hints = family.translate_analysis_hints()

    
    @staticmethod
    def mdp_to_dtmc(mdp):
        tm = mdp.transition_matrix
        tm.make_row_grouping_trivial()
        components = stormpy.storage.SparseModelComponents(tm, mdp.labeling, mdp.reward_models)
        dtmc = stormpy.storage.SparseDtmc(components)
        return dtmc

    
    def build_chain(self, family):
        assert family.size == 1

        _,_,selected_actions_bv = self.select_actions(family)
        mdp,state_map,choice_map = self.restrict_quotient(selected_actions_bv)
        dtmc = QuotientContainer.mdp_to_dtmc(mdp)

        return DTMC(dtmc,self,state_map,choice_map)

    def scheduler_selection(self, mdp, scheduler):
        ''' Get hole options involved in the scheduler selection. '''
        assert scheduler.memoryless and scheduler.deterministic
        
        Profiler.start("quotient::scheduler_selection")

        # construct DTMC that corresponds to this scheduler and filter reachable states/choices
        choices = scheduler.compute_action_support(mdp.model.nondeterministic_choice_indices)
        dtmc,_,choice_map = self.restrict_mdp(mdp.model, choices)
        choices = [ choice_map[state] for state in range(dtmc.nr_states) ]
        
        # map relevant choices to hole options
        selection = [set() for hole_index in mdp.design_space.hole_indices]
        for choice in choices:
            global_choice = mdp.quotient_choice_map[choice]
            choice_options = self.action_to_hole_options[global_choice]
            for hole_index,option in choice_options.items():
                selection[hole_index].add(option)
        selection = [list(options) for options in selection]
        Profiler.resume()

        return selection

    
    @staticmethod
    def make_vector_defined(vector):
        vector_noinf = [ value if value != math.inf else 0 for value in vector]
        default_value = sum(vector_noinf) / len(vector)
        vector_valid = [ value if value != math.inf else default_value for value in vector]
        return vector_valid

    
    def choice_values(self, mdp, prop, result):
        '''
        Get choice values after model checking MDP against a property.
        Value of choice c: s -> s' is computed as
        ev(s) * [ rew(c) + P(s,c,s') * mc(s') ], where
        - ev(s) is the expected number of visits of state s in DTMC induced by
          the primary scheduler
        - rew(c) is the reward associated with choice (c)
        - P(s,c,s') is the probability of transitioning from s to s' under action c
        - mc(s') is the model checking result in state s'
        '''
        Profiler.start("quotient::choice_values")

        # multiply probability with model checking results
        choice_values = stormpy.synthesis.multiply_with_vector(mdp.model.transition_matrix, result.get_values())
        choice_values = QuotientContainer.make_vector_defined(choice_values)

        # if the associated reward model has state-action rewards, then these must be added to choice values
        if prop.reward:
            reward_name = prop.formula.reward_name
            rm = mdp.model.reward_models.get(reward_name)
            assert not rm.has_transition_rewards and (rm.has_state_rewards != rm.has_state_action_rewards)
            if rm.has_state_action_rewards:
                choice_rewards = list(rm.state_action_rewards)
                assert mdp.choices == len(choice_rewards)
                for choice in range(mdp.choices):
                    choice_values[choice] += choice_rewards[choice]

        # sanity check
        for choice in range(mdp.choices):
            assert not math.isnan(choice_values[choice])

        Profiler.resume()

        return choice_values


    def expected_visits(self, mdp, prop, scheduler):
        '''
        Compute expected number of visits in the states of DTMC induced by
        this scheduler.
        '''

        if not QuotientContainer.compute_expected_visits:
            return [1] * mdp.states
        
        # extract DTMC induced by this MDP-scheduler
        choices = scheduler.compute_action_support(mdp.model.nondeterministic_choice_indices)
        sub_mdp,state_map,_ = self.restrict_mdp(mdp.model, choices)
        dtmc = QuotientContainer.mdp_to_dtmc(sub_mdp)

        # compute visits
        dtmc_visits = stormpy.synthesis.compute_expected_number_of_visits(MarkovChain.environment, dtmc).get_values()
        dtmc_visits = list(dtmc_visits)

        # handle infinity- and zero-visits
        if prop.minimizing:
            dtmc_visits = QuotientContainer.make_vector_defined(dtmc_visits)
        else:
            dtmc_visits = [ value if value != math.inf else 0 for value in dtmc_visits]
        
        # map vector of expected visits onto the state space of the quotient MDP
        expected_visits = [0] * mdp.states
        for state in range(dtmc.nr_states):
            mdp_state = state_map[state]
            visits = dtmc_visits[state]
            expected_visits[mdp_state] = visits

        return expected_visits


    def estimate_scheduler_difference(self, mdp, inconsistent_assignments, choice_values, expected_visits):
        Profiler.start("    states loop")

        # for each hole, compute its difference sum and a number of affected states
        hole_difference_sum = {hole_index: 0 for hole_index in inconsistent_assignments}
        hole_states_affected = {hole_index: 0 for hole_index in inconsistent_assignments}
        tm = mdp.model.transition_matrix
        
        for state in range(mdp.states):

            # for this state, compute for each inconsistent hole the difference in choice values between respective options
            hole_min = {hole_index: None for hole_index in inconsistent_assignments}
            hole_max = {hole_index: None for hole_index in inconsistent_assignments}

            for choice in range(tm.get_row_group_start(state),tm.get_row_group_end(state)):
                
                choice_global = mdp.quotient_choice_map[choice]
                if self.default_actions.get(choice_global):
                    continue

                choice_options = self.action_to_hole_options[choice_global]

                # collect holes in which this action is inconsistent
                inconsistent_holes = []
                for hole_index,option in choice_options.items():
                    inconsistent_options = inconsistent_assignments.get(hole_index,set())
                    if option in inconsistent_options:
                        inconsistent_holes.append(hole_index)

                value = choice_values[choice]
                for hole_index in inconsistent_holes:
                    current_min = hole_min[hole_index]
                    if current_min is None or value < current_min:
                        hole_min[hole_index] = value
                    current_max = hole_max[hole_index]
                    if current_max is None or value > current_max:
                        hole_max[hole_index] = value

            # compute the difference
            for hole_index,min_value in hole_min.items():
                if min_value is None:
                    continue
                max_value = hole_max[hole_index]
                difference = (max_value - min_value) * expected_visits[state]
                assert not math.isnan(difference)
                    
                hole_difference_sum[hole_index] += difference
                hole_states_affected[hole_index] += 1

        # aggregate
        inconsistent_differences = {
            hole_index: (hole_difference_sum[hole_index] / hole_states_affected[hole_index])
            for hole_index in inconsistent_assignments
            }

        Profiler.resume()
        return inconsistent_differences

    
    def scheduler_selection_quantitative(self, mdp, prop, result):
        '''
        Get hole options involved in the scheduler selection.
        Use numeric values to filter spurious inconsistencies.
        '''
        Profiler.start("quotient::scheduler_selection_quantitative")

        scheduler = result.scheduler

        # get qualitative scheduler selection, filter inconsistent assignments
        selection = self.scheduler_selection(mdp, scheduler)
        inconsistent_assignments = {hole_index:options for hole_index,options in enumerate(selection) if len(options) > 1 }
        if len(inconsistent_assignments) == 0:
            Profiler.resume()
            return selection,None,None,None

        # extract choice values, compute expected visits and estimate scheduler difference
        choice_values = self.choice_values(mdp, prop, result)
        expected_visits = self.expected_visits(mdp, prop, result.scheduler)
        inconsistent_differences = self.estimate_scheduler_difference(mdp, inconsistent_assignments, choice_values, expected_visits)

        # filter differences below epsilon
        for hole_index in inconsistent_assignments:
            if inconsistent_differences[hole_index] <= QuotientContainer.inconsistency_threshold:
                selection[hole_index] = [selection[hole_index][0]]

        Profiler.resume()
        return selection,choice_values,expected_visits,inconsistent_differences
        

    def scheduler_consistent(self, mdp, prop, result):
        '''
        Get hole assignment induced by this scheduler and fill undefined
        holes by some option from the design space of this mdp.
        :return hole assignment
        :return whether the scheduler is consistent
        '''
        # selection = self.scheduler_selection(mdp, result.scheduler)

        if mdp.is_dtmc:
            selection = [[mdp.design_space[hole_index].options[0]] for hole_index in mdp.design_space.hole_indices]
            return selection, None, None, None, True
        
        selection,choice_values,expected_visits,scores = self.scheduler_selection_quantitative(mdp, prop, result)
        consistent = True
        for hole_index in mdp.design_space.hole_indices:
            options = selection[hole_index]
            if len(options) > 1:
                consistent = False
            if options == []:
                selection[hole_index] = [mdp.design_space[hole_index].options[0]]

        return selection,choice_values,expected_visits,scores,consistent

    
    def suboptions_half(self, mdp, splitter):
        ''' Split options of a splitter into to halves. '''
        options = mdp.design_space[splitter].options
        half = len(options) // 2
        suboptions = [options[:half], options[half:]]
        return suboptions

    def suboptions_unique(self, mdp, splitter, used_options):
        ''' Distribute used options of a splitter into different suboptions. '''
        assert len(used_options) > 1
        suboptions = [[option] for option in used_options]
        index = 0
        for option in mdp.design_space[splitter].options:
            if option in used_options:
                continue
            suboptions[index].append(option)
            index = (index + 1) % len(suboptions)
        return suboptions

    def suboptions_enumerate(self, mdp, splitter, used_options):
        assert len(used_options) > 1
        core_suboptions = [[option] for option in used_options]
        other_suboptions = [option for option in mdp.design_space[splitter].options if option not in used_options]
        memory_holes = [hole for holes in self.pomdp_manager.memory_holes for hole in holes]
        return core_suboptions, other_suboptions

    def holes_with_max_score(self, hole_score):
        max_score = max(hole_score.values())
        with_max_score = [hole_index for hole_index in hole_score if hole_score[hole_index] == max_score]
        return with_max_score

    def most_inconsistent_holes(self, scheduler_assignment):
        num_definitions = [len(options) for options in scheduler_assignment]
        most_inconsistent = self.holes_with_max_score(num_definitions) 
        return most_inconsistent

    def discard(self, mdp, hole_assignments, core_suboptions, other_suboptions):

        # default result
        reduced_design_space = mdp.design_space.copy()
        if len(other_suboptions) == 0:
            suboptions = core_suboptions
        else:
            suboptions = [other_suboptions] + core_suboptions  # DFS solves core first

        # reduce simple holes
        # ds_before = reduced_design_space.size
        # for hole_index in reduced_design_space.hole_indices:
        #     if mdp.hole_simple[hole_index]:
        #         assert len(hole_assignments[hole_index]) == 1
        #         reduced_design_space.assume_hole_options(hole_index, hole_assignments[hole_index])
        # ds_after = reduced_design_space.size
        # self.discarded += ds_before - ds_after

        # discard other suboptions
        # suboptions = core_suboptions
        # self.discarded += (reduced_design_space.size * len(other_suboptions)) / (len(other_suboptions) + len(core_suboptions))

        return reduced_design_space, suboptions


    def split(self, family):
        Profiler.start("quotient::split")

        mdp = family.mdp
        assert not mdp.is_dtmc

        # split family wrt last undecided result
        if family.analysis_result.optimality_result is not None:
            result = family.analysis_result.optimality_result
        else:
            # pick first undecided constraint
            undecided = family.analysis_result.constraints_result.undecided_constraints[0]
            result = family.analysis_result.constraints_result.results[undecided]

        hole_assignments = result.primary_selection
        scores = result.primary_scores
        
        splitters = self.holes_with_max_score(scores)
        splitter = splitters[0]
        assert len(hole_assignments[splitter]) > 1
        core_suboptions,other_suboptions = self.suboptions_enumerate(mdp, splitter, hole_assignments[splitter])

        new_design_space, suboptions = self.discard(mdp, hole_assignments, core_suboptions, other_suboptions)
        
        # construct corresponding design subspaces
        design_subspaces = []
        
        family.splitter = splitter
        parent_info = family.collect_parent_info()
        for suboption in suboptions:
            subholes = new_design_space.subholes(splitter, suboption)
            design_subspace = DesignSpace(subholes, parent_info)
            design_subspace.assume_hole_options(splitter, suboption)
            design_subspaces.append(design_subspace)

        Profiler.resume()
        return design_subspaces

    def double_check_assignment(self, assignment, opt_prop):
        '''
        Double-check whether this assignment truly improves optimum.
        :return singleton family if the assignment truly improves optimum
        '''
        assert assignment.size == 1
        dtmc = self.build_chain(assignment)
        opt_result = dtmc.model_check_property(opt_prop)
        if opt_prop.improves_optimum(opt_result.value):
            opt_prop.update_optimum(opt_result.value)
            return assignment
        else:
            return None



class DTMCQuotientContainer(QuotientContainer):
    
    def __init__(self, *args):
        super().__init__(*args)

        # unfold jani program
        unfolder = JaniUnfolder(self.sketch)
        self.sketch.specification = unfolder.specification

        # build quotient MDP       
        edge_to_hole_options = unfolder.edge_to_hole_options
        self.quotient_mdp = stormpy.build_sparse_model_with_options(unfolder.jani_unfolded, MarkovChain.builder_options)
        logger.debug(f"Constructed quotient MDP with {self.quotient_mdp.nr_states} states.")

        # associate each action of a quotient MDP with hole options
        # remember default actions (actions taken in each hole assignment)
        # TODO handle overlapping colors
        num_choices = self.quotient_mdp.nr_choices

        self.action_to_hole_options = []
        tm = self.quotient_mdp.transition_matrix
        for choice in range(num_choices):
            edges = self.quotient_mdp.choice_origins.get_edge_index_set(choice)            
            hole_options = {}
            for edge in edges:
                combination = edge_to_hole_options.get(edge, None)
                if combination is None:
                    continue
                for hole_index,option in combination.items():
                    options = hole_options.get(hole_index,set())
                    options.add(option)
                    hole_options[hole_index] = options

            for hole_index,options in hole_options.items():
                assert len(options) == 1
            hole_options = {hole_index:list(options)[0] for hole_index,options in hole_options.items()}
            self.action_to_hole_options.append(hole_options)

        self.compute_default_actions()
        self.compute_state_to_holes()


class CTMCQuotientContainer(QuotientContainer):
    def __init__(self, *args):
        super().__init__(*args)


class MDPQuotientContainer(QuotientContainer):
    def __init__(self, *args):
        super().__init__(*args)

    def build_chain(self, assignment):
        model = self.sketch.restrict_prism(assignment)
        return MDP(model, self, None, None, assignment)


class POMDPQuotientContainer(QuotientContainer):

    def __init__(self, *args):
        super().__init__(*args)

        # default quotient attributes
        self.quotient_mdp = None
        self.action_to_hole_options = None
        self.default_actions = None
        self.state_to_holes = None

        # POMDP attributes
        self.pomdp = None
        self.observation_labels = None
        self.actions_at_observation = None
        self.action_labels_at_observation = None

        # (unfolded) quotient MDP attributes
        self.pomdp_manager = None
        
        # for each observation, a list of holes
        self.obs_to_holes = []
        # number of distinct actions associated with this hole
        self.hole_num_actions = None
        # number of distinct memory updates associated with this hole
        self.hole_num_updates = None

        
        # construct quotient POMDP
        if not self.sketch.is_explicit:
            MarkovChain.builder_options.set_build_choice_labels(True)
            self.pomdp = stormpy.build_sparse_model_with_options(self.sketch.prism, MarkovChain.builder_options)
            MarkovChain.builder_options.set_build_choice_labels(False)
            assert self.pomdp.labeling.get_states("overlap_guards").number_of_set_bits() == 0
        else:
            self.pomdp = self.sketch.explicit_model
        self.pomdp = stormpy.pomdp.make_canonic(self.pomdp)
        # ^ this also asserts that states with the same observation have the same number of available actions

        logger.info(f"Constructed POMDP having {self.observations} observations.")
        
        # extract observation labels
        if self.pomdp.has_observation_valuations():
            ov = self.pomdp.observation_valuations
            self.observation_labels = [ov.get_string(obs) for obs in range(self.observations)]
            self.observation_labels = [self.simplify_label(label) for label in self.observation_labels]
        else:
            self.observation_labels = list(range(self.observations))

        # compute actions available at each observation
        self.actions_at_observation = [0] * self.observations
        for state in range(self.pomdp.nr_states):
            obs = self.pomdp.observations[state]
            if self.actions_at_observation[obs] != 0:
                continue
            self.actions_at_observation[obs] = self.pomdp.get_nr_available_actions(state)

        # collect labels of actions available at each observation
        self.action_labels_at_observation = [[] for obs in range(self.observations)]
        for state in range(self.pomdp.nr_states):
            obs = self.pomdp.observations[state]
            if self.action_labels_at_observation[obs] != []:
                continue
            actions = self.pomdp.get_nr_available_actions(state)
            for offset in range(actions):
                choice = self.pomdp.get_choice_index(state,offset)
                labels = self.pomdp.choice_labeling.get_labels_of_choice(choice)
                self.action_labels_at_observation[obs].append(labels)

        # initialize POMDP manager
        self.pomdp_manager = stormpy.synthesis.PomdpManager(self.pomdp)

    
    @property
    def observations(self):
        return self.pomdp.nr_observations

    def simplify_label(self,label):
        label = re.sub(r"\s+", "", label)
        label = label[1:-1]

        output = "[";
        first = True
        for p in label.split("&"):
            if not p.endswith("=0"):
                if first:
                    first = False
                else:
                    output += " & "
                output += p
        output += "]"
        return output

    def unfold_memory(self):
        
        # reset basic attributes
        self.quotient_mdp = None
        self.action_to_hole_options = None
        self.default_actions = None
        self.state_to_holes = None

        # reset family attributes
        self.obs_to_holes = []
        self.hole_num_actions = None
        self.hole_num_updates = None
        
        # unfold MDP using manager
        self.quotient_mdp = self.pomdp_manager.construct_mdp()
        logger.debug(f"Constructed quotient MDP with {self.quotient_mdp.nr_states} states.")

        # short aliases
        pm = self.pomdp_manager
        pomdp = self.pomdp
        mdp = self.quotient_mdp

        # create holes
        holes = Holes()
        self.obs_to_holes = []
        self.hole_num_actions = []
        self.hole_num_updates = []

        for obs in range(self.observations):
            ah = pm.action_holes[obs]
            mh = pm.memory_holes[obs]

            obs_label = self.observation_labels[obs]
            num_actions = self.actions_at_observation[obs]
            num_updates = pm.max_successor_memory_size[obs]
            action_labels = self.action_labels_at_observation[obs]
            action_labels_str = [str(labels) for labels in action_labels]
            memory_labels_str = [str(o) for o in range(num_updates)]

            assert len(ah) == 0 or len(mh) == 0 or len(ah) == len(mh)

            obs_holes = []
            if len(ah) == 0 and len(mh) == 0:
                # no holes
                pass

            elif len(mh) == 0:
                # only action holes
                for mem,old_hole_index in enumerate(ah):

                    name = "A({},{})".format(obs_label,mem)
                    options = list(range(num_actions))
                    hole = Hole(name, options, action_labels_str)

                    obs_holes.append(holes.num_holes)
                    holes.append(hole)
                    self.hole_num_actions.append(num_actions)
                    self.hole_num_updates.append(num_updates)
            
            elif len(ah) == 0:
                # only memory holes
                for mem,old_hole_index in enumerate(mh):
                    name = "M({},{})".format(obs_label,mem)
                    options = list(range(num_updates))
                    memory_labels_str = [str(o) for o in options]
                    hole = Hole(name, options, memory_labels_str)

                    obs_holes.append(holes.num_holes)
                    holes.append(hole)
                    self.hole_num_actions.append(num_actions)
                    self.hole_num_updates.append(num_updates)

            else:
                # pairs of action-memory holes - merge into a single hole
                for mem,action_hole in enumerate(ah):
                    memory_hole = mh[mem]

                    name = "(AM({},{})".format(obs_label,mem)
                    
                    num_options = num_actions * num_updates
                    options = list(range(num_options))

                    option_labels = []
                    for action_option in range(num_actions):
                        for memory_option in range(num_updates):
                            option_label = action_labels_str[action_option] + "+" + memory_labels_str[memory_option]
                            option_labels.append(option_label)

                    hole = Hole(name, options, option_labels)
                    obs_holes.append(holes.num_holes)
                    holes.append(hole)
                    self.hole_num_actions.append(num_actions)
                    self.hole_num_updates.append(num_updates)

            self.obs_to_holes.append(obs_holes)

        # associate actions with hole combinations (explicit)
        self.action_to_hole_options = []
        num_choices = mdp.nr_choices

        # reverse mapping
        self.hole_option_to_actions = [[] for hole in holes]
        for hole_index,hole in enumerate(holes):
            self.hole_option_to_actions[hole_index] = [[] for option in hole.options]

        state_prototype = list(pm.state_prototype)
        state_memory = list(pm.state_memory)
        tm = mdp.transition_matrix
        for state in range(mdp.nr_states):
            pomdp_state = state_prototype[state]
            obs = pomdp.observations[pomdp_state]
            obs_holes = self.obs_to_holes[obs]
            if not obs_holes:
                self.action_to_hole_options.append({})
                continue

            mem = state_memory[state]
            hole_index = obs_holes[mem]

            option = 0
            for row in range(tm.get_row_group_start(state),tm.get_row_group_end(state)):
                self.action_to_hole_options.append({hole_index:option})
                self.hole_option_to_actions[hole_index][option].append(row)
                option += 1

        self.compute_default_actions()
        self.compute_state_to_holes()

        # sanity check
        for state in range(mdp.nr_states):
            assert len(self.state_to_holes[state]) <= 1

        self.sketch.design_space = DesignSpace(holes)
        self.sketch.design_space.property_indices = self.sketch.specification.all_constraint_indices()


    def select_actions(self, family):

        Profiler.start("quotient::select_actions")

        assert family is not None

        if family.parent_info is None:
            hole_selected_actions = []
            for hole_index,hole in enumerate(family):
                hole_actions = []
                for option in hole.options:
                    hole_actions += self.hole_option_to_actions[hole_index][option]
                hole_selected_actions.append(hole_actions)

        else:
            hole_selected_actions = family.parent_info.hole_selected_actions.copy()
            splitter = family.parent_info.splitter
            splitter_actions = []
            for option in family[splitter].options:
                splitter_actions += self.hole_option_to_actions[splitter][option]
            hole_selected_actions[splitter] = splitter_actions

        selected_actions = []
        for actions in hole_selected_actions:
            selected_actions += actions

        # construct bitvector of selected actions
        selected_actions_bv = stormpy.synthesis.construct_selection(self.default_actions, selected_actions)

        Profiler.resume()
        return hole_selected_actions, None, selected_actions_bv

    
    def estimate_scheduler_difference(self, mdp, inconsistent_assignments, choice_values, expected_visits):

        # create inverse map
        # TODO optimize this for multiple properties
        quotient_to_restricted_action_map = [None] * self.quotient_mdp.nr_choices
        for action in range(mdp.choices):
            quotient_to_restricted_action_map[mdp.quotient_choice_map[action]] = action

        # for each hole, compute its difference sum and a number of affected states
        inconsistent_differences = {}
        for hole_index,options in inconsistent_assignments.items():
            difference_sum = 0
            states_affected = 0
            edges_0 = self.hole_option_to_actions[hole_index][options[0]]
            for choice_index,_ in enumerate(edges_0):

                choice_0_global = edges_0[choice_index]
                choice_0 = quotient_to_restricted_action_map[choice_0_global]
                if choice_0 is None:
                    continue
                
                source_state = mdp.choice_to_state[choice_0]
                source_state_visits = expected_visits[source_state]
                # assert source_state_visits != 0
                if source_state_visits == 0:
                    continue

                state_values = []
                for option in options:
                    choice_global = self.hole_option_to_actions[hole_index][option][choice_index]
                    choice = quotient_to_restricted_action_map[choice_global]
                    choice_value = choice_values[choice]
                    state_values.append(choice_value)
                
                min_value = min(state_values)
                max_value = max(state_values)
                difference = (max_value - min_value) * source_state_visits
                assert not math.isnan(difference)
                difference_sum += difference
                states_affected += 1
            
            if states_affected == 0:
                hole_score = 0
            else:
                hole_score = difference_sum / states_affected
            inconsistent_differences[hole_index] = hole_score

        return inconsistent_differences

    
    def break_symmetry(self, family, action_inconsistencies):

        # mark observations having multiple actions and multiple holes, where it makes sense to break symmetry
        obs_with_multiple_holes = { obs for obs,holes in enumerate(self.obs_holes) if len(holes) > 1 }
        if len(obs_with_multiple_holes) == 0:
            return family

        # go through each observation of interest and break symmetry
        restricted_family = family.copy()
        for obs in obs_with_multiple_holes:
            obs_holes = self.obs_to_holes[obs]
            # print("breaking symmetry in observation", obs, obs_holes)

            if obs in action_inconsistencies:
                # use inconsistencies to break symmetries
                actions = action_inconsistencies[obs]
            else:
                # remove actions one by one
                actions = list(range(self.hole_num_actions[obs]))
            
            for action_index,hole_index in enumerate(obs_holes):
                action = actions[action_index % len(actions)]
            
            # for action_index,hole_index in enumerate(obs_holes):
            #     if action_index >= len(actions):
            #         break
            #     action = actions[action_index]
            
                # remove action from options
                options = [option for option in family[hole_index].options if option // quo.hole_num_updates[hole_index] != action]
                # print("{} -> {}".format(family[hole_index].options,options))
                restricted_family[hole_index].assume_options(options)
        logger.debug("Symmetry breaking: reduced design space from {} to {}".format(family.size, restricted_family.size))
        
        return restricted_family

    def break_symmetry_2(self, family, selection):

        # options that are left in the hole
        selection = [ options.copy() for options in selection ]
        print(selection)

        # for each observation round-robin inconsistencies from the holes

        options_removed = [[] for hole in selection ]
        
        for obs in range(self.sketch.quotient.observations):
            obs_holes = self.sketch.quotient.obs_to_holes[obs]
            if len(obs_holes) <= 1:
                continue
            
            # count all different assignments in these holes
            option_count = [0] * family[obs_holes[0]].size
            for hole in obs_holes:
                for option in selection[hole]:
                    option_count[option] += 1

            # go through each hole and try to remove duplicates
            while True:
                changed = False
                for hole in obs_holes:
                    can_remove = [option for option in selection[hole] if option_count[option] > 1]
                    if not can_remove:
                        continue
                    option = can_remove[0]
                    selection[hole].remove(option)
                    options_removed[hole].append(option)
                    option_count[option] -= 1
                    changed = True
                if not changed:
                    break

        print(options_removed)
        print(selection)

        # remove selected options from the family
        restricted_family = family.copy()
        for hole,removed in enumerate(options_removed):
            new_options = [ option for option in family[hole].options if option not in removed ]
            restricted_family[hole].assume_options(new_options)
        
        logger.debug("Symmetry breaking: reduced design space from {} to {}".format(family.size, restricted_family.size))
        return restricted_family

    def sift_actions_and_updates(self, hole, options):
        actions = set()
        updates = set()
        num_updates = self.hole_num_updates[hole]
        for option in options:
            actions.add(option // num_updates)
            updates.add(option %  num_updates)
        return actions,updates

    def disable_action(self, family, hole, action):
        num_actions = self.hole_num_actions(hole)
        num_updates = self.hole_num_updates(hole)
        to_remove = [ (action * num_updates + update) for update in range(num_updates)]
        new_options = [ option for option in family[hole].options if option not in to_remove ]
        family.assume_hole_options(hole, new_options)

    
    def break_symmetry_3(self, family, action_inconsistencies, memory_inconsistencies):
        
        print("breaking symmetry using {} and {}".format(action_inconsistencies, memory_inconsistencies))

        # go through each observation of interest and break symmetry
        restricted_family = family.copy()
        for obs in range(self.observations):
            
            num_actions = self.actions_at_observation[obs]
            num_updates = self.pomdp_manager.max_successor_memory_size[obs]

            obs_holes = self.obs_to_holes[obs]
            num_holes = len(obs_holes)


            all_actions = [action for action in range(num_actions)]
            selected_actions = [all_actions.copy() for hole in obs_holes]
            
            all_updates = [update for update in range(num_updates)]
            selected_updates = [all_updates.copy() for hole in obs_holes]

            inconsistencies = list(action_inconsistencies[obs])
            num_inc = len(inconsistencies)
            if num_inc > 1:
                # action inconsistency: allocate inconsistent actions between holes
                ignored_actions = [action for action in all_actions if action not in inconsistencies]
                selected_actions = [ignored_actions.copy() for hole in obs_holes]
                for index in range(max(num_holes,num_inc)):
                    selected_actions[index % num_holes].append(inconsistencies[index % num_inc])
            else:
                inconsistencies = list(memory_inconsistencies[obs])
                num_inc = len(inconsistencies)
                if num_inc > 1:
                    # memory inconsistency: distribute inconsistent updates between holes
                    ignored_updates = [update for update in all_updates if update not in inconsistencies]
                    selected_updates = [ignored_updates.copy() for hole in obs_holes]
                    for index in range(max(num_holes,num_inc)):
                        selected_updates[index % num_holes].append(inconsistencies[index % num_inc])

            # create options for each hole
            for index in range(num_holes):
                hole = obs_holes[index]
                actions = selected_actions[index]
                updates = selected_updates[index]
                options = []
                for action in actions:
                    for update in updates:
                        options.append(action * num_updates + update)
                restricted_family[hole].assume_options(options)

        logger.debug("Symmetry breaking: reduced design space from {} to {}".format(family.size, restricted_family.size))

        return restricted_family




