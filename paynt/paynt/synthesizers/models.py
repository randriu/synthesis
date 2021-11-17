import stormpy


class MarkovChain:

    # options for the construction of chains
    builder_options = None
    # model checking precision
    precision = 1e-5
    # model checking environment (method & precision)
    environment = None

    @classmethod
    def initialize(cls, properties, optimality_property):
        '''
        Construct builder options wrt formulae of interest.
        Setup model checking environment.
        '''

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
        cls.set_solver_method(is_dtmc=True)

    @staticmethod
    def build_from_program(sketch, assignment):
        program = sketch.restrict(assignment)
        model = stormpy.build_sparse_model_with_options(program, MarkovChain.builder_options)
        MarkovChain.no_overlapping_guards(model)
        return model

    @classmethod
    def set_solver_method(cls, is_dtmc):
        if is_dtmc:
            cls.environment.solver_environment.minmax_solver_environment.method = stormpy.MinMaxMethod.policy_iteration
        else:
            cls.environment.solver_environment.minmax_solver_environment.method = stormpy.MinMaxMethod.value_iteration

    def __init__(self, model):
        self.model = model
        assert model.labeling.get_states("overlap_guards").number_of_set_bits() == 0
    
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
            extract_scheduler=(not self.is_dtmc), environment=self.environment
        )
        return result

    def model_check_property(self, prop):
        return self.model_check_formula(prop.formula)

    def at_initial_state(self, array):
        return array.at(self.initial_state)


class DTMC(MarkovChain):

    def check_property(self, prop):
        ''' Check whether this DTMC satisfies the property. '''
        result = self.model_check_property(prop)
        value = self.at_initial_state(result)
        return prop.satisfies_threshold(value)

    # check 
    def check_properties(self, properties):
        '''
        Check multiple properties.
        :return False as soon as any one is violated, True otherwise
        ''' 
        for p in properties:
            sat = self.check_property(p)
            if not sat:
                return False
        return True

    def check_properties_all(self, properties):
        '''
        Check all properties.
        :return (1) satisfiability (True/False)
        :return (2) a list of unsatisfiable properties if (1) is False
        '''
        unsat_properties = []
        for p in properties:
            sat = self.check_property(p)
            if not sat:
                unsat_properties.append(p)
        return len(unsat_properties) == 0, unsat_properties

    # model check optimality property, return
    # (1) whether the property was satisfied
    # (2) whether the optimal value was improved
    def check_optimality(self, prop):
        '''
        Model check optimality property.
        :return (1) value of this DTMC
        :return (2) whether (1) improves current optimum
        '''
        result = self.model_check_property(prop)
        value = self.at_initial_state(result)
        improves = prop.improves_optimum(value)
        return value,improves


class MDP(MarkovChain):

    def __init__(self, model, design_space, quotient_container, quotient_choice_map = None):
        super().__init__(model)
        self.design_space = design_space
        self.quotient_container = quotient_container
        self.quotient_choice_map = quotient_choice_map
        if quotient_choice_map is None:
            self.quotient_choice_map = [choice for choice in range(self.model.nr_choices)]
        self.design_subspaces = None

    def model_check_property(self, prop, alt = False):
        '''
        Model check MDP against property.
        :param alt if True, alternative direction will be checked
        :return model checking result
        '''
        return self.model_check_formula(prop.formula if not alt else prop.formula_alt)

    def check_property(self, prop):
        '''
        Model check the underlying quotient MDP against a given formula. Return:
        (1) feasibility: SAT = True, UNSAT = False, undecided = None
        (2) (primary, secondary) model checking result
        '''

        # check primary direction
        result_primary = self.model_check_property(prop)
        value_primary = self.at_initial_state(result_primary)
        sat_primary = prop.satisfies_threshold(value_primary)
        if self.is_dtmc:
            return sat_primary, (result_primary, None)

        # no need to check secondary direction if primary direction yields UNSAT
        if not sat_primary:
            return False, (result_primary, None)

        # primary direction is not sufficient
        result_secondary = self.model_check_property(prop, alt = True)
        value_secondary = self.at_initial_state(result_secondary)
        sat_secondary = prop.satisfies_threshold(value_secondary)
        feasible = True if sat_secondary else None
        return feasible, (result_primary, result_secondary)

    def check_properties(self, properties):
        ''' check all properties, return
        (1) satisfiability (True/False/None)
        (2) list of undecided properties
        (3) for each undecided property, a list (of pairs) of model checking results
        '''
        undecided_properties = []
        undecided_results = []
        for prop in properties:
            feasible,results = self.check_property(prop)
            if feasible == False:
                return False, None, None
            if feasible == None:
                undecided_properties.append(prop)
                undecided_results.append(results)
        feasibility = True if undecided_properties == [] else None
        return feasibility, undecided_properties, undecided_results

    def check_optimality(self, prop):
        ''' model check optimality property, return
        (1) (a pair of) model checking results
        (2) new optimal value (or None)
        (3) improving assignment corresponding to (2) (or None)
        (4) whether the optimal value (wrt eps) can still be improved by
            refining the design space
        '''

        # check primary direction
        result_primary = self.model_check_property(prop)
        value_primary = self.at_initial_state(result_primary)
        opt_primary = prop.improves_optimum(value_primary)
        sat_primary = prop.satisfies_threshold(value_primary)

        if not opt_primary:
            # OPT <= LB
            return (result_primary,None), None, None, False

        # LB < OPT
        # check if LB is tight
        if self.is_dtmc:
            assignment = [hole.options for hole in self.design_space]
            consistent = True
        else:
            assignment,consistent = self.quotient_container.scheduler_consistent(self, result_primary)
        if consistent:
            # LB is tight and LB < OPT
            hole_options = self.design_space.copy()
            for hole_index,hole in enumerate(hole_options):
                hole.options = assignment[hole_index]
            return (result_primary,None), value_primary, hole_options, False

        # UB might improve the optimum
        result_secondary = self.model_check_property(prop, alt = True)
        value_secondary = self.at_initial_state(result_secondary)
        opt_secondary = prop.improves_optimum(value_secondary)
        sat_secondary = prop.satisfies_threshold(value_secondary)

        if not opt_secondary:
            # LB < OPT < UB
            if not sat_primary:
                # T < LB < OPT < UB
                return (result_primary,result_secondary), None, None, False
            else:
                # LB < T < OPT < UB
                return (result_primary,result_secondary), None, None, True

        # LB < UB < OPT
        # this family definitely improves the optimum
        assignment = self.design_space.pick_any()
        if not sat_primary:
            # T < LB < UB < OPT
            return (result_primary,result_secondary), value_secondary, assignment, False
        else:
            # LB < T, LB < UB < OPT
            return (result_primary,result_secondary), value_secondary, assignment, True

