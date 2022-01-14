import stormpy

from ..sketch.property import OptimalityProperty

class PropertyResult:
    def __init__(self, prop, result, value):
        self.property = prop
        self.result = result
        self.value = value
        self.sat = prop.satisfies_threshold(value)
        self.improves = None if not isinstance(prop,OptimalityProperty) else prop.improves_optimum(value)

class ConstraintsResult:
    def __init__(self, results):
        self.results = results
        self.all_sat = True
        for result in results:
            if result is not None and result.sat == False:
                self.all_sat = False
                break

class SpecificationResult:
    def __init__(self, constraints_result, optimality_result):
        self.constraints_result = constraints_result
        self.optimality_result = optimality_result

class MdpPropertyResult:
    def __init__(self, prop, primary, secondary, feasibility):
        self.property = prop
        self.primary = primary
        self.secondary = secondary
        self.feasibility = feasibility

class MdpOptimalityResult(MdpPropertyResult):
    def __init__(self, prop, primary, secondary, optimum, improving_assignment, can_improve):
        super().__init__(prop, primary, secondary, None)
        self.optimum = optimum
        self.improving_assignment = improving_assignment
        self.can_improve = can_improve

class MdpConstraintsResult:
    def __init__(self, results):
        self.results = results

        self.feasibility = True
        for result in results:
            if result is None:
                continue
            if result.feasibility == False:
                self.feasibility = False
                break
            if result.feasibility == None:
                self.feasibility = None

class MarkovChain:

    # options for the construction of chains
    builder_options = None
    # model checking precision
    precision = 1e-5
    # model checking environment (method & precision)
    environment = None

    @classmethod
    def initialize(cls, formulae):
        '''
        Construct builder options wrt formulae of interest.
        Setup model checking environment.
        '''
        # builder options
        cls.builder_options = stormpy.BuilderOptions(formulae)
        cls.builder_options.set_build_with_choice_origins(True)
        cls.builder_options.set_build_state_valuations(True)
        cls.builder_options.set_add_overlapping_guards_label()
    
        # model checking environment
        cls.environment = stormpy.Environment()
        env = cls.environment.solver_environment.minmax_solver_environment
        env.precision = stormpy.Rational(cls.precision)
        cls.set_solver_method(is_dtmc=True)

    @staticmethod
    def build_from_prism(sketch, assignment):
        program = sketch.restrict_prism(assignment)
        model = stormpy.build_sparse_model_with_options(program, MarkovChain.builder_options)
        return model

    @classmethod
    def set_solver_method(cls, is_dtmc):
        if is_dtmc:
            cls.environment.solver_environment.minmax_solver_environment.method = stormpy.MinMaxMethod.policy_iteration
        else:
            cls.environment.solver_environment.minmax_solver_environment.method = stormpy.MinMaxMethod.value_iteration

    def __init__(self, model, quotient_state_map = None, quotient_choice_map = None):
        if model.labeling.contains_label("overlap_guards"):
            assert model.labeling.get_states("overlap_guards").number_of_set_bits() == 0
        self.model = model
        self.quotient_choice_map = quotient_choice_map
        if quotient_choice_map is None:
            self.quotient_choice_map = [c for c in range(model.nr_choices)]
        self.quotient_state_map = quotient_state_map
        if quotient_state_map is None:
            self.quotient_state_map = [s for s in range(model.nr_states)]
    
    @property
    def states(self):
        return self.model.nr_states

    @property
    def choices(self):
        return self.model.nr_choices

    @property
    def is_dtmc(self):
        return self.model.nr_choices == self.model.nr_states

    @property
    def initial_state(self):
        return self.model.initial_states[0]

    def model_check_formula(self, formula):
        self.set_solver_method(self.is_dtmc)
        result = stormpy.model_checking(
            self.model, formula, only_initial_states=False,
            # extract_scheduler=(not self.is_dtmc), environment=self.environment # TODO
            extract_scheduler=True, environment=self.environment
        )
        value = result.at(self.initial_state)
        return result, value

    def model_check_property(self, prop, alt = False):
        formula = prop.formula if not alt else prop.formula_alt
        result,value = self.model_check_formula(formula)
        return PropertyResult(prop, result, value)


class DTMC(MarkovChain):

    def __init__(self, *args):
        super().__init__(*args)

    def check_constraints(self, properties, property_indices = None, short_evaluation = False):
        '''
        Check constraints.
        :param properties a list of all constraints
        :param property_indices a selection of property indices to investigate
        :param short_evaluation if set to True, then evaluation terminates as
          soon as a constraint is not satisfied
        '''

        # implicitly, check all constraints
        if property_indices is None:
            property_indices = [index for index,_ in enumerate(properties)]
        
        # check selected properties
        results = [None for prop in properties]
        for index in property_indices:
            prop = properties[index]
            result = self.model_check_property(prop)
            results[index] = result
            if short_evaluation and not result.sat:
                break

        return ConstraintsResult(results)

    def check_specification(self, specification, property_indices = None, short_evaluation = False):
        constraints_result = self.check_constraints(specification.constraints, property_indices, short_evaluation)
        optimality_result = None
        if not (short_evaluation and not constraints_result.sat) and specification.has_optimality:
            optimality_result = self.model_check_property(specification.optimality)
        return SpecificationResult(constraints_result, optimality_result)



class MDP(MarkovChain):

    def __init__(self, model, design_space, quotient_container, quotient_state_map = None, quotient_choice_map = None):
        super().__init__(model, quotient_state_map, quotient_choice_map)
        self.design_space = design_space
        self.quotient_container = quotient_container

    def check_property(self, prop):
        # check primary direction
        primary = self.model_check_property(prop, alt = False)
        
        # no need to check secondary direction if primary direction yields UNSAT
        if not primary.sat:
            return MdpPropertyResult(prop, primary, None, False)

        # no need to check secondary direction if the primary direction is SAT
        # and the corresponding scheduler is consistent
        # TODO
        if self.is_dtmc:
            return MdpPropertyResult(prop, primary, None, primary.sat)
        
        # primary direction is not sufficient
        secondary = self.model_check_property(prop, alt = True)
        feasibility = True if secondary.sat else None
        return MdpPropertyResult(prop, primary, secondary, feasibility)

    def check_constraints(self, properties, property_indices = None, short_evaluation = False):
        if property_indices is None:
            property_indices = [index for index,_ in enumerate(properties)]

        results = [None for prop in properties]
        for index in property_indices:
            prop = properties[index]
            result = self.check_property(prop)
            results[index] = result
            if short_evaluation and result.feasibility == False:
                break

        return MdpConstraintsResult(results)

    def check_optimality(self, prop):
        # check primary direction
        primary = self.model_check_property(prop, alt = False)
        
        if not primary.improves:
            # OPT <= LB
            return MdpOptimalityResult(prop, primary, None, None, None, False)

        # LB < OPT
        # check if LB is tight
        if self.is_dtmc:
            assignment = [hole.options for hole in self.design_space]
            consistent = True
        else:
            assignment,consistent = self.quotient_container.scheduler_consistent(self, primary.result)
        if consistent:
            # LB is tight and LB < OPT
            hole_options = self.design_space.copy()
            for hole_index,hole in enumerate(hole_options):
                hole.options = assignment[hole_index]
            return MdpOptimalityResult(prop, primary, None, primary.value, hole_options, False)

        # UB might improve the optimum
        secondary = self.model_check_property(prop, alt = True)
        
        if not secondary.improves:
            # LB < OPT < UB
            if not primary.sat:
                # T < LB < OPT < UB
                return MdpOptimalityResult(prop, primary, secondary, None, None, False)
            else:
                # LB < T < OPT < UB
                return MdpOptimalityResult(prop, primary, secondary, None, None, True)

        # LB < UB < OPT
        # this family definitely improves the optimum
        assignment = self.design_space.pick_any()
        if not primary.sat:
            # T < LB < UB < OPT
            return MdpOptimalityResult(prop, primary, secondary, secondary.value, assignment, False)
        else:
            # LB < T, LB < UB < OPT
            return MdpOptimalityResult(prop, primary, secondary, secondary.value, assignment, True)


    def check_specification(self, specification, property_indices = None, short_evaluation = False):
        constraints_result = self.check_constraints(specification.constraints, property_indices, short_evaluation)
        optimality_result = None
        if not (short_evaluation and constraints_result.feasibility == False) and specification.has_optimality:
            optimality_result = self.check_optimality(specification.optimality)
        return SpecificationResult(constraints_result, optimality_result)
