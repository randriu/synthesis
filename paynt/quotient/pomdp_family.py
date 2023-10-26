import stormpy
import stormpy.synthesis

import paynt.quotient.holes
import paynt.quotient.quotient
import paynt.quotient.coloring
import paynt.quotient.mdp_family

import paynt.synthesizer.synthesizer_onebyone
import paynt.synthesizer.synthesizer_ar

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

        # a list of action labels
        self.action_labels = None
        # for each choice, an index of its label in self.action_labels
        self.choice_to_action = None
        # for each observation, a list of actions (indices) available
        self.observation_to_actions = None

        # POMDP manager used for unfolding the memory model into the quotient POMDP
        self.quotient_pomdp_manager = None

        assert not self.specification.has_optimality, \
            "expecting specification without the optimality objective"

        self.action_labels,self.choice_to_action,state_to_choice_label_indices = \
            paynt.quotient.mdp_family.MdpFamilyQuotientContainer.extract_choice_labels(self.quotient_mdp)
        self.num_actions = len(self.action_labels)

        # identify labels available at observations
        self.observation_to_actions = [None] * self.num_observations
        for state,state_choice_label_indices in enumerate(state_to_choice_label_indices):
            obs = self.state_to_observation[state]
            if self.observation_to_actions[obs] is not None:
                assert self.observation_to_actions[obs] == state_choice_label_indices,\
                    f"two states in observation class {obs} differ in available actions"
                continue
            self.observation_to_actions[obs] = state_choice_label_indices

        self.quotient_pomdp_manager = stormpy.synthesis.QuotientPomdpManager(
            self.quotient_mdp, self.state_to_observation, self.num_actions, self.choice_to_action)


    @property
    def num_observations(self):
        return self.obs_evaluator.num_obs_classes

    @property
    def state_to_observation(self):
        return self.obs_evaluator.state_to_obs_class
    
    
    def build_pomdp(self, family):
        ''' Construct the sub-POMDP from the given hole assignment. '''
        assert family.size == 1, "expecting family of size 1"
        
        _,_,selected_actions_bv = self.coloring.select_actions(family)
        mdp,state_map,choice_map = self.restrict_quotient(selected_actions_bv)
        pomdp = self.obs_evaluator.add_observations_to_submdp(mdp,state_map)
        return pomdp

    def build_dtmc_sketch(self, fsc, negate_specification=False):
        '''
        Construct the family of DTMCs representing the execution of the given FSC in different environments.
        :param negate_specification if True, a negated specification will be associated with the sketch
        '''

        # create the product
        self.quotient_pomdp_manager.make_product_with_fsc(fsc.num_nodes, fsc.action_function, fsc.update_function)
        product = self.quotient_pomdp_manager.product
        product_choice_to_choice = self.quotient_pomdp_manager.product_choice_to_choice

        # the product inherits the design space
        product_holes = self.design_space.copy()
        
        # the choices of the product inherit colors of the quotient
        product_choice_to_hole_options = []
        for product_choice in range(product.nr_choices):
            choice = product_choice_to_choice[product_choice]
            hole_options = self.coloring.action_to_hole_options[choice].copy()
            product_choice_to_hole_options.append(hole_options)
        product_coloring = paynt.quotient.coloring.Coloring(product, product_holes, product_choice_to_hole_options)
        
        # handle specification
        product_specification = self.specification.copy()
        if negate_specification:
            product_specification = product_specification.negate()

        dtmc_sketch = paynt.quotient.quotient.DtmcQuotientContainer(product, product_coloring, product_specification)
        return dtmc_sketch

    def investigate_fsc(self, fsc):
        sketch = self.build_dtmc_sketch(fsc, negate_specification=True)
        synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR(sketch)
        violating_assignments = synthesizer.synthesize()
        return violating_assignments

