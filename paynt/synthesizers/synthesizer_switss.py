from os import stat_result
from time import sleep
import stormpy.synthesis
from stormpy import ComparisonType

from .synthesizer import SynthesizerCEGIS

from switss.model import MDP, ReachabilityForm
from switss.model import DTMC as SWITSS_DTMC
from switss.problem.qsheur import QSHeur

from .statistic import Statistic
from ..profiler import Timer,Profiler

import logging
logger = logging.getLogger(__name__)


class SynthesizerSwitss(SynthesizerCEGIS):

    @property
    def method_name(self):
        return "CEGIS (SWITSS)"

    def initialize_ce_generator(self):
        return QSHeur(solver="cbc",iterations=10)

    def analyze_family_assignment_cegis(self, family, assignment, ce_generator):
        """
        :return (1) specification satisfiability (True/False)
        :return (2) whether this is an improving assignment
        """

        assert family.property_indices is not None, "analyzed family does not have the relevant properties list"
        assert family.mdp is not None, "analyzed family does not have an associated quotient MDP"

        Profiler.start("CEGIS analysis")
        # print(assignment)

        # build DTMC
        dtmc = self.sketch.quotient.build_chain(assignment)
        self.stat.iteration_dtmc(dtmc.states)

        # model check all properties
        spec = dtmc.check_specification(self.sketch.specification,
            property_indices = family.property_indices, short_evaluation = False)

        # analyze model checking results
        improving = False
        if spec.constraints_result.all_sat:
            if not self.sketch.specification.has_optimality:
                Profiler.resume()
                return True, True
            if spec.optimality_result is not None and spec.optimality_result.improves_optimum:
                self.sketch.specification.optimality.update_optimum(spec.optimality_result.value)
                self.since_last_optimum_update = 0
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

        # TODO: STORM, get rid of
        # prepare DTMC for CE generation
        # ce_generator.prepare_dtmc(dtmc.model, dtmc.quotient_state_map)
        # STORM

        # construct conflict to each unsatisfiable property
        conflicts = []

        def get_labeled_switss_dtmc(dtmc_model, prop, constraints_result) -> SWITSS_DTMC:
            # TODO: create a method from this function or move it somewhere separately
            switss_dtmc = SWITSS_DTMC.from_stormpy(dtmc_model)
            for i,state in enumerate(dtmc_model.states):

                # label fail states
                if not prop.minimizing and not constraints_result.result.at(i) > 0.0:
                    switss_dtmc.add_label(i, "target")

                # relabel states in SWITSS model from STORMPY model
                for label in state.labels:
                    switss_dtmc.add_label(i, label)

            return switss_dtmc

        for request in conflict_requests:
            index,prop,property_result = request


            if prop.property.raw_formula.comparison_type == ComparisonType.GEQ:
                # Use fliped constraint to be able to construct witnesses for >=
                threshold =  1 - prop.threshold
                target_label = "target"
            else:
                # Use normal constraint
                threshold = prop.threshold
                target_label = str(prop.property.raw_formula.subformula.subformula)


            switss_dtmc = get_labeled_switss_dtmc(dtmc.model, prop, property_result)

            # label states by relevant holes id
            for dtmc_id, quotient_mdp_id in zip([state.id for state in dtmc.model.states],dtmc.quotient_state_map):
                for hole in dtmc.quotient_container.coloring.state_to_holes[quotient_mdp_id]:
                    switss_dtmc.add_label(dtmc_id, str(hole))

            bounds = None
            scheduler_selection = None
            if property_result is not None:
                bounds = property_result.primary.result
                scheduler_selection = property_result.primary_selection

            Profiler.start("storm::construct_conflict")

            # TODO: STORM, get rid of
            # conflict = ce_generator.construct_conflict(index, threshold, bounds, family.mdp.quotient_state_map)
            # Profiler.resume()
            # conflict = self.generalize_conflict(assignment, conflict, scheduler_selection)
            # STORM

            switss_dtmc_rf,_,_ = ReachabilityForm.reduce(switss_dtmc, "init", target_label)
            results = list(ce_generator.solveiter(switss_dtmc_rf, threshold, "max"))

            # get last result
            witnessing_subsystem = results[-1].subsystem.subsys.system
            conflict = set([int(label) for label in witnessing_subsystem.states_by_label.keys() if label.isnumeric()])
            conflict = list(conflict)
            conflict = self.generalize_conflict(assignment, conflict, scheduler_selection)
            conflicts.append(conflict)

        # print(conflicts)

        # use conflicts to exclude the generalizations of this assignment
        Profiler.start("holes::exclude_assignment")
        for conflict in conflicts:
            family.exclude_assignment(assignment, conflict)
        Profiler.resume()

        Profiler.resume()
        return False, improving

    
