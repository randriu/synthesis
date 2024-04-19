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
            dtmc = self.quotient.build_assignment(assignment)
            self.stat.iteration(dtmc)
            result = self.quotient.check_specification_for_dtmc(dtmc, short_evaluation=True)
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

        evaluations = []
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
                evaluation = paynt.synthesizer.synthesizer.FamilyEvaluation(assignment, result.value, result.sat, policy)
            evaluations.append(evaluation)
            self.explore(assignment)
        return evaluations

    def export_evaluation_result(self, evaluations, export_filename_base):
        import json
        family_to_evaluation_parsed = []
        for evaluation in evaluations:
            family = evaluation.family
            policy = evaluation.policy
            if policy is None:
                policy = "UNSAT"
            else:
                policy = self.quotient.policy_to_state_valuation_actions(policy)
            family_to_evaluation_parsed.append( (str(family),policy) )
        policies_string = json.dumps(family_to_evaluation_parsed, indent=2)
        policies_filename = export_filename_base + ".json"
        with open(policies_filename, 'w') as file:
            file.write(policies_string)
        logger.info(f"exported satisfied members and correponding policies to {policies_filename}")
