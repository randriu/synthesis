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
    def __init__(self):
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

    def best_action(self):
        action_evaluations = [ action_node.value for action_node in self.action_nodes ]
        return numpy.argmin(action_evaluations)

    def best_exploration_action(self, exploration_constant):
        assert self.num_visits > 0
        action_evaluations = [
            action_node.value + exploration_constant * math.sqrt( math.log(self.num_visits) / (action_node.num_visits+1) )
            for action_node in self.action_nodes ]
        
        return numpy.argmin(action_evaluations)


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

        self.iterations = 100
        self.exploration_constant = .8
        self.horizon = 10

        self.discount_factor = 1

        self.root = None
    
    
    def create_fresh_root(self, observation):
        belief = ParticleBelief()
        for state in range(self.simulated_model.model.nr_states):
            obs = self.simulated_model.model.get_observation(state)
            if obs == observation:
                belief.add(state)
        num_actions = self.quotient.actions_at_observation[observation]
        root = BeliefNode(belief, num_actions)
        return root
    
    
    def simulate(self, belief_node, state, horizon):

        if horizon == 0:
            return 0

        belief_node.num_visits += 1
        action = belief_node.best_exploration_action(self.exploration_constant)
        action_reward = self.simulated_model.state_action_reward(state,action)

        next_state = self.simulated_model.sample_successor(state,action)
        next_observation = self.simulated_model.model.get_observation(next_state)

        action_node = belief_node.action_nodes[action]

        if next_observation not in action_node.belief_nodes:
            # add new belief
            next_belief = ParticleBelief()
            next_belief.add(next_state)
            next_belief_node = BeliefNode(next_belief, num_actions = self.quotient.actions_at_observation[next_observation])
            action_node.belief_nodes[next_observation] = next_belief_node
            # rollout
            path = self.simulated_model.sample_path(next_state, length=horizon)
            future_reward = self.simulated_model.path_discounted_reward(path, self.discount_factor)
        else:
            next_belief_node = action_node.belief_nodes[next_observation]
            next_belief_node.belief.add(next_state)
            future_reward = self.simulate(next_belief_node, next_state, horizon-1)

        total_reward = action_reward + self.discount_factor * future_reward

        # update action node stats
        action_node.num_visits += 1
        action_node.value += (total_reward - action_node.value) / action_node.num_visits

        return total_reward

    
    def run_simulation(self, root, horizon):
        self.root = root
        for _ in range(self.iterations):
            state = self.root.belief.sample()
            self.simulate(self.root, state, horizon)

        return self.root.best_action()

    
    def search_action(self, action, observation, horizon):

        # uniform root in case we cannot re-use the sub-tree
        uniform_root = self.create_fresh_root(observation)

        if action is None:
            # first action selection
            return self.run_simulation(uniform_root, horizon)

        # check if action node has the belief corresponding to this observation
        action_node = self.root.action_nodes[action]
        if observation not in action_node.belief_nodes:
            logger.info("observation {} never experienced in simulation, restarting with uniform belief... ".format(observation))
            return self.run_simulation(uniform_root, horizon)

        # check what??
        new_root = action_node.belief_nodes[observation]
        if new_root.belief.size == 0:
            assert False
            logger.info("POMCP lost track ot the belief, restarting with uniform belief...")
            return self.run_simulation(uniform_root, horizon)

        # can re-use the sub-tree
        return self.run_simulation(new_root, horizon)
    

    def run(self):
        
        accumulated_reward = 0
        self.simulated_model = SimulatedModel(self.quotient.pomdp)

        action = None
        while True:

            state = self.simulated_model.current_state
            if self.simulated_model.state_is_absorbing[self.simulated_model.current_state]:
                break

            observation = self.simulated_model.current_observation
            observation_label = self.quotient.observation_labels[observation]
            print("s: ", self.simulated_model.current_state, observation, observation_label)

            action = self.search_action(action, observation, self.horizon)

            reward = self.simulated_model.state_action_reward(self.simulated_model.current_state,action)
            accumulated_reward += reward
            action_label = self.quotient.action_labels_at_observation[observation][action]
            print("a: ", action, action_label)

            self.simulated_model.simulate_action(action)
            

        logger.info("execution finished")
        logger.info("accumulated reward: {}".format(accumulated_reward))

        
        