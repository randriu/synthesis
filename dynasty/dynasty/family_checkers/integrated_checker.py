# author: Roman Andriushchenko
# co-author: Simon Stupinsky

import logging
import math
import z3

import operator
import stormpy

from collections import OrderedDict
from collections.abc import Iterable

from ..jani.jani_quotient_builder import logger as jani_quotient_builder_logger, JaniQuotientBuilder
from ..jani.quotient_container import logger as quotient_container_logger, ThresholdSynthesisResult
from ..model_handling.mdp_handling import ExplicitMCResult, logger as model_handling_logger
from ..profiler import Profiler, Timer
from .cegis import Synthesiser
from .quotientbased import LiftingChecker, OneByOneChecker, QuotientBasedFamilyChecker, logger as quotienbased_logger
from .familychecker import HoleOptions

# ------------------------------------------------------------------------------
# logging

logger = logging.getLogger(__name__)
dynasty.jani.quotient_container.logger.disabled = True
dynasty.jani.jani_quotient_builder.logger.disabled = True
dynasty.jani.jani_quotient_builder.logger.disabled = True
# dynasty.model_handling.mdp_handling.logger.disabled = True

quotienbased_logger.disabled = True
quotient_container_logger.disabled = True
jani_quotient_builder_logger.disabled = True
model_handling_logger.disabled = True

ONLY_CEGAR = False
ONLY_CEGIS = False
NONTRIVIAL_BOUNDS = True
PRINT_STAGE_INFO = False
PRINT_PROFILING = True


# MANUAL MODEL CHECKING ------------------------------------------------------------------------- MANUAL MODEL CHECKING


def check_dtmc(dtmc, formula, quantitative=False):
    """Model check a DTMC against a (quantitative) property."""
    threshold = formula.threshold_expr.evaluate_as_double()
    if quantitative:
        formula = formula.clone()
        formula.remove_bound()

    result = stormpy.model_checking(dtmc, formula)
    satisfied = result.at(dtmc.initial_states[0])
    if quantitative:
        op = {
            stormpy.ComparisonType.LESS: operator.lt,
            stormpy.ComparisonType.LEQ: operator.le,
            stormpy.ComparisonType.GREATER: operator.gt,
            stormpy.ComparisonType.GEQ: operator.ge
        }[formula.comparison_type]
        satisfied = op(satisfied, threshold)
    return satisfied, result


def check_mdp(mdp, formula, alt_formula, threshold, accept_if_above):
    """
    Model check an MDP against a property.
    Note: the following is a copy of ModelHandling::mc_model and JaniQuotientContainer::decided
    """

    is_dtmc = mdp.nr_choices == mdp.nr_states
    extract_scheduler = not is_dtmc

    # TODO set from the outside.
    env = stormpy.Environment()
    env.solver_environment.minmax_solver_environment.precision = stormpy.Rational(0.000001)
    method = stormpy.MinMaxMethod.policy_iteration if is_dtmc else stormpy.MinMaxMethod.value_iteration
    env.solver_environment.minmax_solver_environment.method = method

    assert not formula.has_bound

    logger.info(f"Start checking direction 1: {formula}")
    prime_result = stormpy.model_checking(
        mdp, formula, only_initial_states=False, extract_scheduler=extract_scheduler, environment=env
    )

    if is_dtmc:
        absolute_min = min([prime_result.at(x) for x in mdp.initial_states])
        absolute_max = max([prime_result.at(x) for x in mdp.initial_states])
        logger.info(f"Done DTMC Checking. Result for initial state is: {absolute_min} -- {absolute_max}")
        return ExplicitMCResult(
            prime_result, prime_result, True, None, None, absolute_min=absolute_min, absolute_max=absolute_max
        )

    absolute_min = -math.inf
    absolute_max = math.inf

    maximise = formula.optimality_type == stormpy.OptimizationDirection.Maximize
    if maximise:
        absolute_max = max([prime_result.at(x) for x in mdp.initial_states])
    else:
        absolute_min = min([prime_result.at(x) for x in mdp.initial_states])

    if absolute_min < threshold < absolute_max:
        logger.info(f"Start checking direction 2: {alt_formula}")
        second_result = stormpy.model_checking(
            mdp, alt_formula, only_initial_states=False, extract_scheduler=extract_scheduler, environment=env
        )

        if maximise:
            absolute_min = min([second_result.at(x) for x in mdp.initial_states])
        else:
            absolute_max = max([second_result.at(x) for x in mdp.initial_states])

    logger.info(f"Done Checking. Result for initial state is: {absolute_min} -- {absolute_max}")

    # result interpretation
    logger.debug(f"Absolute minimum: {absolute_min}, Absolute maximum {absolute_max}, threshold: {threshold}")
    if threshold > absolute_max:
        logger.debug(f"Absolute maximum {absolute_max} is below threshold {threshold}")
        threshold_synthesis_result = ThresholdSynthesisResult.BELOW
    elif threshold <= absolute_min:
        logger.debug(f"Absolute minimum {absolute_min} is above threshold {threshold}")
        threshold_synthesis_result = ThresholdSynthesisResult.ABOVE
    else:
        logger.debug("Threshold is between")
        threshold_synthesis_result = ThresholdSynthesisResult.UNDECIDED

    if threshold_synthesis_result == ThresholdSynthesisResult.UNDECIDED:
        feasible = None
    else:
        all_above = (threshold_synthesis_result == ThresholdSynthesisResult.ABOVE)
        feasible = (all_above == accept_if_above)

    return feasible, prime_result


# Synthesis wrappers ------------------------------------------------------------------------------ Synthesis wrappers

def readable_assignment(assignment):
    # return {k:v[0].__str__() for (k,v) in assignment.items()} if assignment is not None else None
    return ",".join(["{}={}".format(k,v[0].__str__()) for (k,v) in assignment.items()]) if assignment is not None else None

class Statistic:
    """General computation stats."""

    def __init__(self, method, threshold):
        self.method = method
        self.threshold = threshold
        self.timer = Timer()
        self.timer.start()
        self.feasible = False
        self.assignment = {}
        self.iterations = 0

    def finished(self, assignment, iterations):
        self.timer.stop()
        self.feasible = assignment is not None
        self.assignment = readable_assignment(assignment)
        self.iterations = iterations

    def __str__(self):
        feasible = "F" if self.feasible else "U"
        time = int(self.timer.time)
        return "> T={:g} : {} : {} ({} iters, {} sec)\n".format(self.threshold, self.method, feasible, self.iterations, time)
        # return "> {}".format(self.iterations) # FIXME

class EnumerationChecker(OneByOneChecker):
    """1-by-1 enumeration wrapper."""

    def __init__(self, *args):
        super().__init__(*args)
        self.statistic = None

    def run(self):
        threshold = float(self.properties[0].raw_formula.threshold)  # FIXME
        self.statistic = Statistic("1-by-1", threshold)
        iterations = self.run_feasibility()
        assignment = None  # we do not care about assignment
        self.statistic.finished(assignment, iterations)


class CEGISChecker(Synthesiser):
    """CEGIS wrapper."""

    def __init__(self, *args):
        super().__init__(*args)
        self.statistic = None

    def run(self):
        threshold = float(self.properties[0].raw_formula.threshold)  # FIXME
        self.statistic = Statistic("CEGIS", threshold)
        _, assignment, _ = self.run_feasibility()
        assignment = {k:[v] for (k,v) in assignment.items()} if assignment is not None else None
        if assignment is not None:
            logger.info("Found satisfying assignment: {}".format(readable_assignment(assignment)))
        self.statistic.finished(assignment, self.stats.iterations)


class CEGARChecker(LiftingChecker):
    """CEGAR wrapper."""
    
    def __init__(self,*args):
        super().__init__(*args)
        self.iterations = 0

    def initialise(self):
        super().initialise()
        self.formulae = [property.raw_formula for property in self.properties]
        # no optimality support (TODO Simon)
        assert not self.input_has_optimality_property()

    def run_feasibility(self):
        '''
        Run feasibility synthesis. Return either a satisfying assignment
        (feasible) or None (unfeasible).
        '''
        Profiler.initialize()
        logger.info("Running feasibility synthesis.")

        # initialize family description
        logger.debug("Constructing quotient MDP of the superfamily.")
        Family.initialize(
            self.sketch, self.holes, self.hole_options, self.symmetries,
            self.differents, self.formulae, self.mc_formulae, self.mc_formulae_alt,
            self.thresholds, self._accept_if_above
            )

        # initiate CEGAR loop
        family = Family()
        families = [family]
        satisfying_assignment = None
        logger.debug("Initiating CEGAR loop")
        while families != []:
            logger.debug("Current number of families: {}".format(len(families)))
            self.iterations += 1
            logger.debug("CEGAR: iteration {}.".format(self.iterations))
            family = families.pop(-1)
            family.construct()
            feasible = family.analyze()
            if feasible == True:
                logger.debug("CEGAR: all SAT.")
                satisfying_assignment = family.member_assignment
                if satisfying_assignment is not None:
                    break
            elif feasible == False:
                logger.debug("CEGAR: all UNSAT.")
            else: # feasible is None:
                logger.debug("CEGAR: undecided.")
                logger.debug("Splitting the family.")
                subfamily_left,subfamily_right = family.split()
                logger.debug("Constructed two subfamilies of size {} and {}.".format(subfamily_left.size, subfamily_right.size))
                families.append(subfamily_left)
                families.append(subfamily_right)
    
        if satisfying_assignment is not None:
            logger.info("Found satisfying assignment: {}".format(readable_assignment(satisfying_assignment)))
            return satisfying_assignment
        else:
            logger.info("No more options.")
            return None
        
    def run(self):
        threshold = float(self.properties[0].raw_formula.threshold)  # FIXME
        self.statistic = Statistic("CEGAR", threshold)
        # _, assignment, _ = self.run_feasibility()
        assignment = self.run_feasibility()
        self.statistic.finished(assignment, self.iterations)


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
    '''

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

    def __init__(self, parent=None, options=None):
        """
        Construct a family. Each family is either a superfamily represented by
        a Family._quotient_mdp or a (proper) subfamily that is constructed on
        demand via Family._quotient_container.consider_subset(). Subfamilies
        inherit formulae of interest from their parents.
        """
        self.options = Family._hole_options.copy() if parent is None else options
        self.mdp = Family._quotient_mdp if parent is None else None
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
            _mc_formulae, _mc_formulae_alt, _thresholds, _accept_if_above
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

        # build quotient MDP
        quotient_builder = JaniQuotientBuilder(Family._sketch, Family._holes)
        Family._quotient_container = quotient_builder.construct(Family._hole_options, remember=set())
        Family._quotient_container.prepare(Family._mc_formulae, Family._mc_formulae_alt)
        Family._quotient_mdp = Family._quotient_container._mdp_handling.full_mdp
        logger.debug("Constructed MDP of size {}.".format(Family._quotient_mdp.nr_states))

    def __init__(self, parent = None, options = None):
        '''
        Construct a family. Each family is either a superfamily represented by
        a Family._quotient_mdp or a (proper) subfamily that is constructed on
        demand via Family._quotient_container.consider_subset(). Subfamilies
        inherit formulae of interest from their parents.
        '''

        if parent is None:
            # construct the superfamily
            self.options = Family._hole_options.copy()
            self.mdp = Family._quotient_mdp
            self.choice_map = [i for i in range(Family._quotient_mdp.nr_choices)]
            self.formulae_indices = [i for i in range(len(Family._formulae))]
        else:
            # construct a subfamily
            self.options = options
            self.mdp = None # constructed only for the purpose of analysis
            self.choice_map = None
            self.formulae_indices = parent.formulae_indices

        # encode this family
        hole_clauses = dict()
        for var,hole in Family._solver_metavariables.items():
            hole_clauses[hole] = z3.Or([var == Family._hole_option_indices[hole][option] for option in self.options[hole]])
        self.encoding = z3.And(list(hole_clauses.values()))

        # a family that has never been MDP-analyzed is not ready to be split
        self.bounds = [None for index in range(len(Family._formulae))] # assigned when analysis is initiated
        self.suboptions = None
        self.member_assignment = None

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

    def construct(self):
        """ Construct quotient MDP for this family using the quotient container. """
        if self.constructed:
            return
        
        Profiler.start("ar - MDP construction")

        logger.debug(f"Constructing quotient MDP for family {self.options}.")
        indexed_options = Family._hole_options.index_map(self.options)
        Family._quotient_container.consider_subset(self.options, indexed_options)
        self.mdp = Family._quotient_container._mdp_handling.mdp
        self.choice_map = Family._quotient_container._mdp_handling._mapping_to_original
        logger.debug("Constructed MDP of size {}.".format(self.mdp.nr_states))
        
        Profiler.stop()

    def model_check_formula(self, formula_index):
        """
        Model check the underlying quotient MDP against a given formula.
        Return feasibility (SAT = True, UNSAT = False, ? = None) as well as the
        model checking result.
        '''
        assert self.constructed

        threshold = float(Family._thresholds[formula_index])
        Family._quotient_container.analyse(threshold, formula_index)
        threshold_synthesis_result = Family._quotient_container.decided(threshold)

        return feasible, Family._quotient_container._latest_result.result

    def analyze(self):
        '''
        Analyze the underlying quotient MDP for this subfamily with respect
        to all (yet undecided) formulae and store all model checking results.
        Return feasibility (SAT = True, UNSAT = False, ? = None). Whenever an
        undecidable formula is encountered, prepare the family for splitting.
        In the case of inconclusive result, update the set of undecidable
        formulae for future processing. Otherwise, in the case of satisfying
        result, store a hole assignment.
        Note: we do not check here whether the constructed assignment is not None.
        '''
        assert not self.analyzed    # sanity check
        assert self.constructed

        logger.debug("CEGAR: analyzing family {} of size {}.".format(self.options, self.size))            

        undecided_formulae_indices = []
        for formula_index in self.formulae_indices:
            logger.debug("CEGAR: model checking MDP against a formula with index {}.".format(formula_index))
            feasible,bound = self.model_check_formula(formula_index)
            self.bounds[formula_index] = bound
            if feasible == False:
                logger.debug("formula {}: UNSAT".format(formula_index))
                undecided_formulae_indices = None
                break
            elif feasible is None:
                logger.debug(f"Formula {formula_index}: UNDECIDED")
                undecided_formulae_indices.append(formula_index)
                if not self.split_ready:
                    self.prepare_split()
            else:
                logger.debug("Formula {}: SAT".format(formula_index))

        self.formulae_indices = undecided_formulae_indices

        # postprocessing
        if self.formulae_indices is None:
            return False
        if not self.formulae_indices:
            self.pick_assignment()
            return True
        return None

    def prepare_split(self):
        # logger.debug(f"Preparing to split family {self.options}")
        assert self.constructed and not self.split_ready
        Profiler.start("ar - splitting")
        self.suboptions = self.split_options()
        Profiler.stop()

    def split_options(self):
        '''
        The following is the call of scheduler color analysis followed by
        LiftingChecker::_split_hole_options(self.options, Family._quotient_container)
        '''
        Family._quotient_container.scheduler_color_analysis()
        hole_options = self.options
        oracle = Family._quotient_container

        def split_list(a_list):
            half = len(a_list) // 2
            return a_list[:half], a_list[half:]

        # Where to split.
        splitters = []
        selected_splitter = None
        one_side_list = None
        other_side_list = None

        selected_splitter, one_side_list, other_side_list = oracle.propose_split()
        # logger.debug("Oracle proposes a split at {}".format(selected_splitter))

        if not isinstance(one_side_list, Iterable):
            one_side_list = [one_side_list]
        if not isinstance(other_side_list, Iterable):
            other_side_list = [other_side_list]

        # logger.debug("Proposed (pre)split: {} vs. {}".format(one_side_list, other_side_list))

        if selected_splitter is None:
            # Split longest.
            maxlength = 0
            for k, v in hole_options.items():
                maxlength = max(maxlength, len(v))
                if len(v) == maxlength:
                    selected_splitter = k
            if maxlength == 1:
                raise RuntimeError("Undecided result, but cannot split")


        options = hole_options[selected_splitter]
        # logger.debug("Splitting {}...".format([str(val) for val in options]))
        assert len(options) > 1, "Cannot split along {}".format(selected_splitter)

        one_vals = [Family._hole_options[selected_splitter][one_side] for one_side in one_side_list if one_side is not None]
        other_vals = [Family._hole_options[selected_splitter][other_side] for other_side in other_side_list if
                      other_side is not None]
        # logger.debug("Pre-splitted {} and {}".format(one_vals, other_vals))
        remaining_options = [x for x in options if x not in one_vals + other_vals]
        # logger.debug("Now distribute {}".format(remaining_options))
        second, first = split_list(remaining_options)
        # if one_side is not None:
        first = first + one_vals
        # if other_side is not None:
        second = second + other_vals
        splitters.append([selected_splitter, first, second])

        logger.info("Splitting {} into {} and {}".format(selected_splitter, "[" + ",".join([str(x) for x in first]) + "]",
                                                             "[" + ",".join([str(x) for x in second]) + "]"))

        # split
        assert len(splitters) == 1
        split_queue = [hole_options]
        for splitter in splitters:
            new_split_queue = []
            for options in split_queue:
                new_split_queue.append(HoleOptions(options))
                new_split_queue[-1][splitter[0]] = splitter[1]
                new_split_queue.append(HoleOptions(options))
                new_split_queue[-1][splitter[0]] = splitter[2]
            split_queue = new_split_queue
        assert len(split_queue) == 2
        
        # return
        return split_queue

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


# INTEGRATED METHOD --------------------------------------------------------------------------------- INTEGRATED METHOD

class FamilyHybrid(Family):
    """ Family adopted for CEGAR-CEGIS analysis. """

    # TODO: more efficient state-hole mapping?
    
    _choice_to_hole_indices = None

    def initialize(*args):
        Family.initialize(*args)
        
        # map edges of a quotient container to hole indices
        jani = Family._quotient_container._jani_program
        _edge_to_hole_indices = dict()
        for aut_index,aut in enumerate(jani.automata):
            for edge_index,edge in enumerate(aut.edges):
                if edge.color == 0:
                    continue
                index = jani.encode_automaton_and_edge_index(aut_index,edge_index)
                assignment = Family._quotient_container._edge_coloring.get_hole_assignment(edge.color)
                hole_indices = [index for index,value in enumerate(assignment) if value is not None]
                _edge_to_hole_indices[index] = hole_indices

        # map actions of a quotient MDP to hole indices
        FamilyHybrid._choice_to_hole_indices = []
        choice_origins = Family._quotient_mdp.choice_origins
        matrix = Family._quotient_mdp.transition_matrix
        for state in range(Family._quotient_mdp.nr_states):
            for choice_index in range(matrix.get_row_group_start(state),matrix.get_row_group_end(state)):
                choice_hole_indices = set()
                for index in choice_origins.get_edge_index_set(choice_index):
                    hole_indices = _edge_to_hole_indices.get(index, set())
                    choice_hole_indices.update(hole_indices)
                FamilyHybrid._choice_to_hole_indices.append(choice_hole_indices)

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
        for aut_index, aut in enumerate(jani.automata):
            for edge_index, edge in enumerate(aut.edges):
                if edge.color == 0:
                    continue
                index = jani.encode_automaton_and_edge_index(aut_index, edge_index)
                assignment = Family._quotient_container.edge_coloring.get_hole_assignment(edge.color)
                hole_indices = [index for index, value in enumerate(assignment) if value is not None]
                FamilyHybrid._edge_to_hole_indices[index] = hole_indices

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

        Profiler.start("is - MDP holes")
        logger.debug("Constructing state-holes mapping via choice-holes mapping.")
        self._state_to_hole_indices = []
        matrix = self.mdp.transition_matrix
        for state in range(self.mdp.nr_states):
            state_hole_indices = set()
            for choice_index in range(matrix.get_row_group_start(state),matrix.get_row_group_end(state)):
                quotient_choice_index = self.choice_map[choice_index]
                choice_hole_indices = FamilyHybrid._choice_to_hole_indices[quotient_choice_index]
                state_hole_indices.update(choice_hole_indices)
            state_hole_indices = set([index for index in state_hole_indices if len(self.options[Family._hole_list[index]]) > 1])
            self._state_to_hole_indices.append(state_hole_indices)
        Profiler.stop()
        return self._state_to_hole_indices

    def pick_member(self):
        # pick hole assignment
        self.pick_assignment()
        if self.member_assignment is None:
            return None

        # collect edges relevant for this assignment
        indexed_assignment = Family._hole_options.index_map(self.member_assignment)
        subcolors = Family._quotient_container._edge_coloring.subcolors(indexed_assignment)
        color_0_indices = Family._quotient_container._color_to_edge_indices.get(0)
        collected_edge_indices = stormpy.FlatSet(color_0_indices)
        for c in subcolors:
            collected_edge_indices.insert_set(Family._quotient_container._color_to_edge_indices.get(c))

        # construct the DTMC by exploring the quotient MDP for this subfamily
        dtmc,dtmc_state_map = stormpy.dtmc_from_mdp(self.mdp, collected_edge_indices)

        # assert absence of deadlocks or overlapping guargs
        # TODO does not seem to work (builder options?)
        assert dtmc.labeling.get_states("deadlock").number_of_set_bits() == 0
        assert dtmc.labeling.get_states("overlap_guards").number_of_set_bits() == 0
        assert len(dtmc.initial_states) == 1    # to avoid ambiguity

        logger.debug("Constructed DTMC of size {}.".format(dtmc.nr_states))
        self.dtmc = dtmc
        self.dtmc_state_map = dtmc_state_map

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
        sat, _ = check_dtmc(self.dtmc, Family._formulae[formula_index])
        return sat

# ------------------------------------------------------------------------------
# Family encapsulator


class IntegratedChecker(QuotientBasedFamilyChecker):
    """Integrated checker."""

    stage_score_limit = 99999

    def __init__(self):
        QuotientBasedFamilyChecker.__init__(self)
        self.iterations_cegis = 0
        self.iterations_cegar = 0
        self.formulae = []
        self.statistic = None
        self.models_total = 0
        self.cegis_iterations = 0
        self.cegar_iterations = 0
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

    def initialise(self):
        QuotientBasedFamilyChecker.initialise(self)
        self.formulae = [property.raw_formula for property in self.properties]
        # no optimality support (TODO Simon)
        assert not self.input_has_optimality_property()

    # ----- Adaptivity ----- #
    # Main idea: switch between cegar/cegis, allocate more time to the more efficient method; if one method is
    # consistently better than the other, declare it the winner and stop switching. Cegar wins over cegis by reaching
    # the score limit, cegis wins by reaching the negative score limit.
    # note: this is the only parameter in the integrated synthesis
    stage_score_limit = 99999
    
    use_nontrivial_bounds = True
    only_cegar = False
    # only_cegar = True
    only_cegis = False
    # only_cegis = True

    print_stage_info = False
    print_profiling = False
    # print_profiling = True


    def stage_init(self):
        # once a method wins, set this to false and do not switch between methods
        self.stage_switch_allowed = True
        # +1 point whenever cegar wins the stage, -1 otherwise
        self.stage_score = 0
        
        # cegar/cegis stats
        self.stage_time_cegar = 0
        self.stage_pruned_cegar = 0
        self.stage_time_cegis = 0
        self.stage_pruned_cegis = 0

        # multiplier to derive time allocated for cegis
        # =1 is fair, <1 favours cegar, >1 favours cegis
        self.cegis_allocated_time_factor = 1
        self.stage_timer = Timer()

    def stage_start(self, request_stage_cegar):
        self.stage_cegar = request_stage_cegar
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
        print("> ", end="")
        print("{:.2e} \\\\ {:.2e} = {:.1e} ({})".format(
            success_rate_cegar, success_rate_cegis, cegis_dominance, self.stage_score)
        )

        # switch back to cegar
        self.stage_start(request_stage_cegar=True)
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

        # prepare counterexample generator
        mdp = family.mdp
        hole_count = len(Family._hole_list)
        state_to_hole_indices = family.state_to_hole_indices
        formulae = self.formulae
        bounds = family.bounds
        logger.debug("CEGIS: preprocessing quotient MDP")
        Profiler.start("_")
        counterexample_generator = stormpy.SynthesisResearchCounterexample(mdp, hole_count, state_to_hole_indices, formulae, bounds)
        Profiler.stop()

        # process family members
        Profiler.start("is - pick DTMC")
        assignment = family.pick_member()
        Profiler.stop()

        while assignment is not None:
            self.iterations_cegis += 1
            logger.debug(f"CEGIS: iteration {self.iterations_cegis}.")

            # collect indices of violated formulae
            violated_formulae_indices = []
            for formula_index in family.formulae_indices:
                logger.debug("CEGIS: model checking DTMC against formula with index {}.".format(formula_index))
                Profiler.start("is - DTMC model checking")
                sat = family.analyze_member(formula_index)
                Profiler.stop()
                logger.debug("formula {} is {}".format(formula_index, "SAT" if sat else "UNSAT"))
                if not sat:
                    violated_formulae_indices.append(formula_index)
            if not violated_formulae_indices:  # all formulae SAT
                Profiler.add_ce_stats(counterexample_generator.stats)
                return True

            # some formulae UNSAT: construct counterexamples
            logger.debug("CEGIS: preprocessing DTMC.")
            Profiler.start("_")
            counterexample_generator.prepare_dtmc(family.dtmc, family.dtmc_state_map)
            Profiler.stop()

            Profiler.start("is - constructing CE")
            conflicts = []
            for formula_index in violated_formulae_indices:
                logger.debug(f"CEGIS: constructing CE for formula with index {formula_index}.")
                conflict_indices = counterexample_generator.construct_conflict(formula_index)
                # conflict = counterexample_generator.construct(formula_index, self.use_nontrivial_bounds)
                conflict_holes = [Family.hole_list[index] for index in conflict_indices]
                generalized_count = len(Family.hole_list) - len(conflict_holes)
                logger.debug(
                    f"CEGIS: found conflict involving {conflict_holes} (generalized {generalized_count} holes)."
                )
                conflicts.append(conflict_indices)
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
            self.thresholds, self._accept_if_above
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
        logger.debug("CEGAR: iteration {}.".format(self.iterations_cegar))
        Profiler.start("ar - MDP model checking")
        feasible = family.analyze()
        Profiler.stop()
        if feasible == True:
            return family.member_assignment
        elif not feasible and isinstance(feasible, bool):
            return None
        self.stage_step(0)

        # initiate CEGAR-CEGIS loop (first phase: CEGIS) 
        families = [family]
        logger.debug("Initiating CEGAR--CEGIS loop")
        while families != []:
            logger.debug("Current number of families: {}".format(len(families)))
            
            # pick a family
            family = families.pop(-1)
            if not self.stage_cegar:
                # CEGIS
                feasible = self.analyze_family_cegis(family)
                if feasible and isinstance(feasible, bool):
                    logger.debug("CEGIS: some is SAT.")
                    satisfying_assignment = family.member_assignment
                    break
                elif feasible == False:
                    logger.debug("CEGIS: all UNSAT.")
                    self.stage_step(family.size)
                    continue
                else:  # feasible is None:
                    # stage interrupted: leave the family to cegar
                    # note: phase was switched implicitly
                    logger.debug("CEGIS: stage interrupted.")
                    families.append(family)
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
                    feasible = subfamily.analyze()
                    Profiler.stop()
                    if feasible == True:
                        logger.debug("CEGAR: all SAT.")
                        satisfying_assignment = subfamily.member_assignment
                        if satisfying_assignment is not None:
                            break
                        continue
                    if feasible == False:
                        logger.debug("CEGAR: all UNSAT.")
                        models_pruned += subfamily.size
                        continue
                    else:  # feasible is None:
                        logger.debug("CEGAR: undecided.")
                        families.append(subfamily)
                        continue
                self.stage_step(models_pruned)

        if PRINT_PROFILING:
            Profiler.print()

        if satisfying_assignment is not None:
            logger.info("Found satisfying assignment: {}".format(readable_assignment(satisfying_assignment)))
        else:
            logger.info("No more options.")
        return satisfying_assignment
        

    def run(self):
        threshold = float(self.properties[0].raw_formula.threshold)  # FIXME
        self.statistic = Statistic("Hybrid", threshold)
        assignment = self.run_feasibility()
        self.statistic.finished(assignment, (self.iterations_cegar, self.iterations_cegis))


class Research:
    """Entry point: execution setup."""

    def __init__(
            self, check_prerequisites, backward_cuts, sketch_path, allowed_path, property_path,
            optimality_path, constants, restrictions, restriction_path
    ):

        assert not check_prerequisites

        self.sketch_path = sketch_path
        self.allowed_path = allowed_path
        self.property_path = property_path
        self.optimality_path = optimality_path
        self.constants = constants
        self.restrictions = restrictions
        self.restriction_path = restriction_path

        # workdir = "workspace/log"
        # with open(f"{workdir}/parameters.txt", 'r') as f:
        #     lines = f.readlines()
        #     regime = int(lines[0])
        #     stage_score_limit = int(lines[1])

        regime = 3
        stage_score_limit = 99999
        IntegratedChecker.stage_score_limit = stage_score_limit
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
    
    def run_algorithm(self, algorithmClass):
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
        algorithm.run()
        return algorithm.statistic

# ------------------------------------------------------------------------------

# short-term archive

# ----
# splitting

    # def split_at_hole(hole_options,hole):
    #     def split_list(a_list):
    #         half = len(a_list) // 2
    #         return a_list[:half], a_list[half:]

    #     suboptions_left = hole_options.copy()
    #     suboptions_right = hole_options.copy()
    #     split_left, split_right = split_list(hole_options[hole])
    #     suboptions_left[hole] = split_left
    #     suboptions_right[hole] = split_right
    #     return suboptions_left, suboptions_right

    # def split_options_first(self):
    #     splittable = [hole for hole,options in self.options.items() if len(options) > 1]
    #     assert splittable != []
    #     hole = splittable[0]
    #     l,r = Family.split_at_hole(self.options,hole)
    #     return [l,r]

    # def split_options_last(self):
    #     splittable = [hole for hole,options in self.options.items() if len(options) > 1]
    #     assert splittable != []
    #     hole = splittable[-1]
    #     l,r = Family.split_at_hole(self.options,hole)
    #     return [l,r]

    # def split_options_priority(self):
    #     splittable = [hole for hole,options in self.options.items() if len(options) > 1]
    #     assert splittable != []
    #     for hole in Family._permutation:
    #         if hole in splittable:
    #             l,r = Family.split_at_hole(self.options,hole)
    #             return [l,r]

    # def split_options_least_generalized(self):
    #     splittable = [hole for hole,options in self.options.items() if len(options) > 1]
    #     assert splittable != []
    #     hole_max = None
    #     not_generalized_max = -math.inf
    #     for hole in splittable:
    #         not_generalized_this = Family._hole_not_generalized[Family._hole_indices[hole]]
    #         if not_generalized_this > not_generalized_max:
    #             hole_max = hole
    #             not_generalized_max = not_generalized_this
    #     assert hole_max is not None
    #     l,r = Family.split_at_hole(self.options,hole_max)
    #     return [l,r]

    # def split_options_most_generalized(self):
    #     splittable = [hole for hole,options in self.options.items() if len(options) > 1]
    #     assert splittable != []
    #     hole_min = None
    #     not_generalized_min = math.inf
    #     for hole in splittable:
    #         not_generalized_this = Family._hole_not_generalized[Family._hole_indices[hole]]
    #         if not_generalized_this < not_generalized_min:
    #             hole_min = hole
    #             not_generalized_min = not_generalized_this
    #     assert hole_min is not None
    #     l,r = Family.split_at_hole(self.options,hole_min)
    #     return [l,r]

