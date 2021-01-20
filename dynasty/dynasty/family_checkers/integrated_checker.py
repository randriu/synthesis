# author: Roman Andriushchenko
# co-author: Simon Stupinsky

import logging
import operator
import itertools
import z3

import stormpy
import stormpy.synthesis

from collections import OrderedDict

from ..jani.jani_quotient_builder import logger as jani_quotient_builder_logger, JaniQuotientBuilder
from ..jani.quotient_container import logger as quotient_container_logger, ThresholdSynthesisResult
from ..model_handling.mdp_handling import ModelHandling, logger as model_handling_logger
from ..profiler import Profiler, Timer
from .cegis import Synthesiser
from .quotientbased import LiftingChecker, QuotientBasedFamilyChecker, logger as quotientbased_logger
from .familychecker import HoleOptions

# LOGGING -------------------------------------------------------------------------------------------------- LOGGING


logger = logging.getLogger(__name__)

quotientbased_logger.disabled = False
quotient_container_logger.disabled = True
jani_quotient_builder_logger.disabled = True
model_handling_logger.disabled = True

ONLY_CEGAR = False
ONLY_CEGIS = False
NONTRIVIAL_BOUNDS = True
PRINT_STAGE_INFO = False
PRINT_PROFILING = False
STAGE_SCORE_LIMIT = 99999
# Zero approximation to avoid zero division etc.
APPROX_ZERO = 0.000001


# MANUAL MODEL CHECKING ------------------------------------------------------------------------- MANUAL MODEL CHECKING


def safe_division(dividend, divisor):
    """Safe division of dividend by operand
    :param number dividend: upper operand of the division
    :param number divisor: lower operand of the division, may be zero
    :return: safe value after division of approximated zero
    """
    try:
        return dividend / divisor
    except (ZeroDivisionError, ValueError):
        return dividend / APPROX_ZERO


def is_satisfied(formula, result):
    threshold = formula.threshold_expr.evaluate_as_double()
    op = {
        stormpy.ComparisonType.LESS: operator.lt,
        stormpy.ComparisonType.LEQ: operator.le,
        stormpy.ComparisonType.GREATER: operator.gt,
        stormpy.ComparisonType.GEQ: operator.ge
    }[formula.comparison_type]
    return op(result, threshold)


def check_dtmc(dtmc, formula, quantitative=False):
    """Model check a DTMC against a (quantitative) property."""
    if quantitative:
        formula = formula.clone()
        formula.remove_bound()

    result = stormpy.model_checking(dtmc, formula)
    at_init = result.at(dtmc.initial_states[0])
    satisfied = at_init if not quantitative else is_satisfied(formula, at_init)
    return satisfied, result

# Synthesis wrappers ------------------------------------------------------------------------------ Synthesis wrappers


def readable_assignment(assignment):
    # return {k: v.__str__() for (k, v) in assignment.items()} if assignment is not None else None
    return ",".join(
        [f"{k}={[int(v.__str__()) for v in vs] if len(vs) > 1 else int(vs[0].__str__())}" for (k, vs) in assignment.items()]
    ) if assignment is not None else None


class Statistic:
    """General computation stats."""

    def __init__(self, method, formulae, holes_count, opt_setting, short_summary=False):
        self.method = method
        self.short_summary = short_summary
        self.timer = Timer()
        self.timer.start()
        self.feasible = False
        self.assignment = {}
        self.iterations = (0, 0)
        self.optimal_value = None
        self.formulae = formulae
        self.holes_count = holes_count
        self.opt_setting = opt_setting
        self.family_size = 0
        self.super_mdp_size, self.mdp_checks, self.avg_mdp_size = 0, 0, 0
        self.avg_dtmc_size, self.dtmc_checks = 0, 0
        self.ce_quality = None

    def finished(
            self, assignment, iterations, optimal_value, family_size, super_mdp_size,
            avg_mdp_size, mdp_checks, avg_dtmc_size, dtmc_checks, ce_quality=""
    ):
        self.timer.stop()
        self.feasible = assignment is not None
        self.assignment = readable_assignment(assignment)
        self.iterations = iterations
        self.optimal_value = optimal_value
        self.family_size = family_size
        self.super_mdp_size = super_mdp_size
        self.avg_mdp_size = round(avg_mdp_size, 2)
        self.mdp_checks = mdp_checks
        self.avg_dtmc_size = round(avg_dtmc_size, 2)
        self.dtmc_checks = dtmc_checks
        self.ce_quality = ce_quality

    def get_long_summary(self):
        formulae = self.formulae if self.optimal_value is None else self.formulae[:-1]
        formulae = "\n".join([f"formula {i + 1}: {formula}" for i, formula in enumerate(formulae)])
        opt_formula = f"optimal setting: {self.opt_setting}" if self.optimal_value else ""

        timing = f"method: {self.method}, synthesis time: {round(self.timer.time, 2)} s"
        design_space = f"number of holes: {self.holes_count}, family size: {self.family_size}"

        mdp_stats = f"super MDP size: {self.super_mdp_size}, average MDP size: {round(self.avg_mdp_size)}, " \
                    f"MPD checks: {self.mdp_checks}, iterations: {self.iterations[0]}"
        dtmc_stats = f"average DTMC size: {round(self.avg_dtmc_size)}, " \
                     f"DTMC checks: {self.dtmc_checks}, iterations: {self.iterations[1]}"
        family_stats = ""
        if self.method == "CEGAR" or self.method == "Hybrid":
            family_stats += f"{mdp_stats}\n"
        if self.method != "CEGAR":
            family_stats += f"{dtmc_stats}\n"

        feasible = "yes" if self.feasible else "no"
        result = f"feasible: {feasible}" if self.optimal_value is None else f"optimal: {round(self.optimal_value, 6)}"
        assignment = f"hole assignment: {self.assignment}\n" if self.assignment is not None else ""

        summary = f"{formulae}\n{opt_formula}\n{timing}\n{design_space}\n" \
                  f"{family_stats}{self.ce_quality}\n{result}\n{assignment}"
        return summary

    def get_short_summary(self):
        if self.optimal_value is None:
            result = "F" if self.feasible else "U"
        else:
            result = f"opt = {round(self.optimal_value, 6)}"
        if self.method == "CEGAR":
            iters = self.iterations[0]
        elif self.method == "CEGIS" or self.method == "1-by-1":
            iters = self.iterations[1]
        else:
            iters = (self.iterations[0], self.iterations[1])
        thresholds = [round(float(f.threshold), 10) for f in self.formulae]

        return f"> T = {thresholds} - {self.method}: {result} ({iters} iters, {round(self.timer.time, 2)} sec)"

    def __str__(self):
        sep = "--------------------"
        summary = f"{sep}\n{self.get_long_summary()}"
        if self.short_summary:
            summary += f"\n{sep}\n{self.get_short_summary()}\n"
        return summary


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
                if formula_index == len(self.mc_formulae) - 1 and satisfied:
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
                    f"{iters_estimate} ({self.iterations}) iterations in {time_estimate} sec. "
                    f"(OPT: {self._optimal_value})"
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
            "1-by-1", self.mc_formulae, len(self.holes), self._optimality_setting, short_summary=short_summary
        )
        iterations = self.run_feasibility()
        self.statistic.finished(
            self.satisfying_assignment, (0, iterations), self._optimal_value, 0, 0.0, 0.0, 0.0, 0.0, 0.0
        )


class CEGISChecker(Synthesiser):
    """CEGIS wrapper."""

    def __init__(self, *args):
        super().__init__(*args)
        self.statistic = None

    def run(self, short_summary):
        formulae = [property_obj.raw_formula for property_obj in self._verifier.properties]
        self.statistic = Statistic(
            "CEGIS", formulae, len(self.holes), self._optimality_setting, short_summary=short_summary
        )
        _, assignment, optimal_value = self.run_feasibility()
        assignment = {k: [v] for (k, v) in assignment.items()} if assignment is not None else None
        if assignment is not None:
            logger.info(f"Found satisfying assignment: {readable_assignment(assignment)}")
        self.statistic.finished(
            assignment, (0, self.stats.iterations), optimal_value, self.stats.design_space_size, 0, 0, 0,
            self.verifier_stats.average_model_size,
            self.verifier_stats.qualitative_model_checking_calls + self.verifier_stats.quantitative_model_checking_calls
        )


class CEGARChecker(LiftingChecker):
    """CEGAR wrapper."""

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


# Family encapsulator ------------------------------------------------------------------------------ Family encapsulator

class Family:
    """
        notation:
        hole: String
        Holes: a set of all holes
        HoleOptions : Hole -> [Expression]

        Family.holes : Hole -> JaniConstant
        Family.hole_options is HoleOptions
        Family.solver_meta_vars : Var -> Hole
        Family.hole_option_indices : Hole -> (Expression -> int)

        self.options is HoleOptions

        sat_model: Var -> int
        assignment: Hole -> [Expression]
    """

    # TODO: Check beforehand if family is non-empty.

    # Superfamily description

    # - original prism description
    _sketch = None

    # - hole options
    _holes = None  # ordered dictionary
    _hole_options = None
    _hole_option_indices = None

    # - indexed hole options
    hole_list = None
    hole_not_generalized = None
    _hole_indices = None

    # - jani representation + sparse MDP representation
    _quotient_container = None
    _quotient_mdp = None

    # - SMT encoding (used to enable restrictions)
    _solver = None
    _solver_meta_vars = None

    # - formulae of interest
    _formulae = None
    _mc_formulae = None
    _mc_formulae_alt = None
    _thresholds = None
    _accept_if_above = None
    _optimality_setting = None

    # - statistics for summary
    _quotient_mdp_stats = (0, 0)
    _dtmc_stats = (0, 0)
    _mdp_checks = 0
    _dtmc_checks = 0

    # - CEXs for MDP of superfamily
    # global_cex_generator = None

    def __init__(self, parent=None, options=None):
        """
        Construct a family. Each family is either a superfamily represented by
        a Family._quotient_mdp or a (proper) subfamily that is constructed on
        demand via Family._quotient_container.consider_subset(). Subfamilies
        inherit formulae of interest from their parents.
        """
        self.options = Family._hole_options.copy() if parent is None else options
        self.mdp = Family._quotient_mdp if parent is None else None
        self.choice_map = [i for i in range(Family._quotient_mdp.nr_choices)] if parent is None else None
        self.formulae_indices = list(range(len(Family._formulae))) if parent is None else parent.formulae_indices

        # encode this family
        hole_clauses = dict()
        for var, hole in Family._solver_meta_vars.items():
            hole_clauses[hole] = z3.Or(
                [var == Family._hole_option_indices[hole][option] for option in self.options[hole]]
            )
        self.encoding = z3.And(list(hole_clauses.values()))

        # a family that has never been MDP-analyzed is not ready to be split
        self.bounds = [None] * len(Family._formulae)  # assigned when analysis is initiated
        self.suboptions = None
        self.member_assignment = None

    @staticmethod
    def initialize(
            _sketch, _holes, _hole_options, symmetries, differents, _formulae,
            _mc_formulae, _mc_formulae_alt, _thresholds, _accept_if_above, optimality_setting
    ):

        Family._sketch = _sketch
        Family._holes = _holes
        Family._hole_options = _hole_options

        # map holes to their indices
        Family.hole_list = list(Family._holes.keys())
        Family._hole_indices = dict()
        for hole_index, hole in enumerate(Family.hole_list):
            Family._hole_indices[hole] = hole_index

        # map hole options to their indices
        Family._hole_option_indices = dict()
        for hole, options in Family._hole_options.items():
            indices = dict()
            k = 0
            for option in options:
                indices[option] = k
                k += 1
            Family._hole_option_indices[hole] = indices

        # initialize z3 solver
        Family._solver = z3.Solver()
        Family._solver_meta_vars = OrderedDict()
        variables = dict()
        for k, v in Family._hole_options.items():
            # create integer variable
            var = z3.Int(k)
            # store the variable
            Family._solver_meta_vars[var] = k
            variables[k] = var
            # add constraints for the hole assignments
            Family._solver.add(var >= 0)
            Family._solver.add(var < len(v))

        # encode restrictions
        if symmetries is not None:
            for sym in symmetries:
                for x, y in zip(sym, sym[1:]):
                    Family._solver.add(variables[x] < variables[y])
        if differents is not None:
            for diff in differents:
                for idx, x in enumerate(diff):
                    for y in diff[idx + 1:]:
                        Family._solver.add(variables[x] != variables[y])

        # store formulae info
        Family._formulae = _formulae
        Family._mc_formulae = _mc_formulae
        Family._mc_formulae_alt = _mc_formulae_alt
        Family._thresholds = _thresholds
        Family._accept_if_above = _accept_if_above
        Family._optimality_setting = optimality_setting

        # build quotient MDP
        quotient_builder = JaniQuotientBuilder(Family._sketch, Family._holes)
        Family._quotient_container = quotient_builder.construct(Family._hole_options, remember=set())
        Family._quotient_container.prepare(Family._mc_formulae, Family._mc_formulae_alt)
        Family._quotient_mdp = Family._quotient_container.mdp_handling.full_mdp
        Family._quotient_mdp_stats = (
            Family._quotient_mdp_stats[0] + Family._quotient_mdp.nr_states, Family._quotient_mdp_stats[1] + 1
        )
        logger.debug(f"Constructed MDP of size {Family._quotient_mdp.nr_states}.")

    @property
    def size(self):
        return self.options.size()

    @property
    def constructed(self):
        return self.mdp is not None

    @property
    def analyzed(self):
        return all([self.bounds[index] is not None for index in self.formulae_indices])

    @property
    def split_ready(self):
        return self.suboptions is not None

    @property
    def hole_options(self):
        return Family._hole_options

    @property
    def hole_indices(self):
        return Family._hole_indices

    @property
    def formulae(self):
        return Family._formulae

    @staticmethod
    def quotient_mdp_stats(idx):
        return Family._quotient_mdp_stats[idx]

    @staticmethod
    def dtmc_stats(idx):
        return Family._dtmc_stats[idx]

    @staticmethod
    def mdp_checks():
        return Family._mdp_checks

    @staticmethod
    def dtmc_checks():
        return Family._dtmc_checks

    @staticmethod
    def quotient_mdp():
        return Family._quotient_mdp

    @staticmethod
    def get_thresholds():
        return Family._thresholds

    @staticmethod
    def set_thresholds(thresholds):
        Family._thresholds = thresholds

    @staticmethod
    def quotient_container():
        return Family._quotient_container

    @staticmethod
    def mdp_checks_inc():
        Family._mdp_checks += 1

    @staticmethod
    def dtmc_checks_inc():
        Family._dtmc_checks += 1

    def construct(self):
        """ Construct quotient MDP for this family using the quotient container. """
        if self.constructed:
            return

        Profiler.start("ar - MDP construction")

        logger.debug(f"Constructing quotient MDP for family {self.options}.")
        indexed_options = Family._hole_options.index_map(self.options)
        Family._quotient_container.consider_subset(self.options, indexed_options)
        self.mdp = Family._quotient_container.mdp_handling.mdp
        self.choice_map = Family._quotient_container.mdp_handling.mapping_to_original
        logger.debug(f"Constructed MDP of size {self.mdp.nr_states}.")
        Family._quotient_mdp_stats = (
            Family._quotient_mdp_stats[0] + self.mdp.nr_states, Family._quotient_mdp_stats[1] + 1
        )

        Profiler.stop()

    def model_check_formula(self, formula_index):
        """
        Model check the underlying quotient MDP against a given formula.
        Return feasibility (SAT = True, UNSAT = False, ? = None) as well as the model checking result.
        """
        assert self.constructed

        threshold = float(Family._thresholds[formula_index])
        Family._quotient_container.analyse(threshold, formula_index)

        mc_result = Family._quotient_container.decided(threshold)
        accept_if_above = Family._accept_if_above[formula_index]
        if mc_result == ThresholdSynthesisResult.UNDECIDED:
            feasibility = None
        else:
            feasibility = (mc_result == ThresholdSynthesisResult.ABOVE) == accept_if_above
        bounds = Family._quotient_container.latest_result.result

        # +
        # bounds_alt = Family._quotient_container.latest_result.alt_result
        # init_state = self._quotient_mdp.initial_states[0]
        # print("> MDP result: ", bounds.at(init_state), " -> ", feasibility)
        # print("> MDP result (alt): ", bounds_alt.at(init_state))

        return feasibility, bounds

    def analyze(self):
        """
        Analyze the underlying quotient MDP for this subfamily with respect
        to all (yet undecided) formulae and store all model checking results.
        Return feasibility (SAT = True, UNSAT = False, ? = None). Whenever an
        undecidable formula is met, prepare the family for splitting.
        In the case of inconclusive result, update the set of undecidable
        formulae for future processing. Otherwise, in the case of satisfying
        result, store a hole assignment.
        Note: we do not check whether assignment is not None
        """
        # assert not self.analyzed  # sanity check
        assert self.constructed

        logger.debug(f"CEGAR: analyzing family {self.options} of size {self.size}.")

        undecided_formulae_indices = []
        optimal_value = None
        # for formula_index in self.formulae_indices[:-1] \
        #         if superfamily and self._optimality_setting is not None else self.formulae_indices:
        for formula_index in self.formulae_indices:
            # logger.debug(f"CEGAR: model checking MDP against a formula with index {formula_index}.")
            Family.mdp_checks_inc()
            feasible, self.bounds[formula_index] = self.model_check_formula(formula_index)

            if not feasible and isinstance(feasible, bool):
                logger.debug(f"Formula {formula_index}: UNSAT")
                undecided_formulae_indices = None
                if self._optimality_setting is not None and formula_index == len(self.formulae) - 1:
                    if not undecided_formulae_indices:
                        decided, optimal_value = self.check_optimal_property(feasible)
                        # undecided_formulae_indices += [formula_index] if decided is None else []
                break
            elif feasible is None:
                logger.debug(f"Formula {formula_index}: UNDECIDED")
                undecided_formulae_indices.append(formula_index)
                if not self.split_ready:
                    self.prepare_split()
            else:
                logger.debug("Formula {}: SAT".format(formula_index))
                if self._optimality_setting is not None and formula_index == len(self.formulae) - 1:
                    if not undecided_formulae_indices:
                        decided, optimal_value = self.check_optimal_property(feasible)
                        undecided_formulae_indices += [formula_index] if decided is None else []
                    else:
                        undecided_formulae_indices.append(formula_index)

        # if self._optimality_setting is not None:
        #     if not undecided_formulae_indices and isinstance(undecided_formulae_indices, list):
        #         decided, optimal_value = self.check_optimal_property()

        self.formulae_indices = undecided_formulae_indices

        # postprocessing
        if self.formulae_indices is None:
            return False, optimal_value
        elif not self.formulae_indices:
            self.pick_assignment() if self.size == 1 else self.pick_whole_family()
            return True, optimal_value
        return None, optimal_value

    def prepare_split(self):
        # logger.debug(f"Preparing to split family {self.options}")
        assert self.constructed and not self.split_ready
        Profiler.start("ar - splitting")
        Family._quotient_container.scheduler_color_analysis()
        if len(Family._quotient_container.inconsistencies) == 2:
            self.suboptions = LiftingChecker.split_hole_options(
                self.options, Family._quotient_container, Family._hole_options, True
            )
        Profiler.stop()

    def split(self):
        assert self.split_ready
        return Family(self, self.suboptions[0]), Family(self, self.suboptions[1])

    def pick_assignment(self):
        """ Pick any feasible hole assignment. Return None if no instance remains. """
        # get satisfiable assignment
        solver_result = Family._solver.check(self.encoding)

        if solver_result != z3.sat:
            # no further instances
            return None

        # construct the corresponding singleton (a single-member family)
        sat_model = Family._solver.model()
        assignment = HoleOptions()
        self.member_assignment = None
        for var, hole in Family._solver_meta_vars.items():
            assignment[hole] = [Family._hole_options[hole][sat_model[var].as_long()]]
        self.member_assignment = assignment

        return self.member_assignment

    def pick_whole_family(self):
        assignment = HoleOptions()
        for hole, vals in self.options.items():
            assignment[hole] = [int(str(val)) for val in vals]
        self.member_assignment = assignment

    def check_optimal_property(self, feasible):
        is_max = True if self._optimality_setting.direction == "max" else False
        oracle = Family._quotient_container
        optimal_value = None
        decided = None
        if feasible is None:
            logger.debug("Family is UNDECIDED for optimal property.")
            if not self.split_ready:
                self.prepare_split()
            if self.size > 1:
                # oracle.scheduler_color_analysis()
                if (oracle.is_lower_bound_tight() and not is_max) or (oracle.is_upper_bound_tight() and is_max):
                    logger.debug(f'Found a tight {"upper" if is_max else "lower"} bound.')
                    optimal_value = oracle.upper_bound() if is_max else oracle.lower_bound()
                    decided = True
            else:
                decided = True
        elif feasible:
            logger.debug(f'All {"above" if is_max else "below"} within analyses of family for optimal property.')
            if not self.split_ready:
                self.prepare_split()
            # oracle.scheduler_color_analysis()
            improved_tight = oracle.is_upper_bound_tight() if is_max else oracle.is_lower_bound_tight()
            optimal_value = oracle.upper_bound() if (improved_tight and is_max) or (not improved_tight and not is_max) \
                else oracle.lower_bound()
            if improved_tight:
                decided = True
            elif not improved_tight:
                decided = None
        elif not feasible:
            decided = False
            logger.debug("All discarded within analyses of family for optimal property.")

        return decided, optimal_value

    def print_mdp(self):
        print("> MDP info")
        mdp = self.mdp
        tm = mdp.transition_matrix
        for state in range(mdp.nr_states):
            print("> state: ", state)
            for row in range(tm.get_row_group_start(state), tm.get_row_group_end(state)):
                print("> ", str(tm.get_row(row)))

    def check_mdp(self):
        mdp = self.mdp
        tm = mdp.transition_matrix
        init_state = mdp.initial_states[0]
        mdp_actions = tm.get_row_group_end(init_state) - tm.get_row_group_start(init_state)
        hole_combinations = len(self.options["s2a"]) * len(self.options["s2b"]) * len(self.options["s2c"])
        if mdp_actions != hole_combinations:
            print(f"> MDP is invalid ({mdp_actions} actions != {hole_combinations} combinations)")
            print("> family: ", self.options)
            self.print_mdp()
            exit()
        logger.debug("MDP is OK")

    @staticmethod
    def is_in_family(hole_assignment, hole_options):
        hole_assignment = {key: str(value) for key, value in hole_assignment.items()}
        # print("> comparing ", hole_assignment, " and ", hole_options)
        for hole, option in hole_assignment.items():
            family_hole_options = [str(hole_option) for hole_option in hole_options[hole]]
            # print("> ", option, " in ", family_hole_options)
            if option not in family_hole_options:
                return False
        return True

    # interesting_assignment = {"s2a":4,"s2b":1,"s2c":0,"s3a":3,"s3b":4,"s3c":4,"s4a":0,"s4b":1,"s4c":4}
    interesting_assignment = {"s2a": 3, "s2b": 1, "s2c": 2, "s3a": 2, "s3b": 1, "s3c": 4, "s4a": 2, "s4b": 1, "s4c": 3}

    def contains_interesting(self):
        return Family.is_in_family(Family.interesting_assignment, self.options)


# INTEGRATED METHOD --------------------------------------------------------------------------------- INTEGRATED METHOD

class FamilyHybrid(Family):
    """ Family adopted for CEGAR-CEGIS analysis. """

    # TODO: more efficient state-hole mapping?

    _choice_to_hole_indices = {}

    def __init__(self, *args):
        super().__init__(*args)

        self._state_to_hole_indices = None  # evaluated on demand

        # dtmc corresponding to the constructed assignment
        self.dtmc = None
        self.dtmc_state_map = None

    def initialize(*args):
        Family.initialize(*args)

        # map edges of a quotient container to hole indices
        jani = Family._quotient_container.jani_program
        _edge_to_hole_indices = dict()
        for aut_index, aut in enumerate(jani.automata):
            for edge_index, edge in enumerate(aut.edges):
                if edge.color == 0:
                    continue
                index = jani.encode_automaton_and_edge_index(aut_index, edge_index)
                assignment = Family._quotient_container.edge_coloring.get_hole_assignment(edge.color)
                hole_indices = [index for index, value in enumerate(assignment) if value is not None]
                _edge_to_hole_indices[index] = hole_indices

        # map actions of a quotient MDP to hole indices
        FamilyHybrid._choice_to_hole_indices = []
        choice_origins = Family._quotient_mdp.choice_origins
        matrix = Family._quotient_mdp.transition_matrix
        for state in range(Family._quotient_mdp.nr_states):
            for choice_index in range(matrix.get_row_group_start(state), matrix.get_row_group_end(state)):
                choice_hole_indices = set()
                for index in choice_origins.get_edge_index_set(choice_index):
                    hole_indices = _edge_to_hole_indices.get(index, set())
                    choice_hole_indices.update(hole_indices)
                FamilyHybrid._choice_to_hole_indices.append(choice_hole_indices)

    def split(self):
        assert self.split_ready
        return FamilyHybrid(self, self.suboptions[0]), FamilyHybrid(self, self.suboptions[1])

    @property
    def state_to_hole_indices(self):
        """
        Identify holes relevant to the states of the MDP and store only significant ones.
        """
        # if someone (i.e., CEGIS) asks for state indices, the model should already be analyzed
        assert self.constructed and self.analyzed

        # lazy evaluation
        if self._state_to_hole_indices is not None:
            return self._state_to_hole_indices

        Profiler.start("is - MDP holes (edges)")
        # logger.debug("Constructing state-holes mapping via edge-holes mapping.")

        self._state_to_hole_indices = []
        matrix = self.mdp.transition_matrix
        for state in range(self.mdp.nr_states):
            state_hole_indices = set()
            for choice_index in range(matrix.get_row_group_start(state), matrix.get_row_group_end(state)):
                state_hole_indices.update(FamilyHybrid._choice_to_hole_indices[self.choice_map[choice_index]])
            state_hole_indices = set(
                [index for index in state_hole_indices if len(self.options[Family.hole_list[index]]) > 1]
            )
            self._state_to_hole_indices.append(state_hole_indices)

        Profiler.stop()
        return self._state_to_hole_indices

    @property
    def state_to_hole_indices_choices(self):
        """
        Identify holes relevant to the states of the MDP and store only significant ones.
        """
        # if someone (i.e., CEGIS) asks for state indices, the model should already be analyzed
        assert self.constructed and self.analyzed

        # lazy evaluation
        if self._state_to_hole_indices is not None:
            return self._state_to_hole_indices

        Profiler.start("is - MDP holes (choices)")
        logger.debug("Constructing state-holes mapping via choice-holes mapping.")

        self._state_to_hole_indices = []
        matrix = self.mdp.transition_matrix
        for state in range(self.mdp.nr_states):
            state_hole_indices = set()
            for choice_index in range(matrix.get_row_group_start(state), matrix.get_row_group_end(state)):
                quotient_choice_index = self.choice_map[choice_index]
                choice_hole_indices = FamilyHybrid._choice_to_hole_indices[quotient_choice_index]
                state_hole_indices.update(choice_hole_indices)
            state_hole_indices = set(
                [index for index in state_hole_indices if len(self.options[Family.hole_list[index]]) > 1])
            self._state_to_hole_indices.append(state_hole_indices)
        Profiler.stop()
        return self._state_to_hole_indices

    def pick_member(self):
        # pick hole assignment

        self.pick_assignment()
        if self.member_assignment is not None:

            # collect edges relevant for this assignment
            indexed_assignment = Family._hole_options.index_map(self.member_assignment)
            subcolors = Family._quotient_container.edge_coloring.subcolors(indexed_assignment)
            collected_edge_indices = stormpy.FlatSet(
                Family._quotient_container.color_to_edge_indices.get(0, stormpy.FlatSet()))
            for c in subcolors:
                collected_edge_indices.insert_set(Family._quotient_container.color_to_edge_indices.get(c))

            # construct the DTMC by exploring the quotient MDP for this subfamily
            self.dtmc, self.dtmc_state_map = stormpy.synthesis.dtmc_from_mdp(self.mdp, collected_edge_indices)
            Family._dtmc_stats = (Family._dtmc_stats[0] + self.dtmc.nr_states, Family._dtmc_stats[1] + 1)
            logger.debug(f"Constructed DTMC of size {self.dtmc.nr_states}.")

            # assert absence of deadlocks or overlapping guards
            assert self.dtmc.labeling.get_states("deadlock").number_of_set_bits() == 0
            assert self.dtmc.labeling.get_states("overlap_guards").number_of_set_bits() == 0
            assert len(self.dtmc.initial_states) == 1  # to avoid ambiguity

        # success
        return self.member_assignment

    def exclude_member(self, conflicts):
        """
        Exclude the subfamily induced by the selected assignment and a set of conflicts.
        """
        assert self.member_assignment is not None

        for conflict in conflicts:
            counterexample_clauses = dict()
            for var, hole in Family._solver_meta_vars.items():
                if Family._hole_indices[hole] in conflict:
                    option_index = Family._hole_option_indices[hole][self.member_assignment[hole][0]]
                    counterexample_clauses[hole] = (var == option_index)
                else:
                    all_options = [var == Family._hole_option_indices[hole][option] for option in self.options[hole]]
                    counterexample_clauses[hole] = z3.Or(all_options)
            counterexample_encoding = z3.Not(z3.And(list(counterexample_clauses.values())))
            Family._solver.add(counterexample_encoding)
        self.member_assignment = None

    def analyze_member(self, formula_index):
        assert self.dtmc is not None
        sat, result = check_dtmc(self.dtmc, Family._formulae[formula_index], quantitative=True)
        return sat, result

    def print_member(self):
        print("> DTMC info:")
        dtmc = self.dtmc
        tm = dtmc.transition_matrix
        for state in range(dtmc.nr_states):
            row = tm.get_row(state)
            print("> ", str(row))

    def conflict_covers_interesting(self, conflict):
        generalized_options = self.options.copy()
        for hole in conflict:
            generalized_options[hole] = self.member_assignment[hole]
        return Family.is_in_family(Family.interesting_assignment, generalized_options)


# Family encapsulator ------------------------------------------------------------------------------ Family encapsulator

class IntegratedChecker(QuotientBasedFamilyChecker, CEGISChecker):
    """Integrated checker."""

    stage_score_limit = 99999
    ce_quality = False
    ce_maxsat = False

    def __init__(self):
        QuotientBasedFamilyChecker.__init__(self)
        CEGISChecker.__init__(self)
        self.families = []
        self.iterations_cegis = 0
        self.iterations_cegar = 0
        self.formulae = []
        self.statistic = None
        self.models_total = 0
        self.stage_timer = Timer()
        self.stage_switch_allowed = True  # once a method wins, set this to false and do not switch between methods
        self.stage_score = 0  # +1 point whenever cegar wins the stage, -1 otherwise
        # cegar/cegis stats
        self.stage_time_cegar, self.stage_pruned_cegar, self.stage_time_cegis, self.stage_pruned_cegis = 0, 0, 0, 0
        # multiplier to derive time allocated for cegis; =1 is fair, <1 favours cegar, >1 favours cegis
        self.cegis_allocated_time_factor = 1.0
        # start with CEGAR
        self.stage_cegar = True
        self.cegis_allocated_time = 0
        self.stage_time_allocation_cegis = 0
        # CE quality
        self.ce_maxsat, self.ce_zero, self.ce_global, self.ce_local = 0, 0, 0, 0
        self.ce_maxsat_timer, self.ce_zero_timer, self.ce_global_timer, self.ce_local_timer = \
            Timer(), Timer(), Timer(), Timer()

    def initialise(self):
        QuotientBasedFamilyChecker.initialise(self)
        CEGISChecker.initialise(self)
        self.formulae = [property_obj.raw_formula for property_obj in self.properties]
        if self.input_has_optimality_property():
            ct = stormpy.logic.ComparisonType.GREATER if self._optimality_setting.direction == 'max' \
                else stormpy.logic.ComparisonType.LESS
            bound = self.sketch.expression_manager.create_rational(stormpy.Rational(self._optimal_value))
            opt_formula = self._optimality_setting.criterion.raw_formula.clone()
            opt_formula.set_bound(ct, bound)
            self.formulae.append(opt_formula)

    # ----- Adaptivity ----- #
    # Main idea: switch between cegar/cegis, allocate more time to the more efficient method; if one method is
    # consistently better than the other, declare it the winner and stop switching. Cegar wins over cegis by reaching
    # the score limit, cegis wins by reaching the negative score limit.
    # note: this is the only parameter in the integrated synthesis

    def stage_start(self, request_stage_cegar):
        self.stage_cegar = request_stage_cegar
        if ONLY_CEGAR:
            # disallow return to CEGIS
            self.stage_switch_allowed = False
        self.stage_timer.reset()
        self.stage_timer.start()

    def stage_step(self, models_pruned):
        """Performs a stage step, returns True if the method switch took place"""

        # if the method switch is prohibited, we do not care about stats
        if not self.stage_switch_allowed:
            return False

        # record pruned models
        self.stage_pruned_cegar += models_pruned / self.models_total if self.stage_cegar else 0
        self.stage_pruned_cegis += models_pruned / self.models_total if not self.stage_cegar else 0

        # allow cegis another stage step if some time remains
        if not self.stage_cegar and self.stage_timer.read() < self.cegis_allocated_time:
            return False

        # stage is finished: record time
        self.stage_timer.stop()
        current_time = self.stage_timer.read()
        if self.stage_cegar:
            # cegar stage over: allocate time for cegis and switch
            self.stage_time_cegar += current_time
            self.cegis_allocated_time = current_time * self.cegis_allocated_time_factor
            self.stage_start(request_stage_cegar=False)
            return True

        # cegis stage over
        self.stage_time_cegis += current_time

        # calculate average success rate, update stage score
        success_rate_cegar = self.stage_pruned_cegar / self.stage_time_cegar
        success_rate_cegis = self.stage_pruned_cegis / self.stage_time_cegis
        if success_rate_cegar > success_rate_cegis:
            # cegar wins the stage
            self.stage_score += 1
            if self.stage_score >= self.stage_score_limit:
                # cegar wins the synthesis
                # print("> only cegar")
                self.stage_switch_allowed = False
                # switch back to cegar
                self.stage_start(request_stage_cegar=True)
                return True
        elif success_rate_cegar < success_rate_cegis:
            # cegis wins the stage
            self.stage_score -= 1
            if self.stage_score <= -self.stage_score_limit:
                # cegar wins the synthesis
                # print("> only cegis")
                self.stage_switch_allowed = False
                # no need to switch
                return False

        # neither method prevails: adjust cegis time allocation factor
        if self.stage_pruned_cegar == 0 or self.stage_pruned_cegis == 0:
            cegar_dominance = 1
        else:
            cegar_dominance = success_rate_cegar / success_rate_cegis
        cegis_dominance = 1 / cegar_dominance
        self.stage_time_allocation_cegis = cegis_dominance

        # stage log
        if PRINT_STAGE_INFO:
            print("> ", end="")
            print(
                f"{success_rate_cegar:.2e} \\\\ {success_rate_cegis:.2e} = {cegis_dominance:.1e} ({self.stage_score})"
            )

        # switch back to cegar
        self.stage_start(request_stage_cegar=True)
        return True

    # ----- CE quality ----- #

    # def construct_global_cex_generator(self, family):
    #     self.statistic.timer.stop()
    #     self.stage_timer.stop()

    #     if self.ce_quality_compute:
    #         Family.global_cex_generator = stormpy.synthesis.SynthesisCounterexample(
    #             family.mdp, len(Family.hole_list), family.state_to_hole_indices, self.formulae, family.bounds
    #         )

    #     self.stage_timer.start()
    #     self.statistic.timer.start()

    def ce_quality_measure(
            self, assignments, relevant_holes, counterexample_generator, dtmc, dtmc_state_map, formula_idx
    ):
        if not IntegratedChecker.ce_quality:
            return
        self.statistic.timer.stop()
        self.stage_timer.stop()

        # maxsat
        self.ce_maxsat_timer.start()
        instance = self.build_instance(assignments)
        if IntegratedChecker.ce_maxsat:
            _, conflict_maxsat = self._verifier.naive_check(instance, all_conflicts=True)
            conflict_maxsat = conflict_maxsat.pop() if conflict_maxsat else []
            conflict_maxsat = [hole for hole in conflict_maxsat if hole in relevant_holes]
            self.ce_maxsat += safe_division(len(conflict_maxsat), len(relevant_holes))
        self.ce_maxsat_timer.stop()

        # zero
        self.ce_zero_timer.start()
        counterexample_generator.prepare_dtmc(dtmc, dtmc_state_map)
        conflict_zero = counterexample_generator.construct_conflict(formula_idx, use_bounds=False)
        self.ce_zero += safe_division(len(conflict_zero), len(relevant_holes))
        self.ce_zero_timer.stop()

        # global
        # self.ce_global_timer.start()
        # Family.global_cex_generator.prepare_dtmc(dtmc, dtmc_state_map)
        # conflict_global = Family.global_cex_generator.construct_conflict(formula_idx, use_bounds=True)
        # self.ce_global += safe_division(len(conflict_global), len(relevant_holes))
        # self.ce_global_timer.stop()

        # local
        self.ce_local_timer.start()
        counterexample_generator.prepare_dtmc(dtmc, dtmc_state_map)
        conflict_local = counterexample_generator.construct_conflict(formula_idx, use_bounds=True)
        self.ce_local += safe_division(len(conflict_local), len(relevant_holes))
        self.ce_local_timer.stop()

        # resume timers
        self.stage_timer.start()
        self.statistic.timer.start()

    def get_ce_quality_string(self):
        if not IntegratedChecker.ce_quality:
            return ""
        if self.iterations_cegis == 0:
            return "> ce quality: n/a"
        else:
            stats = f"ce quality: maxsat: {self.ce_maxsat / self.iterations_cegis:1.4f}, " + \
                    f"trivial: {self.ce_zero / self.iterations_cegis:1.4f}, " \
                    f"non-trivial: {self.ce_local / self.iterations_cegis:1.4f}"
            times = f"ce time: " + \
                    f"maxsat: {self.ce_maxsat_timer.read() / self.iterations_cegis:1.4f}, " + \
                    f"trivial: {self.ce_zero_timer.read() / self.iterations_cegis:1.4f}, " + \
                    f"non-trivial: {self.ce_local_timer.read() / self.iterations_cegis:1.4f}\n"
            return stats + "\n" + times

    # ----- CE quality ----- #

    def _construct_violation_property(self, family_ref, cex_generator=None):
        vp_index = len(self.formulae) - 1  # Compute the index of the violation property

        # Construct new violation property with respect to the currently optimal value
        vp = self._optimality_setting.get_violation_property(
            self._optimal_value,
            lambda x: self.sketch.expression_manager.create_rational(stormpy.Rational(x)),
        )

        # Update the attributes of the family according to the new optimal values
        # For each family we need to update theirs formulae and formulae indices to check
        for family in self.families + [family_ref]:
            # Replace the last violation property by newly one
            family.formulae[vp_index] = vp.raw_formula
            # When the violation property is not checking, we have to add its index
            if vp_index not in family.formulae_indices:
                family.formulae_indices.append(vp_index)
                family.model_check_formula(vp_index)
                family.bounds[vp_index] = Family.quotient_container().latest_result.result

        # Change the value of threshold of the violation formulae within constructed quotient MDP
        Family.set_thresholds(Family.get_thresholds()[:-1] + [vp.raw_formula.threshold])

        # Update counter-example generator for violation property
        if cex_generator is not None:
            cex_generator.replace_formula_threshold(
                vp_index, vp.raw_formula.threshold_expr.evaluate_as_double(), family_ref.bounds[vp_index]
            )
            # Family.global_cex_generator.replace_formula_threshold(
            #     vp_index, vp.raw_formula.threshold_expr.evaluate_as_double(), family_ref.bounds[vp_index]
            # )

    def _check_optimal_property(self, family_ref, assignment, cex_generator=None, optimal_value=None):

        if optimal_value is None:
            assert family_ref.dtmc is not None
            # Model checking of the optimality property
            result = stormpy.model_checking(family_ref.dtmc, self._optimality_setting.criterion)
            optimal_value = result.at(family_ref.dtmc.initial_states[0])

        # Check whether the improvement was achieved
        if self._optimality_setting.is_improvement(optimal_value, self._optimal_value):
            # Set the new values of the optimal attributes
            self._optimal_value = optimal_value
            self._optimal_assignment = assignment

            # Construct the violation property according newly found optimal value
            self._construct_violation_property(family_ref, cex_generator)

            logger.debug(f"Optimal value improved to: {self._optimal_value}")
            return True

    def analyze_family_cegis(self, family):
        """
        Analyse a family against selected formulae using precomputed MDP data
        to construct generalized counterexamples.
        """

        # TODO preprocess only formulae of interest

        logger.debug(f"CEGIS: analyzing family {family.options} of size {family.size}.")

        assert family.constructed
        assert family.analyzed

        # list of relevant holes (open constants) in this subfamily
        relevant_holes = [hole for hole in family.hole_list if len(family.hole_options[hole]) > 1]

        # prepare counterexample generator
        logger.debug("CEGIS: preprocessing quotient MDP")
        Profiler.start("_")
        counterexample_generator = stormpy.synthesis.SynthesisCounterexample(
            family.mdp, len(Family.hole_list), family.state_to_hole_indices, self.formulae, family.bounds
        )
        Profiler.stop()

        # process family members
        Profiler.start("is - pick DTMC")
        assignment = family.pick_member()
        Profiler.stop()

        while assignment is not None:
            self.iterations_cegis += 1
            logger.debug(f"CEGIS: iteration {self.iterations_cegis}.")
            logger.debug(f"CEGIS: picked family member: {assignment}.")

            # collect indices of violated formulae
            violated_formulae_indices = []
            for formula_index in family.formulae_indices:
                # logger.debug(f"CEGIS: model checking DTMC against formula with index {formula_index}.")
                Profiler.start("is - DTMC model checking")
                Family.dtmc_checks_inc()
                sat, _ = family.analyze_member(formula_index)
                Profiler.stop()
                logger.debug(f"Formula {formula_index} is {'SAT' if sat else 'UNSAT'}")
                if not sat:
                    violated_formulae_indices.append(formula_index)
            if (not violated_formulae_indices or violated_formulae_indices == [len(self.formulae) - 1]) \
                    and self.input_has_optimality_property():
                self._check_optimal_property(family, assignment, counterexample_generator)
            elif not violated_formulae_indices:
                Profiler.add_ce_stats(counterexample_generator.stats)
                return True

            # some formulae UNSAT: construct counterexamples
            # logger.debug("CEGIS: preprocessing DTMC.")
            Profiler.start("_")
            counterexample_generator.prepare_dtmc(family.dtmc, family.dtmc_state_map)
            Profiler.stop()

            Profiler.start("is - constructing CE")
            conflicts = []
            for formula_index in violated_formulae_indices:
                # logger.debug(f"CEGIS: constructing CE for formula with index {formula_index}.")
                conflict_indices = counterexample_generator.construct_conflict(formula_index)
                # conflict = counterexample_generator.construct(formula_index, self.use_nontrivial_bounds)
                conflict_holes = [Family.hole_list[index] for index in conflict_indices]
                generalized_count = len(Family.hole_list) - len(conflict_holes)
                logger.debug(
                    f"CEGIS: found conflict involving {conflict_holes} (generalized {generalized_count} holes)."
                )
                conflicts.append(conflict_indices)

                # compare to maxsat, state exploration, naive hole exploration, global vs local bounds
                self.ce_quality_measure(
                    assignment, relevant_holes, counterexample_generator,
                    family.dtmc, family.dtmc_state_map, formula_index
                )

            family.exclude_member(conflicts)
            Profiler.stop()

            # pick next member
            Profiler.start("is - pick DTMC")
            assignment = family.pick_member()
            Profiler.stop()

            # record stage
            if self.stage_step(0) and not ONLY_CEGIS:
                # switch requested
                Profiler.add_ce_stats(counterexample_generator.stats)
                return None

        # full family pruned
        logger.debug("CEGIS: no more family members.")
        Profiler.add_ce_stats(counterexample_generator.stats)
        return False

    def run_feasibility(self):
        """
        Run feasibility synthesis. Return either a satisfying assignment (feasible) or None (unfeasible).
        """
        Profiler.initialize()
        logger.info("Running feasibility synthesis.")

        # initialize family description
        Profiler.start("_")
        logger.debug("Constructing quotient MDP of the superfamily.")
        FamilyHybrid.initialize(
            self.sketch, self.holes, self.hole_options, self.symmetries,
            self.differents, self.formulae, self.mc_formulae, self.mc_formulae_alt,
            self.thresholds, self._accept_if_above, self._optimality_setting
        )

        # get the first family to analyze
        Profiler.start("_")
        family = FamilyHybrid()
        family.construct()
        Profiler.stop()
        satisfying_assignment = None

        # CEGAR the superfamily
        self.models_total = family.size
        self.stage_start(request_stage_cegar=True)
        self.iterations_cegar += 1
        logger.debug(f"CEGAR: iteration {self.iterations_cegar}.")
        Profiler.start("ar - MDP model checking")
        feasible, optimal_value = family.analyze()
        Profiler.stop()
        # self.construct_global_cex_generator(family)

        if optimal_value is not None:
            self._check_optimal_property(
                family, family.member_assignment, cex_generator=None, optimal_value=optimal_value
            )
        elif feasible and isinstance(feasible, bool) and self._optimality_setting is None:
            return family.member_assignment, None
        elif not feasible and isinstance(feasible, bool) and self._optimality_setting is None:
            return None, None
        self.stage_step(0)

        # initiate CEGAR-CEGIS loop (first phase: CEGIS) 
        self.families = [family]
        logger.debug("Initiating CEGAR--CEGIS loop")
        while self.families:
            logger.debug(f"Current number of families: {len(self.families)}")

            # pick a family
            family = self.families.pop(-1)
            if not self.stage_cegar:
                # CEGIS
                feasible = self.analyze_family_cegis(family)
                if feasible and isinstance(feasible, bool):
                    logger.debug("CEGIS: some is SAT.")
                    satisfying_assignment = family.member_assignment
                    break
                elif not feasible and isinstance(feasible, bool):
                    logger.debug("CEGIS: all UNSAT.")
                    self.stage_step(family.size)
                    continue
                else:  # feasible is None:
                    # stage interrupted: leave the family to cegar
                    # note: phase was switched implicitly
                    logger.debug("CEGIS: stage interrupted.")
                    self.families.append(family)
                    continue
            else:  # CEGAR
                assert family.split_ready

                # family has already been analysed: discard the parent and refine
                logger.debug("Splitting the family.")
                subfamily_left, subfamily_right = family.split()
                subfamilies = [subfamily_left, subfamily_right]
                logger.debug(
                    f"Constructed two subfamilies of size {subfamily_left.size} and {subfamily_right.size}."
                )

                # analyze both subfamilies
                models_pruned = 0
                for subfamily in subfamilies:
                    self.iterations_cegar += 1
                    logger.debug(f"CEGAR: iteration {self.iterations_cegar}.")
                    subfamily.construct()
                    Profiler.start("ar - MDP model checking")
                    feasible, optimal_value = subfamily.analyze()
                    Profiler.stop()
                    if feasible and isinstance(feasible, bool):
                        logger.debug("CEGAR: all SAT.")
                        satisfying_assignment = subfamily.member_assignment
                        if optimal_value is not None:
                            self._check_optimal_property(
                                subfamily, satisfying_assignment, cex_generator=None, optimal_value=optimal_value
                            )
                        elif satisfying_assignment is not None and self._optimality_setting is None:
                            break
                    elif not feasible and isinstance(feasible, bool):
                        logger.debug("CEGAR: all UNSAT.")
                        models_pruned += subfamily.size
                        continue
                    else:  # feasible is None:
                        logger.debug("CEGAR: undecided.")
                        self.families.append(subfamily)
                        continue
                self.stage_step(models_pruned)

        if PRINT_PROFILING:
            Profiler.print()

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

    def run(self, short_summary):
        self.statistic = Statistic(
            "Hybrid", self.formulae, len(self.holes), self._optimality_setting, short_summary=short_summary
        )
        assignment, optimal_value = self.run_feasibility()
        self.statistic.finished(
            assignment, (self.iterations_cegar, self.iterations_cegis), optimal_value, self.models_total,
            Family.quotient_mdp().nr_states, safe_division(Family.quotient_mdp_stats(0), Family.quotient_mdp_stats(1)),
            Family.mdp_checks(), safe_division(Family.dtmc_stats(0), Family.dtmc_stats(1)), Family.dtmc_checks(),
            self.get_ce_quality_string()
        )


class Hybrid:
    """Entry point: execution setup."""

    def __init__(
            self, backward_cuts, sketch_path, allowed_path, property_path, optimality_path,
            constants, restrictions, restriction_path, regime, short_summary, ce_quality, ce_maxsat
    ):

        self.sketch_path = sketch_path
        self.allowed_path = allowed_path
        self.property_path = property_path
        self.optimality_path = optimality_path
        self.constants = constants
        self.restrictions = restrictions
        self.restriction_path = restriction_path
        self.short_summary = short_summary
        self.backward_cuts = backward_cuts

        IntegratedChecker.ce_quality = ce_quality
        IntegratedChecker.ce_maxsat = ce_maxsat
        IntegratedChecker.stage_score_limit = STAGE_SCORE_LIMIT
        stats = []

        if regime == 0:
            stats.append(self.run_algorithm(EnumerationChecker))
        elif regime == 1:
            stats.append(self.run_algorithm(CEGISChecker))
        elif regime == 2:
            stats.append(self.run_algorithm(CEGARChecker))
        elif regime == 3:
            stats.append(self.run_algorithm(IntegratedChecker))
        else:
            assert None

        print("\n")
        for stat in stats:
            print(stat)

    def run_algorithm(self, algorithm_class):
        print("\n\n\n")
        print(algorithm_class.__name__)
        algorithm = algorithm_class()
        algorithm.load_sketch(
            self.sketch_path, self.property_path, optimality_path=self.optimality_path, constant_str=self.constants
        )
        algorithm.load_template_definitions(self.allowed_path)
        if self.restrictions:
            algorithm.load_restrictions(self.restriction_path)
        algorithm.initialise()
        algorithm.run(self.short_summary)
        return algorithm.statistic
