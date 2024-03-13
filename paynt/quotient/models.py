import stormpy

from paynt.verification.property import *
from paynt.verification.property_result import *

import logging
logger = logging.getLogger(__name__)

class MarkovChain:

    # options for the construction of chains
    builder_options = None

    @classmethod
    def initialize(cls, specification):
        # builder options
        formulae = specification.stormpy_formulae()
        cls.builder_options = stormpy.BuilderOptions(formulae)
        cls.builder_options.set_build_with_choice_origins(True)
        cls.builder_options.set_build_state_valuations(True)
        cls.builder_options.set_add_overlapping_guards_label()
        cls.builder_options.set_build_observation_valuations(True)
        # cls.builder_options.set_exploration_checks(True)

    @classmethod
    def assert_no_overlapping_guards(cls, model):
        if model.labeling.contains_label("overlap_guards"):
            assert model.labeling.get_states("overlap_guards").number_of_set_bits() == 0
    
    @classmethod
    def from_prism(cls, prism):
        assert prism.model_type in [stormpy.storage.PrismModelType.MDP, stormpy.storage.PrismModelType.POMDP]
        # TODO why do we disable choice labels here?
        MarkovChain.builder_options.set_build_choice_labels(True)
        model = stormpy.build_sparse_model_with_options(prism, MarkovChain.builder_options)
        MarkovChain.builder_options.set_build_choice_labels(False)
        # MarkovChain.assert_no_overlapping_guards(model)
        return model

    
    def __init__(self, model, quotient_container, quotient_state_map, quotient_choice_map):
        # MarkovChain.assert_no_overlapping_guards(model)
        if len(model.initial_states) > 1:
            logger.warning("WARNING: obtained model with multiple initial states")
        
        self.model = model
        self.quotient_container = quotient_container
        self.quotient_choice_map = quotient_choice_map
        self.quotient_state_map = quotient_state_map

    @property
    def states(self):
        return self.model.nr_states

    @property
    def choices(self):
        return self.model.nr_choices

    @property
    def is_deterministic(self):
        return self.model.nr_choices == self.model.nr_states

    @property
    def initial_state(self):
        return self.model.initial_states[0]

    def model_check_formula(self, formula):
        return stormpy.model_checking(
            self.model, formula, extract_scheduler=True, environment=Property.environment
        )

    def model_check_property(self, prop, alt=False):
        formula = prop.formula if not alt else prop.formula_alt
        result = self.model_check_formula(formula)
        value = result.at(self.initial_state)
        return PropertyResult(prop, result, value)

    
    def check_constraint(self, constraint):
        ''' to be overridden '''
        return None

    def check_optimality(self, optimality):
        ''' to be overridden '''
        return None

    def check_double_optimality(self, optimality):
        ''' to be overridden '''
        return self.check_optimality(optimality)

    def check_constraints(self, constraints, constraint_indices, short_evaluation):
        results = [None for constraint in constraints]
        if constraint_indices is None:
            constraint_indices = range(len(constraints))
        for index in constraint_indices:
            constraint = constraints[index]
            result = self.check_constraint(constraint)
            results[index] = result
            if short_evaluation and result.sat == False:
                break
        return ConstraintsResult(results)

    def check_specification(self, specification, constraint_indices=None, short_evaluation=False):
        '''
        Check specification.
        :param specification containing constraints and optimality
        :param constraint_indices a selection of property indices to investigate (default: all)
        :param short_evaluation if set to True, then evaluation terminates as soon as one constraint violated
        '''
        constraints_result = self.check_constraints(specification.constraints, constraint_indices, short_evaluation)
        optimality_result = None
        if specification.has_optimality and not (short_evaluation and constraints_result.sat == False):
            if not specification.has_double_optimality:
                optimality_result = self.check_optimality(specification.optimality)
            else:
                optimality_result = self.check_double_optimality(specification.optimality)
        return constraints_result, optimality_result


class DTMC(MarkovChain):

    def check_constraint(self, constraint):
        return self.model_check_property(constraint)

    def check_optimality(self, optimality):
        return self.model_check_property(optimality)

    def check_specification(self, specification, constraint_indices=None, short_evaluation=False):
        constraints_result, optimality_result = super().check_specification(specification,constraint_indices,short_evaluation)
        return SpecificationResult(constraints_result, optimality_result)


class MDP(MarkovChain):

    # if True, the secondary direction will be explored when primary is not enough
    compute_secondary_direction = False

    def __init__(self, model, quotient_container, quotient_state_map, quotient_choice_map, design_space):
        super().__init__(model, quotient_container, quotient_state_map, quotient_choice_map)

        self.design_space = design_space
        self.analysis_hints = None
        self.quotient_to_restricted_action_map = None


    def check_constraint(self, prop):

        result = MdpPropertyResult(prop)

        # check primary direction
        result.primary = self.model_check_property(prop, alt = False)
        
        # no need to check secondary direction if primary direction yields UNSAT
        if not result.primary.sat:
            result.sat = False
            return result

        # primary direction is SAT
        # check if the primary scheduler is consistent
        result.primary_selection,result.primary_choice_values,result.primary_expected_visits,result.primary_scores,consistent = \
            self.quotient_container.scheduler_consistent(self, prop, result.primary.result)

        # regardless of whether it is consistent or not, we compute secondary direction to show that all SAT
        result.secondary = self.model_check_property(prop, alt = True)
        if self.is_deterministic and result.primary.value != result.secondary.value:
            logger.warning("WARNING: model is deterministic but min<max")

        if result.secondary.sat:
            result.sat = True
        return result



    def check_optimality(self, prop):
        result = MdpOptimalityResult(prop)

        # check primary direction
        result.primary = self.model_check_property(prop, alt = False)
        if not result.primary.improves_optimum:
            # OPT <= LB
            result.can_improve = False
            return result

        # LB < OPT
        # check if LB is tight
        result.primary_selection,result.primary_choice_values,result.primary_expected_visits,result.primary_scores,consistent = self.quotient_container.scheduler_consistent(self, prop, result.primary.result)
        if consistent:
            # LB is tight and LB < OPT
            result.improving_assignment = self.design_space.assume_options_copy(result.primary_selection)
            result.can_improve = False
            return result

        if not MDP.compute_secondary_direction:
            result.can_improve = True
            return result

        # UB might improve the optimum
        result.secondary = self.model_check_property(prop, alt = True)

        if not result.secondary.improves_optimum:
            # LB < OPT < UB :  T < LB < OPT < UB (can improve) or LB < T < OPT < UB (cannot improve)
            result.can_improve = result.primary.sat
            return result

        # LB < UB < OPT
        # this family definitely improves the optimum
        result.improving_assignment = self.design_space.pick_any()
        # either LB < T, LB < UB < OPT (can improve) or T < LB < UB < OPT (cannot improve)
        result.can_improve = result.primary.sat
        return result



    def check_specification(self, specification, constraint_indices = None, short_evaluation = False, double_check = True):
        constraints_result, optimality_result = super().check_specification(specification,constraint_indices,short_evaluation)
        if optimality_result is not None and optimality_result.improving_assignment is not None and double_check:
            optimality_result.improving_assignment, optimality_result.improving_value = self.quotient_container.double_check_assignment(optimality_result.improving_assignment)
            # print(optimality_result.improving_assignment, optimality_result.improving_value)
        return MdpSpecificationResult(constraints_result, optimality_result)
