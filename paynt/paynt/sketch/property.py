import stormpy

import math
import operator

class Property:
    ''' Wrapper over a formula. '''
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
        # formula is qualitative and does not have optimality type
        self.formula = rf.clone()
        self.formula.remove_bound()
        if self.minimizing:
            self.formula.set_optimality_type(stormpy.OptimizationDirection.Minimize)
        else:
            self.formula.set_optimality_type(stormpy.OptimizationDirection.Maximize)
        self.formula_alt = self.alt_formula(self.formula)
        self.formula_str = rf
        
    @classmethod
    def alt_formula(cls, formula):
        ''' Construct alternative quantitative formula to use in AR. '''
        formula_alt = formula.clone()
        optimality_type = formula.optimality_type
        # negate optimality type
        if optimality_type == stormpy.OptimizationDirection.Minimize:
            optimality_type = stormpy.OptimizationDirection.Maximize
        else:
            optimality_type = stormpy.OptimizationDirection.Minimize
        formula_alt.set_optimality_type(optimality_type)
        return formula_alt

    def __str__(self):
        return str(self.formula_str)

    @property
    def reward(self):
        return self.formula.is_reward_operator

    def meets_threshold(self, result):
        return self.op(result, self.threshold)

    def result_valid(self, result):
        return not self.reward or result != math.inf

    def satisfies_threshold(self, result):
        ''' check if DTMC model checking result satisfies the property '''
        return self.result_valid(result) and self.meets_threshold(result)


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
        self.formula_alt = self.alt_formula(self.formula)
        self.formula_str = rf

        # additional optimality stuff
        self.optimum = None
        self.epsilon = epsilon

    def satisfies_threshold(self, result):
        if not self.result_valid(result):
            return False
        if self.threshold is None:
            return True
        return self.meets_threshold(result)

    def improves_optimum(self, result):
        if not self.result_valid(result):
            return False
        if self.optimum is None:
            return True
        return self.op(result, self.optimum)

    def update_optimum(self, optimum):
        self.optimum = optimum
        if self.minimizing:
            self.threshold = optimum * (1 - self.epsilon)
        else:
            self.threshold = optimum * (1 + self.epsilon)


        
        