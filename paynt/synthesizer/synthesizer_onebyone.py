from __future__ import annotations

from typing import Any

import paynt.parameter_space.parameter_space
import paynt.synthesizer.search_node
import paynt.synthesizer.synthesizer

import logging

logger = logging.getLogger(__name__)


class SynthesizerOneByOne(paynt.synthesizer.synthesizer.Synthesizer):

    @property
    def method_name(self) -> str:
        return "1-by-1"

    def synthesize_one(self, node: paynt.synthesizer.search_node.SearchNode) -> paynt.parameter_space.parameter_space.ParameterSpace | None:

        for parameter_combination in node.parameter_space.all_combinations():

            assignment = node.parameter_space.construct_assignment(parameter_combination)
            dtmc = self.colored_mdp.build_assignment(assignment)
            assert self.stat is not None
            self.stat.iteration(dtmc)
            result = dtmc.check_specification(self.task.specification, short_evaluation=True)
            self.explore(assignment)

            accepting, improving_value = result.accepting_dtmc(self.task.specification)
            if accepting:
                self.best_assignment = assignment
            if improving_value is not None:
                assert self.task.specification.optimality is not None
                self.task.specification.optimality.update_optimum(improving_value)
                self.best_assignment_value = improving_value
            if accepting and not self.task.specification.can_be_improved():
                return self.best_assignment

        return self.best_assignment

    def evaluate_all(self, parameter_space: paynt.parameter_space.parameter_space.ParameterSpace, prop: Any, keep_value_only: bool = False) -> list[Any]:

        if not keep_value_only:
            logger.debug("forcing keep_value_only=True for the one-by-one evaluation")
            keep_value_only = True

        evaluations = []
        assert self.stat is not None
        for parameter_combination in parameter_space.all_combinations():
            assignment = parameter_space.construct_assignment(parameter_combination)
            model = self.colored_mdp.build_assignment(assignment)
            self.stat.iteration(model)
            result = model.model_check_property(prop)
            if keep_value_only:
                evaluation: Any = result.value
            else:
                policy = None
                if result.sat:
                    policy = self.colored_mdp.scheduler_to_policy(result.result.scheduler, model)  # type: ignore[attr-defined]
                evaluation = paynt.synthesizer.synthesizer.ParameterSpaceEvaluation(assignment, result.value, result.sat, policy)
            evaluations.append(evaluation)
            self.explore(assignment)
        return evaluations

    def export_evaluation_result(self, evaluations: list[Any], export_filename_base: str) -> None:
        import json

        parameter_space_to_evaluation_parsed = []
        for evaluation in evaluations:
            parameter_space = evaluation.parameter_space
            policy = evaluation.policy
            if policy is None:
                policy = "UNSAT"
            else:
                policy = self.colored_mdp.policy_to_state_valuation_actions(policy)  # type: ignore[attr-defined]
            parameter_space_to_evaluation_parsed.append((str(parameter_space), policy))
        policies_string = json.dumps(parameter_space_to_evaluation_parsed, indent=2)
        policies_filename = export_filename_base + ".json"
        with open(policies_filename, "w") as file:
            file.write(policies_string)
        logger.info(f"exported satisfied members and correponding policies to {policies_filename}")
