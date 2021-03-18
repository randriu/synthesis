import logging
import z3

from collections import OrderedDict

import stormpy
import stormpy.pars

from ..family_checkers.familychecker import HoleOptions
from ..family_checkers.quotientbased import LiftingChecker
from ..jani.jani_quotient_builder import JaniQuotientBuilder
from ..jani.quotient_container import ThresholdSynthesisResult
from ..model_handling.mdp_handling import MC_ACCURACY_THRESHOLD
from ..profiler import Profiler

logger = logging.getLogger(__name__)


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
    _parameters = None

    # - indexed hole options
    hole_list = None
    hole_not_generalized = None
    _hole_indices = None

    # - jani representation + sparse MDP representation
    _quotient_container = None
    _quotient_mdp = None
    _quotient_builder = None

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
            if hole in self._parameters:
                hole_clauses[hole] = z3.And(var >= self.options[hole][0], var <= self.options[hole][1])
            else:
                hole_clauses[hole] = z3.Or(
                    [var == (Family._hole_option_indices[hole][option]) for _, option in enumerate(self.options[hole])]
                )
        self.encoding = z3.And(list(hole_clauses.values()))

        # a family that has never been MDP-analyzed is not ready to be split
        self.bounds = [None] * len(Family._formulae)  # assigned when analysis is initiated
        self.suboptions = None
        self.member_assignment = None

    @staticmethod
    def initialize(
            _sketch, _holes, _hole_options, _parameters, symmetries, differents, _formulae,
            _mc_formulae, _mc_formulae_alt, _thresholds, _accept_if_above, optimality_setting
    ):

        Family._sketch = _sketch
        Family._holes = _holes
        Family._hole_options = _hole_options
        Family._parameters = _parameters

        # map holes to their indices
        Family.hole_list = list(Family._holes.keys())
        Family._hole_indices = dict()
        for hole_index, hole in enumerate(Family.hole_list):
            Family._hole_indices[hole] = hole_index

        # map hole options to their indices
        Family._hole_option_indices = dict()
        for hole, options in Family._hole_options.items():
            indices = dict()
            for idx, option in enumerate(options):
                indices[option] = idx
            Family._hole_option_indices[hole] = indices

        # initialize z3 solver
        Family._solver = z3.Solver()
        Family._solver_meta_vars = OrderedDict()
        variables = dict()
        for k, v in Family._hole_options.items():
            var = z3.Real(k) if v[0].type.is_rational else z3.Int(k)
            Family._solver.add((var >= v[0], var <= v[1]) if k in Family._parameters else (var >= 0, var < len(v)))
            Family._solver_meta_vars[var] = k
            variables[k] = var

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
        Family._quotient_builder = JaniQuotientBuilder(Family._sketch, Family._holes)
        Family._quotient_container = Family._quotient_builder.construct(
            Family._hole_options, Family._parameters, remember=set()
        )
        Family._quotient_container.prepare(Family._mc_formulae, Family._mc_formulae_alt, param=bool(Family._parameters))
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
        # if self.constructed:
        #     return

        Profiler.start("ar - MDP construction")

        logger.debug(f"Constructing quotient MDP for family {self.options}.")
        indexed_options = Family._hole_options.index_map(self.options, self._parameters)
        Family._quotient_container.consider_subset(self.options, indexed_options)
        self.mdp = Family._quotient_container.mdp_handling.mdp
        self.choice_map = Family._quotient_container.mdp_handling.mapping_to_original
        logger.debug(f"Constructed MDP of size {self.mdp.nr_states}.")
        Family._quotient_mdp_stats = (
            Family._quotient_mdp_stats[0] + self.mdp.nr_states, Family._quotient_mdp_stats[1] + 1
        )

        Profiler.stop()

    def _construct_region(self):
        region_valuation = {}
        for parameter in self.mdp.collect_probability_parameters():
            region_valuation[parameter] = (
                stormpy.RationalRF(self.options[parameter.name][0].evaluate_as_double()),
                stormpy.RationalRF(self.options[parameter.name][1].evaluate_as_double())
            )
        return stormpy.pars.ParameterRegion(region_valuation)

    def model_check_formula(self, formula_index):
        """
        Model check the underlying quotient MDP against a given formula.
        Return feasibility (SAT = True, UNSAT = False, ? = None) as well as the model checking result.
        """
        assert self.constructed

        threshold = float(Family._thresholds[formula_index])
        Family._quotient_container.analyse(
            threshold, formula_index, region=self._construct_region() if self.mdp.has_parameters else None
        )

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

        options = {k: [round(v.evaluate_as_double(), 10) for v in vs] for k, vs in self.options.items()}
        logger.debug(f"CEGAR: analyzing family {options} of size {self.size}.")

        undecided_formulae_indices = []
        optimal_value = None
        for formula_index in self.formulae_indices:
            # logger.debug(f"CEGAR: model checking MDP against a formula with index {formula_index}.")
            Family.mdp_checks_inc()
            feasible, self.bounds[formula_index] = self.model_check_formula(formula_index)

            if not feasible and isinstance(feasible, bool):
                logger.debug(f"Formula {formula_index}: UNSAT")
                undecided_formulae_indices = None  # TODO: Check safeness -- probably ok -> family is destroyed
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

    def _round_robin_split(self):
        def create_expression(num):
            return self._sketch.expression_manager.create_rational(stormpy.Rational(num))

        def interval_len(option):
            return (self.options[option][1].evaluate_as_double() - self.options[option][0].evaluate_as_double()) / 1.0

        def split_options_at_half(options):
            return options[:len(options) // 2], options[len(options) // 2:]

        def get_sub_intervals(start, end, n):
            w = (end - start) / n
            # print(f">> {[[start + i * w, start + (i + 1) * w] for i in range(n)]}")
            return [[create_expression(start + i * w), create_expression(start + (i + 1) * w)] for i in range(n)]

        def construct_split_queue(sub_options):
            for sub_option in sub_options:
                split_queue.append(HoleOptions(self.options))
                split_queue[-1][hole] = sub_option

        options_lengths = [(k, interval_len(k) if k in self._parameters else len(v)) for k, v in self.options.items()]
        singletons = set(filter(lambda x: x[0] not in self._parameters and x[1] == 1, options_lengths))
        options_lengths = list(set(options_lengths) - singletons)
        sorted_options = sorted(options_lengths, key=lambda x: (x[1], x[0]), reverse=True)
        absolute_diff = \
            self._quotient_container.latest_result.absolute_max - self._quotient_container.latest_result.absolute_min
        # print(f">> {absolute_diff}")
        (hole, length) = sorted_options.pop(0) if sorted_options else (None, 0)
        if hole in self._parameters and absolute_diff <= MC_ACCURACY_THRESHOLD:
            hole, length = None, 0
        # print(f">> {hole}: {length}")

        split_queue = []
        sub_intervals_n = 2
        if hole and hole in self._parameters:
            sub_intervals = get_sub_intervals(
                self.options[hole][0].evaluate_as_double(), self.options[hole][1].evaluate_as_double(), sub_intervals_n
            )
            construct_split_queue(sub_intervals)
        elif hole:
            left_part, right_part = split_options_at_half(self.options[hole])
            construct_split_queue([left_part, right_part])
        else:
            split_queue = None
        assert len(split_queue) == sub_intervals_n if hole in self._parameters else True
        assert len(split_queue) == 2 if hole and hole not in self._parameters else True
        return split_queue

    def prepare_split(self, strict=False):
        # logger.debug(f"Preparing to split family {self.options}")
        assert self.constructed and not self.split_ready
        Profiler.start("ar - splitting")
        if self._parameters and not strict:
            self.suboptions = self._round_robin_split()
        else:
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
            if hole in Family._parameters:
                assignment[hole] = [Family._quotient_builder.expression_manager.create_rational(stormpy.Rational(
                    float(sat_model[var].numerator_as_long()) / float(sat_model[var].denominator_as_long())
                ))]
            else:
                assignment[hole] = [Family._hole_options[hole][sat_model[var].as_long()]]
        self.member_assignment = assignment

        return self.member_assignment

    def pick_whole_family(self):
        assignment = HoleOptions()
        for hole, vals in self.options.items():
            assignment[hole] = vals
        self.member_assignment = assignment

    def check_optimal_property(self, feasible):
        is_max = True if self._optimality_setting.direction == "max" else False
        oracle = Family._quotient_container
        optimal_value = None
        decided = None
        if feasible is None:
            logger.debug("Family is UNDECIDED for optimal property.")
            if not self.split_ready:
                self.prepare_split(strict=True)
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
                self.prepare_split(strict=True)
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
