import stormpy

import math
import operator

import logging
logger = logging.getLogger(__name__)

class Property:

    # model checking precision
    mc_precision = 1e-4
    # precision for comparing floats
    float_precision = 1e-10
    
    ''' Wrapper over a stormpy property. '''
    def __init__(self, prop):
        self.property = prop
        rf = prop.raw_formula

        # use comparison type to deduce optimizing direction
        comparison_type = rf.comparison_type
        self.minimizing = comparison_type in [stormpy.ComparisonType.LESS, stormpy.ComparisonType.LEQ]
        self.op = {
            stormpy.ComparisonType.LESS:    operator.lt,
            stormpy.ComparisonType.LEQ:     operator.le,
            stormpy.ComparisonType.GREATER: operator.gt,
            stormpy.ComparisonType.GEQ:     operator.ge
        }[comparison_type]

        # set threshold
        self.threshold = rf.threshold_expr.evaluate_as_double()

        # construct quantitative formula (without bound) for explicit model checking
        # set optimality type
        self.formula = rf.clone()
        self.formula.remove_bound()
        if self.minimizing:
            self.formula.set_optimality_type(stormpy.OptimizationDirection.Minimize)
        else:
            self.formula.set_optimality_type(stormpy.OptimizationDirection.Maximize)
        self.formula_alt = Property.alt_formula(self.formula)
        
    @staticmethod
    def alt_formula(formula):
        '''
        :return formula with the opposite optimality type
        '''
        formula_alt = formula.clone()
        optimality_type = formula.optimality_type
        if optimality_type == stormpy.OptimizationDirection.Minimize:
            optimality_type = stormpy.OptimizationDirection.Maximize
        else:
            optimality_type = stormpy.OptimizationDirection.Minimize
        formula_alt.set_optimality_type(optimality_type)
        return formula_alt

    def __str__(self):
        return str(self.property.raw_formula)

    @property
    def reward(self):
        return self.formula.is_reward_operator

    @property
    def maximizing(self):
        return not self.minimizing

    @staticmethod
    def above_mc_precision(a, b):
        return abs(a-b) > Property.mc_precision

    @staticmethod
    def above_float_precision(a, b):
        return abs(a-b) > Property.float_precision

    def meets_op(self, a, b):
        ''' For constraints, we do not want to distinguish between small differences. '''
        # return not Property.above_float_precision(a,b) or self.op(a,b)
        return self.op(a,b)

    def meets_threshold(self, value):
        return self.meets_op(value, self.threshold)

    def result_valid(self, value):
        return not self.reward or value != math.inf

    def satisfies_threshold(self, value):
        ''' check if DTMC model checking result satisfies the property '''
        return self.result_valid(value) and self.meets_threshold(value)

    @property
    def is_until(self):
        return self.formula.subformula.is_until_formula

    def transform_until_to_eventually(self):
        if not self.is_until:
            return
        logger.info("converting until formula to eventually...")
        formula = stormpy.synthesis.transform_until_to_eventually(self.property.raw_formula)
        prop = stormpy.core.Property("", formula)
        self.__init__(prop)

    @property
    def can_be_improved(self):
        return False



class OptimalityProperty(Property):
    '''
    Optimality property can remember current optimal value and adapt the
    corresponding threshold wrt epsilon.
    '''
    def __init__(self, prop, epsilon = None):
        self.property = prop
        rf = prop.raw_formula

        # use comparison type to deduce optimizing direction
        if rf.optimality_type == stormpy.OptimizationDirection.Minimize:
            self.minimizing = True
            self.op = operator.lt            
            self.threshold = math.inf
        else:
            self.minimizing = False
            self.op = operator.gt
            self.threshold = -math.inf

        # construct quantitative formula (without bound) for explicit model checking
        self.formula = rf.clone()
        self.formula_alt = Property.alt_formula(self.formula)

        # additional optimality stuff
        self.optimum = None
        self.epsilon = epsilon

    def __str__(self):
        eps = f"[eps = {self.epsilon}]" if self.epsilon > 0 else ""
        return f"{str(self.property.raw_formula)} {eps}"

    def reset(self):
        self.optimum = None

    def meets_op(self, a, b):
        ''' For optimality objective, we want to accept improvements above model checking precision. '''
        return b is None or (Property.above_mc_precision(a,b) and self.op(a,b))

    def satisfies_threshold(self, value):
        return self.result_valid(value) and self.meets_op(value, self.threshold)

    def improves_optimum(self, value):
        return self.result_valid(value) and self.meets_op(value, self.optimum)

    def update_optimum(self, optimum):
        # assert self.improves_optimum(optimum)
        #logger.debug(f"New opt = {optimum}.")
        self.optimum = optimum
        if self.minimizing:
            self.threshold = optimum * (1 - self.epsilon)
        else:
            self.threshold = optimum * (1 + self.epsilon)

    def suboptimal_value(self):
        assert self.optimum is not None
        if self.minimizing:
            return self.optimum * (1 + self.mc_precision)
        else:
            return self.optimum * (1 - self.mc_precision)

    def transform_until_to_eventually(self):
        if not self.is_until:
            return
        logger.info("converting until formula to eventually...")
        formula = stormpy.synthesis.transform_until_to_eventually(self.property.raw_formula)
        prop = stormpy.core.Property("", formula)
        self.__init__(prop, self.epsilon)

    @property
    def can_be_improved(self):
        return not( not self.reward and self.minimizing and self.threshold == 0 )



class Specification:
    
    def __init__(self, constraints, optimality):
        self.constraints = constraints
        self.optimality = optimality

    def __str__(self):
        if len(self.constraints) == 0:
            constraints = "none"
        else:
            constraints = ",".join([str(c) for c in self.constraints])
        if self.optimality is None:
            optimality = "none"
        else:
            optimality = str(self.optimality) 
        return f"constraints: {constraints}, optimality objective: {optimality}"

    def reset(self):
        if self.optimality is not None:
            self.optimality.reset()
        
    @property
    def has_optimality(self):
        return self.optimality is not None

    @property
    def num_properties(self):
        return len(self.constraints) + (1 if self.has_optimality else 0)

    @property
    def is_single_property(self):
        return self.num_properties == 1

    def all_constraint_indices(self):
        return [i for i,_ in enumerate(self.constraints)]

    def all_properties(self):
        properties = [c for c in self.constraints]
        if self.has_optimality:
            properties += [self.optimality]
        return properties

    def stormpy_properties(self):
        properties = [c.property for c in self.constraints]
        if self.has_optimality:
            properties += [self.optimality.property]
        return properties

    def stormpy_formulae(self):
        formulae = [c.formula for c in self.constraints]
        if self.has_optimality:
            formulae += [self.optimality.formula]
        return formulae

    def contains_until_properties(self):
        return any([p.is_until for p in self.all_properties()])

    def transform_until_to_eventually(self):
        for p in self.all_properties(): 
            p.transform_until_to_eventually()

    
    def check(self):
        # TODO
        pass

    def can_be_improved(self):
        return any(prop.can_be_improved for prop in self.all_properties())

    @property
    def contains_maximizing_reward_properties(self):
        return any([c.reward and not c.minimizing for c in self.all_properties()])


def construct_reward_property(reward_name, minimizing, target_label):
    direction = "min" if minimizing else "max"
    formula_str = 'R{"' + reward_name + '"}' + '{}=? [F "{}"]'.format(direction, target_label)
    formula = stormpy.parse_properties_without_context(formula_str)[0]
    optimality = OptimalityProperty(formula, 0)
    return optimality

        



class PropertyResult:
    def __init__(self, prop, result, value):
        self.result = result
        self.value = value
        self.sat = prop.satisfies_threshold(value)
        self.improves_optimum = None if not isinstance(prop,OptimalityProperty) else prop.improves_optimum(value)

    def __str__(self):
        return str(self.value)

    def reevaluate(self):
        pass    # left intentionally blank


class ConstraintsResult:
    '''
    A list of property results.
    Note: some results might be None (not evaluated).
    '''
    def __init__(self, results):
        self.results = results

    def __str__(self):
        return ",".join([str(result) for result in self.results])

    @property
    def all_sat(self):
        for result in self.results:
            if result is not None and result.sat == False:
                return False
        return True


class SpecificationResult:
    def __init__(self, constraints_result, optimality_result):
        self.constraints_result = constraints_result
        self.optimality_result = optimality_result

    def __str__(self):
        return str(self.constraints_result) + " : " + str(self.optimality_result)

    def reevaluate(self):
        self.optimality_result.reevaluate()

    def accepting_dtmc(self, specification):
        """
        :return (1) whether specification is satisfied (dtmc is accepting)
        :return (2) new optimal value associated with the accepting dtmc
            (can be None if no optimality)
        """

        if not self.constraints_result.all_sat:
            # constraints not sat
            return False, None

        if self.optimality_result is None:
            # constraints sat and no optimality
            return True, None
        
        if not self.optimality_result.improves_optimum:
            # constraints sat and optimality not sat
            return False, None
        
        # constraints sat and optimality sat
        return True, self.optimality_result.value


    def improving(self, family):
        ''' Interpret MDP specification result. '''

        cr = self.constraints_result
        opt = self.optimality_result

        if cr.feasibility == True:
            # either no constraints or constraints were satisfied
            if opt is not None:
                return opt.improving_assignment, opt.improving_value, opt.can_improve
            else:
                improving_assignment = family.pick_any()
                return improving_assignment, None, False


        if cr.feasibility == False:
            return None,None,False

        # constraints undecided: try to push optimality assignment
        if opt is not None: 
            can_improve = opt.improving_value is None and opt.can_improve
            return opt.improving_assignment, opt.improving_value, can_improve
        else:
            return None, None, True

    def undecided_result(self):
        if self.optimality_result is not None and self.optimality_result.can_improve:
            return self.optimality_result
        return self.constraints_result.results[self.constraints_result.undecided_constraints[0]]
            

class MdpPropertyResult:
    def __init__(self,
        prop, primary, secondary, feasibility,
        primary_selection, primary_choice_values, primary_expected_visits,
        primary_scores
    ):
        self.minimizing = prop.minimizing
        self.primary = primary
        self.secondary = secondary
        self.feasibility = feasibility

        self.primary_selection = primary_selection
        self.primary_choice_values = primary_choice_values
        self.primary_expected_visits = primary_expected_visits
        self.primary_scores = primary_scores

    def __str__(self):
        prim = str(self.primary)
        seco = str(self.secondary)
        if self.minimizing:
            return "{} - {}".format(prim,seco)
        else:
            return "{} - {}".format(seco,prim)
            
class MdpConstraintsResult:
    def __init__(self, results):
        self.results = results
        self.undecided_constraints = [index for index,result in enumerate(results) if result is not None and result.feasibility is None]

        self.feasibility = True
        for result in results:
            if result is None:
                continue
            if result.feasibility == False:
                self.feasibility = False
                break
            if result.feasibility == None:
                self.feasibility = None

    def __str__(self):
        return ",".join([str(result) for result in self.results])

class MdpOptimalityResult(MdpPropertyResult):
    def __init__(self,
        prop, primary, secondary,
        improving_assignment, improving_value, can_improve,
        primary_selection, primary_choice_values, primary_expected_visits,
        primary_scores
    ):
        super().__init__(
            prop, primary, secondary, None,
            primary_selection, primary_choice_values, primary_expected_visits,
            primary_scores)
        self.improving_assignment = improving_assignment
        self.improving_value = improving_value
        self.can_improve = can_improve

    def reevaluate(self):
        pass

