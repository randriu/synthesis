import stormpy.synthesis

import logging
logger = logging.getLogger(__name__)


class ConflictGeneratorStorm():

    def __init__(self, quotient):
        self.quotient = quotient
        self.counterexample_generator = None

    @property
    def name(self):
        return "(Storm)"

    def initialize(self):
        state_to_holes_bv = self.quotient.coloring.getStateToHoles().copy()
        state_to_holes = []
        for state,holes_bv in enumerate(state_to_holes_bv):
            holes = set([hole for hole in holes_bv])
            state_to_holes.append(holes)

        formulae = self.quotient.specification.stormpy_formulae()
        self.counterexample_generator = stormpy.synthesis.CounterexampleGenerator(
            self.quotient.quotient_mdp, self.quotient.design_space.num_holes,
            state_to_holes, formulae)


    def construct_conflicts(self, family, assignment, dtmc, conflict_requests, accepting_assignment):
        
        self.counterexample_generator.prepare_dtmc(dtmc.model, dtmc.quotient_state_map)
        
        conflicts = []
        for request in conflict_requests:
            index,prop,_,family_result = request

            threshold = prop.threshold

            bounds = None
            scheduler_selection = None
            if family_result is not None:
                bounds = family_result.primary.result

            conflict = self.counterexample_generator.construct_conflict(index, threshold, bounds, family.mdp.quotient_state_map)
            conflicts.append(conflict)
        
        return conflicts, accepting_assignment
