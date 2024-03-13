import stormpy
import payntbind

import paynt.family.family
import paynt.quotient.models

import math
import itertools

import logging
logger = logging.getLogger(__name__)


class Quotient:

    # if True, hole scores in the state will be multiplied with the number of expected visits of this state
    compute_expected_visits = True

    @staticmethod
    def make_vector_defined(vector):
        vector_noinf = [ value if value != math.inf else 0 for value in vector]
        default_value = sum(vector_noinf) / len(vector)
        vector_valid = [ value if value != math.inf else default_value for value in vector]
        return vector_valid

    
    def __init__(self, quotient_mdp = None, family = None, coloring = None, specification = None):
        
        # colored qoutient MDP for the super-family
        self.quotient_mdp = quotient_mdp
        self.family = family
        self.coloring = coloring
        self.specification = specification
        self.design_space = None

        # builder options
        self.subsystem_builder_options = stormpy.SubsystemBuilderOptions()
        self.subsystem_builder_options.build_state_mapping = True
        self.subsystem_builder_options.build_action_mapping = True

        # for each choice of the quotient, a list of its state-destinations
        self.choice_destinations = None
        if self.quotient_mdp is not None:
            self.choice_destinations = payntbind.synthesis.computeChoiceDestinations(self.quotient_mdp)

        # (optional) counter of discarded assignments
        self.discarded = 0


    def export_result(self, dtmc):
        ''' to be overridden '''
        pass
    

    def restrict_mdp(self, mdp, choices):
        '''
        Restrict the quotient MDP to the selected actions.
        :param choices a bitvector of selected actions
        :return (1) the restricted model
        :return (2) sub- to full state mapping
        :return (3) sub- to full action mapping
        '''
        keep_unreachable_states = False # TODO investigate this
        all_states = stormpy.BitVector(mdp.nr_states, True)
        submodel_construction = stormpy.construct_submodel(
            mdp, all_states, choices, keep_unreachable_states, self.subsystem_builder_options
        )
        
        model = submodel_construction.model
        state_map = submodel_construction.new_to_old_state_mapping.copy()
        choice_map = submodel_construction.new_to_old_action_mapping.copy()

        return model,state_map,choice_map

 
    def restrict_quotient(self, choices):
        return self.restrict_mdp(self.quotient_mdp, choices)        

    
    def build_from_choice_mask(self, choice_mask):
        mdp,state_map,choice_map = self.restrict_quotient(choice_mask)
        mdp = paynt.quotient.models.MDP(mdp, self, state_map, choice_map, None)
        return mdp

    
    def build(self, family):
        ''' Construct the quotient MDP for the family. '''
        # select actions compatible with the family and restrict the quotient
        choices = self.coloring.selectCompatibleChoices(family.family)
        family.selected_choices = choices
        family.mdp = self.build_from_choice_mask(choices)
        family.mdp.design_space = family


    def build_with_second_coloring(self, family, main_coloring, main_family):
        ''' Construct the quotient MDP for the family. '''

        # select actions compatible with the family and restrict the quotient
        choices_alt = self.coloring.selectCompatibleChoices(family.family)
        choices_main = main_coloring.selectCompatibleChoices(main_family.family)

        choices = choices_main.__and__(choices_alt)
        main_family.mdp = self.build_from_choice_mask(choices)
        main_family.mdp.design_space = main_family
        family.mdp = self.build_from_choice_mask(choices)
        family.mdp.design_space = family

    
    @staticmethod
    def mdp_to_dtmc(mdp):
        tm = mdp.transition_matrix
        tm.make_row_grouping_trivial()
        assert tm.nr_columns == tm.nr_rows, "expected transition matrix without non-trivial row groups"
        components = stormpy.storage.SparseModelComponents(tm, mdp.labeling, mdp.reward_models)
        dtmc = stormpy.storage.SparseDtmc(components)
        return dtmc

    def build_assignment(self, family):
        assert family.size == 1, "expecting family of size 1"
        choices = self.coloring.selectCompatibleChoices(family.family)
        mdp,state_map,choice_map = self.restrict_quotient(choices)
        dtmc = Quotient.mdp_to_dtmc(mdp)
        return paynt.quotient.models.DTMC(dtmc,self,state_map,choice_map)
    
    def empty_scheduler(self):
        return [None] * self.quotient_mdp.nr_states

    def discard_unreachable_choices(self, state_to_choice):
        state_to_choice_reachable = self.empty_scheduler()
        state_visited = [False]*self.quotient_mdp.nr_states
        initial_state = list(self.quotient_mdp.initial_states)[0]
        state_visited[initial_state] = True
        state_queue = [initial_state]
        while state_queue:
            state = state_queue.pop()
            choice = state_to_choice[state]
            state_to_choice_reachable[state] = choice
            for dst in self.choice_destinations[choice]:
                if not state_visited[dst]:
                    state_visited[dst] = True
                    state_queue.append(dst)
        return state_to_choice_reachable

    def scheduler_to_state_to_choice(self, mdp, scheduler, discard_unreachable_choices=True):
        state_to_quotient_choice = payntbind.synthesis.schedulerToStateToGlobalChoice(scheduler, mdp.model, mdp.quotient_choice_map)
        state_to_choice = self.empty_scheduler()
        for state in range(mdp.model.nr_states):
            quotient_choice = state_to_quotient_choice[state]
            quotient_state = mdp.quotient_state_map[state]
            state_to_choice[quotient_state] = quotient_choice
        if discard_unreachable_choices:
            state_to_choice = self.discard_unreachable_choices(state_to_choice)
        return state_to_choice

    def state_to_choice_to_choices(self, state_to_choice):
        num_choices = self.quotient_mdp.nr_choices
        choices = stormpy.BitVector(num_choices,False)
        for choice in state_to_choice:
            if choice is not None and choice < num_choices:
                choices.set(choice,True)
        return choices
    
    def scheduler_selection(self, mdp, scheduler, coloring=None):
        ''' Get hole options involved in the scheduler selection. '''
        assert scheduler.memoryless and scheduler.deterministic
        state_to_choice = self.scheduler_to_state_to_choice(mdp, scheduler)
        choices = self.state_to_choice_to_choices(state_to_choice)
        if coloring is None:
            coloring = self.coloring
        hole_selection = coloring.collectHoleOptions(choices)
        return hole_selection

    
    
    def choice_values(self, mdp, prop, state_values):
        '''
        Get choice values after model checking MDP against a property.
        Value of choice c: s -> s' is computed as
        rew(c) + sum_s' [ P(s,c,s') * mc(s') ], where
        - rew(c) is the reward associated with choice (c)
        - P(s,c,s') is the probability of transitioning from s to s' under action c
        - mc(s') is the model checking result in state s'
        '''

        # multiply probability with model checking results
        choice_values = payntbind.synthesis.multiply_with_vector(mdp.transition_matrix, state_values)
        choice_values = Quotient.make_vector_defined(choice_values)

        # if the associated reward model has state-action rewards, then these must be added to choice values
        if prop.reward:
            reward_name = prop.formula.reward_name
            rm = mdp.reward_models.get(reward_name)
            assert rm.has_state_action_rewards
            choice_rewards = list(rm.state_action_rewards)
            assert mdp.nr_choices == len(choice_rewards)
            for choice in range(mdp.nr_choices):
                choice_values[choice] += choice_rewards[choice]

        return choice_values


    def expected_visits(self, mdp, prop, choices):
        '''
        Compute expected number of visits in the states of DTMC induced by the shoices.
        '''
        if not Quotient.compute_expected_visits:
            return None

        # extract DTMC induced by this MDP-scheduler
        sub_mdp,state_map,_ = self.restrict_mdp(mdp, choices)
        dtmc = Quotient.mdp_to_dtmc(sub_mdp)

        # compute visits
        dtmc_visits = stormpy.compute_expected_number_of_visits(paynt.verification.property.Property.environment, dtmc).get_values()
        dtmc_visits = list(dtmc_visits)

        # handle infinity- and zero-visits
        if prop.minimizing:
            dtmc_visits = Quotient.make_vector_defined(dtmc_visits)
        else:
            dtmc_visits = [ value if value != math.inf else 0 for value in dtmc_visits]

        # map vector of expected visits onto the state space of the quotient MDP
        expected_visits = [0] * mdp.nr_states
        for state in range(dtmc.nr_states):
            mdp_state = state_map[state]
            visits = dtmc_visits[state]
            expected_visits[mdp_state] = visits

        return expected_visits


    def estimate_scheduler_difference(self, mdp, quotient_choice_map, inconsistent_assignments, choice_values, expected_visits=None):
        if expected_visits is None:
            expected_visits = [1] * mdp.nr_states
        hole_variance = payntbind.synthesis.computeInconsistentHoleVariance(
            self.design_space.family, mdp.nondeterministic_choice_indices, quotient_choice_map, choice_values,
            self.coloring, inconsistent_assignments, expected_visits)
        return hole_variance

    
    def scheduler_consistent(self, mdp, prop, result):
        '''
        Get hole assignment induced by this scheduler and fill undefined
        holes by some option from the design space of this mdp.
        :return hole assignment
        :return whether the scheduler is consistent
        '''
        # selection = self.scheduler_selection(mdp, result.scheduler)
        if mdp.is_deterministic:
            selection = [[mdp.design_space.hole_options(hole)[0]] for hole in range(mdp.design_space.num_holes)]
            return selection, None, None, None, True

        # get qualitative scheduler selection, filter inconsistent assignments
        selection = self.scheduler_selection(mdp, result.scheduler)
        inconsistent_assignments = {hole:options for hole,options in enumerate(selection) if len(options) > 1 }
        scheduler_is_consistent = len(inconsistent_assignments) == 0
        choice_values = None
        expected_visits = None
        inconsistent_differences = None
        if not scheduler_is_consistent:
            # extract choice values, compute expected visits and estimate scheduler difference
            choice_values = self.choice_values(mdp.model, prop, result.get_values())
            choices = result.scheduler.compute_action_support(mdp.model.nondeterministic_choice_indices)
            expected_visits = self.expected_visits(mdp.model, prop, choices)
            inconsistent_differences = self.estimate_scheduler_difference(mdp.model, mdp.quotient_choice_map, inconsistent_assignments, choice_values, expected_visits)

        for hole,options in enumerate(selection):
            if len(options) == 0:
                # TODO why is this necessary?
                selection[hole] = [mdp.design_space.hole_options(hole)[0]]

        return selection, choice_values, expected_visits, inconsistent_differences, scheduler_is_consistent

    
    def suboptions_half(self, mdp, splitter):
        ''' Split options of a splitter into two halves. '''
        options = mdp.design_space.hole_options(splitter)
        half = len(options) // 2
        suboptions = [options[:half], options[half:]]
        return suboptions

    def suboptions_unique(self, mdp, splitter, used_options):
        ''' Distribute used options of a splitter into different suboptions. '''
        assert len(used_options) > 1
        suboptions = [[option] for option in used_options]
        index = 0
        for option in mdp.design_space.hole_options(splitter):
            if option in used_options:
                continue
            suboptions[index].append(option)
            index = (index + 1) % len(suboptions)
        return suboptions

    def suboptions_enumerate(self, mdp, splitter, used_options):
        assert len(used_options) > 1
        core_suboptions = [[option] for option in used_options]
        other_suboptions = [option for option in mdp.design_space.hole_options(splitter) if option not in used_options]
        return core_suboptions, other_suboptions

    def holes_with_max_score(self, hole_score):
        max_score = max(hole_score.values())
        with_max_score = [hole_index for hole_index in hole_score if hole_score[hole_index] == max_score]
        return with_max_score

    def most_inconsistent_holes(self, scheduler_assignment):
        num_definitions = [len(options) for options in scheduler_assignment]
        most_inconsistent = self.holes_with_max_score(num_definitions) 
        return most_inconsistent

    def discard(self, mdp, hole_assignments, core_suboptions, other_suboptions, incomplete_search):

        # default result
        reduced_design_space = mdp.design_space.copy()
        if len(other_suboptions) == 0:
            suboptions = core_suboptions
        else:
            suboptions = [other_suboptions] + core_suboptions  # DFS solves core first

        if not incomplete_search:
            return reduced_design_space, suboptions

        # reduce simple holes
        ds_before = reduced_design_space.size

        hole_to_states = [0] * self.design_space.num_holes
        state_to_holes = self.coloring.getStateToHoles().copy()
        for state in range(mdp.model.nr_states):
            quotient_state = mdp.quotient_state_map[state]
            for hole in state_to_holes[quotient_state]:
                hole_to_states[hole] += 1

        for hole in range(reduced_design_space.num_holes):
            if hole_to_states[hole] <= 1:
                reduced_design_space.hole_set_options(hole, hole_assignments[hole])
        ds_after = reduced_design_space.size
        self.discarded += ds_before - ds_after

        # discard other suboptions
        suboptions = core_suboptions
        # self.discarded += (reduced_design_space.size * len(other_suboptions)) / (len(other_suboptions) + len(core_suboptions))

        return reduced_design_space, suboptions


    def split(self, family, incomplete_search):

        mdp = family.mdp
        assert not mdp.is_deterministic

        # split family wrt last undecided result
        result = family.analysis_result.undecided_result()

        hole_assignments = result.primary_selection
        scores = result.primary_scores
        if scores is None:
            scores = {hole:0 for hole in range(mdp.design_space.num_holes) if mdp.design_space.hole_num_options(hole) > 1}
        
        splitters = self.holes_with_max_score(scores)
        splitter = splitters[0]
        if len(hole_assignments[splitter]) > 1:
            core_suboptions,other_suboptions = self.suboptions_enumerate(mdp, splitter, hole_assignments[splitter])
        else:
            assert mdp.design_space.hole_num_options(splitter) > 1
            core_suboptions = self.suboptions_half(mdp, splitter)
            other_suboptions = []
        # print(mdp.design_space[splitter], core_suboptions, other_suboptions)

        new_design_space, suboptions = self.discard(mdp, hole_assignments, core_suboptions, other_suboptions, incomplete_search)
        
        # construct corresponding design subspaces
        design_subspaces = []
        
        family.splitter = splitter
        parent_info = family.collect_parent_info(self.specification)
        for suboption in suboptions:
            subholes = new_design_space.subholes(splitter, suboption)
            design_subspace = paynt.family.family.DesignSpace(subholes, parent_info)
            design_subspace.hole_set_options(splitter, suboption)
            design_subspaces.append(design_subspace)

        return design_subspaces


    def double_check_assignment(self, assignment):
        '''
        Double-check whether this assignment truly improves optimum.
        '''
        dtmc = self.build_assignment(assignment)
        res = dtmc.check_specification(self.specification)
        # opt_result = dtmc.model_check_property(opt_prop)
        if res.constraints_result.sat and self.specification.optimality.improves_optimum(res.optimality_result.value):
            return assignment, res.optimality_result.value
        else:
            return None, None

    
    def sample(self):
        
        # parameters
        path_length = 1000
        num_paths = 100
        output_path = 'samples.txt'

        import json

        # assuming optimization of reward property
        assert len(self.specification.constraints) == 0
        opt = self.specification.optimality
        assert opt.reward
        reward_name = opt.formula.reward_name
        
        # build the mdp
        self.build(self.design_space)
        mdp = self.design_space.mdp
        state_row_group = mdp.prepare_sampling()
        
        paths = []
        for _ in range(num_paths):
            path = mdp.random_path(path_length,state_row_group)
            path_reward = mdp.evaluate_path(path,reward_name)
            paths.append( {"path":path,"reward":path_reward} )

        path_json = [json.dumps(path) for path in paths]
        
        output_json = "[\n" + ",\n".join(path_json) + "\n]\n"

        # logger.debug("attempting to reconstruct samples from JSON ...")
        # json.loads(output_json)
        # logger.debug("OK")
        
        logger.info("writing generated samples to {} ...".format(output_path))
        with open(output_path, 'w') as f:
            print(output_json, end="", file=f)
        logger.info("done")


    def identify_absorbing_states(self, model):
        state_is_absorbing = [True] * model.nr_states
        tm = model.transition_matrix
        for state in range(model.nr_states):
            for choice in tm.get_rows_for_group(state):
                for entry in tm.get_row(choice):
                    if entry.column != state:
                        state_is_absorbing[state] = False
                        break
                if not state_is_absorbing[state]:
                    break
        return state_is_absorbing

    def get_property(self):
        assert self.specification.num_properties == 1, "expecting a single property"
        return self.specification.all_properties()[0]



class DtmcFamilyQuotient(Quotient):
    
    def __init__(self, quotient_mdp, family, coloring, specification):
        super().__init__(quotient_mdp = quotient_mdp, family = family, coloring = coloring, specification = specification)
        self.design_space = paynt.family.family.DesignSpace(family)
