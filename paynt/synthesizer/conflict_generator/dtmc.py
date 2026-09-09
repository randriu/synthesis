from __future__ import annotations

from typing import Any

import paynt.colored_mdp
import paynt.task
import paynt.synthesizer.search_node

import payntbind

import logging
logger = logging.getLogger(__name__)


class ConflictGeneratorDtmc():

    def __init__(self, colored_mdp : paynt.colored_mdp.ColoredMdp, task : paynt.task.Task):
        self.colored_mdp = colored_mdp
        self.task = task
        self.counterexample_generator : Any = None

    @property
    def name(self) -> str:
        return "(DTMC)"

    def initialize(self) -> None:
        state_to_parameters_bv = self.colored_mdp.coloring.getStateToHoles().copy()
        state_to_parameters = []
        for state,parameters_bv in enumerate(state_to_parameters_bv):
            parameters = set([parameter for parameter in parameters_bv])
            state_to_parameters.append(parameters)
        formulae = self.task.specification.stormpy_formulae()
        self.counterexample_generator = payntbind.synthesis.CounterexampleGenerator(
            self.colored_mdp.underlying_mdp, self.colored_mdp.parameter_space.num_parameters,
            state_to_parameters, formulae
        )


    def prepare_model(self, model : Any) -> None:
        self.counterexample_generator.prepare_dtmc(model.model, model.underlying_mdp_state_map)

    def construct_conflicts(
        self, node : paynt.synthesizer.search_node.SearchNode, assignment : Any, dtmc : Any, conflict_requests : list[tuple[int, Any, Any]]
    ) -> list[Any]:

        self.prepare_model(dtmc)

        conflicts = []
        for request in conflict_requests:
            index,prop,parameter_space_result = request

            threshold = prop.threshold

            bounds = None
            if parameter_space_result is not None:
                bounds = parameter_space_result.primary.result

            assert node.mdp is not None
            conflict = self.counterexample_generator.construct_conflict(index, threshold, bounds, node.mdp.underlying_mdp_state_map)
            conflicts.append(conflict)

        return conflicts
