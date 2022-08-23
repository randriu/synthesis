from switss.model import MDP, ReachabilityForm
from switss.model import DTMC as SWITSS_DTMC
from switss.problem.qsheur import QSHeur

from .synthesizer import SynthesizerCEGIS

import logging
logger = logging.getLogger(__name__)


class SynthesizerSwitss(SynthesizerCEGIS):

    @property
    def method_name(self):
        return "CEGIS (SWITSS)"

    
    def initialize_ce_generator(self):
        return QSHeur(solver="cbc",iterations=10)

    
    def get_labeled_switss_dtmc(self, dtmc_model, prop, constraints_result):
        switss_dtmc = SWITSS_DTMC.from_stormpy(dtmc_model)
        for i,state in enumerate(dtmc_model.states):

            # label fail states
            if not prop.minimizing and not constraints_result.result.at(i) > 0.0:
                switss_dtmc.add_label(i, "target")

            # relabel states in SWITSS model from STORMPY model
            for label in state.labels:
                switss_dtmc.add_label(i, label)

        return switss_dtmc

    
    def construct_conflicts(self, family, assignment, dtmc, conflict_requests, ce_generator):
        
        conflicts = []
        for request in conflict_requests:
            index,prop,property_result = request

            if not prop.minimizing:
                # Use fliped constraint to be able to construct witnesses for >=
                threshold =  1 - prop.threshold
                target_label = "target"
            else:
                # Use normal constraint
                threshold = prop.threshold
                target_label = str(prop.property.raw_formula.subformula.subformula)

            switss_dtmc = self.get_labeled_switss_dtmc(dtmc.model, prop, property_result)

            # label states by relevant holes id
            for dtmc_id, quotient_mdp_id in zip([state.id for state in dtmc.model.states],dtmc.quotient_state_map):
                for hole in dtmc.quotient_container.coloring.state_to_holes[quotient_mdp_id]:
                    switss_dtmc.add_label(dtmc_id, str(hole))

            bounds = None
            scheduler_selection = None
            if property_result is not None:
                bounds = property_result.primary.result
                scheduler_selection = property_result.primary_selection

            switss_dtmc_rf,_,_ = ReachabilityForm.reduce(switss_dtmc, "init", target_label)
            results = list(ce_generator.solveiter(switss_dtmc_rf, threshold, "max"))

            # get last result
            witnessing_subsystem = results[-1].subsystem.subsys.system
            conflict = set([int(label) for label in witnessing_subsystem.states_by_label.keys() if label.isnumeric()])
            conflict = list(conflict)
            conflict = self.generalize_conflict(assignment, conflict, scheduler_selection)
            conflicts.append(conflict)

        return conflicts    
