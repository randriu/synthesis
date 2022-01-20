import stormpy

import math
import operator

class Property:
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
        self.formula_alt = Property.alt_formula(self.formula)
        self.formula_str = rf

        # additional optimality stuff
        self.optimum = None
        self.epsilon = epsilon

    def __str__(self):
        return f"{self.formula_str} [eps = {self.epsilon}]"

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
        
    @property
    def has_optimality(self):
        return self.optimality is not None

    def all_constraint_indices(self):
        return [i for i,_ in enumerate(self.constraints)]

    def stormpy_properties(self):
        properties = [c.property for c in self.constraints]
        if self.has_optimality:
            properties += [self.optimality.property]
        return properties

    def stormpy_formulae(self):
        mc_formulae = [c.formula for c in self.constraints]
        if self.has_optimality:
            mc_formulae += [self.optimality.formula]
        return mc_formulae




class PropertyResult:
    def __init__(self, prop, result, value):
        self.property = prop
        self.result = result
        self.value = value
        self.sat = prop.satisfies_threshold(value)
        self.improves_optimum = None if not isinstance(prop,OptimalityProperty) else prop.improves_optimum(value)

    def __str__(self):
        return str(self.value)

class ConstraintsResult:
    '''
    A list of property results.
    Note: some results might be None (not evaluated).
    '''
    def __init__(self, results):
        self.results = results
        self.all_sat = True
        for result in results:
            if result is not None and result.sat == False:
                self.all_sat = False
                break

    def __str__(self):
        return ",".join([str(result) for result in self.results])

class SpecificationResult:
    def __init__(self, constraints_result, optimality_result):
        self.constraints_result = constraints_result
        self.optimality_result = optimality_result

    def __str__(self):
        return str(self.constraints_result) + " : " + str(self.optimality_result)

class MdpPropertyResult:
    def __init__(self, prop, primary, secondary, feasibility):
        self.property = prop
        self.primary = primary
        self.secondary = secondary
        self.feasibility = feasibility

    def __str__(self):
        prim = str(self.primary)
        seco = str(self.secondary)
        if self.property.minimizing:
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

class MdpOptimalityResult(MdpPropertyResult):
    def __init__(self, prop, primary, secondary, optimum, improving_assignment, can_improve):
        super().__init__(prop, primary, secondary, None)
        self.optimum = optimum
        self.improving_assignment = improving_assignment
        self.can_improve = can_improve

    def __str__(self):
        return ",".join([str(result) for result in self.results])

