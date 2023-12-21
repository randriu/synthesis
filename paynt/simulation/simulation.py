import random
import numpy
import json
import math

import logging
logger = logging.getLogger(__name__)


class SimulatedModel:

    def __init__(self, model, reward_name):

        # underlying model, can be MDP or POMDP
        self.model = model
        # default reward name
        self.reward_name = reward_name

        # current state for the simulation
        self.current_state = self.initial_state

        # [simulation cash] for each state, a number of actions
        self.state_num_actions = [model.get_nr_available_actions(s) for s in range(model.nr_states)]

        # [simulation cash] transition matrix
        self.state_row_group = []
        tm = self.model.transition_matrix
        for state in range(self.model.nr_states):
            row_group = []
            num_actions = self.model.get_nr_available_actions(state)
            for row_index in range(tm.get_row_group_start(state),tm.get_row_group_end(state)):
                columns = [entry.column for entry in tm.get_row(row_index)]
                values = [entry.value() for entry in tm.get_row(row_index)]
                row_group.append( (columns,values) )
            self.state_row_group.append(row_group)

        # identify which states are absorbing
        self.state_is_absorbing = []
        for state in range(self.model.nr_states):
            absorbing = True
            for row_index in range(tm.get_row_group_start(state),tm.get_row_group_end(state)):
                for entry in tm.get_row(row_index):
                    if entry.column != state:
                        absorbing = False
                        break
                if not absorbing:
                    break
            self.state_is_absorbing.append(absorbing)


    @property
    def initial_state(self):
        return self.model.initial_states[0]

    def state_valuation(self, state):
        return json.loads(str(self.model.state_valuations.get_json(state)))

    def finished(self):
        return self.state_is_absorbing[self.current_state]

    @property
    def is_partially_observable(self):
        return self.model.is_partially_observable
    
    def state_observation(self, state=None):
        if state is None:
            state = self.current_state
        assert self.is_partially_observable
        return self.model.get_observation(state)
    
    def state_action_reward(self, state, action):
        reward_model = self.model.get_reward_model(self.reward_name)
        action_index = self.model.get_choice_index(state,action)
        return reward_model.get_state_action_reward(action_index)

    def sample_action(self, state):
        # return self.simulated_model_storm.sample_action(state)
        num_actions = self.state_num_actions[state]
        action = random.randint(0,num_actions-1)
        return action
    
    def sample_successor(self, state, action):
        # return self.simulated_model_storm.sample_successor(state,action)
        succs,probs = self.state_row_group[state][action]
        successor = random.choices(succs, probs)[0]
        return successor

    def discounted_reward(self, rewards, discount_factor):
        factor = 1
        total_reward = 0
        for reward in rewards:
            total_reward += factor * reward
            factor *= discount_factor
        return total_reward

    def state_action_rollout(self, state, action, length, discount_factor):
        # return self.simulated_model_storm.state_action_rollout(state,action,length,reward_name,discount_factor)
        rewards = []
        for _ in range(length):
            if self.state_is_absorbing[state]:
                break
            reward = self.state_action_reward(state,action)
            state = self.sample_successor(state,action)
            action = self.sample_action(state)
            rewards.append(reward)
        return self.discounted_reward(rewards, discount_factor)

    def state_action_rollout_history(self, state, action, length):
        history = []
        for _ in range(length):
            if self.state_is_absorbing[state]:
                break
            reward = self.state_action_reward(state,action)
            history.append( (state,action,reward) )
            state = self.sample_successor(state,action)
            action = self.sample_action(state)
        return history

    
    def reset(self):
        self.current_state = self.initial_state

    def simulate_action(self, action):
        self.current_state = self.sample_successor(self.current_state, action)    

    
    # sample generation

    def sample_path_annotated(self, state, length, reward_name):
        path = []
        for _ in range(length):
            if self.state_is_absorbing[state]:
                break
            action = self.sample_action(state)
            reward = self.state_action_reward(state, action, reward_name)
            path.append({
                "state" : state,
                "action" : action,
                "reward" : reward
                })
            state = self.sample_successor(state,action)
        return path

    def export_json(self, output, output_path):
        logger.info("Exporting info to {}".format(output_path))
        with open(output_path, 'w') as f:
            print(json.dumps(output, indent=4), file=f)

    def produce_samples(self):
        num_paths = 100
        length = 100

        reward_name = list(self.model.reward_models)[0]

        # collect state valuations
        state_valuations = []
        for state in range(self.model.nr_states):
            valuation = self.state_valuation(state)
            state_valuations.append({"state" : state, "valuation" : valuation})
        self.export_json(state_valuations, "valuations.json")

        # sample paths
        paths = []
        for _ in range(num_paths):
            path = self.sample_path_annotated(self.initial_state,length,reward_name)
            paths.append(path)
        self.export_json(paths, "paths.json")

        # aggregate path rewards by states
        state_rewards = [[] for state in range(self.model.nr_states)]
        for path in paths:
            reward_sum = 0
            path_length = 0
            for entry in reversed(path):
                state = entry["state"]
                reward = entry["reward"]
                reward_sum += reward
                path_length += 1
                state_rewards[state].append({"length" : path_length, "total reward" : reward_sum})
        state_info = []
        for state in range(self.model.nr_states):
            info = {
                "state" : state,
                "paths" : state_rewards[state]
            }
            state_info.append(info)
        
        # write to files
        self.export_json(state_info, "states.json")

        exit()
        


    



