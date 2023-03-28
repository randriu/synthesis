import stormpy

import paynt
from paynt.utils.profiler import Timer
from paynt.simulation.simulation import SimulatedModel
from paynt.quotient.quotient_pomdp import POMDPQuotientContainer

import logging
logger = logging.getLogger(__name__)

import collections
import math, numpy

import random


# TODO: handle absorbing states


class ActionOracleRandom:
    def __init__(self, simulated_model):
        self.simulated_model = simulated_model

    def reset(self):
        pass
    
    def get_next_action(self, last_action, simulation_step):
        return self.simulated_model.sample_action(self.simulated_model.current_state)



class BeliefNode:
    def __init__(self, observation, num_actions):
        self.particles = []
        self.observation = observation
        self.action_nodes = [ActionNode() for action in range(num_actions)]
        self.num_visits = 0

    def __str__(self):
        return f"{self.particles} {[str(n) for n in self.action_nodes]} [{self.num_visits}]"

    def add(self, particle):
        self.particles.append(particle)

    def sample(self):
        return random.choice(self.particles)

    def distribution(self):
        state_count = collections.defaultdict(int)
        for state in self.particles:
            state_count[state] += 1
        distribution = {state : count / len(self.particles) for state,count in state_count.items()}
        return distribution



class ActionNode:
    def __init__(self):
        self.belief_nodes = {}
        self.num_visits = 0
        self.value = 0

    def __str__(self):
        return f"{self.value} {self.belief_nodes} [{self.num_visits}]"

    def visit(self, value):
        self.num_visits += 1
        self.value += (value - self.value) / self.num_visits


class ActionOracleMcts:
    
    def __init__(self, simulated_model, discount_factor, relevant_horizon):
        
        # exploration parameters
        self.exploration_iterations = 100
        self.exploration_horizon = relevant_horizon
        self.exploration_constant_ucb = 10000

        self.simulated_model = simulated_model
        self.discount_factor = discount_factor

        self.pomdp = self.simulated_model.model
        self.actions_at_observation = [0] * self.pomdp.nr_observations
        for state in range(self.pomdp.nr_states):
            obs = self.pomdp.observations[state]
            num_actions = self.pomdp.get_nr_available_actions(state)
            self.actions_at_observation[obs] = num_actions
        
        self.actions_produced = 0

    
    def reset(self):
        self.root = None

    
    def create_empty_belief(self, observation):
        num_actions = self.actions_at_observation[observation]
        return BeliefNode(observation, num_actions)
    
    def create_belief_from_state(self, state):
        observation = self.pomdp.observations[state]
        belief = self.create_empty_belief(observation)
        belief.add(state)
        return belief

    
    def best_action(self, action_evaluations):
        return numpy.argmax(action_evaluations)

    def pick_action_value(self, belief_node):
        action_evaluations = [ action_node.value for action_node in belief_node.action_nodes ]
        return self.best_action(action_evaluations)

    def pick_action_exploration(self, belief_node):
        action_evaluations = []
        for action,action_node in enumerate(belief_node.action_nodes):
            value = action_node.value
            value_ucb = math.sqrt( math.log(belief_node.num_visits) / action_node.num_visits )
            value_ucb *= self.exploration_constant_ucb
            total_value = value + value_ucb
            action_evaluations.append(total_value)
        return self.best_action(action_evaluations)

    def pick_action_execution(self, belief_node):
        return self.pick_action_value(belief_node)


    def predict_state_action_value(self, state, action, horizon):
        return self.simulated_model.state_action_rollout(state,action,horizon,self.discount_factor)

    def predict_values_at_belief(self, belief_node, horizon):
        state = belief_node.sample()
        for action,action_node in enumerate(belief_node.action_nodes):
            value = self.simulated_model.state_action_rollout(state,action,horizon,self.discount_factor)
            belief_node.action_nodes[action].visit(value)
    
    def explore(self, belief_node, state, horizon):

        if horizon == 0:
            return 0

        belief_node.num_visits += 1
        action = self.pick_action_exploration(belief_node)
        action_reward = self.simulated_model.state_action_reward(state,action)
        action_node = belief_node.action_nodes[action]

        next_state = self.simulated_model.sample_successor(state,action)
        next_observation = self.simulated_model.state_observation(next_state)

        if next_observation not in action_node.belief_nodes:
            # fresh belief
            next_belief_node = self.create_belief_from_state(next_state)
            action_node.belief_nodes[next_observation] = next_belief_node
            self.predict_values_at_belief(next_belief_node, horizon-1)
            next_best_action = self.pick_action_value(next_belief_node)
            future_reward = next_belief_node.action_nodes[next_best_action].value
        else:
            next_belief_node = action_node.belief_nodes[next_observation]
            next_belief_node.add(next_state)
            future_reward = self.explore(next_belief_node, next_state, horizon-1)

        total_reward = action_reward + self.discount_factor * future_reward
        action_node.visit(total_reward)
        return total_reward

    
    def get_next_action(self, last_action, simulation_step):

        current_observation = self.simulated_model.state_observation()

        if self.root is None:
            # first call: create belief root corresponding to the initial state
            self.root = self.create_belief_from_state(self.simulated_model.current_state)
            self.predict_values_at_belief(self.root,self.exploration_horizon)
        else:
            # check if action node has the belief corresponding to this observation
            action_node = self.root.action_nodes[last_action]
            if current_observation not in action_node.belief_nodes:
                # cannot re-use the sub-tree: use uniform belief over all states with the given observation
                logger.info("observation {} never experienced in simulation, restarting with uniform belief... ".\
                    format(current_observation))
                self.root = self.create_empty_belief(current_observation)
                for state in range(self.pomdp.nr_states):
                    obs = self.pomdp.observations[state]
                    if obs == current_observation:
                        self.root.add(state)
                self.predict_values_at_belief(self.root,self.exploration_horizon)
            else:
                # can reuse the sub-tree
                self.root = action_node.belief_nodes[current_observation]

        for _ in range(self.exploration_iterations):
            state = self.root.sample()
            self.explore(self.root, state, self.exploration_horizon)

        return self.pick_action_value(self.root)

        

class ActionOracleSubpomdp(ActionOracleMcts):


    def __init__(self, simulated_model, discount_factor, relevant_horizon, reward_name, target_label):
        super().__init__(simulated_model, discount_factor, relevant_horizon)
        self.subpomdp_builder = stormpy.synthesis.SubPomdpBuilder(self.pomdp, reward_name, target_label)


    def get_next_action(self, last_action, simulation_step):
        # run MCTS
        action = super().get_next_action(last_action, simulation_step)
        
        # extract sub-POMDP from the tree
        if simulation_step % 20 == 0:
            subpomdp = self.construct_subpomdp()
            print(subpomdp)
        return action


    def collect_relevant_states(self, initial_belief_node):

        all_visited = False
        visited_most = True
        important_percentage = 0.05

        # traverse the tree, count how many times each state was visited
        state_visits = collections.defaultdict(int)
        nodes = [initial_belief_node]
        while nodes:
            node = nodes.pop(-1)
            for state in node.particles:
                state_visits[state] += 1
            for action_node in node.action_nodes:
                for belief_node in action_node.belief_nodes.values():
                    nodes.append(belief_node)

        # the output set of relevant states
        relevant_states_set = set()

        if all_visited:
            # collect all visited states
            for state in state_visits.keys():
                relevant_states_set.add(state)
        
        if visited_most:
            # collect up to x% of the most visited states
            states = list(state_visits.keys())
            states_ordered = sorted(states, key=lambda x : state_visits[x], reverse=True)

            capacity = math.floor(self.pomdp.nr_states * 0.05)
            # always add initial states
            for state in initial_belief_node.particles:
                relevant_states_set.add(state)
            for state in states:
                if len(relevant_states_set) >= capacity:
                    break
                relevant_states_set.add(state)

        for state in initial_belief_node.particles:
            assert state in relevant_states_set   


        # convert set to bitvector
        relevant_states = stormpy.storage.BitVector(self.pomdp.nr_states,False)
        for state in relevant_states_set:
            relevant_states.set(state)        
        return relevant_states

    def construct_subpomdp(self):
        initial_distribution = self.root.distribution()
        relevant_states = self.collect_relevant_states(self.root)
        self.subpomdp_builder.set_relevant_states(relevant_states)
        frontier_states = self.subpomdp_builder.get_frontier_states()
        state_values = {}
        for state in frontier_states:
            state_values[state] = 0
        subpomdp = self.subpomdp_builder.restrict_pomdp(initial_distribution, state_values)
        return subpomdp


class POMCP:
    
    def __init__(self, quotient):
        self.pomdp = quotient.pomdp
        self.specification = quotient.specification
        
        invalid_spec_msg = "expecting a single maximizing reward property"
        assert self.specification.is_single_property, invalid_spec_msg
        assert len(self.specification.constraints) == 0, invalid_spec_msg
        opt = self.specification.optimality
        assert opt.reward, invalid_spec_msg
        assert not opt.minimizing, invalid_spec_msg
        
        self.reward_name = opt.formula.reward_name
        self.max_reward = max(self.pomdp.get_reward_model(self.reward_name).state_action_rewards)
        self.target_label = str(opt.formula.subformula.subformula)
        assert self.pomdp.labeling.contains_label(self.target_label),\
            "formula must contain reachability wrt a simple label"

        self.simulated_model = SimulatedModel(self.pomdp, self.reward_name)

        # disable synthesis logging
        paynt.quotient.quotient_pomdp.logger.disabled = True
        paynt.quotient.property.logger.disabled = True
        paynt.synthesizer.synthesizer.logger.disabled = True


    def run_simulation(self, simulation_horizon, discount_factor, action_oracle):
        self.simulated_model.reset()
        action_oracle.reset()

        last_action = None
        accumulated_reward = 0
        discount_factor_to_k = 1
        for simulation_step in range(simulation_horizon):
            if self.simulated_model.finished():
                break
            action = action_oracle.get_next_action(last_action,simulation_step)
            reward = self.simulated_model.state_action_reward(self.simulated_model.current_state, action)
            accumulated_reward += discount_factor_to_k * reward
            discount_factor_to_k *= discount_factor
            self.simulated_model.simulate_action(action)
            last_action = action
        return accumulated_reward


    def run(self):

        # random.seed(42)

        # specification parameters
        discount_factor = 0.9
        precision = 1e-1
        # max horizon is ln(eps*(1-d)/Rmax) / ln(d)
        relevant_horizon = math.floor(
            math.log(precision*(1-discount_factor) / self.max_reward) /
            math.log(discount_factor)
            )
        print("relevant horizon for precision {} is {}".format(precision,relevant_horizon))

        # simulation parameters
        simulation_iterations = 10
        simulation_horizon = relevant_horizon

        # action picker
        # action_oracle = ActionOracleRandom(self.simulated_model)
        # action_oracle = ActionOracleMcts(self.simulated_model, discount_factor, relevant_horizon)
        action_oracle = ActionOracleSubpomdp(self.simulated_model, discount_factor, relevant_horizon, self.reward_name, self.target_label)

        # run simulations
        import progressbar
        bar = progressbar.ProgressBar(maxval=simulation_iterations, \
            widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage(), progressbar.AdaptiveETA()])
        bar.start()
        simulation_values = []
        for simulation_iteration in range(simulation_iterations):
            simulation_value = self.run_simulation(simulation_horizon, discount_factor, action_oracle)
            simulation_values.append(simulation_value)
            bar.update(simulation_iteration)
        bar.finish()

        simulation_value_avg = numpy.mean(simulation_values)
        # simulation_value_std = numpy.std(simulation_values)

        print("{} simulations: mean value = {}".format(simulation_iterations,simulation_value_avg))





# class FSC:

#     def __init__(self, num_nodes, num_observations):
#         # self.num_nodes = num_nodes
#         # self.num_observations = num_observations
        
#         # gamma: NxZ -> Act
#         self.action_function = [ [None]*num_observations for _ in range(num_nodes) ]
#         # delta: NxZ -> N
#         self.update_function = [ [None]*num_observations for _ in range(num_nodes) ]

#     @classmethod
#     def from_hole_assignment(cls, quotient, num_nodes, assignment):
#         assert not quotient.posterior_aware
#         fsc = FSC(num_nodes,quotient.pomdp.nr_observations)
#         for hole in assignment:
#             option = hole.options[0]
#             is_action_hole, observation, node = quotient.decode_hole_name(hole.name)
#             if is_action_hole:
#                 fsc.action_function[node][observation] = option
#             else:
#                 fsc.update_function[node][observation] = option
#         return fsc

#     def decide(self, decision_map, node, observation):
#         '''
#         Make decision using decision_map based on the observation and memory
#         node. decision_map is either self.action_function or
#         self.update_function
#         '''
#         decision = decision_map[node][observation]
#         if decision is None:
#             # default to 0 node
#             decision = decision_map[0][node]
#             if decision is None:
#                 # default to first decision
#                 decision = 0
#         return decision

#     def suggest_action(self, node, observation):
#         return self.decide(self.action_function, node, observation)

#     def suggest_update(self, node, observation):
#         return self.decide(self.update_function, node, observation)

