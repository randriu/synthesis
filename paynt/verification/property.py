import stormpy
import payntbind
import math
import operator

import logging
logger = logging.getLogger(__name__)


def construct_property(prop, relative_error, use_exact=False):
    rf = prop.raw_formula
    player_index = None
    if rf.is_reward_operator and use_exact:
        raise ValueError("exact synthesis is not supported for reward properties")
    
    if not (rf.is_reward_operator or rf.is_probability_operator) and rf.is_game_formula:
        if use_exact:
            raise ValueError("exact synthesis is not supported for game properties")
        
        player_index = extract_player_index(rf)
        game_rf = rf
        rf = rf.subformula
        prop = stormpy.core.Property("", rf)
    assert rf.has_bound != rf.has_optimality_type, \
        "optimizing formula contains a bound or a comparison formula does not"
    if rf.has_bound:
        prop = Property(prop, use_exact)
    else:
        prop = OptimalityProperty(prop, relative_error, use_exact)

    if player_index is not None:
        prop.game_optimizing_player = player_index
        prop.game_formula = game_rf
        alt_formula_str = f"<<{prop.game_optimizing_player}>> " + prop.formula_alt.__str__()
        formulas = stormpy.parse_properties(alt_formula_str)
        prop.game_formula_alt = formulas[0].raw_formula

    return prop

def extract_player_index(formula):
    # TODO add support for multiple players in coalition
    string = formula.__str__()
    l_idx = string.index('<<')
    r_idx = string.index('>>')
    player_num = string[l_idx + len('<<') : r_idx]
    return int(player_num)

def construct_reward_property(reward_name, minimizing, target_label):
    direction = "min" if minimizing else "max"
    formula_str = 'R{"' + reward_name + '"}' + '{}=? [F "{}"]'.format(direction, target_label)
    formula = stormpy.parse_properties_without_context(formula_str)[0]
    optimality = OptimalityProperty(formula, 0)
    return optimality

class Property:
    ''' Wrapper over a stormpy property. '''

    # model checking environment (method & precision)
    environment = None
    # model checking precision
    model_checking_precision = 1e-4

    @classmethod
    def set_model_checking_precision(cls, precision):
        cls.model_checking_precision = precision
        payntbind.synthesis.set_precision_native(cls.environment.solver_environment.native_solver_environment, precision)
        payntbind.synthesis.set_precision_minmax(cls.environment.solver_environment.minmax_solver_environment, precision)

    @classmethod
    def initialize(cls, use_exact=False):
        cls.environment = stormpy.Environment()
        cls.set_model_checking_precision(cls.model_checking_precision)

        se = cls.environment.solver_environment
        # se.set_linear_equation_solver_type(stormpy.EquationSolverType.native)
        # se.set_linear_equation_solver_type(stormpy.EquationSolverType.gmmxx)
        se.set_linear_equation_solver_type(stormpy.EquationSolverType.eigen)

        if use_exact:
            se.minmax_solver_environment.method = stormpy.MinMaxMethod.policy_iteration
        else:
            se.minmax_solver_environment.method = stormpy.MinMaxMethod.optimistic_value_iteration

    @classmethod
    def model_check(cls, model, formula):
        return stormpy.model_checking(model, formula, extract_scheduler=True, environment=cls.environment)

    @classmethod
    def compute_expected_visits(cls, model):
        result = stormpy.compute_expected_number_of_visits(cls.environment, model)
        values = list(result.get_values())
        return values

    @staticmethod
    def above_model_checking_precision(a, b):
        if isinstance(a, stormpy.Rational):
            return True
        return abs(a-b) > Property.model_checking_precision


    def __init__(self, prop, use_exact=False):
        self.property = prop
        rf = prop.raw_formula

        self.game_optimizing_player = None # player index for game properties
        self.game_formula = None

        self.use_exact = use_exact

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
        if use_exact:
            self.threshold = rf.threshold_expr.evaluate_as_rational()
            self.threshold_plus_precision = self.threshold
        else:
            self.threshold = rf.threshold_expr.evaluate_as_double()
            if self.minimizing:
                self.threshold_plus_precision = self.threshold + Property.model_checking_precision
            else:
                self.threshold_plus_precision = self.threshold - Property.model_checking_precision

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
    def is_discounted_reward(self):
        # TODO add discounted reward as a type to Stormpy formula
        # return self.formula.is_reward_operator and self.formula.subformula.is_discounted_total_reward_formula
        return self.formula.is_reward_operator and "discount" in str(self.formula.subformula)

    @property
    def maximizing(self):
        return not self.minimizing

    @property
    def is_until(self):
        return self.formula.subformula.is_until_formula

    @property
    def has_game_formula(self):
        return self.game_formula is not None

    def transform_until_to_eventually(self):
        if not self.is_until:
            return
        logger.info("converting until formula to eventually...")
        formula = payntbind.synthesis.transform_until_to_eventually(self.property.raw_formula)
        prop = stormpy.core.Property("", formula)
        self.__init__(prop, self.use_exact)

    def property_copy(self):
        return stormpy.core.Property("", self.property.raw_formula.clone())

    def copy(self):
        return Property(self.property_copy())

    def result_valid(self, value):
        return not self.reward or value != math.inf

    def satisfies_threshold(self, value):
        return self.result_valid(value) and self.op(value, self.threshold)

    def satisfies_threshold_within_precision(self, value):
        return self.result_valid(value) and self.op(value, self.threshold_plus_precision)

    @property
    def can_be_improved(self):
        return False

    def negate(self):
        negated_formula = self.property.raw_formula.clone()
        negated_formula.comparison_type = {
            stormpy.ComparisonType.LESS:    stormpy.ComparisonType.GEQ,
            stormpy.ComparisonType.LEQ:     stormpy.ComparisonType.GREATER,
            stormpy.ComparisonType.GREATER: stormpy.ComparisonType.LEQ,
            stormpy.ComparisonType.GEQ:     stormpy.ComparisonType.LESS
        }[negated_formula.comparison_type]
        stormpy_property_negated = stormpy.core.Property("", negated_formula)
        property_negated = Property(stormpy_property_negated)
        return property_negated

    def get_target_label(self):
        target = self.formula.subformula.subformula
        if isinstance(target, stormpy.logic.AtomicLabelFormula):
            target_label = target.label
        elif isinstance(target, stormpy.logic.AtomicExpressionFormula):
            target_label = str(target)
        else:
            raise ValueError(f"unknown type of target expression {str(target)}, expected atomic label or atomic expression")
        return target_label

    def get_reward_name(self):
        assert self.reward
        return self.formula.reward_name

    def transform_to_optimality_formula(self, prism):
        direction = "min" if self.minimizing else "max"
        if self.reward:
            if isinstance(self.formula.subformula.subformula, stormpy.logic.AtomicLabelFormula):
                formula_str = f"R{{\"{self.get_reward_name()}\"}}{direction}=? [F \"{self.get_target_label()}\"]"
            else:
                formula_str = f"R{{\"{self.get_reward_name()}\"}}{direction}=? [F {self.get_target_label()}]"
        else:
            if isinstance(self.formula.subformula.subformula, stormpy.logic.AtomicLabelFormula):
                formula_str = f"P{direction}=? [F \"{self.get_target_label()}\"]"
            else:
                formula_str = f"P{direction}=? [F {self.get_target_label()}]"
        formula = stormpy.parse_properties_for_prism_program(formula_str, prism)[0]
        return formula



class OptimalityProperty(Property):
    '''
    Optimality property can remember current optimal value and adapt the
    corresponding threshold wrt epsilon.
    '''
    def __init__(self, prop, epsilon=0, use_exact=False):
        self.property = prop
        rf = prop.raw_formula

        self.game_optimizing_player = None # player index for game properties
        self.game_formula = None

        self.use_exact = use_exact

        # use comparison type to deduce optimizing direction
        if rf.optimality_type == stormpy.OptimizationDirection.Minimize:
            self.minimizing = True
            self.op = operator.lt
        else:
            self.minimizing = False
            self.op = operator.gt

        # construct quantitative formula (without bound) for explicit model checking
        self.formula = rf.clone()
        self.formula_alt = Property.alt_formula(self.formula)

        # additional optimality stuff
        self.optimum = None
        if use_exact:
            self.epsilon = stormpy.Rational(epsilon)
        else:
            self.epsilon = epsilon

        self.reset()


    def __str__(self):
        eps = f"[eps = {self.epsilon}]" if self.epsilon > 0 else ""
        return f"{str(self.formula)} {eps}"

    def copy(self):
        return OptimalityProperty(self.property_copy(), self.epsilon)

    def reset(self):
        self.optimum = None
        if self.minimizing:
            if self.use_exact:
                self.threshold = stormpy.Rational(2) # TODO: does not work for rewards
            else:
                self.threshold = math.inf
        else:
            if self.use_exact:
                self.threshold = stormpy.Rational(-1) # TODO: does not work for rewards
            else:
                self.threshold = -math.inf

    def meets_op(self, a, b):
        ''' For optimality objective, we want to accept improvements above model checking precision. '''
        return b is None or (Property.above_model_checking_precision(a,b) and self.op(a,b))

    def satisfies_threshold(self, value):
        return self.result_valid(value) and self.meets_op(value, self.threshold)

    def improves_optimum(self, value):
        return self.result_valid(value) and self.meets_op(value, self.optimum)

    def update_optimum(self, optimum):
        self.optimum = optimum
        if self.minimizing:
            self.threshold = optimum * (1 - self.epsilon)
        else:
            self.threshold = optimum * (1 + self.epsilon)

    def suboptimal_value(self):
        assert self.optimum is not None
        if self.minimizing:
            return self.optimum * (1 + self.model_checking_precision)
        else:
            return self.optimum * (1 - self.model_checking_precision)

    def transform_until_to_eventually(self):
        if not self.is_until:
            return
        logger.info("converting until formula to eventually...")
        formula = payntbind.synthesis.transform_until_to_eventually(self.property.raw_formula)
        prop = stormpy.core.Property("", formula)
        self.__init__(prop, self.epsilon, self.use_exact)

    @property
    def can_be_improved(self):
        return not( not self.reward and self.minimizing and self.threshold == 0 )

    def negate(self):
        negated_formula = self.property.raw_formula.clone()
        negate_optimality_type = {
            stormpy.OptimizationDirection.Minimize:    stormpy.OptimizationDirection.Maximize,
            stormpy.OptimizationDirection.Maximize:    stormpy.OptimizationDirection.Minimize
        }[negated_formula.optimality_type]
        negated_formula.set_optimality_type(negate_optimality_type)
        stormpy_property_negated = stormpy.core.Property("", negated_formula)
        property_negated = OptimalityProperty(stormpy_property_negated,self.epsilon)
        return property_negated


class Specification:

    def __init__(self, properties):
        self.constraints = []
        self.optimality = None

        # sort the properties
        optimalities = []
        for p in properties:
            if type(p) == Property:
                self.constraints.append(p)
            if type(p) == OptimalityProperty:
                optimalities.append(p)
        assert len(optimalities) <=1, "multiple optimality objectives were specified"
        if optimalities:
            self.optimality = optimalities[0]

    def __str__(self):
        s = ""
        if self.constraints:
            s += "constraints: " + ",".join([str(c) for c in self.constraints]) + "; "
        if self.optimality is not None:
            s += "optimality: " + str(self.optimality)
        return s

    def copy(self):
        properties = [p.copy() for p in self.all_properties()]
        return Specification(properties)

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

    def all_properties(self):
        properties = [c for c in self.constraints]
        if self.has_optimality:
            properties += [self.optimality]
        return properties

    def all_constraint_indices(self):
        return range(len(self.constraints))

    def stormpy_properties(self):
        return [p.property for p in self.all_properties()]

    def stormpy_formulae(self):
        return [p.formula for p in self.all_properties()]

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

    def negate(self):
        properties_negated = [p.negate() for p in self.all_properties()]
        return Specification(properties_negated)

