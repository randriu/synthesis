import stormpy.synthesis

from .synthesizer import Synthesizer

import logging
logger = logging.getLogger(__name__)


class SynthesizerCEGIS(Synthesizer):

    @property
    def method_name(self):
        return "CEGIS"

    def generalize_conflict(self, assignment, conflict, scheduler_selection):

        if not Synthesizer.incomplete_search:
            return conflict

        # filter holes set to consistent assignment
        conflict_filtered = []
        for hole in conflict:
            scheduler_options = scheduler_selection[hole]
            # if len(scheduler_options) == 1 and assignment[hole].options[0] == scheduler_options[0]:
            if len(scheduler_options) == 1:
                continue
            conflict_filtered.append(hole)

        return conflict_filtered

    
    def construct_conflicts(self, family, assignment, dtmc, conflict_requests, ce_generator):
        
        ce_generator.prepare_dtmc(dtmc.model, dtmc.quotient_state_map)
        
        conflicts = []
        for request in conflict_requests:
            index,prop,_,family_result = request

            threshold = prop.threshold

            bounds = None
            scheduler_selection = None
            if family_result is not None:
                bounds = family_result.primary.result
                scheduler_selection = family_result.primary_selection

            conflict = ce_generator.construct_conflict(index, threshold, bounds, family.mdp.quotient_state_map)
            conflict = self.generalize_conflict(assignment, conflict, scheduler_selection)
            conflicts.append(conflict)
        
        return conflicts

    

    def analyze_family_assignment_cegis(self, family, assignment, ce_generator):
        """
        :return (1) specification satisfiability (True/False)
        :return (2) whether this is an improving assignment
        """

        assert family.property_indices is not None, "analyzed family does not have the relevant properties list"
        assert family.mdp is not None, "analyzed family does not have an associated quotient MDP"

        # print(assignment)

        dtmc = self.quotient.build_chain(assignment)
        self.stat.iteration_dtmc(dtmc.states)
        spec = dtmc.check_specification(self.quotient.specification,
            property_indices = family.property_indices, short_evaluation = False)

        # analyze model checking results
        improving = False
        if spec.constraints_result.all_sat:
            if not self.quotient.specification.has_optimality:
                return True, True
            if spec.optimality_result is not None and spec.optimality_result.improves_optimum:
                opt = self.quotient.specification.optimality
                opt.update_optimum(spec.optimality_result.value)
                if not opt.reward and opt.minimizing and opt.threshold == 0:
                    return True, True
                self.since_last_optimum_update = 0
                improving = True

        # construct conflict wrt each unsatisfiable property
        # pack all unsatisfiable properties as well as their MDP results (if exists)
        conflict_requests = []
        for index in family.property_indices:
            member_result = spec.constraints_result.results[index]
            if member_result.sat:
                continue
            prop = self.quotient.specification.constraints[index]
            family_result = family.analysis_result.constraints_result.results[index] if family.analysis_result is not None else None
            conflict_requests.append( (index,prop,member_result,family_result) )
        if self.quotient.specification.has_optimality:
            member_result = spec.optimality_result
            index = len(self.quotient.specification.constraints)
            prop = self.quotient.specification.optimality
            family_result = family.analysis_result.optimality_result if family.analysis_result is not None else None
            conflict_requests.append( (index,prop,member_result,family_result) )

        conflicts = self.construct_conflicts(family, assignment, dtmc, conflict_requests, ce_generator)

        # use conflicts to exclude the generalizations of this assignment
        for conflict in conflicts:
            family.exclude_assignment(assignment, conflict)

        return False, improving


    def initialize_ce_generator(self):
        quotient_relevant_holes = self.quotient.coloring.state_to_holes
        formulae = self.quotient.specification.stormpy_formulae()
        ce_generator = stormpy.synthesis.CounterexampleGenerator(
            self.quotient.quotient_mdp, self.quotient.design_space.num_holes,
            quotient_relevant_holes, formulae)
        return ce_generator

    
    def synthesize(self, family):

        logger.info("Synthesis initiated.")
        self.stat.start()

        # assert that no reward formula is maximizing
        msg = "Cannot use CEGIS for maximizing reward formulae -- consider using AR or hybrid methods."
        for c in self.quotient.specification.constraints:
            assert not (c.reward and not c.minimizing), msg
        if self.quotient.specification.has_optimality:
            c = self.quotient.specification.optimality
            assert not (c.reward and not c.minimizing), msg

        # build the quotient, map mdp states to hole indices
        self.quotient.build(family)
        
        ce_generator = self.initialize_ce_generator()

        # use sketch design space as a SAT baseline
        self.quotient.design_space.sat_initialize()
        
        # CEGIS loop
        satisfying_assignment = None
        assignment = family.pick_assignment()
        while assignment is not None:
            
            sat, improving = self.analyze_family_assignment_cegis(family, assignment, ce_generator)
            if improving:
                satisfying_assignment = assignment
            if sat:
                break
            
            # construct next assignment
            assignment = family.pick_assignment()

        self.stat.finished(satisfying_assignment)
        return satisfying_assignment
