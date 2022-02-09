import stormpy
import stormpy.synthesis
import stormpy.pomdp

import math
import re
import itertools
import random
from collections import OrderedDict

from .statistic import Statistic

from ..sketch.jani import JaniUnfolder
from ..sketch.property import Property
from ..sketch.holes import Hole,Holes,DesignSpace,CombinationColoring

from ..profiler import Profiler

from .models import MarkovChain,MDP,DTMC

import logging
logger = logging.getLogger(__name__)


class QuotientContainer:

    # holes with avg choice value difference below this threshold will be considered consistent
    inconsistency_threshold = 0

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


        Profiler.resume()
        return None,selected_actions


    def restrict_quotient(self, family):
        '''
        Restrict the quotient MDP to the selected actions.
        :return (1) the restricted model
        :return (2) sub- to full state mapping
        :return (3) sub- to full action mapping
        '''

        # select actions compatible with the family
        hole_selected_actions,selected_actions = self.select_actions(family)
        Profiler.start("quotient::restrict_quotient")

        # construct bitvector of selected actions
        selected_actions_bv = stormpy.synthesis.construct_selection(self.default_actions, selected_actions)
        
        # construct the submodel
        Profiler.start("    submodel")
        keep_unreachable_states = True
        all_states = stormpy.BitVector(self.quotient_mdp.nr_states, True)
        submodel_construction = stormpy.construct_submodel(
            self.quotient_mdp, all_states, selected_actions_bv, keep_unreachable_states, self.subsystem_builder_options
        )
        Profiler.resume()

        model = submodel_construction.model
        state_map = list(submodel_construction.new_to_old_state_mapping)
        choice_map = list(submodel_construction.new_to_old_action_mapping)
        Profiler.resume()
        return hole_selected_actions,selected_actions,model,state_map,choice_map

    
    def build(self, family):
        ''' Construct the quotient MDP for the family. '''
        hole_selected_actions,selected_actions,model,state_map,choice_map = self.restrict_quotient(family)
        family.hole_selected_actions = hole_selected_actions
        family.selected_actions = selected_actions
        family.mdp = MDP(model, self, state_map, choice_map, family)
        family.mdp.analysis_hints = family.translate_analysis_hints()

    def build_chain(self, family):
        assert family.size == 1

        # restrict quotient
        _,_,sub_mdp,state_map,choice_map = self.restrict_quotient(family)
        
        # convert restricted MDP to DTMC
        tm = sub_mdp.transition_matrix
        tm.make_row_grouping_trivial()
        components = stormpy.storage.SparseModelComponents(tm, sub_mdp.labeling, sub_mdp.reward_models)
        dtmc = stormpy.storage.SparseDtmc(components)

        return DTMC(dtmc,self,state_map,choice_map)

    def scheduler_selection(self, mdp, scheduler):
        ''' Get hole options involved in the scheduler selection. '''
        assert scheduler.memoryless and scheduler.deterministic
        
        Profiler.start("quotient::scheduler_selection")
        choice_selection = scheduler.compute_action_support(mdp.model.nondeterministic_choice_indices)
        selection = [set() for hole_index in mdp.design_space.hole_indices]
        for choice in choice_selection:
            global_choice = mdp.quotient_choice_map[choice]
            choice_options = self.action_to_hole_options[global_choice]
            for hole_index,option in choice_options.items():
                selection[hole_index].add(option)
        selection = [list(options) for options in selection]
        Profiler.resume()

        return selection

    def estimate_scheduler_difference(self, mdp, inconsistent_assignments, choice_values):
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
                difference = max_value - min_value
                if math.isnan(difference):
                    assert max_value == min_value and min_value == math.inf
                    difference = 0
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
        # return super().scheduler_selection_quantitative(mdp,prop,result)
        Profiler.start("quotient::scheduler_selection_quantitative")

        # get qualitative scheduler selection, filter inconsistent assignments        
        selection = self.scheduler_selection(mdp, result.scheduler)

        inconsistent_assignments = {hole_index:options for hole_index,options in enumerate(selection) if len(options) > 1 }
        if len(inconsistent_assignments) == 0:
            Profiler.resume()
            return selection,None

        choice_values = stormpy.synthesis.multiply_with_vector(mdp.model.transition_matrix,result.get_values())
        choice_values = list(choice_values)

        if prop.reward:
            # if the associated reward model has state-action rewards, then these must be added to choice values
            reward_name = prop.formula.reward_name
            rm = mdp.model.reward_models.get(reward_name)
            assert not rm.has_transition_rewards and (rm.has_state_rewards != rm.has_state_action_rewards)
            if rm.has_state_action_rewards:
                choice_rewards = list(rm.state_action_rewards)
                assert mdp.choices == len(choice_rewards)
                for choice in range(mdp.choices):
                    choice_values[choice] += choice_rewards[choice]

        inconsistent_differences = self.estimate_scheduler_difference(mdp, inconsistent_assignments, choice_values)

        # filter differences below epsilon
        for hole_index in inconsistent_assignments:
            if inconsistent_differences[hole_index] <= QuotientContainer.inconsistency_threshold:
                selection[hole_index] = [selection[hole_index][0]]

        Profiler.resume()
        return selection,inconsistent_differences
        

    def scheduler_consistent(self, mdp, prop, result):
        '''
        Get hole assignment induced by this scheduler and fill undefined
        holes by some option from the design space of this mdp.
        :return hole assignment
        :return whether the scheduler is consistent
        '''
        # selection = self.scheduler_selection(mdp, result.scheduler)
        selection,scores = self.scheduler_selection_quantitative(mdp, prop, result)
        consistent = True
        for hole_index in mdp.design_space.hole_indices:
            options = selection[hole_index]
            if len(options) > 1:
                consistent = False
            if options == []:
                selection[hole_index] = [mdp.design_space[hole_index].options[0]]

        return selection,scores,consistent

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
        hole_assignments,scores = mdp.scheduler_results[next(reversed(mdp.scheduler_results))]
        
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
        logger.debug("Constructing quotient MDP ... ")
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

    # merge_holes_in_observation = False
    merge_holes_in_observation = True

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

    def unfold_partial_memory(self):
        
        # reset basic attributes
        self.quotient_mdp = None
        self.action_to_hole_options = None
        self.default_actions = None
        self.state_to_holes = None

        # number of distinct actions associated with this hole
        self.hole_num_actions = None
        # number of distinct memory updates associated with this hole
        self.hole_num_updates = None
        
        # unfold MDP using manager
        logger.debug("Constructing quotient MDP ... ")
        self.quotient_mdp = self.pomdp_manager.construct_mdp()
        logger.debug(f"Constructed quotient MDP with {self.quotient_mdp.nr_states} states.")

        # shortcuts
        pm = self.pomdp_manager
        pomdp = self.pomdp
        mdp = self.quotient_mdp

        '''
        PM attributes:

        observation_memory_size: obs -> allocated states (default: 1)

        num_holes: total # of holes
        action_holes: obs -> list of action holes
        memory_holes: obs -> list of memory holes
        hole_options: hole -> # of options

        state_prototype: MDP state -> POMDP state
        row_action_hole,row_action_option: MDP choice -> action hole/option (or num_holes)
        row_memory_hole,row_memory_option: MDP choice -> memory hole/option (or num_holes)
        '''
        
        if not POMDPQuotientContainer.merge_holes_in_observation:
            # create holes
            holes = Holes()
            for hole_index in range(pm.num_holes):
                holes.append(None)

            # create action holes
            for obs,hole_indices in enumerate(pm.action_holes):
                obs_label = self.observation_labels[obs]
                action_labels = self.action_labels_at_observation[obs]
                for mem,hole_index in enumerate(hole_indices):
                    name = "A({},{})".format(obs_label,mem)
                    options = list(range(pm.hole_options[hole_index]))
                    option_labels = [str(labels) for labels in action_labels]
                    hole = Hole(name, options, option_labels)
                    holes[hole_index] = hole

            # create memory holes
            for obs,hole_indices in enumerate(pm.memory_holes):
                obs_label = self.observation_labels[obs]
                for mem,hole_index in enumerate(hole_indices):
                    name = "M({},{})".format(obs_label,mem)
                    options = list(range(pm.hole_options[hole_index]))
                    option_labels = [str(o) for o in options]
                    hole = Hole(name, options, option_labels)
                    holes[hole_index] = hole

            # create domains for each hole
            self.sketch.design_space = DesignSpace(holes)
            self.sketch.design_space.property_indices = self.sketch.specification.all_constraint_indices()
            
            # printo info about this unfolding
            # print("# of holes: ", pm.num_holes)
            # print("design space size: ", self.sketch.design_space.size)
            # print("", flush=True)

            # associate actions with hole combinations (colors)
            self.action_to_hole_options = []
            num_choices = mdp.nr_choices

            
            row_action_hole = list(pm.row_action_hole)
            row_memory_hole = list(pm.row_memory_hole)
            row_action_option = list(pm.row_action_option)
            row_memory_option = list(pm.row_memory_option)
            num_holes = pm.num_holes
            for row in range(num_choices):
                relevant_holes = {}
                action_hole = row_action_hole[row]
                if action_hole != num_holes:
                    relevant_holes[action_hole] = row_action_option[row]
                memory_hole = row_memory_hole[row]
                if memory_hole != num_holes:
                    relevant_holes[memory_hole] = row_memory_option[row]
                if not relevant_holes:
                    self.action_to_hole_options.append({})
                else:
                    self.action_to_hole_options.append(relevant_holes)

            self.compute_default_actions()
            self.compute_state_to_holes()

        else:

            # create holes
            holes = Holes()

            # for each observation, a list of holes
            obs_to_holes = []

            self.hole_num_actions = []
            self.hole_num_updates = []

            hole_options = list(pm.hole_options)

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

                obs_to_holes.append(obs_holes)

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
                obs_holes = obs_to_holes[obs]
                if not obs_holes:
                    self.action_to_hole_options.append({})
                    continue

                mem = state_memory[state]
                hole_index = obs_holes[mem]

                # assert tm.get_row_group_end(state) - tm.get_row_group_start(state) == holes[hole_index].size

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

        if not POMDPQuotientContainer.merge_holes_in_observation:
            return super().select_actions(family)

        Profiler.start("quotient::select_actions")

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

        Profiler.resume()
        return hole_selected_actions, selected_actions

    
    def estimate_scheduler_difference(self, mdp, inconsistent_assignments, choice_values):

        if not POMDPQuotientContainer.merge_holes_in_observation:
            return super().estimate_scheduler_difference(mdp, inconsistent_assignments, choice_values)

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
            for choice_index,_ in enumerate(self.hole_option_to_actions[hole_index][0]):
                state_values = []
                for option in options:
                    choice_global = self.hole_option_to_actions[hole_index][option][choice_index]
                    choice = quotient_to_restricted_action_map[choice_global]
                    choice_value = choice_values[choice]
                    state_values.append(choice_value)
                min_value = min(state_values)
                max_value = max(state_values)
                difference = max_value - min_value
                if math.isnan(difference):
                    assert max_value == min_value and min_value == math.inf
                    difference = 0
                difference_sum += difference
                states_affected += 1
            inconsistent_differences[hole_index] = difference_sum / states_affected

        return inconsistent_differences

    def suboptions_enumerate(self, mdp, splitter, used_options):

        if not POMDPQuotientContainer.merge_holes_in_observation or True:
            return super().suboptions_enumerate(mdp, splitter, used_options)

        # check if splitter is a merged hole
        num_actions = self.hole_num_actions[splitter]
        num_updates = self.hole_num_updates[splitter]
        if num_actions == 0 or num_updates == 0:
            # non-merged hole
            return super().suboptions_enumerated(mdp, splitter, used_options)
        
        # merged hole
        assert len(used_options) > 1
        
        # use first two holes to decide whether inconsistency was in actions or updates
        all_options = mdp.design_space[splitter].options
        option_0 = used_options[0]
        option_1 = used_options[1]
        other_suboptions = []
        if option_0 % num_actions == option_1 % num_actions:
            # inconsistent actions: aggregate wrt actions and split
            used_actions = set([option//num_actions for option in used_options])
            core_suboptions = {action:[] for action in used_actions}
            for option in all_options:
                if option//num_actions in used_actions:
                    core_suboptions[option//num_actions].append(option)
                else:
                    other_suboptions.append(option)
        else:
            # inconsistent updates: aggregate wrt udpates and split
            used_updates = set([option%num_actions for option in used_options])
            core_suboptions = {update:[] for update in used_updates}
            for option in all_options:
                if option%num_actions in used_updates:
                    core_suboptions[option%num_actions].append(option)
                else:
                    other_suboptions.append(option)
        
        core_suboptions = list(core_suboptions.values())
        
        return core_suboptions, other_suboptions

    


            


