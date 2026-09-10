"""
Factory producing a FamilyColoredMdp from an already-built (underlying_mdp, parameter_space, coloring) triple
-- unlike the POMDP/POSMG/Dec-POMDP factories, this one does not construct the parameter space/coloring from
scratch (the parser already builds those for any PRISM-with-parameters sketch); its only extra job is
optionally unfolding scheduler memory on top of what it was given.
"""

from __future__ import annotations

from typing import Any

import payntbind

import paynt.family.colored_mdp
import paynt.family.task
import paynt.parameter_space.parameter_space
import paynt.underlying_model.underlying_model

import logging

logger = logging.getLogger(__name__)


class FamilyColoredMdpFactory:

    def __init__(
        self,
        underlying_mdp: Any,
        parameter_space: paynt.parameter_space.parameter_space.ParameterSpace,
        coloring: Any,
        task: paynt.family.task.FamilyTask,
        use_exact: bool = False,
    ):
        self.task = task
        self.use_exact = use_exact
        self.memory_unfolder: Any = None

        if self.task.memory_size > 1:
            underlying_mdp, parameter_space, coloring = self.unfold_scheduler_memory(underlying_mdp, parameter_space, coloring)

        self.underlying_mdp = underlying_mdp
        self.parameter_space = parameter_space
        self.coloring = coloring

        self.action_labels: list[str]
        self.choice_to_action: list[int]
        self.action_labels, self.choice_to_action = payntbind.synthesis.extractActionLabels(underlying_mdp)
        self.num_actions = len(self.action_labels)
        self.state_action_choices = FamilyColoredMdpFactory.map_state_action_to_choices(underlying_mdp, self.num_actions, self.choice_to_action)
        self.state_to_actions = FamilyColoredMdpFactory.map_state_to_available_actions(self.state_action_choices)

        self.colored_mdp = self._construct_colored_mdp()

    def _construct_colored_mdp(self) -> paynt.family.colored_mdp.FamilyColoredMdp:
        """Overridable so subclasses (e.g. PomdpFamilyColoredMdpFactory) can produce their own ColoredMdp
        subclass while reusing all of the construction above."""
        return paynt.family.colored_mdp.FamilyColoredMdp(
            self.underlying_mdp,
            self.parameter_space,
            self.coloring,
            self.use_exact,
            self.num_actions,
            self.action_labels,
            self.choice_to_action,
            self.state_action_choices,
            self.state_to_actions,
        )

    def unfold_scheduler_memory(
        self, underlying_mdp: Any, parameter_space: paynt.parameter_space.parameter_space.ParameterSpace, coloring: Any
    ) -> tuple[Any, paynt.parameter_space.parameter_space.ParameterSpace, Any]:
        """
        Unfold the scheduler memory of the underlying MDP to the initial_memory_size.
        :returns a new underlying MDP with unfolded scheduler memory
        """

        logger.info(f"unfolding scheduler memory of {self.task.memory_size} into the model.")

        # unfold the scheduler memory into the model
        self.memory_unfolder = payntbind.synthesis.MemoryUnfolder(underlying_mdp)
        unfolded_mdp = self.memory_unfolder.construct_unfolded_model(self.task.memory_size)

        # create new coloring
        choice_to_parameter_options = []
        original_choice_to_parameter_options = coloring.getChoiceToAssignment()
        choice_map = list(self.memory_unfolder.choice_map)
        for choice in range(unfolded_mdp.nr_choices):
            original_choice = choice_map[choice]
            choice_to_parameter_options.append(original_choice_to_parameter_options[original_choice])

        new_coloring = payntbind.synthesis.Coloring(parameter_space.native, unfolded_mdp.nondeterministic_choice_indices, choice_to_parameter_options)

        logger.info(f"unfolded model has {unfolded_mdp.nr_states} states and {unfolded_mdp.nr_choices} choices.")

        return unfolded_mdp, parameter_space, new_coloring

    @staticmethod
    def map_state_action_to_choices(mdp: Any, num_actions: int, choice_to_action: list[int]) -> list[list[list[int]]]:
        state_action_choices = []
        for state in range(mdp.nr_states):
            action_choices: list[list[int]] = [[] for action in range(num_actions)]
            for choice in mdp.transition_matrix.get_rows_for_group(state):
                action = choice_to_action[choice]
                action_choices[action].append(choice)
            state_action_choices.append(action_choices)
        return state_action_choices

    @staticmethod
    def map_state_to_available_actions(state_action_choices: list[list[list[int]]]) -> list[list[int]]:
        state_to_actions = []
        for _state, action_choices in enumerate(state_action_choices):
            available_actions = []
            for action, choices in enumerate(action_choices):
                if choices:
                    available_actions.append(action)
            state_to_actions.append(available_actions)
        return state_to_actions
