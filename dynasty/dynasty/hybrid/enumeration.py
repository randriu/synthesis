import itertools
import logging

import stormpy

from ..family_checkers.quotientbased import LiftingChecker
from ..model_handling.mdp_handling import ModelHandling
from ..profiler import Timer
from .helpers import is_satisfied, safe_division
from .statistic import Statistic

logger = logging.getLogger(__name__)


class EnumerationChecker(LiftingChecker):
    """1-by-1 checker wrapper."""

    def __init__(self, *args):
        super().__init__(*args)
        self.statistic = None
        self.iterations = 0
        self.satisfying_assignment = None

    def run_feasibility(self):
        jani_program = self.sketch
        total_nr_options = self.hole_options.size()

        if self.input_has_optimality_property():
            ct = stormpy.logic.ComparisonType.GREATER if self._optimality_setting.direction == 'max' \
                else stormpy.logic.ComparisonType.LESS
            self.mc_formulae[len(self.mc_formulae) - 1].set_bound(
                ct, self.sketch.expression_manager.create_rational(stormpy.Rational(self._optimal_value))
            )

        estimation_timer = Timer()
        estimation_timer.start()

        for constant_assignment in itertools.product(*self.hole_options.values()):
            self.iterations += 1
            if self.iterations % 10 == 0:
                logger.info(f"Iteration: {self.iterations} / {total_nr_options}")
            constants = [jani_program.get_constant(c).expression_variable for c in self.hole_options.keys()]
            substitution = dict(zip(constants, constant_assignment))
            instance = jani_program.define_constants(substitution)
            mh = ModelHandling()
            mh.build_model(instance, self.mc_formulae, self.mc_formulae_alt)

            improved = False
            all_sat = True
            for formula_index in range(len(self.mc_formulae)):
                mc_result = mh.mc_model(index=formula_index).result
                satisfied = is_satisfied(self.mc_formulae[formula_index], mc_result.at(mh.full_mdp.initial_states[0]))
                # logger.debug(f"1-by-1: model checking DTMC against a formula with index {formula_index}: {satisfied}")
                if not satisfied:
                    all_sat = False
                    break
                if self.input_has_optimality_property() and formula_index == len(self.mc_formulae) - 1 and satisfied:
                    improved = self._check_optimal_property(mh.full_mdp)
            if all_sat:
                if not self.input_has_optimality_property():
                    self.satisfying_assignment = {c.name: [v] for (c, v) in substitution.items()}
                    break
                elif improved:
                    self.satisfying_assignment = {c.name: [v] for (c, v) in substitution.items()}

            if self.iterations % 10 == 0:
                percentage_rejected = safe_division(self.iterations, total_nr_options)  # division by zero fix
                iters_estimate = self.iterations / percentage_rejected
                time_estimate = estimation_timer.read() / percentage_rejected
                logger.info(
                    f">> Performance estimation (unfeasible): "
                    f"{iters_estimate} iterations in {time_estimate} sec "
                    f"(opt: {self._optimal_value})."
                )
        return self.iterations

    def _check_optimal_property(self, dtmc):
        # Model checking of the optimality property
        result = stormpy.model_checking(dtmc, self._optimality_setting.criterion)
        optimal_value = result.at(dtmc.initial_states[0])

        # Check whether the improvement was achieved
        if self._optimality_setting.is_improvement(optimal_value, self._optimal_value):
            # Set the new values of the optimal attributes
            self._optimal_value = optimal_value

            # Construct new violation property with respect to the currently optimal value
            vp = self._optimality_setting.get_violation_property(
                self._optimal_value,
                lambda x: self.sketch.expression_manager.create_rational(stormpy.Rational(x)),
            )

            # Replace the last violation property by newly one
            self.mc_formulae[len(self.mc_formulae) - 1] = vp.raw_formula

            logger.debug(f"Optimal value improved to: {self._optimal_value}")

            return True
        return False

    def run(self, short_summary):
        self.statistic = Statistic(
            "1-by-1", [p.raw_formula for p in self.properties], len(self.holes),
            self._optimality_setting, short_summary=short_summary
        )
        iterations = self.run_feasibility()
        self.statistic.finished(
            self.satisfying_assignment, (0, iterations), self._optimal_value, 0, 0.0, 0.0, 0.0, 0.0, 0.0
        )
