from .models import MarkovChain,MDP,DTMC
from .holes import Hole,Holes,DesignSpace
from .quotient import QuotientContainer
from .coloring import MdpColoring

import logging
logger = logging.getLogger(__name__)

import collections
import math, numpy

import random

from paynt.simulation.simulation import SimulatedModel
    




class ParticleBelief:
    def __init__(self, observation):
        # self.observation = observation
        self.particle_counts = collections.defaultdict(int)

    def __str__(self):
        return f"{self.observation} : {self.particle_counts}"

    def add(self,particle):
        count = self.particle_counts[particle]
        self.particle_counts[particle] = count + 1

    def size(self):
        return len(self.particle_counts)

    def sample(self):
        objects = list(self.particle_counts.keys())
        frequencies = list(self.particle_counts.values())
        sampled_object = random.choices(objects,frequencies)[0]
        return sampled_object




class BeliefNode:
    def __init__(self, belief, num_actions):
        self.belief = belief
        self.action_nodes = [ActionNode() for action in range(num_actions)]

        self.num_visits = 0

    def __str__(self):
        return f"{self.belief} {self.action_nodes} [{self.num_visits}]"


class ActionNode:
    def __init__(self):
        self.num_visits = 0
        self.belief_nodes = {}

        self.value = 0

    def __str__(self):
        return f"{self.value} {self.belief_nodes} [{self.num_visits}]"

class POMCP:

    
    def __init__(self, quotient):
        self.quotient = quotient

        # self.belief_size = self.num_states
        self.iterations = 100
        self.exploration = 0.5
        self.horizon = 10

        self.discount_factor = 1

        self.graph = None

        # assuming state reward
        reward_model = list(self.quotient.pomdp.reward_models.values())[0]
        assert reward_model.state_rewards

        num_states = self.quotient.pomdp.nr_states
        self.state_rewards = [reward_model.get_state_reward(state) for state in range(num_states)]

    
    @property
    def num_states(self):
        return self.quotient.pomdp.nr_states

    
    def random_action(self, state):
        num_actions = self.quotient.pomdp.get_nr_available_actions(state)
        action = random.randint(0,num_actions-1)
        return action

    def random_transition(self, state, action):
        
        # get row
        tm = self.quotient.pomdp.transition_matrix
        row_index = tm.get_row_group_start(state) + action
        row = tm.get_row(row_index)

        # pack successor and probabilities
        succs = []
        probs = []
        for entry in row:
            succs.append(entry.column)
            probs.append(entry.value())

        # sample a successor
        res = random.choices(succs, probs)
        return res[0]

    def uniform_belief(self, observation):
        belief = ParticleBelief(observation)
        for state in range(self.quotient.pomdp.nr_states):
            obs = self.quotient.pomdp.get_observation(state)
            if obs == observation:
                belief.add(state)
        return belief

    
    def choose_action(self, observation, belief, horizon):
        num_actions = self.quotient.actions_at_observation[observation]
        self.graph = BeliefNode(belief, num_actions)

        return self.run_simulation(horizon)


    def sample_action(self, action, next_observation, horizon):

        action_node = self.graph.action_nodes[action]

        if next_observation not in action_node.belief_nodes:
            logger.info("Observation {} never experienced in simulation, restarting with uniform belief... ".format(next_observation))
            belief = self.uniform_belief(next_observation)
            return self.choose_action(next_observation, belief, horizon)

        next_belief = action_node.belief_nodes[next_observation]
        self.graph = next_belief
        if self.graph.belief.size == 0:
            logger.info("POMCP lost track ot the belief, restarting with uniform...")
            belief = self.uniform_belief(next_observation)
            return self.choose_action(next_observation, belief, horizon)

        return self.run_simulation(horizon)


    def run_simulation(self, horizon):
        if horizon == 0:
            return 0

        self.max_depth = horizon
        for _ in range(self.iterations):
            state = self.graph.belief.sample()
            self.simulate(self.graph, state, 0)

        return self.find_best_action(self.graph)


    def rollout(self, state, max_depth):
        
        total_reward = 0
        discount_factor = 1
        for depth in range(max_depth):
            # TODO optimise for absorbing states
            action = self.random_action(state)
            action_reward = self.state_rewards[state]
            next_state = self.random_transition(state,action)
            total_reward += discount_factor * action_reward
            discount_factor *= self.discount_factor
        return total_reward

    
    def simulate(self, belief_node, state, depth):

        belief_node.num_visits += 1
        action = self.find_best_bonus_action(belief_node)

        next_state = self.random_transition(state,action)
        next_observation = self.quotient.pomdp.get_observation(next_state)
        reward = self.state_rewards[state]

        action_node = belief_node.action_nodes[action]

        future_reward = 0
        if next_observation not in action_node.belief_nodes:
            next_belief = ParticleBelief(next_observation)
            next_belief.add(next_state)
            next_belief_node = BeliefNode(next_belief, num_actions = self.quotient.actions_at_observation[next_observation])
            action_node.belief_nodes[next_observation] = next_belief_node
            futureRew = self.rollout(next_state, self.max_depth - depth + 1);
        else:
            next_belief_node = action_node.belief_nodes[next_observation]
            next_belief_node.belief.add(next_state)
            if depth + 1 < self.max_depth:
                future_reward = self.simulate(next_belief_node, next_state, depth+1)

        reward += self.discount_factor * future_reward

        action_node.num_visits += 1
        action_node.value += (reward - action_node.value) / action_node.num_visits

        return reward

    
    def find_best_action(self, belief_node):
        action_evaluations = [ action_node.value for action_node in belief_node.action_nodes ]
        return numpy.argmin(action_evaluations)

    def find_best_bonus_action(self, belief_node):
        action_evaluations = [
            action_node.value + self.exploration * math.sqrt( math.log(belief_node.num_visits) / (action_node.num_visits+1) )
            for action_node in belief_node.action_nodes ]
        
        return numpy.argmin(action_evaluations)


    def foo(self):
        assert len(self.quotient.pomdp.initial_states) == 1

        simulated_model = SimulatedModel(self.quotient.pomdp)
        simulated_model.reset_simulation()

        # initial choice

        observation = simulated_model.current_observation
        print(simulated_model.current_state, observation, self.quotient.observation_labels[observation])

        initial_belief = self.uniform_belief(observation)
        action = self.choose_action(observation, initial_belief, self.horizon)
        action_label = self.quotient.action_labels_at_observation[observation][action]
        print(action, action_label)

        # perform an action
        simulated_model.simulate_action(action)
        observation = simulated_model.current_observation

        print(simulated_model.current_state, observation, self.quotient.observation_labels[observation])
        
        action = self.sample_action(action, observation, self.horizon)
        action_label = self.quotient.action_labels_at_observation[observation][action]
        print(action, action_label)
        
        