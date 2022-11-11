import paynt

from .models import MarkovChain,MDP,DTMC
from .holes import Hole,Holes,DesignSpace
from .quotient import QuotientContainer
from .coloring import MdpColoring
from paynt.simulation.simulation import SimulatedModel

import logging
logger = logging.getLogger(__name__)

import collections
import math, numpy

import random


class ParticleBelief(collections.defaultdict):
    
    def add(self,particle):
        count = self[particle]
        self[particle] = count + 1

    def sample(self):
        objects = list(self.keys())
        frequencies = list(self.values())
        sampled_object = random.choices(objects,frequencies)[0]
        return sampled_object

    @property
    def size(self):
        return sum(list(self.values()))


class BeliefNode:
    def __init__(self, belief, observation, num_actions, fsc_state):
        self.belief = belief
        self.observation = observation
        self.action_nodes = [ActionNode() for action in range(num_actions)]
        self.num_visits = 0
        self.fsc_state = fsc_state

    def __str__(self):
        return f"{self.belief} {[str(n) for n in self.action_nodes]} [{self.num_visits}]"


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

    def evaluate(self, minimizing):
        value = self.value
        if minimizing:
            value *= -1
        return value


class FSC:

    def __init__(self, quotient, memory_size, assignment):
        
        self.quotient = quotient

        self.selected_action = [ [None]*memory_size for obs in range(self.num_observations)]
        self.selected_update = [ [None]*memory_size for obs in range(self.num_observations)]
        for hole in assignment:
            option = hole.options[0]
            is_action_hole, observation, memory = self.quotient.decode_hole_name(hole.name)
            if is_action_hole:
                self.selected_action[observation][memory] = option
            else:
                self.selected_update[observation][memory] = option

    @property
    def num_observations(self):
        return self.quotient.pomdp.nr_observations

    def decide(self, decision_map, observation, memory):
        '''
        Make decision from the decision_map based on the observation and memory value.
        '''
        decision = decision_map[observation][memory]
        if decision is None:
            # default to 0 memory
            decision = decision_map[observation][0]
            if decision is None:
                # default to first decision
                decision = 0
        return decision

    def suggest_action(self, observation, memory):
        return self.decide(self.selected_action, observation, memory)

    def suggest_update(self, observation, memory):
        return self.decide(self.selected_update, observation, memory)
    
    def suggest_action_in_belief(self, belief_node):
        return self.suggest_action(belief_node.observation, belief_node.fsc_state)

    def suggest_update_in_belief(self, belief_node):
        return self.suggest_update(belief_node.observation, belief_node.fsc_state)


class POMCP:
    
    def __init__(self, quotient):
        self.quotient = quotient
        self.root = None

    def create_belief_node(self, observation, fsc_state):
        belief = ParticleBelief(int)
        num_actions = self.quotient.actions_at_observation[observation]
        belief_node = BeliefNode(belief, observation, num_actions, fsc_state)
        return belief_node

    def approximate_action_values(self, belief_node, horizon):
        state = belief_node.belief.sample()
        for action,action_node in enumerate(belief_node.action_nodes):
            # rollout
            next_state = self.simulated_model.sample_successor(state,action)
            path = self.simulated_model.sample_path(next_state, length=horizon)
            path_reward = self.simulated_model.path_discounted_reward(path, self.discount_factor)
            # reward_value = path_reward + (self.exploration_horizon - horizon)
            # if reward_value < 90:
                # print(reward_value)
                # print(dir(self.simulated_model.model.state_valuations))
                # print(self.simulated_model.model.state_valuations.get_string(state))
            action_node.visit(path_reward)

    def approximate_action_value_fsc(self, belief_node):

        avg_path_reward = 0
        for simulation in range(self.exploration_iterations):
            path = []
            state = belief_node.belief.sample()
            obs = belief_node.observation
            mem = belief_node.fsc_state
            for _ in range(self.exploration_horizon):
                action = self.fsc.suggest_action(obs,mem)
                path.append( (state,action ) )
                mem = self.fsc.suggest_update(obs,mem)
                state = self.simulated_model.sample_successor(state,action)
                obs = next_observation = self.simulated_model.model.get_observation(state)
            path_reward = self.simulated_model.path_discounted_reward(path, self.discount_factor)
            avg_path_reward += (path_reward - avg_path_reward) / (simulation+1)

        if self.minimizing:
            avg_path_reward *= -1
        return avg_path_reward
    
    def best_action(self, action_evaluations):
        return numpy.argmax(action_evaluations)

    def pick_action_value(self, belief_node):
        action_evaluations = [ action_node.evaluate(self.minimizing) for action_node in belief_node.action_nodes ]
        return self.best_action(action_evaluations)

    def pick_action_exploration(self, belief_node):
        fsc_action = self.fsc.suggest_action_in_belief(belief_node)
        action_evaluations = []
        for action,action_node in enumerate(belief_node.action_nodes):

            value = action_node.evaluate(self.minimizing)

            value_ucb = math.sqrt( math.log(belief_node.num_visits) / action_node.num_visits )
            value_ucb *= self.exploration_constant_ucb

            # value_fsc = 1 if action == fsc_action else 0
            # value_fsc *= self.exploration_constant_fsc

            total_value = value + value_ucb # + value_fsc
            
            action_evaluations.append(total_value)
            
        return self.best_action(action_evaluations)

    def pick_action_play(self, belief_node):
        action_evaluations = [
            action_node.evaluate(self.minimizing)
            for action,action_node in enumerate(belief_node.action_nodes)
        ]
        self.total_decisions += 1
        best_action = self.best_action(action_evaluations)
        if self.use_fsc_to_play:
            fsc_action = self.fsc.suggest_action_in_belief(belief_node)
            fsc_action_value = self.approximate_action_value_fsc(belief_node)
            # fsc_action_value = numpy.inf

            if fsc_action == best_action:
                self.actions_same += 1
            else:
                if fsc_action_value > action_evaluations[best_action]:
                    self.fsc_better += 1
                else:
                    self.mcts_better += 1

            
            if fsc_action_value > action_evaluations[best_action]:
                best_action = fsc_action

        return best_action
    
    
    def explore(self, belief_node, state, horizon):

        if horizon == 0:
            return 0

        belief_node.num_visits += 1
        action = self.pick_action_exploration(belief_node)
        # action_fsc = self.fsc.suggest_action_in_belief(belief_node)
        # assert action == action_fsc

        action_reward = self.simulated_model.state_action_reward(state,action,self.reward_name)


        next_state = self.simulated_model.sample_successor(state,action)
        next_observation = self.simulated_model.model.get_observation(next_state)

        action_node = belief_node.action_nodes[action]

        if next_observation not in action_node.belief_nodes:
            # new belief
            fsc_state = self.fsc.suggest_update_in_belief(belief_node)
            next_belief_node = self.create_belief_node(next_observation,fsc_state)
            next_belief_node.belief.add(next_state)
            self.approximate_action_values(next_belief_node, horizon-1)
            action_node.belief_nodes[next_observation] = next_belief_node

            next_best_action = self.pick_action_value(next_belief_node)
            future_reward = next_belief_node.action_nodes[next_best_action].value
        else:
            next_belief_node = action_node.belief_nodes[next_observation]
            next_belief_node.belief.add(next_state)
            future_reward = self.explore(next_belief_node, next_state, horizon-1)

        total_reward = action_reward + self.discount_factor * future_reward
        action_node.visit(total_reward)
        return total_reward

    
    def search_action(self, action, observation, horizon):

        
        root = None
        fsc_state = None
        if action is None:
            # action is None when no action has been played, i.e. in the beginning
            fsc_state = 0
        else:

            # compute next state of the FSC
            fsc_state = self.fsc.suggest_update_in_belief(self.root)
            # check if action node has the belief corresponding to this observation
            action_node = self.root.action_nodes[action]
            if observation not in action_node.belief_nodes:
                # logger.info("observation {} never experienced in simulation, restarting with uniform belief... ".format(observation))
                pass
            else:
                # can reuse the sub-tree
                root = action_node.belief_nodes[observation]

        if root is None:
            # cannot re-use the sub-tree: use uniform belief over all states
            # with the given observation
            root = self.create_belief_node(observation,fsc_state)
            for state in range(self.simulated_model.model.nr_states):
                obs = self.simulated_model.model.get_observation(state)
                if obs == observation:
                    root.belief.add(state)
            self.approximate_action_values(root,horizon)

        self.root = root

        # nothing to do if only 1 action is available
        if len(self.root.action_nodes) == 1:
            return 0

        for _ in range(self.exploration_iterations):
            state = self.root.belief.sample()
            self.explore(self.root, state, horizon)

        # print("action values: ", [n.evaluate(self.minimizing) for n in self.root.action_nodes])
        # return self.pick_action_value(self.root)
        return self.pick_action_play(self.root)


    def run_simulation(self):
        
        self.simulated_model = SimulatedModel(self.quotient.pomdp)

        accumulated_reward = 0
        action = None
        for depth in range(self.simulation_horizon):

            state = self.simulated_model.current_state
            observation = self.simulated_model.current_observation
            # observation_label = self.quotient.observation_labels[observation]
            # print("s: ", self.simulated_model.current_state, observation, observation_label)
            if self.simulated_model.state_is_absorbing[self.simulated_model.current_state]:
                break

            action = self.search_action(action, observation, self.exploration_horizon)
            action_fsc = self.fsc.suggest_action_in_belief(self.root)
            # if action != action_fsc:
                # print("selected {}, FSC suggests {}".format(action,action_fsc))
            # assert action == action_fsc

            reward = self.simulated_model.state_action_reward(self.simulated_model.current_state, action, self.reward_name)
            accumulated_reward += reward
            # action_label = self.quotient.action_labels_at_observation[observation][action]
            # print("a: ", action, action_label)

            self.simulated_model.simulate_action(action)

        # logger.info("finished, accumulated reward: {}".format(accumulated_reward))
        print(accumulated_reward)
        return accumulated_reward

    
    def run(self):

        # assuming reward optimization without constraints
        assert len(self.quotient.specification.constraints) == 0
        opt = self.quotient.specification.optimality
        assert opt.reward
        self.reward_name = opt.formula.reward_name
        self.minimizing = opt.minimizing

        self.discount_factor = 1

        self.simulation_iterations = 100
        self.simulation_horizon = 40
        
        self.exploration_iterations = 20
        self.exploration_horizon = 20

        self.exploration_constant_ucb = 10000
        self.use_fsc_to_play = False
        # self.use_fsc_to_play = True

        # run synthesis
        memory_size = paynt.quotient.quotient_pomdp.POMDPQuotientContainer.initial_memory_size
        self.quotient.set_imperfect_memory_size(memory_size)
        from paynt.synthesizer.synthesizer_ar import SynthesizerAR
        synthesizer = SynthesizerAR(self.quotient)
        assignment = synthesizer.synthesize()
        if assignment is None:
            logger.info("no assignment was found, try to increase memory")
        self.fsc = FSC(self.quotient, memory_size, assignment)
        self.quotient.set_imperfect_memory_size(1)

        self.total_decisions = 0
        self.actions_same = 0
        self.fsc_better = 0
        self.mcts_better = 0

        # run simulations
        import progressbar
        bar = progressbar.ProgressBar(maxval=self.simulation_iterations, \
            widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage(), progressbar.AdaptiveETA()])
        bar.start()

        simulation_values = []
        for simulation in range(self.simulation_iterations):
            simulation_value = self.run_simulation()
            simulation_values.append(simulation_value)
            bar.update(simulation)
        bar.finish()

        simulation_value_avg = numpy.mean(simulation_values)
        simulation_value_std = numpy.std(simulation_values)

        print("{} simulations: mean value = {} [std={:.2f}]".format(self.simulation_iterations,simulation_value_avg, simulation_value_std))

        print("MCTS = FSC: {} / {}".format(self.actions_same, self.total_decisions))
        print("FSC is better: {} / {}".format(self.fsc_better, self.total_decisions))
        print("TS is better: {} / {}".format(self.mcts_better, self.total_decisions))


        
        