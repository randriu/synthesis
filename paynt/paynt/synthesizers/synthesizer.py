import stormpy

from .models import MarkovChain, DTMC, MDP
from ..sketch.holes import Holes,DesignSpace

from .statistic import Statistic
from ..profiler import Timer,Profiler

import logging
logger = logging.getLogger(__name__)

class Synthesizer:

    def __init__(self, sketch):
        self.sketch = sketch
        self.stat = Statistic(sketch, self)
        self.explored = 0

    @property
    def method_name(self):
        """ to be overridden """
        pass
    
    def print_stats(self):
        print(self.stat.get_summary())
        Profiler.print_all()

    def synthesize(self, family):
        """ to be overridden """
        pass

    def run(self):
        logger.info("Synthesis initiated.")
        assignment = self.synthesize(self.sketch.design_space)
        # double-check assignment
        if assignment is not None:
            dtmc = self.sketch.quotient.build_chain(assignment)
            spec_result = dtmc.check_specification(self.sketch.specification)
            print("double-checking: ", spec_result)
        return assignment

    def explore(self, family):
        self.explored += family.size

        
class Synthesizer1By1(Synthesizer):
    
    @property
    def method_name(self):
        return "1-by-1"

    def synthesize(self, family):

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
    
    @property
    def method_name(self):
        return "AR"

    def analyze_family_ar(self, family):
        """
        :return (1) family feasibility (True/False/None)
        :return (2) new satisfying assignment (or None)
        """
        Profiler.start("MDP analysis")
        # logger.debug("analyzing family {}".format(family))
        family.mdp = self.sketch.quotient.build(family)
        family.translate_analysis_hints()
        # print("family size: {}, mdp size: {}".format(family.size, family.mdp.states))
        self.stat.iteration_mdp(family.mdp.states)


        res = family.mdp.check_specification(self.sketch.specification, property_indices = family.property_indices, short_evaluation = True)
        family.analysis_result = res
        satisfying_assignment = None
        Profiler.resume()

        can_improve = res.constraints_result.feasibility is None
        if res.constraints_result.feasibility == True:
            if not self.sketch.specification.has_optimality:
                satisfying_assignment = family.pick_any()
                return True, satisfying_assignment
            else:
                can_improve = res.optimality_result.can_improve
                if res.optimality_result.optimum is not None:
                    # double-check the assignment and update optimum
                    satisfying_assignment = res.optimality_result.improving_assignment
                    assert satisfying_assignment.size == 1
                    dtmc = self.sketch.quotient.build_chain(satisfying_assignment)
                    opt_result = dtmc.model_check_property(self.sketch.specification.optimality)
                    self.sketch.specification.optimality.update_optimum(opt_result.value)
        
        if not can_improve:
            self.explore(family)
            return False, satisfying_assignment

        feasibility = None if can_improve else False
        return feasibility, satisfying_assignment

    
    def generalize_hint(self, family, hint):
        hint_global = dict()
        for state in range(family.mdp.states):
            hint_global[family.mdp.quotient_state_map[state]] = hint.at(state)
        return hint_global

    def generalize_hints(self, family, result):
        prop = result.property
        hint_prim = self.generalize_hint(family, result.primary.result)
        hint_seco = self.generalize_hint(family, result.secondary.result) if result.secondary is not None else None
        return prop, (hint_prim, hint_seco)

    def collect_analysis_hints(self, family):
        return None # hints are disabled
        res = family.analysis_result
        analysis_hints = dict()
        for index in res.constraints_result.undecided_constraints:
            prop, hints = self.generalize_hints(family, res.constraints_result.results[index])
            analysis_hints[prop] = hints
        if res.optimality_result is not None:
            prop, hints = self.generalize_hints(family, res.optimality_result)
            analysis_hints[prop] = hints
        return analysis_hints

    def split_family(self, family):
        # filter undecided constraints, collect analysis hints
        res = family.analysis_result
        undecided = res.constraints_result.undecided_constraints
        analysis_hints = self.collect_analysis_hints(family)

        # split
        subfamilies = self.sketch.quotient.split(family.mdp)
        for subfamily in subfamilies:
            subfamily.set_analysis_hints(undecided, analysis_hints)
        return subfamilies

    def synthesize(self, family):

        self.stat.start()

        satisfying_assignment = None
        families = [family]
        Profiler.start("synthesis loop")
        while families:
            family = families.pop(-1) # DFS
            # family = families.pop(0) # BFS

            feasibility,assignment = self.analyze_family_ar(family)
            if assignment is not None:
                satisfying_assignment = assignment
            if feasibility == True:
                break
            if feasibility == False:
                continue

            # undecided
            subfamilies = self.split_family(family)            
            families = families + subfamilies

        Profiler.stop()
        self.stat.finished(satisfying_assignment)
        return satisfying_assignment


class SynthesizerCEGIS(Synthesizer):

    @property
    def method_name(self):
        return "CEGIS"

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
        self.stat.iteration_dtmc(dtmc.states)
        Profiler.resume()

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
        ce_generator.prepare_dtmc(dtmc.model, dtmc.quotient_state_map)
        conflicts = []
        for index in family.property_indices:
            if spec.constraints_result.results[index].sat:
                continue
            threshold = self.sketch.specification.constraints[index].threshold
            bounds = None if family.analysis_result is None else family.analysis_result.constraints_result.results[index].primary.result
            Profiler.start("    generating conflicts")
            conflict = ce_generator.construct_conflict(index, threshold, bounds, family.mdp.quotient_state_map)
            Profiler.resume()
            conflicts.append(conflict)

        if self.sketch.specification.has_optimality:
            index = len(self.sketch.specification.constraints)
            threshold = self.sketch.specification.optimality.threshold
            bounds = None if family.analysis_result is None else family.analysis_result.optimality_result.primary.result
            Profiler.start("    generating conflicts")
            conflict = ce_generator.construct_conflict(index, threshold, bounds, family.mdp.quotient_state_map)
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

        self.stat.start()

        # assert that no reward formula is maximizing
        msg = "Cannot use CEGIS for maximizing reward formulae -- consider using AR or hybrid methods."
        for c in self.sketch.specification.constraints:
            assert not (c.reward and not c.minimizing), msg
        if self.sketch.specification.has_optimality:
            c = self.sketch.specification.optimality
            assert not (c.reward and not c.minimizing), msg

        # map mdp states to hole indices
        quotient_relevant_holes = self.sketch.quotient.quotient_relevant_holes

        # initialize CE generator
        formulae = self.sketch.specification.stormpy_formulae()
        ce_generator = stormpy.synthesis.CounterexampleGenerator(
            self.sketch.quotient.quotient_mdp, self.sketch.design_space.num_holes,
            quotient_relevant_holes, formulae)

        # encode family
        family.z3_initialize()
        
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
        self.cegis_efficiency = 10


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

        if self.pruned_ar == 0 and self.pruned_cegis == 0:
            self.cegis_efficiency = 1
        elif self.pruned_ar == 0 and self.pruned_cegis > 0:
            self.cegis_efficiency = 2
        elif self.pruned_ar > 0 and self.pruned_cegis == 0:
            self.cegis_efficiency = 0.5
        else:
            success_rate_cegis = self.pruned_cegis / self.timer_cegis.read()
            success_rate_ar = self.pruned_ar / self.timer_ar.read()
            self.cegis_efficiency = success_rate_cegis / success_rate_ar
        return True

class SynthesizerHybrid(SynthesizerAR, SynthesizerCEGIS):

    @property
    def method_name(self):
        return "hybrid"

    def synthesize(self, family):

        self.stat.start()

        self.stage_control = StageControl(family.size)

        quotient_relevant_holes = self.sketch.quotient.quotient_relevant_holes
        formulae = self.sketch.specification.stormpy_formulae()
        ce_generator = stormpy.synthesis.CounterexampleGenerator(
            self.sketch.quotient.quotient_mdp, self.sketch.design_space.num_holes,
            quotient_relevant_holes, formulae)
        
        Profiler.start("synthesis loop")

        # encode family
        family.z3_initialize()

        # AR loop
        satisfying_assignment = None
        families = [family]
        while families:
            # MDP analysis
            self.stage_control.start_ar()
            
            family = families.pop(-1) # DFS
            # family = families.pop(0) # BFS

            feasibility,improving_assignment = self.analyze_family_ar(family)
            if improving_assignment is not None:
                satisfying_assignment = improving_assignment
            if feasibility == True:
                break
            if feasibility == False:
                self.stage_control.prune_ar(family.size)
                continue

            # undecided: initiate CEGIS
            self.stage_control.start_cegis()
            assignment = family.pick_assignment()
            sat = False
            while assignment is not None:
                
                sat, improving, _ = self.analyze_family_assignment_cegis(family, assignment, ce_generator)
                if improving:
                    satisfying_assignment = assignment
                if sat:
                    break
                # member is UNSAT
                if self.stage_control.cegis_step():
                    break
                
                # cegis still has time: check next assignment
                assignment = family.pick_assignment()

            if sat:
                break
            if assignment is None:
                self.explore(family)
                self.stage_control.prune_cegis(family.size)
                continue
        
            # CEGIS could not process the family: split
            subfamilies = self.split_family(family)
            families = families + subfamilies

        ce_generator.print_profiling()

        self.stat.finished(satisfying_assignment)
        Profiler.stop()
        return satisfying_assignment

