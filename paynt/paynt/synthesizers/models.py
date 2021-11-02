
import stormpy
import stormpy.pomdp
import math
import itertools
from collections import OrderedDict

from .statistic import Statistic

from ..sketch.property import Property
from ..sketch.holes import *

import logging
logger = logging.getLogger(__name__)


class MarkovChain:

    # options for the construction of chains
    builder_options = None
    # model checking precision
    precision = 1e-5
    # model checking environment (method & precision)
    environment = None

    @classmethod
    def initialize(cls, properties, optimality_property):

        # builder options
        mc_formulae = [p.formula for p in properties]
        if optimality_property is not None:
            mc_formulae.append(optimality_property.formula)
        cls.builder_options = stormpy.BuilderOptions(mc_formulae)
        cls.builder_options.set_build_with_choice_origins(True)
        cls.builder_options.set_build_state_valuations(True)
        cls.builder_options.set_add_overlapping_guards_label()
    
        # model checking environment
        cls.environment = stormpy.Environment()
        env = cls.environment.solver_environment.minmax_solver_environment
        env.precision = stormpy.Rational(cls.precision)
        # PI is the default method for DTMCs?
        cls.set_solver_method(stormpy.MinMaxMethod.policy_iteration)

    @classmethod
    def set_solver_method(cls, method):
        cls.environment.solver_environment.minmax_solver_environment.method = method
    
    def __init__(self, sketch):
        self.sketch = sketch

    def build(self, program):
        self.model = stormpy.build_sparse_model_with_options(program, MarkovChain.builder_options)
        assert self.model.labeling.get_states("overlap_guards").number_of_set_bits() == 0

    @property
    def states(self):
        return self.model.nr_states

    @property
    def is_dtmc(self):
        return self.model.nr_choices == self.model.nr_states

    @property
    def initial_state(self):
        return self.model.initial_states[0]

    def at_initial_state(self, array):
        return array.at(self.initial_state)


class DTMC(MarkovChain):

    def __init__(self, sketch, assignment):
        super().__init__(sketch)
        program = sketch.restrict(assignment)
        self.build(program)

    def analyze_property(self, prop):
        ''''
        Model check dtmc against a property
        :return value in the initial state
        '''
        mc_result = stormpy.model_checking(
            self.model, prop.formula, only_initial_states=False,
            extract_scheduler=False, environment=self.environment
        )
        return self.at_initial_state(mc_result)

    def check_property(self, prop):
        ''' Check whether this DTMC satisfies the property. '''
        result = self.analyze_property(prop)
        return prop.satisfies_threshold(result)

    # check multiple properties, return False as soon as any one is violated
    def check_properties(self, properties):
        for p in properties:
            sat = self.check_property(p)
            if not sat:
                return False
        return True

    # check all properties, return unsatisfiable ones
    def check_properties_all(self, properties):
        unsat_properties = []
        for p in properties:
            sat = self.check_property(p)
            if not sat:
                unsat_properties.append(p)
        return unsat_properties

    # model check optimality property, return
    # (1) whether the property was satisfied
    # (2) whether the optimal value was improved
    def check_optimality(self, prop):
        result = self.analyze_property(prop)
        sat = prop.satisfies_threshold(result)
        improves = prop.improves_optimum(result)
        return sat,improves


class MDP(MarkovChain):

    def __init__(self, sketch, design_space, model, quotient_container, quotient_choice_map = None):
        super().__init__(sketch)
        self.design_space = design_space
        self.model = model
        self.quotient_container = quotient_container
        self.quotient_choice_map = quotient_choice_map
        self.design_subspaces = None

    def analyze_property(self, prop, alt = False):
        '''
        Model check MDP against property.
        :param alt if True, alternative direction will be checked
        :return bounds on satisfiability
        '''
        if self.is_dtmc:
            self.set_solver_method(stormpy.MinMaxMethod.policy_iteration)
        else:
            self.set_solver_method(stormpy.MinMaxMethod.value_iteration)
        formula = prop.formula if not alt else prop.formula_alt
        bounds = stormpy.model_checking(
            self.model, formula, only_initial_states=False,
            extract_scheduler=(not self.is_dtmc), environment=self.environment
        )
        return bounds

    def check_property(self, prop):
        '''
        Model check the underlying quotient MDP against a given formula. Return:
        (1) feasibility: SAT = True, UNSAT = False, undecided = None
        (2) bounds on the primary direction
        (3) bounds on the secondary direction (None if not necessary)
        '''

        # check primary direction
        bounds_primary = self.analyze_property(prop)
        result_primary = self.at_initial_state(bounds_primary)
        sat_primary = prop.satisfies_threshold(result_primary)
        if self.is_dtmc:
            return sat_primary, bounds_primary, None

        # no need to check secodary direction if optimizing direction yields UNSAT
        if not sat_primary:
            return False, bounds_primary, None

        # primary direction is not sufficient
        bounds_secondary = self.analyze_property(prop, alt = True)
        result_secondary = self.at_initial_state(bounds_secondary)
        sat_secondary = prop.satisfies_threshold(result_secondary)
        feasible = True if sat_secondary else None
        return feasible, bounds_primary, bounds_secondary

    def check_properties(self, properties):
        ''' check all properties, return
        (1) satisfiability (True/False/None)
        (2) list of undecided properties
        (3) list of bounds for undecided properties
        '''
        undecided_properties = []
        undecided_bounds = []
        for prop in properties:
            feasible,bounds_primary,bounds_secondary = self.check_property(prop)
            if feasible == False:
                return False, None, None
            if feasible == None:
                undecided_properties.append(prop)
                undecided_bounds.append(bounds_primary)
        feasibility = True if undecided_properties == [] else None
        return feasibility, undecided_properties, undecided_bounds

    def check_optimality(self, prop):
        ''' model check optimality property, return
        (1) bounds in primary direction
        (2) new optimal value (or None)
        (3) improving assignment corresponding to (2) (or None)
        (4) whether the optimal value (wrt eps) can still be improved by
            refining the design space
        '''

        # check primary direction
        bounds_primary = self.analyze_property(prop)
        result_primary = self.at_initial_state(bounds_primary)
        opt_primary = prop.improves_optimum(result_primary)
        sat_primary = prop.satisfies_threshold(result_primary)

        if not opt_primary:
            # OPT <= LB
            return bounds_primary, None, None, False

        # LB < OPT
        # check if LB is tight
        assignment,consistent = self.quotient_container.scheduler_consistent(self, bounds_primary.scheduler)
        if consistent:
            # LB is tight and LB < OPT
            return bounds_primary, result_primary, HoleOptions(assignment), False

        # UB might improve the optimum
        bounds_secondary = self.analyze_property(prop, alt = True)
        result_secondary = self.at_initial_state(bounds_secondary)
        opt_secondary = prop.improves_optimum(result_secondary)
        sat_secondary = prop.satisfies_threshold(result_secondary)

        if not opt_secondary:
            # LB < OPT < UB
            if not sat_primary:
                # T < LB < OPT < UB
                return bounds_primary, None, None, False
            else:
                # LB < T < OPT < UB
                return bounds_primary, None, None, True

        # LB < UB < OPT
        # this family definitely improves the optimum
        assignment = self.design_space.pick_any()
        if not sat_primary:
            # T < LB < UB < OPT
            return bounds_primary, result_secondary, assignment, False
        else:
            # LB < T, LB < UB < OPT
            return bounds_primary, result_secondary, assignment, True
        





