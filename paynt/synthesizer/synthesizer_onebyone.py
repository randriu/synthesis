from .synthesizer import Synthesizer

import logging
logger = logging.getLogger(__name__)


class SynthesizerOneByOne(Synthesizer):
    
    @property
    def method_name(self):
        return "1-by-1"

    def synthesize_assignment(self, family):
        
        satisfying_assignment = None
        for hole_combination in family.all_combinations():
            
            assignment = family.construct_assignment(hole_combination)
            chain = self.quotient.build_chain(assignment)
            self.stat.iteration_dtmc(chain.states)
            result = chain.check_specification(self.quotient.specification, short_evaluation = True)
            self.explore(assignment)

            accepting,improving_value = result.accepting_dtmc(self.quotient.specification)
            if accepting:
                satisfying_assignment = assignment
            if improving_value is not None:
                self.quotient.specification.optimality.update_optimum(improving_value)
            if accepting and not self.quotient.specification.can_be_improved:
                return accepting_assignment

        return satisfying_assignment

    def evaluate_all(self, family=None):
        raise NotImplementedError("One-by-one synthesizer does not support evaluation of all family members")
