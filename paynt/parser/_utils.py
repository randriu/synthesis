from __future__ import annotations

from typing import Any

import payntbind
import stormpy

import logging

logger = logging.getLogger(__name__)


def substitute_suffix(string: str, delimiter: str, replacer: Any) -> str:
    """Subsitute the suffix behind the last delimiter."""
    output_string = string.split(delimiter)
    output_string[-1] = str(replacer)
    return delimiter.join(output_string)


def make_rewards_action_based(model: Any) -> None:
    tm = model.transition_matrix
    for name, reward_model in model.reward_models.items():
        assert not reward_model.has_transition_rewards, "Paynt does not support transition rewards"
        if not reward_model.has_state_rewards:
            continue
        logger.info(f"converting state rewards '{name}' to state-action rewards")
        if reward_model.has_state_action_rewards:
            logger.info(f"state rewards '{name}' will be added to existing state-action rewards")
            action_reward = reward_model.state_action_rewards.copy()
        else:
            action_reward = [0] * model.nr_choices

        for state in range(model.nr_states):
            state_reward = reward_model.get_state_reward(state)
            for action in range(tm.get_row_group_start(state), tm.get_row_group_end(state)):
                action_reward[action] += state_reward

        if model.is_exact:
            payntbind.synthesis.remove_reward_model_exact(model, name)
            new_reward_model = stormpy.storage.SparseExactRewardModel(optional_state_action_reward_vector=action_reward)
            model.add_reward_model(name, new_reward_model)
        else:
            payntbind.synthesis.remove_reward_model(model, name)
            new_reward_model = stormpy.storage.SparseRewardModel(optional_state_action_reward_vector=action_reward)
            model.add_reward_model(name, new_reward_model)
