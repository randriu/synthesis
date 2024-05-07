import paynt.synthesizer.synthesizer
import paynt.synthesizer.synthesizer_ar
import paynt.synthesizer.synthesizer_cegis

import paynt.family.smt

from ..utils.profiler import Timer

import logging
logger = logging.getLogger(__name__)


class StageControl:
    '''
    AR-CEGIS adaptivity: switch between ar/cegis, allocate more time to
    the more efficient method
    '''

    # whether only AR is performed
    only_ar = False
    # whether 1 AR followed by only CEGIS is performed
    only_cegis = False
    # whether adaptive hybrid is enabled
    adaptive_hybrid = True

    def __init__(self, family_size):
        # timings
        self.timer_ar = Timer()
        self.timer_cegis = Timer()

        self.family_size = family_size
        self.pruned_ar = 0
        self.pruned_cegis = 0
        
        # multiplier to derive time allocated for cegis
        # time_ar * factor = time_cegis
        # =1 is fair, >1 favours cegis, <1 favours ar
        self.cegis_efficiency = 1

    def start_ar(self):
        self.timer_cegis.stop()
        self.timer_ar.start()

    def start_cegis(self):
        self.timer_ar.stop()
        self.timer_cegis.start()

    def prune_ar(self, pruned):
        self.pruned_ar += pruned / self.family_size

    def prune_cegis(self, pruned):
        self.pruned_cegis += pruned / self.family_size

    def cegis_has_time(self):
        """
        :return True if cegis still has some time
        """
        
        # whether only AR is performed
        if StageControl.only_ar:
            return False

        # whether only CEGIS is performed
        if StageControl.only_cegis:
            return True

        # whether CEGIS has more time
        if self.timer_cegis.read() < self.timer_ar.read() * self.cegis_efficiency:
            return True

        # stop CEGIS
        self.timer_cegis.stop()

        if StageControl.adaptive_hybrid:
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
        
        return False


class SynthesizerHybrid(paynt.synthesizer.synthesizer_ar.SynthesizerAR, paynt.synthesizer.synthesizer_cegis.SynthesizerCEGIS):

    @property
    def method_name(self):
        return "hybrid"

    def synthesize_one(self, family):

        self.conflict_generator.initialize()
        smt_solver = paynt.family.smt.SmtSolver(self.quotient.design_space)

        # AR-CEGIS loop
        satisfying_assignment = None
        families = [family]
        self.stage_control = StageControl(family.size)
        while families:

            # initiate AR analysis
            self.stage_control.start_ar()
            
            # choose family
            family = families.pop(-1)

            # reset SMT solver level
            smt_solver.level(family.refinement_depth)

            # analyze the family
            self.verify_family(family)
            self.update_optimum(family)
            if family.analysis_result.improving_assignment is not None:
                satisfying_assignment = family.analysis_result.improving_assignment
            if family.analysis_result.can_improve == False:
                self.explore(family)
                self.stage_control.prune_ar(family.size)
                continue

            # undecided: initiate CEGIS analysis
            self.stage_control.start_cegis()

            # construct priority subfamily that corresponds to primary scheduler
            if family.analysis_result.optimality_result is not None:
                result = family.analysis_result.optimality_result
            else:
                result = family.analysis_result.constraints_result.results[0]
            priority_subfamily = family.assume_options_copy(result.primary_selection)

            # explore family assignments
            family_explored = False
            while True:

                if not self.stage_control.cegis_has_time():
                    break   # CEGIS timeout

                family.encode(smt_solver)
                # assignment = smt_solver.pick_assignment(family)
                assignment = smt_solver.pick_assignment_priority(family, priority_subfamily)
                if assignment is None:
                    family_explored = True
                    break   # explored whole family
                
                conflicts, accepting_assignment = self.analyze_family_assignment_cegis(family, assignment)
                pruned = smt_solver.exclude_conflicts(family, assignment, conflicts)
                self.explored += pruned
                self.stage_control.prune_cegis(pruned)

                if accepting_assignment is not None:
                    satisfying_assignment = accepting_assignment
                    if not self.quotient.specification.can_be_improved:
                        return satisfying_assignment

                # assignment is UNSAT: move on to the next assignment

            if family_explored:
                continue
        
            subfamilies = self.quotient.split(family, paynt.synthesizer.synthesizer.Synthesizer.incomplete_search)
            families = families + subfamilies

        return satisfying_assignment
