import stormpy
import payntbind

import paynt.quotient.models
import paynt.quotient.quotient
import paynt.quotient.mdp_family
import paynt.verification.property

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
        

class SubPomdp:
    '''
    Simple container for a (sub-)POMDP created from the quotient.
    '''
    def __init__(self, model, quotient, quotient_state_map, quotient_choice_map):
        # the Stormpy POMDP
        self.model = model
        # POMDP family quotient from which this POMDP was constructed
        # self.quotient = quotient
        # for each state of the POMDP, a state in the quotient
        self.quotient_state_map = quotient_state_map
        # for each choice of the POMDP, a choice in the quotient
        self.quotient_choice_map = quotient_choice_map

        # for each state and for each action, a local index of the choice labeled with this action,
        # or None if action is not available in the state
        self.state_action_to_local_choice = []
        tm = model.transition_matrix
        for state in range(model.nr_states):
            action_to_local_choice = [None]*quotient.num_actions
            for local_choice,pomdp_choice in enumerate(range(tm.get_row_group_start(state),tm.get_row_group_end(state))):
                quotient_choice = quotient_choice_map[pomdp_choice]
                action = quotient.choice_to_action[quotient_choice]
                assert action_to_local_choice[action] is None, "duplicate action {} in POMDP state {}".format(action,state)
                action_to_local_choice[action] = local_choice
            self.state_action_to_local_choice.append(action_to_local_choice)


class PomdpFamilyQuotient(paynt.quotient.mdp_family.MdpFamilyQuotient):

    def __init__(self, quotient_mdp, family, coloring, specification, obs_evaluator):
        super().__init__(quotient_mdp = quotient_mdp, family = family, coloring = coloring, specification = specification)
        self.obs_evaluator = obs_evaluator

        # for each observation, a list of actions (indices) available
        self.observation_to_actions = None
        # POMDP manager used for unfolding the memory model into the quotient POMDP
        self.product_pomdp_fsc = None

        # identify actions available at each observation
        self.observation_to_actions = [None] * self.num_observations
        state_to_observation = self.state_to_observation
        for state,available_actions in enumerate(self.state_to_actions):
            obs = state_to_observation[state]
            if self.observation_to_actions[obs] is not None:
                assert self.observation_to_actions[obs] == available_actions,\
                    f"two states in observation class {obs} differ in available actions"
                continue
            self.observation_to_actions[obs] = available_actions


    @property
    def num_observations(self):
        return self.obs_evaluator.num_obs_classes

    @property
    def state_to_observation(self):
        return self.obs_evaluator.state_to_obs_class

    def observation_is_trivial(self, obs):
        return len(self.observation_to_actions[obs])==1

    
    def initialize_fsc_unfolder(self, fsc_is_deterministic=False):
        if fsc_is_deterministic and not isinstance(self.product_pomdp_fsc, payntbind.synthesis.ProductPomdpFsc):
            self.product_pomdp_fsc = payntbind.synthesis.ProductPomdpFsc(
                self.quotient_mdp, self.state_to_observation, self.num_actions, self.choice_to_action)
        if not fsc_is_deterministic and not isinstance(self.product_pomdp_fsc, payntbind.synthesis.ProductPomdpRandomizedFsc):
            self.product_pomdp_fsc = payntbind.synthesis.ProductPomdpRandomizedFsc(
                self.quotient_mdp, self.state_to_observation, self.num_actions, self.choice_to_action)
    
    
    def build_pomdp(self, family):
        ''' Construct the sub-POMDP from the given hole assignment. '''
        assert family.size == 1, "expecting family of size 1"
        
        choices = self.coloring.selectCompatibleChoices(family.family)
        mdp,state_map,choice_map = self.restrict_quotient(choices)
        pomdp = self.obs_evaluator.add_observations_to_submdp(mdp,state_map)
        return SubPomdp(pomdp,self,state_map,choice_map)


    def build_dtmc_sketch(self, fsc):
        '''
        Construct the family of DTMCs representing the execution of the given FSC in different environments.
        '''

        # create the product
        fsc.check(self.observation_to_actions)
        self.initialize_fsc_unfolder(fsc.is_deterministic)
        self.product_pomdp_fsc.apply_fsc(fsc.action_function, fsc.update_function)
        product = self.product_pomdp_fsc.product
        product_choice_to_choice = self.product_pomdp_fsc.product_choice_to_choice

        # the product inherits the design space
        product_family = self.design_space.copy()
        
        # the choices of the product inherit colors of the quotient
        product_choice_to_hole_options = []
        quotient_num_choces = self.quotient_mdp.nr_choices
        choice_to_hole_assignment = self.coloring.getChoiceToAssignment()
        for product_choice in range(product.nr_choices):
            choice = product_choice_to_choice[product_choice]
            if choice == quotient_num_choces:
                hole_options = []
            else:
                hole_options = [(hole,option) for hole,option in choice_to_hole_assignment[choice]]
            product_choice_to_hole_options.append(hole_options)
        product_coloring = payntbind.synthesis.Coloring(product_family.family, product.nondeterministic_choice_indices, product_choice_to_hole_options)
        
        # handle specification
        product_specification = self.specification.copy()
        dtmc_sketch = paynt.quotient.quotient.DtmcFamilyQuotient(product, product_family, product_coloring, product_specification)
        return dtmc_sketch


    def compute_qvalues_for_product_submdp(self, product_submdp : paynt.quotient.models.MDP):
        '''
        Given an MDP obtained after applying FSC to a family of POMDPs, compute for each state s, (reachable)
        memory node n, and action a, the Q-value Q((s,n),a).
        :note it is assumed that a randomized FSC was used
        :note it is assumed the provided DTMC sketch is the one obtained after the last unfolding, i.e. no other DTMC
            sketch was constructed afterwards
        :return a dictionary mapping (s,n,a) to Q((s,n),a)
        '''
        assert isinstance(self.product_pomdp_fsc, payntbind.synthesis.ProductPomdpRandomizedFsc), \
            "to compute Q-values, unfolder for randomized FSC must have been used"

        # model check
        prop = self.get_property()
        result = product_submdp.model_check_property(prop)
        product_state_sub_to_value = result.result.get_values()

        # map states of a sub-MDP to the states of the quotient-MDP to the state-memory pairs of the quotient POMDP
        # map states values to the resulting map
        product_state_to_state_memory_action = self.product_pomdp_fsc.product_state_to_state_memory_action.copy()
        state_memory_action_to_value = {}
        invalid_action = self.num_actions
        for product_state_sub in range(product_submdp.model.nr_states):
            product_state = product_submdp.quotient_state_map[product_state_sub]
            state,memory_action = product_state_to_state_memory_action[product_state]
            memory,action = memory_action
            if action == invalid_action:
                continue
            value = product_state_sub_to_value[product_state_sub]
            state_memory_action_to_value[(state,memory,action)] = value
        return state_memory_action_to_value


    def translate_path_to_trace(self, dtmc_sketch, dtmc, path):
        invalid_choice = self.quotient_mdp.nr_choices
        trace = []
        for dtmc_state in path:
            product_choice = dtmc.quotient_choice_map[dtmc_state]
            choice = self.product_pomdp_fsc.product_choice_to_choice[product_choice]
            if choice == invalid_choice:
                # randomized FSC: we are in the intermediate state, move on to the next one
                continue
            
            product_state = dtmc.quotient_state_map[dtmc_state]
            state = self.product_pomdp_fsc.product_state_to_state[product_state]
            obs = self.state_to_observation[state]
            action = self.choice_to_action[choice]
            trace.append( (obs,action) )

        # in the last state, we remove the action since it was not actually used
        trace[-1] = (obs,None)

        # sanity check
        for obs,action in trace[:-1]:
            assert action in self.observation_to_actions[obs], "invalid trace"

        return trace
    
    
    def compute_witnessing_traces(self, dtmc_sketch, satisfying_assignment, num_traces, trace_max_length):
        '''
        Generate witnessing paths in the DTMC induced by the DTMC sketch and a satisfying assignment.
        If the set of target states is not reachable, then random traces are simulated
        :return a list of state-action pairs
        :note the method assumes that the DTMC sketch is the one that was last constructed using build_dtmc_sketch()
        '''
        fsc_is_randomized = isinstance(self.product_pomdp_fsc, payntbind.synthesis.ProductPomdpRandomizedFsc)
        if fsc_is_randomized:
            # double the trace length to account for intermediate states
            trace_max_length *= 2

        # logger.debug("constructing witnesses...")
        dtmc = dtmc_sketch.build_assignment(satisfying_assignment)

        # assuming a single probability reachability property
        spec = dtmc_sketch.specification
        assert spec.num_properties == 1, "expecting a single property"
        prop = spec.all_properties()[0]
        if prop.is_reward:
            logger.warning("WARNING: specification is a reward property, but generated traces \
                will be based on transition probabilities")
        
        target_label = self.extract_target_label()
        target_states = dtmc.model.labeling.get_states(target_label)

        traces = []
        if target_states.number_of_set_bits()==0:
            # target is not reachable: use Stormpy simulator to obtain some random walk in a DTMC
            logger.debug("target is not reachable, generating random traces...")
            simulator = stormpy.core._DiscreteTimeSparseModelSimulatorDouble(dtmc.model)
            for _ in range(num_traces):
                simulator.reset_to_initial_state()
                path = [simulator.get_current_state()]
                for _ in range(trace_max_length):
                    success = simulator.random_step()
                    if not success:
                        break
                    path.append(simulator.get_current_state())
                trace = self.translate_path_to_trace(dtmc_sketch,dtmc,path)
                traces.append(trace)
        else:
            # target is reachable: use KSP
            logger.debug("target is reachable, computing shortest paths to...")
            if prop.minimizing:
                logger.debug("...target states")
                shortest_paths_generator = stormpy.utility.ShortestPathsGenerator(dtmc.model, target_label)
            else:
                logger.debug("...BSCCs from which target states are unreachable...")
                phi_states = stormpy.storage.BitVector(dtmc.model.nr_states,True)
                states0,_ = stormpy.core._compute_prob01states_double(dtmc.model,phi_states,target_states)
                shortest_paths_generator = stormpy.utility.ShortestPathsGenerator(dtmc.model, states0)
            for k in range(1,num_traces+1):
                path = shortest_paths_generator.get_path_as_list(k)
                path.reverse()
                trace = self.translate_path_to_trace(dtmc_sketch,dtmc,path)
                traces.append(trace)
        return traces
