import random
import numpy

import logging
logger = logging.getLogger(__name__)


class SimulatedModel:

    def __init__(self, model):

        # underlying model, can be MDP or POMDP
        self.model = model

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

    def state_action_reward(self, state, action, reward_name):
        reward_model = self.model.get_reward_model(reward_name)
        action_index = self.model.get_choice_index(state,action)
        return reward_model.get_state_action_reward(action_index)

    @property
    def is_partially_observable(self):
        return self.model.is_partially_observable
    
    @property
    def current_observation(self):
        assert self.is_partially_observable
        return self.model.get_observation(self.current_state)
    
    def sample_action(self, state):
        num_actions = self.state_num_actions[state]
        action = random.randint(0,num_actions-1)
        return action
    
    def sample_successor(self, state, action):
        succs,probs = self.state_row_group[state][action]
        successor = random.choices(succs, probs)[0]
        # successor = numpy.random.choice(succs, size=1, p=probs)[0]
        return successor

    def sample_path(self, state, length):
        path = []
        for _ in range(length):
            if self.state_is_absorbing[state]:
                break
            action = self.sample_action(state)
            path.append((state,action))
            state = self.sample_successor(state,action)
        return path

    def path_discounted_reward(self, path, reward_name, discount_factor):
        total_reward = 0
        factor = 1
        for state,action in path:
            reward = self.state_action_reward(state,action,reward_name)
            total_reward += factor * reward
            factor *= discount_factor
        return total_reward

    def reset_simulation(self):
        self.current_state = self.initial_state

    def simulate_action(self, action):
        self.current_state = self.sample_successor(self.current_state, action)


    



