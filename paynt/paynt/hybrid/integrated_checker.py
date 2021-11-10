import logging
import multiprocessing
import os
from multiprocessing import Process

import stormpy
import stormpy.synthesis
from .cegis_worker_return_obj import CegisWorkerObj
from ..family_checkers.familychecker import HoleOptions

from ..family_checkers.quotientbased import QuotientBasedFamilyChecker, logger as quotientbased_logger
from ..globals import Globals
from ..jani.jani_quotient_builder import logger as jani_quotient_builder_logger
from ..jani.quotient_container import logger as quotient_container_logger
from ..model_handling.mdp_handling import logger as model_handling_logger
from ..profiler import Profiler, Timer
from .cegis import CEGISChecker
from .family import Family
from .helpers import readable_assignment, safe_division
from .hybrid_family import FamilyHybrid
from .statistic import Statistic
import time
import datetime

# LOGGING -------------------------------------------------------------------------------------------------- LOGGING


logger = logging.getLogger(__name__)

quotientbased_logger.disabled = False
quotient_container_logger.disabled = True
jani_quotient_builder_logger.disabled = True
model_handling_logger.disabled = True

ONLY_CEGAR = False
ONLY_CEGIS = True
NONTRIVIAL_BOUNDS = True
PRINT_STAGE_INFO = False
PRINT_PROFILING = True


class IntegratedChecker(QuotientBasedFamilyChecker, CEGISChecker):
    """Integrated checker."""

    stage_score_limit = 99999
    ce_quality = False
    ce_maxsat = False
    lock = multiprocessing.Lock()
    start_synthesis_time = 0
    end_synthesis_time = 0

    def __init__(self, *args):
        QuotientBasedFamilyChecker.__init__(self, *args)
        CEGISChecker.__init__(self, *args)
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

    def cegis_analyze_member_assigment(self, process_order_number, member_assignment, family, relevant_holes, return_process):
        # init phase for each worker
        cegis_worker_obj = CegisWorkerObj()
        Profiler.initialize()

        # prepare counterexample generator
        logger.debug("CEGIS: preprocessing quotient MDP")
        Profiler.start("_")
        counterexample_generator = stormpy.synthesis.SynthesisCounterexample(
            family.mdp, len(Family.hole_list), family.state_to_hole_indices, self.formulae, family.bounds
        )
        Profiler.stop()

        logger.info(f"Hi guys from Process: {os.getpid()}")
        logger.debug(f"CEGIS: picked family member: {member_assignment}.")

        # collect indices of violated formulae
        violated_formulae_indices = []
        for formula_index in family.formulae_indices:
            # logger.debug(f"CEGIS: model checking DTMC against formula with index {formula_index}.")
            Profiler.start("CEGIS - DTMC model checking")
            Family.dtmc_checks_inc()
            sat, _ = family.analyze_member(formula_index)
            Profiler.stop()
            logger.debug(f"Formula {formula_index} is {'SAT' if sat else 'UNSAT'}")
            if not sat:
                violated_formulae_indices.append(formula_index)
        if (not violated_formulae_indices or violated_formulae_indices == [len(self.formulae) - 1]) \
                and self.input_has_optimality_property():
            self._check_optimal_property(family, member_assignment, counterexample_generator)
            cegis_worker_obj.optimal_value = self._optimal_value
            cegis_worker_obj.optimal_assignment = HoleOptions.toJson(self._optimal_assignment)
            cegis_worker_obj.return_value = True
        elif not violated_formulae_indices:
            Profiler.add_ce_stats(counterexample_generator.stats)
            # TODO: check this...
            cegis_worker_obj.return_value = True
            return_process.send(cegis_worker_obj)

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
                member_assignment, relevant_holes, counterexample_generator,
                family.dtmc, family.dtmc_state_map, formula_index
            )

        # record stage
        if self.stage_step(0) and not ONLY_CEGIS:
            # switch requested
            Profiler.add_ce_stats(counterexample_generator.stats)
            cegis_worker_obj.return_value = None
            return_process.send(cegis_worker_obj)

        Profiler.stop()

        cegis_worker_obj.conflicts = conflicts
        cegis_worker_obj.return_value = "default"

        # flush profiler timers to the directory
        Profiler.flush_stats_to_the_file(process_order_number)

        return_process.send(cegis_worker_obj)


    def analyze_family_cegis(self, family):
        """
        Analyse a family against selected formulae using precomputed MDP data
        to construct generalized counterexamples.
        """
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

        # TODO:
        #  1. - for n processes pick unique member and analyze it
        #  2. - worker returns master only conflicts, which master will then update to the Solver..

        # TODO preprocess only formulae of interest

        member_assignments = []

        # pokial je vzdy member assignemnts nieco cize nie 'None'
        while not None in member_assignments:

            pipe_list = []
            jobs = []
            member_assignments = []

            for i in range(Globals.CEGIS_CPU_COUNT):
                self.iterations_cegis += 1
                logger.debug(f"CEGIS: iteration {self.iterations_cegis}.")

                # pick members for each worker
                Profiler.start("CEGIS - pick DTMC")
                member_to_analyze = family.pick_member_with_exclude_all_holes()

                if member_to_analyze is None:
                    # full family pruned
                    logger.debug("CEGIS: no more family members.")
                    Profiler.add_ce_stats(counterexample_generator.stats)
                    return False
                else:
                    member_assignments.append(member_to_analyze)

                Profiler.stop()

                recv_end, send_value = multiprocessing.Pipe(False)

                pipe_list.append(recv_end)

                job = Process(target=self.cegis_analyze_member_assigment, args=(i, member_assignments[i], family, relevant_holes, send_value))
                job.start()

                jobs.append(job)

            for pipe in pipe_list:
                i = 0
                # fetch somehow output from process 'conflicts' (this is blocking operation)
                returned_value_from_process = pipe.recv()
                logger.info("CEGIS: received from process " + str(returned_value_from_process))

                if returned_value_from_process.return_value is None:
                    member_assignments.append(None)
                    return None
                elif returned_value_from_process.return_value is True:
                    return True
                else:
                    # 1. set opt values if it's improvement...
                    if self._optimality_setting.is_improvement(returned_value_from_process.optimal_value, self._optimal_value):
                        logger.info("Find the new optimal value: " + str(returned_value_from_process.optimal_value))
                        self._optimal_value = returned_value_from_process.optimal_value
                        self._optimal_assignment = HoleOptions.fromJson(returned_value_from_process.optimal_assignment)

                        # 2-3. update counter-example generator thresholds (`set thresholds`)
                        # TODO: make it for all processes...
                        self._construct_violation_property(family, counterexample_generator)

                    # 4. in this case return value is conflicts to exclude
                    if returned_value_from_process.conflicts is not []:
                        # TODO: setter of pick_assignment of the family
                        family.set_member_assignment(member_assignments[i])
                        family.exclude_member(returned_value_from_process.conflicts)

                i += 1

            # TODO: here should be evalutation of files created by processes...


    def run_feasibility(self):
        """
        Run feasibility synthesis. Return either a satisfying assignment (feasible) or None (unfeasible).
        """
        Profiler.initialize()
        IntegratedChecker.start_synthesis_time = time.time_ns()
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

        # delete files
        Profiler.delete_worker_files()

        IntegratedChecker.end_synthesis_time = time.time_ns()
        execution_time_of_the_synthesis_ns = IntegratedChecker.end_synthesis_time - IntegratedChecker.start_synthesis_time
        execution_time_of_the_synthesis_ms = execution_time_of_the_synthesis_ns / 1000000
        execution_time_of_the_synthesis_s = execution_time_of_the_synthesis_ms / 1000
        print("Program execution time:" + str(execution_time_of_the_synthesis_s) + " (s)")

        if self.input_has_optimality_property() and self._optimal_value is not None:
            assert not self.families
            logger.info(f"Found optimal assignment: {self._optimal_value}")
            return self._optimal_assignment, self._optimal_value
        elif satisfying_assignment is not None:
            logger.info(f"Found satisfying assignment: {satisfying_assignment}")
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
