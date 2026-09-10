"""
Constructs a PomdpColoredMdp by unfolding the agent's imperfect-information strategy into an FSC template
of a given memory size. Like paynt.posmg's factory, this supports re-unfolding at a larger memory size
after construction (PomdpSynthesizer/SayntSynthesizer increase it step by step), so the set_*_memory_size
methods are public entry points, not just __init__-time setup: each produces a fresh PomdpColoredMdp rather
than mutating the previous one in place, and the caller reassigns.
"""

from __future__ import annotations

from typing import Any

import stormpy
import stormpy.pomdp
import payntbind

import re

import paynt.colored_mdp
import paynt.pomdp.task
import paynt.parameter_space.parameter_space
from paynt.pomdp.colored_mdp import PomdpColoredMdp

import logging

logger = logging.getLogger(__name__)


class PomdpColoredMdpFactory:

    def __init__(self, pomdp: Any, task: paynt.pomdp.task.PomdpTask, decpomdp_manager: Any = None, use_exact: bool = False):
        self.task = task
        self.use_exact = use_exact
        self.posterior_aware = task.posterior_aware

        # construct the canonical POMDP
        self.pomdp = stormpy.pomdp.make_canonic(pomdp)
        # ^ this also asserts that states with the same observation have the
        # same number and the same order of available actions

        logger.info(f"constructed {'exact' if self.pomdp.is_exact else ''} POMDP having {self.observations} observations.")

        state_obs = self.pomdp.observations.copy()

        # extract observation labels
        if self.pomdp.has_observation_valuations():
            ov = self.pomdp.observation_valuations
            self.observation_labels = [ov.get_string(obs) for obs in range(self.observations)]
        else:
            if decpomdp_manager is None:
                self.observation_labels = list(range(self.observations))
                self.observation_labels = [str(label) for label in self.observation_labels]
            else:
                # map each 'joint' observation to the agent's observation and use the corresponding label
                self.observation_labels = []
                for obs in range(self.observations):
                    agent_obs = decpomdp_manager.joint_observations[obs][0]
                    agent_obs_label = decpomdp_manager.agent_observation_labels[0][agent_obs]
                    self.observation_labels.append(agent_obs_label)

        # compute actions available at each observation
        self.actions_at_observation = [0] * self.observations
        for state in range(self.pomdp.nr_states):
            obs = state_obs[state]
            if self.actions_at_observation[obs] != 0:
                continue
            self.actions_at_observation[obs] = self.pomdp.get_nr_available_actions(state)

        # collect labels of actions available at each observation
        self.action_labels_at_observation: list[list[str]] = [[] for obs in range(self.observations)]
        for state in range(self.pomdp.nr_states):
            obs = state_obs[state]
            if self.action_labels_at_observation[obs] != []:
                continue
            for offset in range(self.actions_at_observation[obs]):
                choice = self.pomdp.get_choice_index(state, offset)
                labels = self.pomdp.choice_labeling.get_labels_of_choice(choice)
                assert len(labels) <= 1, "expected at most 1 label"
                if len(labels) == 0:
                    label = paynt.colored_mdp.ColoredMdp.EMPTY_LABEL
                else:
                    label = list(labels)[0]
                self.action_labels_at_observation[obs].append(label)
        for obs, labels in enumerate(self.action_labels_at_observation):
            if len(labels) == 0:
                logger.warning(f"WARNING: POMDP has no action for observation {obs}")

        # mark perfect observations
        self.observation_states = [0 for obs in range(self.observations)]
        for state in range(self.pomdp.nr_states):
            self.observation_states[state_obs[state]] += 1

        # initialize POMDP manager
        if self.pomdp.is_exact:
            if not self.posterior_aware:
                self.pomdp_manager = payntbind.synthesis.ExactPomdpManager(self.pomdp)
            else:
                self.pomdp_manager = payntbind.synthesis.ExactPomdpManagerAposteriori(self.pomdp)
        else:
            if not self.posterior_aware:
                self.pomdp_manager = payntbind.synthesis.PomdpManager(self.pomdp)
            else:
                self.pomdp_manager = payntbind.synthesis.PomdpManagerAposteriori(self.pomdp)

        # number of memory states allocated to each observation, and the current unfolding
        self.observation_memory_size: list[int] | None = None
        self.current_memory_size: int | None = None

        # do initial unfolding
        self.colored_mdp = self.set_imperfect_memory_size(task.memory_size)
        self.current_memory_size = task.memory_size

    @property
    def observations(self) -> int:
        return self.pomdp.nr_observations

    def create_parameter_name(self, obs: int, mem: int, is_action_parameter: bool) -> str:
        category = "A" if is_action_parameter else "M"
        obs_label = self.observation_labels[obs]
        return f"{category}({obs_label},{mem})"

    def create_parameter_name_aposteriori(self, is_action_parameter: bool, mem: int, prior: int, posterior: int | None = None) -> str:
        category = "A" if is_action_parameter else "M"
        prior_label = self.observation_labels[prior]
        if posterior is None:
            return f"{category}({mem},{prior_label})"
        posterior_label = self.observation_labels[posterior]
        return f"{category}({mem},{prior_label},{posterior_label})"

    def decode_parameter_name(self, name: str) -> tuple[bool, int | None, int]:
        result = re.search(r"([A|M])\((.*?),(\d+)\)", name)
        assert result is not None
        is_action_parameter = result.group(1) == "A"
        observation_label = result.group(2)
        memory = int(result.group(3))

        observation = None
        for obs in range(self.observations):
            if observation_label == self.observation_labels[obs]:
                observation = obs
                break
        return (is_action_parameter, observation, memory)

    def set_manager_memory_vector(self) -> None:
        assert self.observation_memory_size is not None
        for obs in range(self.observations):
            mem = self.observation_memory_size[obs]
            self.pomdp_manager.set_observation_memory_size(obs, mem)

    def set_global_memory_size(self, memory_size: int) -> PomdpColoredMdp:
        self.observation_memory_size = [memory_size] * self.observations
        self.set_manager_memory_vector()
        self.current_memory_size = memory_size
        self.colored_mdp = self._unfold_memory()
        return self.colored_mdp

    def set_imperfect_memory_size(self, memory_size: int) -> PomdpColoredMdp:
        """Set given memory size only to imperfect observations."""
        self.observation_memory_size = [memory_size if self.observation_states[obs] > 1 else 1 for obs in range(self.observations)]
        self.set_manager_memory_vector()
        self.current_memory_size = memory_size
        self.colored_mdp = self._unfold_memory()
        return self.colored_mdp

    def increase_memory_size(self, obs: int) -> PomdpColoredMdp:
        assert self.observation_memory_size is not None
        self.observation_memory_size[obs] += 1
        self.set_manager_memory_vector()
        self.colored_mdp = self._unfold_memory()
        return self.colored_mdp

    def set_memory_from_dict(self, obs_memory_dict: dict[int, int]) -> PomdpColoredMdp:
        memory_list = []
        for obs in range(self.observations):
            memory_list.append(obs_memory_dict[obs])

        self.observation_memory_size = memory_list
        self.set_manager_memory_vector()
        self.colored_mdp = self._unfold_memory()
        return self.colored_mdp

    def set_memory_from_result_new(self, obs_memory_dict: dict[int, int], obs_memory_dict_cutoff: dict[int, int], memory_limit: int) -> PomdpColoredMdp:
        assert self.observation_memory_size is not None
        memory_list = []
        for obs in range(self.observations):
            if self.observation_states[obs] <= 1:
                memory = 1
            elif obs in obs_memory_dict.keys():
                memory = max(obs_memory_dict[obs], self.observation_memory_size[obs] + 1)
            elif obs in obs_memory_dict_cutoff.keys():
                memory = obs_memory_dict_cutoff[obs]
            else:
                memory = memory_limit
            memory_list.append(memory)

        self.observation_memory_size = memory_list
        self.set_manager_memory_vector()
        self.colored_mdp = self._unfold_memory()
        return self.colored_mdp

    def create_coloring(
        self, underlying_mdp: Any
    ) -> tuple[paynt.parameter_space.parameter_space.ParameterSpace, list[list[tuple[int, int]]], list[list[int]], list[list[int]]]:
        assert self.observation_memory_size is not None
        if self.posterior_aware:
            return self.create_coloring_aposteriori(underlying_mdp)

        # create parameters
        parameter_space = paynt.parameter_space.parameter_space.ParameterSpace()
        observation_action_parameters = []
        observation_memory_parameters = []

        for obs in range(self.observations):

            # action parameters
            parameter_indices = []
            num_actions = self.actions_at_observation[obs]
            if num_actions > 1:
                option_labels = self.action_labels_at_observation[obs]
                for mem in range(self.observation_memory_size[obs]):
                    parameter_indices.append(parameter_space.num_parameters)
                    name = self.create_parameter_name(obs, mem, True)
                    parameter_space.add_parameter(name, option_labels)
            observation_action_parameters.append(parameter_indices)

            # memory parameters
            parameter_indices = []
            num_updates = self.pomdp_manager.max_successor_memory_size[obs]
            if num_updates > 1:
                option_labels = [str(x) for x in range(num_updates)]
                for mem in range(self.observation_memory_size[obs]):
                    name = self.create_parameter_name(obs, mem, False)
                    parameter_indices.append(parameter_space.num_parameters)
                    parameter_space.add_parameter(name, option_labels)
            observation_memory_parameters.append(parameter_indices)

        # create the coloring
        assert self.pomdp_manager.num_holes == parameter_space.num_parameters
        num_parameters = parameter_space.num_parameters
        choice_action_parameter = self.pomdp_manager.row_action_hole
        choice_memory_parameter = self.pomdp_manager.row_memory_hole
        choice_action_option = self.pomdp_manager.row_action_option
        choice_memory_option = self.pomdp_manager.row_memory_option
        choice_to_parameter_options = []
        for choice in range(underlying_mdp.nr_choices):
            parameter_options = []
            parameter = choice_action_parameter[choice]
            if parameter != num_parameters:
                parameter_options.append((parameter, choice_action_option[choice]))
            parameter = choice_memory_parameter[choice]
            if parameter != num_parameters:
                parameter_options.append((parameter, choice_memory_option[choice]))
            choice_to_parameter_options.append(parameter_options)

        return parameter_space, choice_to_parameter_options, observation_action_parameters, observation_memory_parameters

    def create_coloring_aposteriori(
        self, underlying_mdp: Any
    ) -> tuple[paynt.parameter_space.parameter_space.ParameterSpace, list[Any], list[list[int]], list[list[int]]]:
        # a posteriori unfolding
        choice_to_parameter_options = self.pomdp_manager.coloring
        parameter_num_options = self.pomdp_manager.hole_num_options
        action_parameters = self.pomdp_manager.action_holes
        update_parameters = self.pomdp_manager.update_holes

        parameters: list[tuple[str, list[str]] | None] = [None] * len(parameter_num_options)

        # action parameters
        for key, index in action_parameters.items():
            num_options = parameter_num_options[index]
            if num_options <= 1:
                continue
            mem, prior = key
            name = self.create_parameter_name_aposteriori(True, mem, prior)
            option_labels = [str(labels) for labels in self.action_labels_at_observation[prior]]
            parameters[index] = (name, option_labels)

        # update parameters
        for key, index in update_parameters.items():
            num_options = parameter_num_options[index]
            if num_options <= 1:
                continue
            mem, prior, posterior = key
            name = self.create_parameter_name_aposteriori(False, mem, prior, posterior)
            option_labels = [str(x) for x in range(num_options)]
            parameters[index] = (name, option_labels)

        # filter out trivial parameters
        parameter_space = paynt.parameter_space.parameter_space.ParameterSpace()
        old_to_new_indices: list[int | None] = [None] * len(parameters)
        for index, name_labels in enumerate(parameters):
            if name_labels is None:
                continue
            old_to_new_indices[index] = parameter_space.num_parameters
            name, option_labels = name_labels
            parameter_space.add_parameter(name, option_labels)

        choice_to_parameter_options_new = []
        for parameter_options in choice_to_parameter_options:
            parameter_options_new = [
                (old_to_new_indices[parameter], v) for parameter, v in parameter_options.items() if old_to_new_indices[parameter] is not None
            ]
            choice_to_parameter_options_new.append(parameter_options_new)
        choice_to_parameter_options = choice_to_parameter_options_new

        # creating this list to make it work with Paynt-Storm integration
        observation_action_parameters: list[list[int]] = [[] for obs in range(self.observations)]
        for key, index in action_parameters.items():
            _, prior = key
            new_index = old_to_new_indices[index]
            if new_index is not None:
                observation_action_parameters[prior].append(new_index)
        observation_memory_parameters: list[list[int]] = [[] for obs in range(self.observations)]

        return parameter_space, choice_to_parameter_options, observation_action_parameters, observation_memory_parameters

    def _unfold_memory(self) -> PomdpColoredMdp:
        assert self.observation_memory_size is not None
        logger.debug(f"unfolding {max(self.observation_memory_size)}-FSC template into POMDP...")
        underlying_mdp = self.pomdp_manager.construct_mdp()
        logger.debug(f"constructed underlying MDP having {underlying_mdp.nr_states} states and {underlying_mdp.nr_choices} actions.")

        parameter_space, choice_to_parameter_options, observation_action_parameters, observation_memory_parameters = self.create_coloring(underlying_mdp)
        coloring = payntbind.synthesis.Coloring(parameter_space.native, underlying_mdp.nondeterministic_choice_indices, choice_to_parameter_options)

        # to each parameter-option pair a list of actions colored by this combination
        parameter_option_to_actions: list[list[list[int]]] = [[] for parameter in range(parameter_space.num_parameters)]
        for parameter in range(parameter_space.num_parameters):
            parameter_option_to_actions[parameter] = [[] for option in parameter_space.parameter_options(parameter)]
        for choice in range(underlying_mdp.nr_choices):
            for parameter, option in choice_to_parameter_options[choice]:
                parameter_option_to_actions[parameter][option].append(choice)

        return PomdpColoredMdp(
            underlying_mdp,
            parameter_space,
            coloring,
            self.use_exact,
            self.pomdp,
            self.pomdp_manager,
            self.observation_labels,
            self.actions_at_observation,
            self.action_labels_at_observation,
            self.observation_states,
            self.observation_memory_size,
            observation_action_parameters,
            observation_memory_parameters,
            parameter_option_to_actions,
            self.posterior_aware,
        )
