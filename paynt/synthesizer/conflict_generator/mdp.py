from .storm import ConflictGeneratorStorm

from paynt.verification.property import OptimalityProperty

import logging
logger = logging.getLogger(__name__)


class ConflictGeneratorMdp(ConflictGeneratorStorm):

    @property
    def name(self):
        return "(MDP generalization)"

    def initialize(self):
        # left intentionally blank
        pass

    def construct_conflicts(self, family, assignment, dtmc, conflict_requests, accepting_assignment):

        assert len(conflict_requests) == 1, \
        "we don't know how to handle multiple conflict requests in this mode, consider CEGIS in another mode"

        # generalize simple holes, i.e. starting from the full family, fix each
        # non-simple hole to the option selected by the assignment
        subfamily = family.copy()
        non_simple_holes = [hole for hole in range(subfamily.num_holes) if not family.mdp.hole_simple[hole]]
        # percentage = (1 - len(non_simple_holes) / family.num_holes) * 100
        for hole in non_simple_holes:
            subfamily.hole_set_options(hole,assignment.hole_options(hole))
        self.quotient.build(subfamily)
        submdp = subfamily.mdp

        _,prop,_,family_result = conflict_requests[0]

        # check primary direction
        primary = submdp.model_check_property(prop)
        if primary.sat:
            # found satisfying assignment
            selection,_,_,_,consistent = self.quotient.scheduler_consistent(submdp, prop, primary.result)
            assert consistent
            if isinstance(prop, OptimalityProperty):
                self.quotient.specification.optimality.update_optimum(primary.value)
            accepting_assignment = family.copy()
            for hole in range(family.num_holes):
                accepting_assignment.hole_set_options(hole,selection[hole])
        conflict = non_simple_holes
        conflicts = [conflict]

        return conflicts, accepting_assignment

    

