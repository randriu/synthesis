import stormpy

from switss.model import MDP, ReachabilityForm
from switss.model import DTMC as SWITSS_DTMC
from switss.problem.qsheur import QSHeur

from .synthesizer_cegis import SynthesizerCEGIS

import logging
logger = logging.getLogger(__name__)


class SynthesizerSWITSS(SynthesizerCEGIS):

    @property
    def method_name(self):
        return "CEGIS (SWITSS)"

    
    def initialize_ce_generator(self):
        return QSHeur(solver="cbc",iterations=10)

    
    def construct_conflicts(self, family, assignment, dtmc, conflict_requests, ce_generator):
        
        conflicts = []
        for request in conflict_requests:
            index,prop,member_result,family_result = request

            if prop.minimizing:
                # safety
                threshold = prop.threshold
                subformula = prop.property.raw_formula.subformula.subformula
                if isinstance(subformula, stormpy.logic.AtomicLabelFormula):
                    target_label = subformula.label
                else:
                    assert isinstance(subformula, stormpy.logic.AtomicExpressionFormula)
                    target_label = str(subformula)
            else:
                # liveness: flip threshold
                threshold =  1 - prop.threshold
                target_label = "target"
                
            # construct a labeled SWITSS DTMC
            switss_dtmc = SWITSS_DTMC.from_stormpy(dtmc.model)
            for i,state in enumerate(dtmc.model.states):
                # copy labels
                for label in state.labels:
                    switss_dtmc.add_label(i, label)

                # label fail states
                if not prop.minimizing and not member_result.result.at(i) > 0.0:
                    switss_dtmc.add_label(i, "target")

            # label states by relevant holes id
            for dtmc_state in range(dtmc.states):
                mdp_state = dtmc.quotient_state_map[dtmc_state]
                for hole in dtmc.quotient_container.coloring.state_to_holes[mdp_state]:
                    switss_dtmc.add_label(dtmc_state, str(hole))

            switss_dtmc_rf,_,_ = ReachabilityForm.reduce(switss_dtmc, "init", target_label)
            results = list(ce_generator.solveiter(switss_dtmc_rf, threshold, "max"))

            # get last result
            witnessing_subsystem = results[-1].subsystem.subsys.system
            conflict = set([int(label) for label in witnessing_subsystem.states_by_label.keys() if label.isnumeric()])
            conflict = list(conflict)
            
            scheduler_selection = None
            if family_result is not None:
                scheduler_selection = family_result.primary_selection
            conflict = self.generalize_conflict(assignment, conflict, scheduler_selection)
            conflicts.append(conflict)

        return conflicts    
