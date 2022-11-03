import random

import logging
logger = logging.getLogger(__name__)


class SimulatedModel:

    def __init__(self, model):

        self.model = model

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

        self.current_state = None

    @property
    def initial_state(self):
        return self.model.initial_states[0]

    @property
    def is_partially_observable(self):
        return self.model.is_partially_observable
    
    @property
    def current_observation(self):
        assert self.is_partially_observable
        return self.model.get_observation(self.current_state)
    
    @property
    def select_random_action(self, state):
        num_actions = self.model.get_nr_available_actions(state)
        action = random.randint(0,num_actions-1)
        return action
    
    def select_random_successor(self, state, action):
        assert self.state_row_group is not None
        succs,probs = self.state_row_group[state][action]
        successor = random.choices(succs, probs)[0]
        return successor


    def random_path(self, length, state_row_group=None):
        path = []
        state = self.initial_state
        while length > 0:
            action = self.random_action(state)
            path.append((state,action))
            length -= 1
            state = self.random_transition(state,action,state_row_group)
        return path

    def evaluate_path(self, path, reward_name):

        # assuming state reward
        reward_model = self.model.get_reward_model(reward_name)
        assert reward_model.state_rewards

        reward_sum = 0
        for state,_ in path:
            reward = reward_model.get_state_reward(state)
            reward_sum += reward
        return reward_sum
    
    def reset_simulation(self):
        self.current_state = self.initial_state

    def simulate_action(self, action):
        self.current_state = self.select_random_successor(self.current_state, action)


    



