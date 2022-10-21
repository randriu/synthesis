import stormpy.synthesis

from .synthesizer import Synthesizer
from .synthesizer_ar import SynthesizerAR
from .synthesizer_cegis import SynthesizerCEGIS
from ..quotient.smt import SmtSolver

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

    def __init__(self):
        # timings
        self.timer_ar = Timer()
        self.timer_cegis = Timer()
        
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
        return False


class SynthesizerHybrid(SynthesizerAR, SynthesizerCEGIS):

    @property
    def method_name(self):
        return "hybrid"

    def synthesize_assignment(self, family):

        self.stage_control = StageControl()

        self.conflict_generator.initialize()
        smt_solver = SmtSolver(self.quotient.design_space)

        # AR loop
        satisfying_assignment = None
        families = [family]
        while families:

            # initiate AR analysis
            self.stage_control.start_ar()
            
            # choose family
            if SynthesizerAR.exploration_order_dfs:
                family = families.pop(-1)
            else:
                family = families.pop(0)

            # reset SMT solver level
            if SynthesizerAR.exploration_order_dfs:
                smt_solver.level(family.refinement_depth)

            # analyze the family
            can_improve,improving_assignment = self.analyze_family_ar(family)
            if improving_assignment is not None:
                satisfying_assignment = improving_assignment
            if improving_assignment is not None:
                satisfying_assignment = improving_assignment
            if can_improve == False:
                self.explore(family)
                continue

            # undecided: initiate CEGIS analysis
            self.stage_control.start_cegis()

            # construct priority subfamily that corresponds to primary scheduler
            scheduler_selection = family.analysis_result.optimality_result.primary_selection
            priority_subfamily = family.copy()
            priority_subfamily.assume_options(scheduler_selection)

            # explore family assignments
            family.encode(smt_solver)
            while True:

                if not self.stage_control.cegis_has_time():
                    break   # CEGIS timeout

                assignment = smt_solver.pick_assignment(family)
                # assignment = family.pick_assignment_priority(priority_subfamily)
                if assignment is None:
                    break   # explored whole family
                
                conflicts, accepting_assignment = self.analyze_family_assignment_cegis(family, assignment)
                smt_solver.exclude_conflicts(family, assignment, conflicts)

                if accepting_assignment is not None:
                    satisfying_assignment = accepting_assignment
                    if not self.quotient.specification.can_be_improved:
                        return satisfying_assignment

                # assignment is UNSAT: move on to the next assignment

            if not family.encoding.has_assignments:
                self.explore(family)
                continue
        
            subfamilies = self.quotient.split(family, Synthesizer.incomplete_search)
            families = families + subfamilies

        return satisfying_assignment

