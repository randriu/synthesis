import json

import logging
logger = logging.getLogger(__name__)


class FSC:
    '''
    Class for encoding an FSC having
    - a fixed number of nodes
    - action selection is either:
        + deterministic: gamma: NxZ -> Act, or
        + randomized: gamma: NxZ -> Distr(Act), where gamma(n,z) is a dictionary of pairs (action,probability)
    - deterministic posterior-unaware memory update delta: NxZ -> N
    '''

    def __init__(self, num_nodes, num_observations, is_deterministic=False):
        self.num_nodes = num_nodes
        self.num_observations = num_observations
        self.is_deterministic = is_deterministic
        
        self.action_function = [ [None]*num_observations for _ in range(num_nodes) ]
        self.update_function = [ [None]*num_observations for _ in range(num_nodes) ]

        self.observation_labels = None
        self.action_labels = None

    def __str__(self):
        return json.dumps(self.to_json(), indent=4)

    def action_function_signature(self):
        if self.is_deterministic:
            return " NxZ -> Act"
        else:
            return " NxZ -> Distr(Act)"

    def to_json(self):
        json = {}
        json["num_nodes"] = self.num_nodes
        json["num_observations"] = self.num_observations
        json["__comment_action_function"] = "action function has signature {}".format(self.action_function_signature())
        json["__comment_update_function"] = "update function has signature NxZ -> N"

        json["action_function"] = self.action_function
        json["update_function"] = self.update_function

        if self.action_labels is not None:
            json["action_labels"] = self.action_labels
        if self.observation_labels is not None:
            json["observation_labels"] = self.observation_labels

        return json

    @classmethod
    def from_json(cls, json):
        num_nodes = json["num_nodes"]
        num_observations = json["num_observations"]
        fsc = FSC(num_nodes,num_observations)
        fsc.action_function = json["action_function"]
        fsc.update_function = json["update_function"]
        return fsc

    def check_action_function(self, observation_to_actions):
        assert len(self.action_function) == self.num_nodes, "FSC action function is not defined for all memory nodes"
        for node in range(self.num_nodes):
            assert len(self.action_function[node]) == self.num_observations, \
                "in memory node {}, FSC action function is not defined for all observations".format(node)
            for obs in range(self.num_observations):
                if self.is_deterministic:
                    action = self.action_function[node][obs]
                    assert action in observation_to_actions[obs], "in observation {} FSC chooses invalid action {}".format(obs,action)
                else:
                    for action,_ in self.action_function[node][obs].items():
                        assert action in observation_to_actions[obs], "in observation {} FSC chooses invalid action {}".format(obs,action)

    def check_update_function(self):
        assert len(self.update_function) == self.num_nodes, "FSC update function is not defined for all memory nodes"
        for node in range(self.num_nodes):
            assert len(self.update_function[node]) == self.num_observations, \
                "in memory node {}, FSC update function is not defined for all observations".format(node)
            for obs in range(self.num_observations):
                update = self.update_function[node][obs]
                assert 0 <= update and update < self.num_nodes, "invalid FSC memory update {}".format(update)

    def check(self, observation_to_actions):
        ''' Check whether fields of FSC have been initialized appropriately. '''
        assert self.num_nodes > 0, "FSC must have at least 1 node"
        self.check_action_function(observation_to_actions)
        self.check_update_function()

    def fill_trivial_actions(self, observation_to_actions):
        ''' For each observation with 1 available action, set gamma(n,z) to that action. '''
        for obs,actions in enumerate(observation_to_actions):
            if len(actions)>1:
                continue
            action = actions[0]
            if not self.is_deterministic:
                action = {action:1}
            for node in range(self.num_nodes):
                self.action_function[node][obs] = action

    def fill_trivial_updates(self, observation_to_actions):
        ''' For each observation with 1 available action, set delta(n,z) to n. '''
        for obs,actions in enumerate(observation_to_actions):
            if len(actions)>1:
                continue
            for node in range(self.num_nodes):
                self.update_function[node][obs] = node

    def fill_zero_updates(self):
        for node in range(self.num_nodes):
            self.update_function[node] = [0] * self.num_observations

