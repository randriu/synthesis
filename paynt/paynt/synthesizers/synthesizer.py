
import stormpy
from ..jani.quotient_container import Engine
from ..model_handling.mdp_handling import ModelHandling
from .statistic import Statistic

import math
import operator
from collections import OrderedDict

import logging
logger = logging.getLogger(__name__)




class Formula:
    def __init__(self, prop, epsilon = None):
        self.property = prop
        self.formula = prop.raw_formula.clone()
        self.optimality = self.formula.has_optimality_type
        
        if self.optimality:
            # optimality criterion
            if self.minimizing:
                self.threshold = math.inf
                self.op = operator.lt
            else:
                self.threshold = -math.inf
                self.op = operator.gt
            self.epsilon = epsilon
            self.optimal_value = None
        else:
            # constraint
            comparison_type = self.formula.comparison_type
            self.formula.remove_bound()
            self.threshold = self.formula.threshold_expr.evaluate_as_double()
            self.op = {
                stormpy.ComparisonType.LESS: operator.lt,
                stormpy.ComparisonType.LEQ: operator.le,
                stormpy.ComparisonType.GREATER: operator.gt,
                stormpy.ComparisonType.GEQ: operator.ge
            }[comparison_type]
            self.formula_alt = self.formula.clone()
            if comparison_type in [stormpy.ComparisonType.LESS, stormpy.ComparisonType.LEQ]:
                self.formula.set_optimality_type(stormpy.OptimizationDirection.Minimize)
            else:
                assert comparison_type in [stormpy.ComparisonType.GREATER, stormpy.ComparisonType.GEQ]
                self.formula.set_optimality_type(stormpy.OptimizationDirection.Maximize)

        self.formula_alt = self.formula.clone()
        if self.minimizing:
            self.formula_alt.set_optimality_type(stormpy.OptimizationDirection.Maximize)
        else:
            self.formula_alt.set_optimality_type(stormpy.OptimizationDirection.Minimize)

    def __str__(self):
        return str(self.formula)

    @property
    def minimizing(self):
        return self.formula.optimality_type == stormpy.OptimizationDirection.Minimize

    def satisfied(self, result):
        return self.op(result, self.threshold)

    def improve_threshold(self, optimal_value):
        assert self.optimality
        logger.info(f"New optimal value: {optimal_value}")
        self.optimal_value = optimal_value
        if self.minimizing:
            self.threshold = optimal_value * (1 - self.epsilon)
        else:
            self.threshold = optimal_value * (1 + self.epsilon)


class DTMC:

    def __init__(self, sketch, assignment):
        constants = [sketch.jani.get_constant(c).expression_variable for c in sketch.design_space.keys()]
        substitution = dict(zip(constants, assignment))
        instance = sketch.jani.define_constants(substitution)

        self.mh = ModelHandling()
        self.formulae = [f.formula for f in sketch.formulae]
        self.formulae_alt = [f.formula_alt for f in sketch.formulae]
        if sketch.optimality_formula is not None:
            self.formulae.append(sketch.optimality_formula.formula)
            self.formulae_alt.append(sketch.optimality_formula.formula_alt)
        self.mh.build_model(instance, self.formulae, self.formulae_alt)

        # logger.debug(f"TODO built dtmc")

    @property
    def states(self):
        return self.mh.full_mdp.nr_states

    def model_check(self, formula_index):
        mc_result = self.mh.mc_model(index=formula_index).result
        return mc_result.at(self.mh.full_mdp.initial_states[0])

class Synthesizer:
    def __init__(self, sketch):
        
        self.sketch = sketch
        self.formulae = sketch.formulae + [sketch.optimality_formula]
        self.stat = Statistic(sketch, self.method_name)
        
        # self._check_prereq = False # FIXME: specify behaviour for <=0 and >=1 properties
        # self.expression_manager = sketch.program.expression_manager
        # self.hole_constants = OrderedDict([(c.name, c) for c in sketch.jani.constants if not c.defined])
        # self.qualitative_properties = None
        # self.engine = Engine.Sparse # FIXME: dd engine

    @property
    def method_name(self):
        return "onebyone"
    
    @property
    def has_optimality_formula(self):
        return self.sketch.optimality_formula is not None

    def print_stats(self, short_summary = False):
        print(self.stat.get_summary(short_summary))

    def run(self):
        self.stat.start()
        satisfying_assignment = None
        for assignment in self.sketch.design_space.all_assignments():
            dtmc = DTMC(self.sketch, assignment)
            self.stat.iteration_dtmc(dtmc.states)
            all_sat = True
            results = []
            for index,formula in enumerate(self.formulae):
                result = dtmc.model_check(index)
                self.stat.check_dtmc()
                if not formula.satisfied(result):
                    all_sat = False
                    break
                if formula.optimality:
                    formula.improve_threshold(result)
            if all_sat:
                satisfying_assignment = assignment
                if not self.has_optimality_formula:
                    break
            self.stat.pruned(1)

        optimal_value = self.sketch.optimality_formula.optimal_value if self.has_optimality_formula else None
        self.stat.finished(satisfying_assignment,optimal_value)

