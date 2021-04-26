import logging

import stormpy

from ..family_checkers.quotientbased import LiftingChecker
from ..profiler import Profiler, Timer
from .family import Family
from .helpers import readable_assignment, safe_division
from .statistic import Statistic

logger = logging.getLogger(__name__)


class ARChecker(LiftingChecker):
    """AR wrapper."""

    def __init__(self, *args):
        super().__init__(*args)
        self.statistic = None
        self.formulae = []
        self.iterations = 0
        self.family = None
        self.families = []
        self.models_total = 0

    def initialise(self):
        super().initialise()
        # QuotientBasedFamilyChecker.initialise(self)
        self.formulae = [property_obj.raw_formula for property_obj in self.properties]
        if self.input_has_optimality_property():
            ct = stormpy.logic.ComparisonType.GREATER if self._optimality_setting.direction == 'max' \
                else stormpy.logic.ComparisonType.LESS
            bound = self.sketch.expression_manager.create_rational(stormpy.Rational(self._optimal_value))
            opt_formula = self._optimality_setting.criterion.raw_formula.clone()
            opt_formula.set_bound(ct, bound)
            self.formulae.append(opt_formula)

    def run(self, short_summary):
        self.statistic = Statistic(
            "CEGAR", self.formulae, len(self.holes), self._optimality_setting, short_summary=short_summary
        )
        assignment, optimal_value = self.run_feasibility()
        self.statistic.finished(
            assignment, (self.iterations, 0), optimal_value, self.models_total,
            Family.quotient_mdp().nr_states, safe_division(Family.quotient_mdp_stats(0), Family.quotient_mdp_stats(1)),
            Family.mdp_checks(), 0.0, 0.0
        )

    def run_feasibility(self):
        """
        Run feasibility synthesis. Return either a satisfying assignment (feasible) or None (unfeasible).
        """
        Profiler.initialize()
        estimation_timer = Timer()
        estimation_timer.start()

        logger.info("Running feasibility + optimal synthesis.")

        # initialize family description
        logger.debug("Constructing quotient MDP of the superfamily.")
        Family.initialize(
            self.sketch, self.holes, self.hole_options, self.symmetries,
            self.differents, self.formulae, self.mc_formulae, self.mc_formulae_alt,
            self.thresholds, self._accept_if_above, self._optimality_setting
        )

        # initiate CEGAR loop
        self.family = Family()
        self.models_total = self.family.size
        models_rejected = 0
        self.families = [self.family]
        satisfying_assignment = None
        logger.debug("Initiating CEGAR loop")
        while self.families:
            logger.debug(f"Current number of families: {len(self.families)}")
            percentage_rejected = max((models_rejected / self.models_total), 0.0000000001)  # division by zero fix
            iters_estimate = self.iterations / percentage_rejected
            time_estimate = estimation_timer.read() / percentage_rejected
            logger.info(f"Performance estimation (unfeasible): {iters_estimate} iterations in {time_estimate} sec.")

            self.iterations += 1
            logger.debug("CEGAR: iteration {}.".format(self.iterations))

            self.family = self.families.pop(-1)
            self.family.construct()
            feasible, optimal_value = self.family.analyze()
            if feasible and isinstance(feasible, bool):
                logger.debug("CEGAR: all SAT.")
                satisfying_assignment = self.family.member_assignment
                if optimal_value is not None:
                    self._check_optimal_property(optimal_value, self.family.member_assignment)
                if satisfying_assignment is not None and self._optimality_setting is None:
                    break
            elif not feasible and isinstance(feasible, bool):
                if optimal_value is not None:
                    self._check_optimal_property(optimal_value, self.family.member_assignment)
                logger.debug("CEGAR: all UNSAT.")
                models_rejected += self.family.size
            else:  # feasible is None:
                if optimal_value is not None:
                    self._check_optimal_property(optimal_value, self.family.member_assignment)
                logger.debug("CEGAR: undecided.")
                logger.debug("Splitting the family.")
                subfamily_left, subfamily_right = self.family.split()
                logger.debug(
                    f"Constructed two subfamilies of size {subfamily_left.size} and {subfamily_right.size}."
                )
                self.families.append(subfamily_left)
                self.families.append(subfamily_right)

        if self._optimal_value is not None:
            assert not self.families
            logger.info(f"Found optimal assignment: {self._optimal_value}")
            return self._optimal_assignment, self._optimal_value
        elif satisfying_assignment is not None:
            logger.info(f"Found satisfying assignment: {readable_assignment(satisfying_assignment)}")
            return satisfying_assignment, None
        else:
            logger.info("No more options.")
            return None, None

    def _construct_violation_property(self):
        vp_index = len(self.formulae) - 1  # Compute the index of the violation property

        # Construct new violation property with respect to the currently optimal value
        vp = self._optimality_setting.get_violation_property(
            self._optimal_value,
            lambda x: self.sketch.expression_manager.create_rational(stormpy.Rational(x)),
        )

        # Update the attributes of the family according to the new optimal values
        # For each family we need to update theirs formulae and formulae indices to check
        for family in self.families + [self.family]:
            # Replace the last violation property by newly one
            family.formulae[vp_index] = vp.raw_formula
            # When the violation property is not checking, we have to add its index
            if vp_index not in family.formulae_indices:
                family.formulae_indices.append(vp_index)
                family.model_check_formula(vp_index)
                family.bounds[vp_index] = Family.quotient_container().latest_result.result

        # Change the value of threshold of the violation formulae within constructed quotient MDP
        Family.set_thresholds(Family.get_thresholds()[:-1] + [vp.raw_formula.threshold])

    def _check_optimal_property(self, optimal_value, assignment):
        # Check whether the improvement was achieved
        if self._optimality_setting.is_improvement(optimal_value, self._optimal_value):
            # Set the new values of the optimal attributes
            self._optimal_value = optimal_value
            self._optimal_assignment = assignment

            # Construct the violation property according newly found optimal value
            self._construct_violation_property()

            logger.debug(f"Optimal value improved to: {self._optimal_value}")
            return True
