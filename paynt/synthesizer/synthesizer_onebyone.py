from .synthesizer import Synthesizer

import logging
logger = logging.getLogger(__name__)


class SynthesizerOneByOne(Synthesizer):
    
    @property
    def method_name(self):
        return "1-by-1"

    def synthesize(self, family):
        
        logger.info("Synthesis initiated.")
        self.stat.start()

        satisfying_assignment = None
        for hole_combination in family.all_combinations():
            
            assignment = family.construct_assignment(hole_combination)
            chain = self.quotient.build_chain(assignment)
            self.stat.iteration_dtmc(chain.states)
            result = chain.check_specification(self.quotient.specification, short_evaluation = True)
            self.explore(assignment)

            if not result.constraints_result.all_sat:
                continue
            if not self.quotient.specification.has_optimality:
                satisfying_assignment = assignment
                break
            if result.optimality_result.improves_optimum:
                self.quotient.specification.optimality.update_optimum(result.optimality_result.value)
                satisfying_assignment = assignment

        self.stat.finished(satisfying_assignment)

        return satisfying_assignment
