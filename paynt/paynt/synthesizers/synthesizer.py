import stormpy.synthesis

from .statistic import Statistic
from ..profiler import Timer,Profiler

import logging
logger = logging.getLogger(__name__)


# TODO
# X 1) memory injection
# X 2) symmetry breaking
#   3) stopping criteria
#   4) experiment headlines (where > ATVA, where > NFA [grid-av MO], hard benchmark with good results, )
# X 5) remove consistent holes from conflicts
# X 6) use primary scheduler from AR to select assignments for CEGIS
#   7) use MDP scheduler for memory injection ?
#   8) CEGIS time allocation
#   -) use belief-based



class Synthesizer:

    def __init__(self, sketch):
        self.sketch = sketch
        self.stat = Statistic(sketch, self)
        self.explored = 0

    @property
    def method_name(self):
        ''' to be overridden '''
        pass
    
    def print_stats(self):
        self.stat.print()

    def synthesize(self, family):
        ''' to be overridden '''
        pass

    def run(self):
        Profiler.start("synthesis")
        self.sketch.quotient.discarded = 0
        # self.sketch.specification.optimality.update_optimum(0.96)
        opt_assignment = self.synthesize(self.sketch.design_space)
        Profiler.stop()
        return opt_assignment

    def explore(self, family):
        self.explored += family.size

        
class Synthesizer1By1(Synthesizer):
    
    @property
    def method_name(self):
        return "1-by-1"

    def synthesize(self, family):

        logger.info("Synthesis initiated.")
        self.stat.start()

        satisfying_assignment = None
        for hole_combination in family.all_combinations():
            
            assignment = family.construct_assignment(hole_combination)
            chain = self.sketch.quotient.build_chain(assignment)
            self.stat.iteration_dtmc(chain.states)
            result = chain.check_specification(self.sketch.specification, short_evaluation = True)
            self.explore(assignment)

            if not result.constraints_result.all_sat:
                continue
            if not self.sketch.specification.has_optimality:
                satisfying_assignment = assignment
                break
            if result.optimality_result.improves_optimum:
                self.sketch.specification.optimality.update_optimum(result.optimality_result.value)
                satisfying_assignment = assignment

        self.stat.finished(satisfying_assignment)
        return satisfying_assignment


class SynthesizerAR(Synthesizer):

    # family exploration order: True = DFS, False = BFS
    exploration_order_dfs = True
    
    @property
    def method_name(self):
        return "AR"

    def analyze_family_ar(self, family):
        """
        :return (1) family feasibility (True/False/None)
        :return (2) new satisfying assignment (or None)
        """
        # logger.debug("analyzing family {}".format(family))
        Profiler.start("synthesizer::analyze_family_ar")
        
        self.sketch.quotient.build(family)
        self.stat.iteration_mdp(family.mdp.states)

        res = family.mdp.check_specification(self.sketch.specification, property_indices = family.property_indices, short_evaluation = True)
        family.analysis_result = res
        Profiler.resume()

        satisfying_assignment = None
        can_improve = res.constraints_result.feasibility is None
        if res.constraints_result.feasibility == True:
            if not self.sketch.specification.has_optimality:
                satisfying_assignment = family.pick_any()
                return True, satisfying_assignment
            else:
                can_improve = res.optimality_result.can_improve
                if res.optimality_result.improving_assignment is not None:
                    satisfying_assignment = res.optimality_result.improving_assignment
        
        if not can_improve:
            self.explore(family)
            return False, satisfying_assignment

        feasibility = None if can_improve else False
        return feasibility, satisfying_assignment
    
    def synthesize(self, family):

        logger.info("Synthesis initiated.")
        self.stat.start()

        satisfying_assignment = None
        families = [family]
        while families:
            
            # if self.stat.iterations_mdp == 10:
            #     exit()
            
            if SynthesizerAR.exploration_order_dfs:
                family = families.pop(-1)
            else:
                family = families.pop(0)

            feasibility,assignment = self.analyze_family_ar(family)
            if assignment is not None:
                satisfying_assignment = assignment
            if feasibility == True:
                break
            if feasibility == False:
                continue

            # undecided
            subfamilies = self.sketch.quotient.split(family)

            # print(family.splitter, family.analysis_result.optimality_result.primary_scores)

            families = families + subfamilies

        self.stat.finished(satisfying_assignment)
        return satisfying_assignment


class SynthesizerCEGIS(Synthesizer):

    # generalize_consistent_holes = False
    generalize_consistent_holes = True

    # explore_scheduler_assignments_first = False
    explore_scheduler_assignments_first = True

    @property
    def method_name(self):
        return "CEGIS"

    def generalize_conflict(self, assignment, conflict, scheduler_selection):

        if not SynthesizerCEGIS.generalize_consistent_holes:
            return conflict

        # filter holes set to consistent assignment
        conflict_filtered = []
        for hole in conflict:
            scheduler_options = scheduler_selection[hole]
            if len(scheduler_options) == 1 and assignment[hole].options[0] == scheduler_options[0]:
                continue
            conflict_filtered.append(hole)

        return conflict_filtered

    def analyze_family_assignment_cegis(self, family, assignment, ce_generator):
        """
        :return (1) overall satisfiability (True/False)
        :return (2) whether this is an improving assignment
        :return (3) pruning estimate
        """
        
        # logger.debug("analyzing assignment {}".format(assignment))
        Profiler.start("CEGIS analysis")
        
        # build DTMC
        Profiler.start("    dtmc construction")
        dtmc = self.sketch.quotient.build_chain(assignment)
        Profiler.resume()
        self.stat.iteration_dtmc(dtmc.states)

        # model check all properties
        Profiler.start("    dtmc model checking")
        spec = dtmc.check_specification(self.sketch.specification, 
            property_indices = family.property_indices, short_evaluation = False)
        Profiler.resume()

        improving = False

        # analyze model checking results
        if spec.constraints_result.all_sat:
            if not self.sketch.specification.has_optimality:
                Profiler.resume()
                return True, True, None
            if spec.optimality_result is not None and spec.optimality_result.improves_optimum:
                self.sketch.specification.optimality.update_optimum(spec.optimality_result.value)
                improving = True

        # construct conflict wrt each unsatisfiable property
        # pack all unsatisfiable properties as well as their MDP results (if exists)
        conflict_requests = []
        for index in family.property_indices:
            if spec.constraints_result.results[index].sat:
                continue
            prop = self.sketch.specification.constraints[index]
            property_result = family.analysis_result.constraints_result.results[index] if family.analysis_result is not None else None
            conflict_requests.append( (index,prop,property_result) )
        if self.sketch.specification.has_optimality:
            index = len(self.sketch.specification.constraints)
            prop = self.sketch.specification.optimality
            property_result = family.analysis_result.optimality_result if family.analysis_result is not None else None
            conflict_requests.append( (index,prop,property_result) )

        # prepare DTMC for CE generation
        ce_generator.prepare_dtmc(dtmc.model, dtmc.quotient_state_map)

        # construct conflict to each unsatisfiable property
        conflicts = []
        for request in conflict_requests:
            index,prop,property_result = request

            threshold = prop.threshold

            bounds = None
            scheduler_selection = None
            if property_result is not None:
                bounds = property_result.primary.result
                scheduler_selection = property_result.primary_selection

            Profiler.start("    generating conflicts")
            conflict = ce_generator.construct_conflict(index, threshold, bounds, family.mdp.quotient_state_map)
            conflict = self.generalize_conflict(assignment, conflict, scheduler_selection)
            Profiler.resume()
            conflicts.append(conflict)
                    
        # use conflicts to exclude the generalizations of this assignment
        pruned_estimate = 0
        Profiler.start("    excluding assignment")
        for conflict in conflicts:
            pruned_estimate += family.exclude_assignment(assignment, conflict)
        Profiler.resume()

        Profiler.resume()
        return False, improving, pruned_estimate

    def synthesize(self, family):

        logger.info("Synthesis initiated.")
        self.stat.start()

        # assert that no reward formula is maximizing
        msg = "Cannot use CEGIS for maximizing reward formulae -- consider using AR or hybrid methods."
        for c in self.sketch.specification.constraints:
            assert not (c.reward and not c.minimizing), msg
        if self.sketch.specification.has_optimality:
            c = self.sketch.specification.optimality
            assert not (c.reward and not c.minimizing), msg


        # map mdp states to hole indices
        family.mdp = self.sketch.quotient.build(family)
        self.sketch.quotient.compute_state_to_holes()
        quotient_relevant_holes = self.sketch.quotient.state_to_holes

        # initialize CE generator
        formulae = self.sketch.specification.stormpy_formulae()
        ce_generator = stormpy.synthesis.CounterexampleGenerator(
            self.sketch.quotient.quotient_mdp, self.sketch.design_space.num_holes,
            quotient_relevant_holes, formulae)

        # use sketch design space as a SAT baseline
        self.sketch.design_space.sat_initialize()
        
        # CEGIS loop
        satisfying_assignment = None
        assignment = family.pick_assignment()
        while assignment is not None:
            
            sat, improving, _ = self.analyze_family_assignment_cegis(family, assignment, ce_generator)
            if improving:
                satisfying_assignment = assignment
            if sat:
                break
            
            # construct next assignment
            assignment = family.pick_assignment()

        self.stat.finished(satisfying_assignment)
        return satisfying_assignment


# ----- Adaptivity ----- #
# idea: switch between ar/cegis, allocate more time to the more efficient method

class StageControl:

    # strategy
    strategy_equal = True
    only_cegis = False

    def __init__(self, members_total):

        # pruning stats
        self.members_total = members_total
        self.pruned_ar = 0
        self.pruned_cegis = 0

        # timings
        self.timer_ar = Timer()
        self.timer_cegis = Timer()
        
        # multiplier to derive time allocated for cegis
        # time_ar * factor = time_cegis
        # =1 is fair, >1 favours cegis, <1 favours ar
        self.cegis_efficiency = 1


    @property
    def ar_running(self):
        return self.timer_ar.running

    def start_ar(self):
        # print(self.pruned_ar, self.pruned_cegis)
        # print(self.timer_ar.read(), self.timer_cegis.read())
        self.timer_cegis.stop()
        self.timer_ar.start()

    def start_cegis(self):
        self.timer_ar.stop()
        self.timer_cegis.start()

    def prune_ar(self, pruned):
        self.pruned_ar += pruned / self.members_total

    def prune_cegis(self, pruned):
        self.pruned_cegis += pruned / self.members_total

    def cegis_step(self):
        """
        :return True if cegis time is over
        """
        
        if StageControl.only_cegis:
            return False

        if self.timer_cegis.read() < self.timer_ar.read() * self.cegis_efficiency:
            return False

        # calculate average success rate, adjust cegis time allocation factor
        self.timer_cegis.stop()

        if StageControl.strategy_equal:
            return True

        factor = 1

        if self.pruned_ar == 0 and self.pruned_cegis == 0:
            self.cegis_efficiency = 1 / factor
        elif self.pruned_ar == 0 and self.pruned_cegis > 0:
            self.cegis_efficiency = 2 / factor
        elif self.pruned_ar > 0 and self.pruned_cegis == 0:
            self.cegis_efficiency = 0.5 / factor
        else:
            success_rate_cegis = self.pruned_cegis / self.timer_cegis.read()
            success_rate_ar = self.pruned_ar / self.timer_ar.read()
            self.cegis_efficiency = success_rate_cegis / success_rate_ar / factor
        return True


class SynthesizerHybrid(SynthesizerAR, SynthesizerCEGIS):

    @property
    def method_name(self):
        return "hybrid"

    def synthesize(self, family):

        logger.info("Synthesis initiated.")
        self.stat.start()
        self.stage_control = StageControl(family.size)

        quotient_relevant_holes = self.sketch.quotient.state_to_holes
        formulae = self.sketch.specification.stormpy_formulae()
        ce_generator = stormpy.synthesis.CounterexampleGenerator(
            self.sketch.quotient.quotient_mdp, self.sketch.design_space.num_holes,
            quotient_relevant_holes, formulae)

        # use sketch design space as a SAT baseline
        self.sketch.design_space.sat_initialize()

        # AR loop
        satisfying_assignment = None
        families = [family]

        while families:
            
            # MDP analysis
            self.stage_control.start_ar()
            
            # choose family
            if SynthesizerAR.exploration_order_dfs:
                family = families.pop(-1)
            else:
                family = families.pop(0)

            # reset SMT solver level
            if SynthesizerAR.exploration_order_dfs:
                family.sat_level()

            # analyze the family
            feasibility,improving_assignment = self.analyze_family_ar(family)
            if improving_assignment is not None:
                satisfying_assignment = improving_assignment
            if feasibility == True:
                break
            if feasibility == False:
                self.stage_control.prune_ar(family.size)
                continue

            # undecided: initiate CEGIS analysis
            self.stage_control.start_cegis()

            # construct priority subfamily
            priority_subfamily = None
            if SynthesizerCEGIS.explore_scheduler_assignments_first:
                # construct family that corresponds to primary scheduler
                scheduler_selection = family.analysis_result.optimality_result.primary_selection
                priority_subfamily = family.copy()
                priority_subfamily.assume_options(scheduler_selection)

            # explore family assignments
            sat = False
            while True:

                # pick assignment
                assignment = family.pick_assignment_priority(priority_subfamily)
                if assignment is None:
                    break
                
                # analyze this assignment
                sat, improving, _ = self.analyze_family_assignment_cegis(family, assignment, ce_generator)
                if improving:
                    satisfying_assignment = assignment
                if sat:
                    break
                
                # assignment is UNSAT
                if self.stage_control.cegis_step():
                    # CEGIS timeout
                    break

            if sat:
                break
            
            if not family.has_assignments:
                self.explore(family)
                self.stage_control.prune_cegis(family.size)
                continue

        
            # CEGIS could not process the family: split
            subfamilies = self.sketch.quotient.split(family)
            families = families + subfamilies

        ce_generator.print_profiling()

        self.stat.finished(satisfying_assignment)
        return satisfying_assignment

