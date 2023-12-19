import paynt.synthesizer.synthesizer

import logging
logger = logging.getLogger(__name__)

class SynthesizerOneByOne(paynt.synthesizer.synthesizer.Synthesizer):
    
    @property
    def method_name(self):
        return "1-by-1"

    def synthesize_one(self, family):
        
        satisfying_assignment = None
        for hole_combination in family.all_combinations():
            
            assignment = family.construct_assignment(hole_combination)
            model = self.quotient.build_assignment(assignment)
            self.stat.iteration(model)
            result = model.check_specification(self.quotient.specification, short_evaluation = True)
            self.explore(assignment)

            accepting,improving_value = result.accepting_dtmc(self.quotient.specification)
            if accepting:
                satisfying_assignment = assignment
            if improving_value is not None:
                self.quotient.specification.optimality.update_optimum(improving_value)
            if accepting and not self.quotient.specification.can_be_improved:
                return accepting_assignment

        return satisfying_assignment

    def evaluate_all(self, family, prop, keep_value_only=False):

        family_to_evaluation = []
        for hole_combination in family.all_combinations():
            assignment = family.construct_assignment(hole_combination)
            model = self.quotient.build_assignment(assignment)
            self.stat.iteration(model)
            result = model.model_check_property(prop)
            if keep_value_only:
                evaluation = result.value
            else:
                policy = None
                if result.sat:
                    policy = self.quotient.scheduler_to_policy(result.result.scheduler, model)
                evaluation = paynt.synthesizer.synthesizer.FamilyEvaluation(result.value, result.sat, policy)
            family_to_evaluation.append( (assignment,evaluation) )
            self.explore(assignment)
        return family_to_evaluation
