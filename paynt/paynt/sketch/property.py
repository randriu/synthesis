import stormpy

import math
import operator

class Property:
    '''
    Wrapper over a formula.
    Optimality property remembers current optimal value and adapts the
    corresponding threshold wrt epsilon.
    '''
    def __init__(self, prop, epsilon = None):
        self.property = prop
        rf = prop.raw_formula

        # to process model checking results
        self.comparison_type = None
        self.op = None
        self.threshold = None

        # for optimality formula
        self.optimality = rf.has_optimality_type
        self.optimal_value = None
        self.epsilon = epsilon
        
        # formulae for model checking
        self.formula = None
        self.formula_alt = None

        # set comparison type
        self.comparison_type = rf.comparison_type
        if self.optimality:
            if rf.optimality_type == stormpy.OptimizationDirection.Minimize:
                self.comparison_type = stormpy.ComparisonType.LESS 
            else:
                self.comparison_type = stormpy.ComparisonType.GREATER
        
        # set operator according to comparison type
        self.op = {
            stormpy.ComparisonType.LESS:    operator.lt,
            stormpy.ComparisonType.LEQ:     operator.le,
            stormpy.ComparisonType.GREATER: operator.gt,
            stormpy.ComparisonType.GEQ:     operator.ge
        }[self.comparison_type]

        # set threshold
        if self.optimality:
            if self.minimizing:
                self.threshold = math.inf
            else:
                self.threshold = -math.inf
        else:
            self.threshold = rf.threshold_expr.evaluate_as_double()

        # construct quantitative formula (without bound) for explicit model checking
        self.formula = rf.clone()
        if not self.optimality:
            # formula is qualitative and does not have optimality type
            self.formula.remove_bound()
            if self.minimizing:
                self.formula.set_optimality_type(stormpy.OptimizationDirection.Minimize)
            else:
                self.formula.set_optimality_type(stormpy.OptimizationDirection.Maximize)

        # construct alternative quantitative formula (used in AR)
        self.formula_alt = self.formula.clone()
        if self.minimizing:
            self.formula_alt.set_optimality_type(stormpy.OptimizationDirection.Maximize)
        else:
            self.formula_alt.set_optimality_type(stormpy.OptimizationDirection.Minimize)

        # qualitatitve formula to print constraints
        self.formula_str = self.formula
        if not self.optimality:
            self.formula_str = rf

    def __str__(self):
        return str(self.formula_str)

    @property
    def minimizing(self):
        return self.comparison_type in [stormpy.ComparisonType.LESS, stormpy.ComparisonType.LEQ]

    @property
    def reward(self):
        return self.formula.is_reward_operator

    def result_valid(self, result):
        ''' :return true if model checking result is valid '''
        # reward properties can be satisfied only when result is finite
        return not self.reward or result != math.inf

    def meets_threshold(self, result):
        ''' check if model checking result meets threshold wrt operator '''
        # precision_multiplier = 1.0000000001
        # if self.minimizing:
        #     result /= precision_multiplier
        # else:
        #     result *= precision_multiplier
        return self.op(result, self.threshold)

    def satisfied(self, result):
        ''' check if model checking result satisfies the property '''
        return self.result_valid(result) and self.meets_threshold(result)

    def update_optimum(self, new_value):
        '''
        update current optimum (as well as the threshold) if the new value is better
        : return True if update took place
        '''
        if not self.result_valid(new_value):
            return False
        if self.optimal_value is not None and not self.op(new_value, self.optimal_value):
            return False

        # optimal value improved
        self.optimal_value = new_value
        if self.minimizing:
            self.threshold = new_value * (1 - self.epsilon)
        else:
            self.threshold = new_value * (1 + self.epsilon)
        return True

    def decided(self, lower_bound, upper_bound):
        '''
        process MDP model checking results
        :return
          True if both bounds meet the treshold (all SAT)
          False if neither meet the threshold (all UNSAT)
          None otherwise (undecided)
        '''
        lb_ok = self.meets_threshold(lower_bound)
        ub_ok = self.meets_threshold(upper_bound)
        if lb_ok != ub_ok:
            return None
        return lb_ok
