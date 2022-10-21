import stormpy.synthesis

from .synthesizer import Synthesizer
from ..quotient.smt import SmtSolver
from .conflict_generator.storm import ConflictGeneratorStorm
from .conflict_generator.switss import ConflictGeneratorSwitss
from .conflict_generator.mdp import ConflictGeneratorMdp

import logging
logger = logging.getLogger(__name__)


class SynthesizerCEGIS(Synthesizer):

    # CLI argument selecting conflict generator
    conflict_generator_type = None

    def __init__(self, quotient):
        super().__init__(quotient)

        self.conflict_generator = self.choose_conflict_generator(quotient)

        # assert that no reward formula is maximizing
        assert not self.quotient.specification.contains_maximizing_reward_properties, \
            "Cannot use CEGIS for maximizing reward formulae -- consider using AR or hybrid methods."

    
    def choose_conflict_generator(self, quotient):
        if SynthesizerCEGIS.conflict_generator_type == "storm":
            conflict_generator = ConflictGeneratorStorm(quotient)
        elif SynthesizerCEGIS.conflict_generator_type == "switss":
            conflict_generator = ConflictGeneratorSwitss(quotient)
        elif SynthesizerCEGIS.conflict_generator_type == "mdp":
            conflict_generator = ConflictGeneratorMdp(quotient)
        else:
            pass # left intentionally blank
        return conflict_generator

    
    @property
    def method_name(self):
        return "CEGIS " + self.conflict_generator.name

    
    # def generalize_conflict(self, assignment, conflict, scheduler_selection):

    #     if not Synthesizer.incomplete_search:
    #         return conflict

    #     # filter holes set to consistent assignment
    #     conflict_filtered = []
    #     for hole in conflict:
    #         scheduler_options = scheduler_selection[hole]
    #         # if len(scheduler_options) == 1 and assignment[hole].options[0] == scheduler_options[0]:
    #         if len(scheduler_options) == 1:
    #             continue
    #         conflict_filtered.append(hole)

    #     return conflict_filtered

    def collect_conflict_requests(self, family, mc_result):
        '''
        Construct conflict request wrt each unsatisfiable property,
            pack such properties as well as their MDP results (if available)
        '''
        conflict_requests = []
        for index in family.property_indices:
            member_result = mc_result.constraints_result.results[index]
            if member_result.sat:
                continue
            prop = self.quotient.specification.constraints[index]
            family_result = family.analysis_result.constraints_result.results[index] if family.analysis_result is not None else None
            conflict_requests.append( (index,prop,member_result,family_result) )
        if self.quotient.specification.has_optimality:
            member_result = mc_result.optimality_result
            index = len(self.quotient.specification.constraints)
            prop = self.quotient.specification.optimality
            family_result = family.analysis_result.optimality_result if family.analysis_result is not None else None
            conflict_requests.append( (index,prop,member_result,family_result) )

        return conflict_requests


    def analyze_family_assignment_cegis(self, family, assignment):
        """
        :return (1) list of conflicts to exclude from design space (might be empty)
        :return (2) accepting assignment (or None)
        """

        assert family.property_indices is not None, "analyzed family does not have the relevant properties list"
        assert family.mdp is not None, "analyzed family does not have an associated quotient MDP"

        dtmc = self.quotient.build_chain(assignment)
        self.stat.iteration_dtmc(dtmc.states)
        mc_result = dtmc.check_specification(self.quotient.specification,
            property_indices = family.property_indices, short_evaluation = False)

        # analyze model checking results
        accepting_assignment = None
        accepting,improving_value = mc_result.accepting_dtmc(self.quotient.specification)
        if accepting:
            accepting_assignment = assignment
        if improving_value is not None:
            self.quotient.specification.optimality.update_optimum(improving_value)
        if accepting and not self.quotient.specification.can_be_improved:
            return [], accepting_assignment

        conflict_requests = self.collect_conflict_requests(family, mc_result)
        conflicts, accepting_assignment = self.conflict_generator.construct_conflicts(
            family, assignment, dtmc, conflict_requests, accepting_assignment)

        return conflicts, accepting_assignment


    def synthesize_assignment(self, family):

        # build the quotient, map mdp states to hole indices
        self.quotient.build(family)

        simple_holes = [hole_index for hole_index in family.hole_indices if family.mdp.hole_simple[hole_index]]
        logger.info("{}/{} holes are trivial".format(len(simple_holes), family.num_holes))
        
        self.conflict_generator.initialize()

        # use sketch design space as a SAT baseline (TODO why?)
        smt_solver = SmtSolver(self.quotient.design_space)
        
        # CEGIS loop
        satisfying_assignment = None
        assignment = smt_solver.pick_assignment(family)
        while assignment is not None:
            
            conflicts, accepting_assignment = self.analyze_family_assignment_cegis(family, assignment)
            pruned = smt_solver.exclude_conflicts(family, assignment, conflicts)
            self.explored += pruned

            if accepting_assignment is not None:
                satisfying_assignment = accepting_assignment
                if not self.quotient.specification.can_be_improved:
                    return satisfying_assignment
            
            # construct next assignment
            assignment = smt_solver.pick_assignment(family)
        return satisfying_assignment
