import stormpy

import math
import operator

import logging
logger = logging.getLogger(__name__)


def construct_reward_property(reward_name, minimizing, target_label):
    direction = "min" if minimizing else "max"
    formula_str = 'R{"' + reward_name + '"}' + '{}=? [F "{}"]'.format(direction, target_label)
    formula = stormpy.parse_properties_without_context(formula_str)[0]
    optimality = OptimalityProperty(formula, 0)
    return optimality


class Property:

    # model checking precision
    mc_precision = 1e-4
    # precision for comparing floats
    float_precision = 1e-10
    
    ''' Wrapper over a stormpy property. '''
    def __init__(self, prop, discount_factor=1):
        self.property = prop
        self.discount_factor = discount_factor
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
        self.__init__(prop, self.discount_factor)

    @property
    def can_be_improved(self):
        return False



class OptimalityProperty(Property):
    '''
    Optimality property can remember current optimal value and adapt the
    corresponding threshold wrt epsilon.
    '''
    def __init__(self, prop, discount_factor=1, epsilon=0):
        self.property = prop
        self.discount_factor = discount_factor
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
        self.__init__(prop, self.discount_factor, self.epsilon)

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



