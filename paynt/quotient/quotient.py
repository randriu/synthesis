import stormpy
import payntbind

import paynt.family.family
import paynt.models.models

import math
import itertools

import logging
logger = logging.getLogger(__name__)


class Quotient:

    # if True, expected visits will not be computed for hole scoring
    disable_expected_visits = False

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

        # builder options
        self.subsystem_builder_options = stormpy.SubsystemBuilderOptions()
        self.subsystem_builder_options.build_state_mapping = True
        self.subsystem_builder_options.build_action_mapping = True

        # for each choice of the quotient, a list of its state-destinations
        self.choice_destinations = None
        if self.quotient_mdp is not None:
            self.choice_destinations = payntbind.synthesis.computeChoiceDestinations(self.quotient_mdp)


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
    
    def build_from_choice_mask(self, choices):
        mdp,state_map,choice_map = self.restrict_quotient(choices)
        return paynt.models.models.SubMdp(mdp, state_map, choice_map)
    
    def build(self, family):
        ''' Construct the quotient MDP for the family. '''
        # select actions compatible with the family and restrict the quotient
        choices = self.coloring.selectCompatibleChoices(family.family)
        family.mdp = self.build_from_choice_mask(choices)
        family.selected_choices = choices
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
        model = Quotient.mdp_to_dtmc(mdp)
        return paynt.models.models.SubMdp(model,state_map,choice_map)
    
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
    
    def scheduler_selection(self, mdp, scheduler):
        ''' Get hole options involved in the scheduler selection. '''
        assert scheduler.memoryless and scheduler.deterministic
        state_to_choice = self.scheduler_to_state_to_choice(mdp, scheduler)
        choices = self.state_to_choice_to_choices(state_to_choice)
        hole_selection = self.coloring.collectHoleOptions(choices)
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


    def compute_expected_visits(self, mdp, prop, choices):
        '''
        Compute expected number of visits in the states of DTMC induced by the shoices.
        '''
        if Quotient.disable_expected_visits:
            return [1]*self.quotient_mdp.nr_states

        # extract DTMC induced by this MDP-scheduler
        sub_mdp,state_map,_ = self.restrict_mdp(mdp, choices)
        dtmc = Quotient.mdp_to_dtmc(sub_mdp)
        dtmc_visits = paynt.verification.property.Property.compute_expected_visits(dtmc)

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


    def estimate_scheduler_difference(self, mdp, quotient_choice_map, inconsistent_assignments, choice_values, expected_visits):
        hole_variance = payntbind.synthesis.computeInconsistentHoleVariance(
            self.design_space.family, mdp.nondeterministic_choice_indices, quotient_choice_map, choice_values,
            self.coloring, inconsistent_assignments, expected_visits)
        return hole_variance

    
    def scheduler_is_consistent(self, mdp, prop, result):
        '''
        Get hole assignment induced by this scheduler and fill undefined
        holes by some option from the design space of this mdp.
        :return hole assignment
        :return whether the scheduler is consistent
        '''
        if mdp.is_deterministic:
            selection = [[mdp.design_space.hole_options(hole)[0]] for hole in range(mdp.design_space.num_holes)]
            return selection, True

        # get qualitative scheduler selection, filter inconsistent assignments
        selection = self.scheduler_selection(mdp, result.scheduler)
        inconsistent_assignments = {hole:options for hole,options in enumerate(selection) if len(options) > 1 }
        scheduler_is_consistent = len(inconsistent_assignments) == 0
        for hole,options in enumerate(selection):
            if len(options) == 0:
                # if some hole options are not involved in the selection, we can fix an arbitrary value
                selection[hole] = [mdp.design_space.hole_options(hole)[0]]

        return selection, scheduler_is_consistent

    def scheduler_get_quantitative_values(self, mdp, prop, result, selection):
        '''
        :return choice values
        :return expected visits
        :return hole scores
        '''
        inconsistent_assignments = {hole:options for hole,options in enumerate(selection) if len(options) > 1 }
        choice_values = self.choice_values(mdp.model, prop, result.get_values())
        choices = result.scheduler.compute_action_support(mdp.model.nondeterministic_choice_indices)
        expected_visits = self.compute_expected_visits(mdp.model, prop, choices)
        inconsistent_differences = self.estimate_scheduler_difference(mdp.model, mdp.quotient_choice_map, inconsistent_assignments, choice_values, expected_visits)
        return choice_values, expected_visits, inconsistent_differences


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

    def split(self, family):

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

        new_design_space = mdp.design_space.copy()
        if len(other_suboptions) == 0:
            suboptions = core_suboptions
        else:
            suboptions = [other_suboptions] + core_suboptions  # DFS solves core first

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
        res = self.check_specification_for_dtmc(dtmc)
        # opt_result = dtmc.model_check_property(opt_prop)
        if res.constraints_result.sat and self.specification.optimality.improves_optimum(res.optimality_result.value):
            return assignment, res.optimality_result.value
        else:
            return None, None


    def get_property(self):
        assert self.specification.num_properties == 1, "expecting a single property"
        return self.specification.all_properties()[0]

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

    def identify_target_states(self, model, prop):
        target_label = prop.get_target_label()
        return model.labeling.get_states(target_label)


    def check_specification_for_dtmc(self, dtmc, constraint_indices=None, short_evaluation=False):
        
        # check constraints
        if constraint_indices is None:
            constraint_indices = range(len(self.specification.constraints))
        results = [None for _ in self.specification.constraints]
        for index in constraint_indices:
            result = dtmc.model_check_property(self.specification.constraints[index])
            results[index] = result
            if short_evaluation and result.sat is False:
                break
        constraints_result = paynt.verification.property_result.ConstraintsResult(results)

        #check optimality
        optimality_result = None
        if self.specification.has_optimality and not (short_evaluation and constraints_result.sat is False):
            optimality_result = dtmc.model_check_property(self.specification.optimality)

        return paynt.verification.property_result.SpecificationResult(constraints_result, optimality_result)


    def check_specification_for_mdp(self, mdp, constraint_indices=None, double_check=True):
        '''
        Check specification.
        :param specification containing constraints and optimality
        :param constraint_indices a selection of property indices to investigate (default: all)
        :param double_check if True, the new optimum is double-checked
        '''
        # check constraints
        if constraint_indices is None:
            constraint_indices = range(len(self.specification.constraints))
        results = [None for _ in self.specification.constraints]
        for index in constraint_indices:
            constraint = self.specification.constraints[index]
            result = paynt.verification.property_result.MdpPropertyResult(constraint)

            # check primary direction
            result.primary = mdp.model_check_property(constraint)

            # no need to check secondary direction if primary direction yields UNSAT
            if not result.primary.sat:
                result.sat = False
            else:
                # check secondary direction
                result.secondary = mdp.model_check_property(constraint, alt=True)
                if mdp.is_deterministic and result.primary.value != result.secondary.value:
                    logger.warning("WARNING: model is deterministic but min<max")
                if result.secondary.sat:
                    result.sat = True

            # primary direction is SAT
            if result.sat is None:
                # check if the primary scheduler is consistent
                result.primary_selection,consistent = self.scheduler_is_consistent(mdp, constraint, result.primary.result)
                if not consistent:
                    result.primary_choice_values,result.primary_expected_visits,result.primary_scores = \
                        self.scheduler_get_quantitative_values(mdp, constraint, result.primary.result, result.primary_selection)

            results[index] = result
            if result.sat is False:
                break
        constraints_result = paynt.verification.property_result.ConstraintsResult(results)

        # check optimality
        optimality_result = None
        if self.specification.has_optimality and not constraints_result.sat is False:
            opt = self.specification.optimality
            result = paynt.verification.property_result.MdpOptimalityResult(opt)

            # check primary direction
            result.primary = mdp.model_check_property(opt, alt = False)
            if not result.primary.improves_optimum:
                # OPT <= LB
                result.can_improve = False
            else:
                # LB < OPT
                # check if LB is tight
                result.primary_selection,consistent = self.scheduler_is_consistent(mdp, opt, result.primary.result)
                if not consistent:
                    result.primary_choice_values,result.primary_expected_visits,result.primary_scores = \
                        self.scheduler_get_quantitative_values(mdp, opt, result.primary.result, result.primary_selection)                        
                if consistent:
                    # LB is tight and LB < OPT
                    result.improving_assignment = mdp.design_space.assume_options_copy(result.primary_selection)
                    result.can_improve = False
                else:
                    result.can_improve = True
            optimality_result = result

            if optimality_result.improving_assignment is not None and double_check:
                optimality_result.improving_assignment, optimality_result.improving_value = self.double_check_assignment(optimality_result.improving_assignment)
        return paynt.verification.property_result.MdpSpecificationResult(constraints_result, optimality_result)


class DtmcFamilyQuotient(Quotient):
    
    def __init__(self, quotient_mdp, family, coloring, specification):
        super().__init__(quotient_mdp = quotient_mdp, family = family, coloring = coloring, specification = specification)
        self.design_space = paynt.family.family.DesignSpace(family)
