import stormpy
import stormpy.synthesis

import paynt.quotient.holes
import paynt.quotient.quotient

import json

import logging
logger = logging.getLogger(__name__)


class FSC:
    '''
    Class for encoding an FSC having
    - a fixed number of nodes
    - deterministic action selection gamma: NxZ -> Act
    - deterministic posterior-unaware memory update delta: NxZ -> N
    '''

    def __init__(self, num_nodes, num_observations):
        self.num_nodes = num_nodes
        self.num_observations = num_observations
        
        # gamma: NxZ -> Act
        self.action_function = [ [None]*num_observations for _ in range(num_nodes) ]
        # delta: NxZ -> N
        self.update_function = [ [None]*num_observations for _ in range(num_nodes) ]

    
    def __str__(self):
        return json.dumps(self.to_json(), indent=4)

    def to_json(self):
        json = {}
        json["num_nodes"] = self.num_nodes
        json["num_observations"] = self.num_observations
        json["__comment_action_function"] = "action function has signature NxZ -> Act"
        json["__comment_update_function"] = "update function has signature NxZ -> N"
        json["action_function"] = self.action_function
        json["update_function"] = self.update_function
        return json

    @classmethod
    def from_json(cls, json):
        num_nodes = json["num_nodes"]
        num_observations = json["num_observations"]
        fsc = FSC(num_nodes,num_observations)
        fsc.action_function = json["action_function"]
        fsc.update_function = json["update_function"]
        return fsc


    def decide(self, decision_map, node, observation):
        '''
        Make decision using decision_map based on the given observation and memory node. decision_map is either
        self.action_function or self.update_function
        '''
        decision = decision_map[node][observation]
        if decision is None:
            # default to 0 node
            decision = decision_map[0][observation]
            if decision is None:
                # default to first decision
                decision = 0
        return decision

    def suggest_action(self, node, observation):
        return self.decide(self.action_function, node, observation)

    def suggest_update(self, node, observation):
        return self.decide(self.update_function, node, observation)




class PomdpFamilyQuotientContainer(paynt.quotient.quotient.QuotientContainer):

    def __init__(self, quotient_mdp, coloring, specification, obs_evaluator):
        super().__init__(quotient_mdp = quotient_mdp, coloring = coloring, specification = specification)
        self.obs_evaluator = obs_evaluator
        self.design_space = paynt.quotient.holes.DesignSpace(coloring.holes)
        self.quotient_mdp = stormpy.synthesis.add_choice_labels_from_jani(self.quotient_mdp)
    
    @property
    def num_observations(self):
        return self.obs_evaluator.num_obs_classes

    
    def build_pomdp(self, family):
        ''' Construct the sub-POMDP from the given hole assignment. '''
        assert family.size == 1, "expecting family of size 1"
        
        _,_,selected_actions_bv = self.coloring.select_actions(family)
        mdp,state_map,choice_map = self.restrict_quotient(selected_actions_bv)
        pomdp = self.obs_evaluator.build_sub_pomdp(mdp,state_map)
        return pomdp

    
    def compute_actions_at_observation(self, pomdp):
        ''' For each observation, compute the number of available actions. '''
        actions_at_observation = [0] * self.num_observations
        for state in range(pomdp.nr_states):
            obs = pomdp.observations[state]
            if actions_at_observation[obs] != 0:
                continue
            actions_at_observation[obs] = pomdp.get_nr_available_actions(state)
        return actions_at_observation


