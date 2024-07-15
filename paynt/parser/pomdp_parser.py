import stormpy

from collections import defaultdict

import os
import re
import uuid

import logging
logger = logging.getLogger(__name__)


class PomdpParser:

    @classmethod
    def write_model_in_pomdp_solve_format(cls, pomdp, output_path, property_path):

        num_states = pomdp.nr_states
        num_choices = pomdp.nr_choices
        num_obs = pomdp.nr_observations
        max_num_choices = max([pomdp.get_nr_available_actions(state) for state in range(num_states)])


        desc = """\
# auto-generated from PRISM program

discount: 0.95
values: reward
states: {}
actions: {}
observations: {}

""".format(num_states,max_num_choices,num_obs)

        # initial state
        state_init = pomdp.initial_states[0]
        initial_distr = [1 if state == state_init else 0 for state in range(num_states)]
        initial_distr = [str(x) for x in initial_distr]
        initial_distr = ' '.join(initial_distr)
        desc += f"start:\n{initial_distr}\n\n"

        # transition matrix
        desc += "# transition matrix\n\n"

        tm = pomdp.transition_matrix
        for state in range(num_states):
            action_index = 0
            group_start = tm.get_row_group_start(state)
            group_end = tm.get_row_group_end(state)
            trivial_action = group_end == group_start + 1
            for row_index in range(group_start, group_end):
                for entry in tm.get_row(row_index):
                    action_index_str = action_index if not trivial_action else "*"
                    desc += f"T: {action_index_str} : {state} : {entry.column} {entry.value()}\n"
                action_index += 1

        # observations
        desc += "\n# observations\n\n"
        for state in range(num_states):
            desc += f"O: * : {state} : {pomdp.observations[state]} 1\n"

        # rewards
        if len(pomdp.reward_models) > 0:
            # rewards
            desc += "\n# rewards\n\n"

            # assuming a single reward model
            rewards = next(iter(pomdp.reward_models.values()))

            # convert rewards to state-based
            state_rewards = []
            if rewards.has_state_rewards:
                state_rewards = list(rewards.state_rewards)
            elif rewards.has_state_action_rewards:
                state_action_rewards = list(rewards.state_action_rewards)
                for state in range(num_states):
                    group_start = tm.get_row_group_start(state)
                    state_rewards.append(state_action_rewards[group_start])
            else:
                raise TypeError("unknown reward type")
                    
            # print state-based rewards
            for state in range(num_states):
                rew = state_rewards[state]
                if rew != 0:
                    desc += f"R: * : {state} : * : * {rew}\n"
        
        # ready to print
        logger.info("Writing POMDP in pomdp-solve format to {} ...".format(output_path))
        with open(output_path, 'w') as f:
            f.write(desc)
        logger.info("Writing default discount property to {} ...".format(property_path))
        with open(property_path, 'w') as f:
            f.write('R{"rew0"}max=? [F "target"]')
        logger.info("Write OK, aborting ...")
        exit(0)
