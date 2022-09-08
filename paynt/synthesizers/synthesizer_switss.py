from opcode import hasconst
import stormpy
from scipy.sparse import dok_matrix

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


    def construct_conflicts(self, family, assignment, dtmc, conflict_requests, ce_generator):

        conflicts = []
        for request in conflict_requests:
            index, prop, member_result, family_result = request

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

            # label states by relevant holes id
            for dtmc_state in range(dtmc.states):
                mdp_state = dtmc.quotient_state_map[dtmc_state]
                for hole in dtmc.quotient_container.coloring.state_to_holes[mdp_state]:
                    switss_dtmc.add_label(dtmc_state, str(hole))

            if prop.minimizing:
                switss_dtmc_rf, _, _ = ReachabilityForm.reduce(switss_dtmc, "init", target_label)
                results = list(ce_generator.solveiter(switss_dtmc_rf, threshold, "max", ignore_consistency_checks=True))
                witnessing_subsystem = results[-1].subsystem.subsys.system # TODO: remove unreachable states

                conflict = set([int(label) for label in witnessing_subsystem.states_by_label.keys() if label.isnumeric()])
                conflict = list(conflict)
            else:
                no_states = switss_dtmc.N

                # compute all bottom SCCs
                scc_arr, proper_scc_mask, no_of_sccs = switss_dtmc.maximal_end_components()
                new_transation_matrix = dok_matrix((no_of_sccs,no_of_sccs))

                labels = { "init" : { scc_arr[0] }, "target" : set() }

                # collapse states according to computed bottom SCCs
                for i in range(no_states):
                    i_scc = scc_arr[i]

                    labels[str(i)] = set()
                    # save old id of state via label
                    labels[str(i)].add(i_scc)

                    if proper_scc_mask[i_scc] == 1:
                        # label target states
                        labels["target"].add(i_scc)
                        new_transation_matrix[i_scc,i_scc] = 1
                    else:
                        for j in range(no_states):
                            j_scc = scc_arr[j]
                            new_transation_matrix[i_scc,j_scc] += switss_dtmc.P[i,j]

                transformed_switss_dtmc = SWITSS_DTMC(new_transation_matrix, label_to_states=labels)
                switss_dtmc_rf,_,_ = ReachabilityForm.reduce(transformed_switss_dtmc, "init", target_label)
                results = list(ce_generator.solveiter(switss_dtmc_rf, threshold, "max", ignore_consistency_checks=True))
                witnessing_subsystem = results[-1].subsystem.subsys.system # TODO: remove unreachable states

                conflict = set()
                for state_label in witnessing_subsystem.states_by_label.keys():
                    if state_label.isnumeric():
                        conflict |= switss_dtmc.labels_by_state[int(state_label)]
                conflict = [int(hole_id) for hole_id in conflict if hole_id.isnumeric()]

            scheduler_selection = None
            if family_result is not None:
                scheduler_selection = family_result.primary_selection
            conflict = self.generalize_conflict(assignment, conflict, scheduler_selection)
            conflicts.append(conflict)

        return conflicts    
