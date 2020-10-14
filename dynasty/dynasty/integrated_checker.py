# author: Roman Andriushchenko

import z3

import stormpy
import stormpy.utility
import stormpy.core

import dynasty.jani
from dynasty.jani.jani_quotient_builder import *
from dynasty.family_checkers.cegis import Synthesiser
from dynasty.family_checkers.quotientbased import LiftingChecker
from dynasty.family_checkers.familychecker import HoleOptions

from collections import OrderedDict
# from collections.abc import Iterable
# import re
import operator

# ------------------------------------------------------------------------------
# wrappers

def check_model(model, property, quantitative=False):
    """Model check a model against a (quantitative) property."""
    raw_formula = property.raw_formula
    formula = raw_formula
    if(quantitative):
        formula = formula.clone()
        formula.remove_bound()

    result = stormpy.model_checking(model, formula)
    satisfied = result.at(model.initial_states[0])
    if(quantitative):
        op = {
            stormpy.ComparisonType.LESS : operator.lt,
            stormpy.ComparisonType.LEQ : operator.le,
            stormpy.ComparisonType.GREATER: operator.gt,
            stormpy.ComparisonType.GEQ: operator.ge
        } [raw_formula.comparison_type] 
        satisfied = op(satisfied,raw_formula.threshold_expr.evaluate_as_double())
    return satisfied,result
 
def readable_assignment(assignment):
    return {k:v.__str__() for (k,v) in assignment.items()} if assignment is not None else None

class Timer:
    def __init__(self):
        self.reset()

    def reset(self):
        self.running = False
        self.timer = None        
        self.time = 0

    def start(self):
        if self.running:
            return
        self.timer = time.time()
        self.running = True

    def stop(self):
        if not self.running:
            return
        self.time += time.time() - self.timer
        self.timer = None
        self.running = False

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def read(self):
        if not self.running:
            return self.time
        else:
            return self.time + (time.time() - self.timer)
            

class Statistic:
    """General computation stats."""
    def __init__(self, method):
        self.method = method
        self.timer = Timer()
        self.timer.toggle()
        

    def finished(self, assignment, iterations):
        self.timer.toggle()
        self.result = assignment is not None
        self.assignment = readable_assignment(assignment)
        self.iterations = iterations
    
    def __str__(self):
        is_feasible = "feasible" if self.result else  "unfeasible"
        return "> {}: {} ({} iters, {} sec)\n".format(self.method, is_feasible, self.iterations, round(self.timer.time,2))

class CEGISChecker(Synthesiser):
    """CEGIS wrapper."""
    def __init__(self, *args):
        super().__init__(*args)
        self.statistic = Statistic("CEGIS")

    def run(self):
        _, assignment, _ = self.run_feasibility()
        self.statistic.finished(assignment, self.stats.iterations)

class CEGARChecker(LiftingChecker):
    """CEGAR wrapper."""
    def __init__(self,*args):
        super().__init__(*args)
        self.statistic = Statistic("CEGAR")

    def cegar_initialisation(self):
        self.iterations = 0
        self.jani_quotient_builder = JaniQuotientBuilder(self.sketch, self.holes)
        self._open_constants = self.holes
        self.use_oracle = True

        self.oracle = None
        hole_options = [self.hole_options]
        self.threshold = float(self.thresholds[0])

        self.new_options = None
        self.satisfying_assignment = None

        # logger.debug("Threshold is {}".format(self.threshold))        
        # logger.info("Total number of options: {}".format(self.hole_options.size()))

        return hole_options

    def cegar_split_option(self, option):
        self.oracle.scheduler_color_analysis()
        return self._split_hole_options(option, self.oracle)

    def _analyse_from_scratch(self, option):
        self.oracle = LiftingChecker._analyse_from_scratch(self, self._open_constants, option, set(), self.threshold) 

    def _analyse_suboptions(self, option):
        LiftingChecker._analyse_suboptions(self, self.oracle, option, self.threshold)
        
    def _analyse_option(self, option):
        if self.oracle is None:
            self._analyse_from_scratch(option)
        else:
            self._analyse_suboptions(option)

    def cegar_analyse_option(self, option):
        self.iterations += 1
        logger.info("CEGAR: iteration {}, analysing option {}.".format(self.iterations, option)) #~
        self._analyse_option(option)

        self.new_options = None
        threshold_synthesis_result = self.oracle.decided(self.threshold)
        if threshold_synthesis_result == dynasty.jani.quotient_container.ThresholdSynthesisResult.UNDECIDED:
            # undecided
            logger.debug("Undecided.")
            self.new_options = self.cegar_split_option(option)
        else:
            # decided
            if (threshold_synthesis_result == ThresholdSynthesisResult.ABOVE) == self._accept_if_above[0]:
                logger.debug("All above or all below.")
                self.satisfying_assignment = option.pick_one_in_family()
            else:
                logger.debug("Decided: unsatisfying.")
            
    def run_feasibility(self):
        if self.input_has_optimality_property():
            return self._run_optimal_feasibility()
        if self.input_has_multiple_properties():
            raise RuntimeError("Lifting is only implemented for single properties")
        if self.input_has_restrictions():
            raise RuntimeError("Restrictions are not supported by quotient based approaches")

        hole_options = self.cegar_initialisation()

        while len(hole_options) > 0:
            option = hole_options.pop(0)
            self.cegar_analyse_option(option)
            if self.satisfying_assignment is not None:
                return self.satisfying_assignment
            if self.new_options is not None:
                hole_options = self.new_options + hole_options

        logger.info("No more options to explore.")
        return None
        
    def run(self):
        assignment = self.run_feasibility()
        self.statistic.finished(assignment, self.iterations)

# ------------------------------------------------------------------------------
# integrated method

class IntegratedStatistic(Statistic):
    """Base stats + region info + CE stats"""

    def __init__(self):
        super().__init__("Hybrid")
        self.region_stats = []

    def new_region(self, bound):
        self.bound = bound
        self.iters = 0
        self.commands_old = 0
        self.commands_new = 0
        self.holes_old = 0
        self.holes_new = 0

    def new_counterexample(self, commands_old, commands_new, holes_old, holes_new):
        self.iters += 1
        self.commands_old += commands_old
        self.commands_new += commands_new
        self.holes_old += holes_old
        self.holes_new += holes_new

    def end_region(self, storm_stat):
        # average
        self.iters = max(1, self.iters)
        region_stat = (
            (
                self.bound,
                self.iters,
                self.commands_old / self.iters,
                self.commands_new / self.iters,
                self.holes_old / self.iters,
                self.holes_new / self.iters
            ), storm_stat
        )
        self.region_stats.append(region_stat)

    def __str__(self):
        s = super().__str__()
        for (region_stat, storm_stat) in self.region_stats:
            region_stat = [round(x,3) for x in region_stat]
            storm_stat = [round(x,3) for x in storm_stat]
            s += "> {} : {}\n".format(region_stat, storm_stat)
        return s

class IntegratedChecker(CEGISChecker,CEGARChecker):
    """Integrated checker."""
    
    def __init__(self):
        CEGISChecker.__init__(self)
        CEGARChecker.__init__(self)
        self.cegis_iterations = 0
        self.cegar_iterations = 0
        self.statistic = IntegratedStatistic()

    def initialise(self):
        CEGARChecker.initialise(self)
        CEGISChecker.initialise(self)
        assert len(self._verifier.properties) == 1
        self.property = self._verifier.properties[0].property        

    def result_exists(self, hole_options):
        """Check whether a satisfying assignment has been obtained or all regions have been explored."""
        return (self.satisfying_assignment is not None) or (len(hole_options) == 0)

    def compose_result(self, hole_options):
        """Compose synthesis result: either satisfying assignment has been obtained or all regions have been explored."""
        if self.satisfying_assignment is not None:
            logger.info("Found satisfying assignment.")
            return self.satisfying_assignment
        if len(hole_options) == 0:
            logger.info("No more options.")
            return None

    def cegar_analyse_option(self, option):
        """Analyse region and store mdp data."""
        CEGARChecker.cegar_analyse_option(self, option)
        self.cegar_iterations += 1
        self.mdp = self.oracle._mdp_handling.mdp
        self.mdp_mc_result = self.oracle._latest_result.result
        
    # ----- Adaptivity ----- #
    # Main idea: switch between cegar/cegis, allocate more time to the more
    # efficient method; if one method is consistently better than the other,
    # declare it the winner and stop switching

    # cegar wins over cegis by reaching the score limit, cegis wins by reaching the negative
    # note: this is the only parameter in the integrated synthesis
    stage_score_limit = None

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

        # start with CEGAR 
        self.stage_start(request_stage_cegar = True)

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
        if self.stage_cegar:
            self.stage_pruned_cegar += models_pruned / self.models_total
        else:
            self.stage_pruned_cegis += models_pruned / self.models_total

        # allow cegis another stage step if some time remains
        if not self.stage_cegar:
            if self.stage_timer.read() < self.cegis_allocated_time:
                return False

        # stage is finished: record time
        self.stage_timer.stop()
        time = self.stage_timer.read()
        if self.stage_cegar:
            # cegar stage over: allocate time for cegis and switch
            self.stage_time_cegar += time
            self.cegis_allocated_time = time * self.cegis_allocated_time_factor
            self.stage_start(request_stage_cegar = False)
            return True

        # cegis stage over
        self.stage_time_cegis += time

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
                self.stage_start(request_stage_cegar = True)
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
        # print("> {:.2f} \\\\ {:.2f} = {:.1f} ({})".format(success_rate_cegar, success_rate_cegis, cegis_dominance, self.stage_score))

        # switch back to cegar
        self.stage_start(request_stage_cegar = True)
        return True

    # ----- CE quality ----- #

    ce_quality_compute = False

    def ce_quality_init(self):
        if not self.ce_quality_compute:
            return
        self.ce_maxsat = self.ce_zero = self.ce_global = self.ce_local = 0
        self.ce_maxsat_timer = Timer()
        self.ce_zero_timer = Timer()
        self.ce_global_timer = Timer()
        self.ce_local_timer = Timer()
        self.global_mdp = self.global_mdp_result = None

    def ce_quality_global(self,mdp,mdp_result):
        if not self.ce_quality_compute:
            return
        if self.global_mdp is not None:
            return
        self.global_mdp = mdp
        self.global_mdp_result = mdp_result

    def ce_quality_subfamily(self,sketch,relevant_holes_flatset,formula):
        if not self.ce_quality_compute:
            return
        self.counterexample_global = stormpy.SynthesisResearchCounterexample(sketch, relevant_holes_flatset, formula, self.global_mdp, self.global_mdp_result)

    def ce_quality_measure(self,instance,relevant_holes,counterexample,dtmc):
        if not self.ce_quality_compute:
            return
        self.statistic.timer.stop()
        self.stage_timer.stop()
        
        # ce_states = counterexample.construct_via_states(dtmc, dtmc_result, 1, 99999)
        # conflict_states = self.relevant_holes(ce_states, relevant_holes)
        # self.ce_states += len(conflict_states) / len(relevant_holes)

        # maxsat
        self.ce_maxsat_timer.start()
        conflict_maxsat = self.conflict_maxsat(instance)
        # conflict_maxsat = relevant_holes.copy()
        conflict_maxsat = [hole for hole in conflict_maxsat if hole in relevant_holes]
        self.ce_maxsat += len(conflict_maxsat) / len(relevant_holes)
        self.ce_maxsat_timer.stop()

        # zero
        self.ce_zero_timer.start()
        conflict_zero = counterexample.construct_via_holes(dtmc, False)
        self.ce_zero += len(conflict_zero) / len(relevant_holes)
        self.ce_zero_timer.stop()
        
        # global
        self.ce_global_timer.start()
        conflict_global = self.counterexample_global.construct_via_holes(dtmc,True)
        self.ce_global += len(conflict_global) / len(relevant_holes)
        self.ce_global_timer.stop()

        # resume timers and compute normal bounds
        self.stage_timer.start()
        self.statistic.timer.start()

        # local
        self.ce_local_timer.start()
        conflict_local = counterexample.construct_via_holes(dtmc, True)
        self.ce_local += len(conflict_local) / len(relevant_holes)
        self.ce_local_timer.stop()

        print("> {} vs {}".format(self.ce_maxsat / self.cegis_iterations, self.ce_local / self.cegis_iterations))

        return conflict_local

    def ce_quality_print(self):
        if not self.ce_quality_compute:
            return
        if self.cegis_iterations < 2:
            print("> ce quality: n/a")
        else:
            iters = self.cegis_iterations - 1
            quality_maxsat = self.ce_maxsat / iters
            time_maxsat = self.ce_maxsat_timer.read() / iters
            quality_zero = self.ce_zero / iters
            time_zero = self.ce_zero_timer.read() / iters
            quality_global = self.ce_global / iters
            time_global = self.ce_global_timer.read() / iters
            quality_local = self.ce_local / iters
            time_local = self.ce_local_timer.read() / iters
            print("> ce quality: {:1.4f} - {:1.4f} - {:1.4f} - {:1.4f}".format(quality_maxsat, quality_zero, quality_global, quality_local))
            print("> ce time: {:1.4f} - {:1.4f} - {:1.4f} - {:1.4f}".format(time_maxsat, time_zero, time_global, time_local))

    def conflict_maxsat(self, instance, all_conflicts=True, naive_deadlocks=True, check_conflicts=False):
        """Naive counterexample generation (for comparison)."""

        model = self._verifier._build_model(instance)
        qualitative_conflicts_properties, quantitative_conflict_properties = self._verifier._naive_check_model(model,
                                                                                                     all_conflicts)
        if qualitative_conflicts_properties:
            # conflicts.add(tuple([c.name for c in self.sketch.used_constants()]))
            # TODO handling for qualitative conflicts can certainly be improved.
            return qualitative_conflicts_properties, set()

        # Construct the environment for the counterexample generator.
        env = stormpy.core.Environment()
        env.solver_environment.set_linear_equation_solver_type(stormpy.EquationSolverType.native)
        # env.solver_environment.set_force_sound()

        # We can sometimes merge properties into a single meta-property for conflict analysis.
        merged_conflict_props = self._verifier._merge_conflict_properties(quantitative_conflict_properties)
        assert(len(merged_conflict_props) == 1)
        (p,additional) = next(iter(merged_conflict_props.items()))

        # Create input for the counterexample generation.
        symbolic_model = stormpy.SymbolicModelDescription(instance)
        cex_input = stormpy.core.SMTCounterExampleGenerator.precompute(env, symbolic_model, model, p.raw_formula)
        for a in additional:
            cex_input.add_reward_and_threshold(a[0], a[1])

        # Prepare execution of the counterexample generation
        cex_stats = stormpy.core.SMTCounterExampleGeneratorStats()
        # Generate the counterexample
        result = stormpy.core.SMTCounterExampleGenerator.build(
            env, cex_stats, symbolic_model, model, cex_input, self._verifier._dont_care_set, self._verifier.cex_options
        )
        # assert(result.__len__() == 1)
        critical_edges_fs = result.pop()
        
        # Translate the counterexamples into conflicts.
        conflict = self._verifier._conflict_analysis(critical_edges_fs)
        return conflict

    # ----- hybrid method ----- #

    def relevant_holes(self, critical_edges, relevant_holes):
        holes = self._verifier._conflict_analysis(critical_edges)
        holes = [hole for hole in holes if hole in relevant_holes]
        return holes

    def cegis_analyse_family(self, builder_options, family, mdp, mdp_result):
        """Analyse a family using provided mdp data to construct generalized counterexamples."""
        logger.debug("CEGIS stage.")
        # print("> cegis stage".format(), flush=True)

        # list of relevant holes (open constants) in this subfamily
        relevant_holes = [hole for hole in self.holes if len(family[hole]) > 1]

        # encode family
        family_clauses = dict()
        for var,hole in self.template_metavariables.items():
            family_clauses[hole] = z3.Or([var == self.hole_option_indices[hole][option] for option in family[hole]])
        family_encoding = z3.And(list(family_clauses.values()))
        
        # prepare counterexample generator
        relevant_holes_flatset = stormpy.core.FlatSetString()
        for hole in relevant_holes:
            relevant_holes_flatset.insert(hole)
        counterexample = stormpy.SynthesisResearchCounterexample(self.sketch, relevant_holes_flatset, self.property.raw_formula, mdp, mdp_result)

        # CE generator for global MDP bounds
        self.ce_quality_subfamily(self.sketch, relevant_holes_flatset, self.property.raw_formula)
        
        # get satisfiable assignments (within the subfamily)
        solver_result = self.solver.check(family_encoding)
        while solver_result == z3.sat:
            self.cegis_iterations += 1
            logger.info("CEGIS iteration {}.".format(self.cegis_iterations))
            # print("> cegis iter: {}".format(self.cegis_iterations), flush=True)
        
            # create an assignment for the holes
            sat_model = self.solver.model()
            assignment = OrderedDict()
            for var, hole in self.template_metavariables.items():
                val = sat_model[var].as_long()
                assignment[hole] = self.hole_options[hole][val]
            
            # construct an instance based on the hole assignment
            constants_map = dict()
            ep = stormpy.storage.ExpressionParser(self.expression_manager)
            ep.set_identifier_mapping(dict())
            for hole_name, expr in assignment.items():
                constants_map[self.holes[hole_name].expression_variable] = expr
            instance = self.sketch.define_constants(constants_map).substitute_constants()

            # construct and model check a DTMC
            dtmc = stormpy.build_sparse_model_with_options(instance, builder_options)
            logger.debug("Constructed DTMC of size {}.".format(dtmc.nr_states))

            assert len(dtmc.initial_states) == 1 # to avoid ambiguity
            assert dtmc.initial_states[0] == 0 # should be implied by topological ordering
            dtmc_sat, dtmc_result = check_model(dtmc, self.property, quantitative=True)
            if dtmc_sat:
                self.satisfying_assignment = assignment
                return True

            # unsat: construct a counterexample
            conflict = counterexample.construct_via_holes(dtmc, True)
            # print("> ce : {}", counterexample.stats)

            # compare maxsat vs state exploration vs naive hole exploration vs global bounds vs local bounds
            # conflict = self.ce_quality_measure(instance, relevant_holes, counterexample, dtmc)
            
            # estimate number of (virtually) pruned models
            # models_pruned = 1
            # irrelevant_holes = set(relevant_holes) - set(conflict)
            # for hole in irrelevant_holes:
                # models_pruned *= len(family[hole])
            # print("> is: CE - holes {}/{} | models {}/{} = {:1.4f}".format(len(conflict), len(self.holes), models_pruned, family_size, models_pruned/family_size))

            # add new clause
            counterexample_clauses = family_clauses.copy()
            for var,hole in self.template_metavariables.items():
                if hole in conflict:
                    counterexample_clauses[hole] = (var == sat_model[var])
            counterexample_encoding = z3.Not(z3.And(list(counterexample_clauses.values())))
            self.solver.add(counterexample_encoding)

            # read next solution
            solver_result = self.solver.check(family_encoding)

            # record stage
            if self.stage_step(0):
                # switch requested
                return False

        # full subfamily pruned
        return True
        
    
    def run_feasibility(self):
        """Run feasibility synthesis."""
        logger.info("Running feasibility synthesis.")
        assert not self.input_has_optimality_property()
        assert not self.input_has_multiple_properties()
        assert not self.input_has_restrictions()

        # measure ce quality
        self.ce_quality_init()
        
        # precompute DTMC builder options
        builder_options = stormpy.BuilderOptions([self.property.raw_formula])
        builder_options.set_build_with_choice_origins(True)
        builder_options.set_build_state_valuations(True)
        # builder_options.set_add_overlapping_guards_label() #?
        
        # initialize solver describing the family and counterexamples
        # note: restricting to subfamilies is encoded separately
        self._initialize_solver()

        # a map for indices of options
        self.hole_option_indices = dict()
        for hole, options in self.hole_options.items():
            indices = dict()
            k = 0
            for option in options:
                indices[option] = k
                k += 1
            self.hole_option_indices[hole] = indices
        
        # initialize cegar
        families = self.cegar_initialisation()
        family = families[0]
        logger.info("Family members: {}.".format(family.size()))

        # initiate cegar-cegis loop
        problems = [(family,None,None)]
        self.models_total = family.size()
        self.stage_init()
        while problems:
            logger.debug("Current number of problems: {}".format(len(problems)))
            # print("> ", format(len(problems)))
            
            # pick a problem
            problem = problems.pop(-1)
            family, bound, subfamilies = problem
            family_size = family.size()
            logger.info("Analysing subfamily of size {}.".format(family_size))

            if self.stage_cegar:
                # CEGAR
                if subfamilies is not None:
                    # family has been already analysed: refine and continue
                    # note: subfamilies inherit bound from the parent family
                    logger.info("Splitting the family.")
                    subproblems = [(subfamily, bound, None) for subfamily in subfamilies]
                    problems.extend(subproblems)
                    continue

                # family has not been analysed yet
                logger.info("CEGAR iteration {}.".format(self.cegar_iterations+1))
                # print("> cegar iter {}".format(self.cegar_iterations+1))
                self.cegar_analyse_option(family)
                if self.satisfying_assignment is not None:
                    # sat
                    logger.debug("Sat")
                    # print("> (a) sat")
                    break
                if self.new_options is None:
                    # unsat
                    logger.debug("Unsat")
                    # print("> (a) unsat")
                    models_pruned = family_size
                else:
                    # undecided: do not refine yet, store analysis result for cegis
                    logger.debug("Undecided.")
                    # print("> (a) undecided")
                    models_pruned = 0
                    bound = (self.mdp, self.mdp_mc_result)
                    analysed_family = (family, bound, self.new_options)
                    problems.append(analysed_family) #DFS
                    # problems = [analysed_family] + problems # BFS
                    self.ce_quality_global(self.mdp, self.mdp_mc_result)
                    
                self.stage_step(models_pruned)
            
            else:
                # CEGIS
                assert(bound is not None)
                analysis_success = self.cegis_analyse_family(builder_options, family, bound[0], bound[1])
                if self.satisfying_assignment is not None:
                    # sat
                    logger.debug("Sat")
                    # print("> (i) sat")
                    break
                if analysis_success:
                    # unsat
                    logger.debug("Unsat")
                    # print("> (i) unsat")
                    self.stage_step(family_size)
                else:
                    # stage interrupted: leave the family to cegar
                    # note: phase was switched implicitly
                    logger.debug("Stage interrupted.")
                    # print("> (i) interrupted")
                    problems.append(problem)
            
        return self.compose_result([])

    def run(self):
        assignment = self.run_feasibility()
        self.statistic.finished(assignment, (self.cegar_iterations, self.cegis_iterations))
        self.ce_quality_print()


class Research():
    """Entry point: execution setup."""
    def __init__(
            self, check_prerequisites, backward_cuts,
            sketch_path, allowed_path, property_path, optimality_path, constants,
            restrictions, restriction_path
        ):

        assert not check_prerequisites
        assert not restrictions

        self.sketch_path = sketch_path
        self.allowed_path = allowed_path
        self.property_path = property_path
        self.optimality_path = optimality_path
        self.constants = constants
        self.restrictions = restrictions
        self.restriction_path = restriction_path

        # import research.generator1
        # import research.generator2
        # workspace.generator2.run()
        
        workdir = "workspace/experiments"
        with open(f"{workdir}/parameters.txt", 'r') as f:
            lines = f.readlines()
            regime = int(lines[0])
            stage_score_limit = int(lines[1])
        IntegratedChecker.stage_score_limit = stage_score_limit
        
        stats = []
        
        if regime == 0:
            # stats.append(self.run_algorithm(CEGISChecker))
            # stats.append(self.run_algorithm(CEGARChecker))
            stats.append(self.run_algorithm(IntegratedChecker))
        elif regime == 1:
            stats.append(self.run_algorithm(CEGISChecker))
        elif regime == 2:
            stats.append(self.run_algorithm(CEGARChecker))
        elif regime == 3:
            stats.append(self.run_algorithm(IntegratedChecker))
        # elif regime in [2,3]:
            # stats.append(self.run_algorithm(IntegratedChecker))
        else:
            assert None
              
        print("\n")
        for stat in stats:
            print(stat)
        
    def run_algorithm(self, algorithmClass):
        print("\n\n\n")
        print(algorithmClass.__name__)    
        algorithm = algorithmClass()
        algorithm.load_sketch(self.sketch_path, self.property_path, optimality_path=self.optimality_path, constant_str=self.constants)
        algorithm.load_template_definitions(self.allowed_path)
        if self.restrictions:
            algorithm.load_restrictions(self.restriction_path)
        algorithm.initialise()
        algorithm.run()
        return algorithm.statistic

'''
# building dtmc from mdp
            single_member = HoleOptions()
            for var, hole in self.template_metavariables.items():
                hole_option_index = sat_model[var].as_long()
                single_member[hole] = [family[hole][hole_option_index]]
            print("> single member ", single_member)
            
            # for hole,options in family:

            print("> model_checking mdp(1)...")
            self._analyse_suboptions(single_member)
            threshold_synthesis_result = self.oracle.decided(self.threshold)
            assert(threshold_synthesis_result != ThresholdSynthesisResult.UNDECIDED)
            if (threshold_synthesis_result == ThresholdSynthesisResult.ABOVE) == self._accept_if_above[0]:
                self.satisfying_assignment = single_member.pick_one_in_family()
                return True
            
            print("> converting to dtmc...")
            dtmc_mdp = self.oracle._mdp_handling.mdp._as_sparse_dtmc()
'''