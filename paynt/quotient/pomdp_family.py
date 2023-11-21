import stormpy
import stormpy.utility
import stormpy.synthesis

import paynt.quotient.holes
import paynt.quotient.quotient
import paynt.quotient.coloring
import paynt.quotient.mdp_family

import paynt.synthesizer.conflict_generator.storm

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

    def check_action_function(self, num_observations, observation_to_actions):
        assert len(self.action_function) == self.num_nodes, "FSC action function is not defined for all memory nodes"
        for node in range(self.num_nodes):
            assert len(self.action_function[node]) == num_observations, \
                "in memory node {}, FSC action function is not defined for all observations".format(node)
            for obs in range(num_observations):
                if self.is_deterministic:
                    action = self.action_function[node][obs]
                    assert action in observation_to_actions[obs], "in observation {} FSC chooses invalid action {}".format(obs,action)
                else:
                    for action,_ in self.action_function[node][obs].items():
                        assert action in observation_to_actions[obs], "in observation {} FSC chooses invalid action {}".format(obs,action)

    def check_update_function(self, num_observations):
        assert len(self.update_function) == self.num_nodes, "FSC update function is not defined for all memory nodes"
        for node in range(self.num_nodes):
            assert len(self.update_function[node]) == num_observations, \
                "in memory node {}, FSC update function is not defined for all observations".format(node)
            for obs in range(num_observations):
                update = self.update_function[node][obs]
                assert 0 <= update and update < self.num_nodes, "invalid FSC memory update {}".format(update)

    def check(self, num_observations, observation_to_actions):
        ''' Check whether fields of FSC have been initialized appropriately. '''
        assert self.num_nodes > 0, "FSC must have at least 1 node"
        self.check_action_function(num_observations,observation_to_actions)
        self.check_update_function(num_observations)


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
        self.product_pomdp_fsc = None

        assert not self.specification.has_optimality, \
            "expecting specification without the optimality objective"

        self.action_labels,self.choice_to_action,state_to_actions = \
            paynt.quotient.mdp_family.MdpFamilyQuotientContainer.extract_choice_labels(self.quotient_mdp)

        # identify labels available at observations
        self.observation_to_actions = [None] * self.num_observations
        for state,state_actions in enumerate(state_to_actions):
            obs = self.state_to_observation[state]
            if self.observation_to_actions[obs] is not None:
                assert self.observation_to_actions[obs] == state_actions,\
                    f"two states in observation class {obs} differ in available actions"
                continue
            self.observation_to_actions[obs] = state_actions

    @property
    def num_actions(self):
        return len(self.action_labels)

    @property
    def num_observations(self):
        return self.obs_evaluator.num_obs_classes

    @property
    def state_to_observation(self):
        return self.obs_evaluator.state_to_obs_class

    def extract_target_label(self):
        spec = self.specification
        assert not spec.has_optimality and spec.num_properties == 1, "expecting a single property"
        prop = spec.constraints[0]
        label = str(prop.formula.subformula.subformula)
        return label

    def initialize_fsc_unfolder(self, fsc_is_deterministic=False):
        if fsc_is_deterministic:
            self.product_pomdp_fsc = stormpy.synthesis.ProductPomdpFsc(
                self.quotient_mdp, self.state_to_observation, self.num_actions, self.choice_to_action)
        else:
            self.product_pomdp_fsc = stormpy.synthesis.ProductPomdpRandomizedFsc(
                self.quotient_mdp, self.state_to_observation, self.num_actions, self.choice_to_action)
    
    
    def build_pomdp(self, family):
        ''' Construct the sub-POMDP from the given hole assignment. '''
        assert family.size == 1, "expecting family of size 1"
        
        _,_,selected_actions_bv = self.coloring.select_actions(family)
        mdp,state_map,choice_map = self.restrict_quotient(selected_actions_bv)
        pomdp = self.obs_evaluator.add_observations_to_submdp(mdp,state_map)
        return SubPomdp(pomdp,self,state_map,choice_map)


    def build_dtmc_sketch(self, fsc, negate_specification=False):
        '''
        Construct the family of DTMCs representing the execution of the given FSC in different environments.
        :param negate_specification if True, a negated specification will be associated with the sketch
        '''
        # create the product
        fsc.check(self.num_observations, self.observation_to_actions)
        self.product_pomdp_fsc.apply_fsc(fsc.action_function, fsc.update_function)
        product = self.product_pomdp_fsc.product
        product_choice_to_choice = self.product_pomdp_fsc.product_choice_to_choice

        # the product inherits the design space
        product_holes = self.design_space.copy()
        
        # the choices of the product inherit colors of the quotient
        product_choice_to_hole_options = []
        quotient_num_choces = self.quotient_mdp.nr_choices
        for product_choice in range(product.nr_choices):
            choice = product_choice_to_choice[product_choice]
            if choice == quotient_num_choces:
                hole_options = {}
            else:
                hole_options = self.coloring.action_to_hole_options[choice].copy()
            product_choice_to_hole_options.append(hole_options)
        product_coloring = paynt.quotient.coloring.Coloring(product, product_holes, product_choice_to_hole_options)
        
        # handle specification
        product_specification = self.specification.copy()
        if negate_specification:
            product_specification = product_specification.negate()

        dtmc_sketch = paynt.quotient.quotient.DtmcQuotientContainer(product, product_coloring, product_specification)
        return dtmc_sketch

    
    def translate_path_to_trace(self, dtmc_sketch, dtmc, path):
        invalid_choice = self.quotient_mdp.nr_choices
        trace = []
        for dtmc_state in path:
            product_choice = dtmc.quotient_choice_map[dtmc_state]
            choice = self.product_pomdp_fsc.product_choice_to_choice[product_choice]
            if choice == invalid_choice:
                # randomized FSC: we are in the intermediate states, continue to the next one
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
        fsc_is_randomized = isinstance(self.product_pomdp_fsc, stormpy.synthesis.ProductPomdpRandomizedFsc)
        if fsc_is_randomized:
            # double the trace length to account for intermediate states
            trace_max_length *= 2

        # logger.debug("constructing witnesses...")
        dtmc = dtmc_sketch.build_chain(satisfying_assignment)

        # assuming a single probability reachability property
        spec = dtmc_sketch.specification
        assert not spec.has_optimality and spec.num_properties == 1 and not spec.constraints[0].reward, \
            "expecting a single reachability probability constraint"
        prop = dtmc_sketch.specification.constraints[0]
        
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
