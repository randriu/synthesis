import stormpy

import paynt
from paynt.simulation.simulation import SimulatedModel

import logging
logger = logging.getLogger(__name__)

import collections
import math, numpy

import random


class FSC:

    def __init__(self, quotient, memory_size, assignment):
        self.selected_action = [ [None]*memory_size for obs in range(quotient.pomdp.nr_observations)]
        self.selected_update = [ [None]*memory_size for obs in range(quotient.pomdp.nr_observations)]
        for hole in assignment:
            option = hole.options[0]
            is_action_hole, observation, memory = quotient.decode_hole_name(hole.name)
            if is_action_hole:
                self.selected_action[observation][memory] = option
            else:
                self.selected_update[observation][memory] = option

    def decide(self, decision_map, observation, memory):
        '''
        Make decision using decision_map based on the observation and memory
        value. decision_map is either self.selected_action or
        self.selected_update
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

    def play_history(self, history):
        memory = 0
        for observation,_ in history:
            memory = self.suggest_update(observation,memory)
        return memory





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
        return self.value if not minimizing else -self.value





class POMCP:
    
    def __init__(self, quotient):
        self.quotient = quotient
        assert(self.quotient.specification.is_single_property)

    def create_belief_node(self, observation):
        num_actions = self.quotient.actions_at_observation[observation]
        return BeliefNode(observation, num_actions)

    
    def predict_action_value(self, state, action, horizon):
        # rollout
        next_state = self.simulated_model.sample_successor(state,action)
        path = self.simulated_model.sample_path(next_state, length=horizon)
        path_reward = self.simulated_model.path_discounted_reward(path, self.reward_name, self.discount_factor)
        return path_reward

    def predict_state_value(self, state, horizon):
        num_actions = self.quotient.pomdp.get_nr_available_actions(state)
        action_values = []
        for action in range(num_actions):
            action_value = self.predict_action_value(state, action, horizon)
            action_values.append(action_value)
        return action_values

    def predict_belief_values(self, belief_node, horizon):
        state = belief_node.sample()
        action_values = self.predict_state_value(state, horizon)
        for action,value in enumerate(action_values):
            belief_node.action_nodes[action].visit(value)

    
    def approximate_action_value_fsc(self, belief_node, fsc):
        avg_path_reward = 0
        for simulation in range(self.exploration_iterations):
            path = []
            state = belief_node.sample()
            obs = belief_node.observation
            mem = belief_node.fsc_state
            for _ in range(self.exploration_horizon):
                action = fsc.suggest_action(obs,mem)
                path.append( (state,action ) )
                mem = fsc.suggest_update(obs,mem)
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
        action_evaluations = []
        for action,action_node in enumerate(belief_node.action_nodes):

            value = action_node.evaluate(self.minimizing)

            value_ucb = math.sqrt( math.log(belief_node.num_visits) / action_node.num_visits )
            value_ucb *= self.exploration_constant_ucb

            total_value = value + value_ucb
            
            action_evaluations.append(total_value)
            
        return self.best_action(action_evaluations)

    def pick_action_play(self, belief_node, fsc, fsc_state):
        action_evaluations = [
            action_node.evaluate(self.minimizing)
            for action,action_node in enumerate(belief_node.action_nodes)
        ]
        # print("action values: ", action_evaluations)
        self.total_decisions += 1
        best_action = self.best_action(action_evaluations)
        
        if self.use_fsc_to_play and fsc is not None:
            fsc_action = fsc.suggest_action_in_belief(belief_node)
            fsc_action_value = self.approximate_action_value_fsc(belief_node)

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

        action_reward = self.simulated_model.state_action_reward(state,action,self.reward_name)


        next_state = self.simulated_model.sample_successor(state,action)
        next_observation = self.simulated_model.model.get_observation(next_state)

        action_node = belief_node.action_nodes[action]

        if next_observation not in action_node.belief_nodes:
            # new belief
            next_belief_node = self.create_belief_node(next_observation)
            next_belief_node.add(next_state)
            self.predict_belief_values(next_belief_node, horizon-1)
            action_node.belief_nodes[next_observation] = next_belief_node

            next_best_action = self.pick_action_value(next_belief_node)
            future_reward = next_belief_node.action_nodes[next_best_action].value
        else:
            next_belief_node = action_node.belief_nodes[next_observation]
            next_belief_node.add(next_state)
            future_reward = self.explore(next_belief_node, next_state, horizon-1)

        total_reward = action_reward + self.discount_factor * future_reward
        action_node.visit(total_reward)
        return total_reward

    
    def build_tree(self, action, observation, horizon):

        root = None
        
        if action is not None:
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
            root = self.create_belief_node(observation)
            for state in range(self.simulated_model.model.nr_states):
                obs = self.simulated_model.model.get_observation(state)
                if obs == observation:
                    root.add(state)
            self.predict_belief_values(root,horizon)

        self.root = root

        # nothing to do if only 1 action is available
        # FIXME
        # if len(self.root.action_nodes) == 1:
            # return 0

        for _ in range(self.exploration_iterations):
            state = self.root.sample()
            self.explore(self.root, state, horizon)


    def collect_relevant_states(self, initial_belief_node):
        state_visits = [0 for state in range(self.quotient.pomdp.nr_states)]
        nodes = [initial_belief_node]
        while nodes:
            node = nodes.pop(-1)
            for state in node.particles:
                state_visits[state] += 1
            for action_node in node.action_nodes:
                for belief_node in action_node.belief_nodes.values():
                    nodes.append(belief_node)

        relevant_states = stormpy.storage.BitVector(self.quotient.pomdp.nr_states,False)
        for s,v in enumerate(state_visits):
            if v>0:
                relevant_states.set(s)

        # add states in the initial belief
        for state in initial_belief_node.particles:
            relevant_states.set(state)
        
        return relevant_states
    
    def synthesize(self, initial_belief_node):
        relevant_states = self.collect_relevant_states(initial_belief_node)
        self.builder.set_relevant_states(relevant_states)
        
        # approximate values in horizon states
        pomdp = self.quotient.pomdp
        horizon_states = self.builder.get_horizon_states()
        print(relevant_states)
        print(horizon_states)
        horizon_values = {}
        for s in horizon_states:
            action_values = self.predict_state_value(s, self.exploration_horizon)
            if self.minimizing:
                best_value = numpy.min(action_values)
            else:
                best_value = numpy.max(action_values)
            horizon_values[s] = best_value

        # construct initial distribution from particle belief
        particle_count = collections.defaultdict(int)
        for s in initial_belief_node.particles:
            particle_count[s] += 1
        frequency_sum = len(initial_belief_node.particles)
        initial_belief = {}
        for s,frequency in particle_count.items():
            initial_belief[s] = frequency / frequency_sum

        print(initial_belief)
        subpomdp = self.builder.restrict_pomdp(initial_belief, horizon_values)
        print(subpomdp)
        exit()

        # construct initial FSC
        memory_size = paynt.quotient.quotient_pomdp.POMDPQuotientContainer.initial_memory_size
        self.quotient.set_imperfect_memory_size(memory_size)
        synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR(self.quotient)
        assignment = synthesizer.synthesize()
        assert assignment is not None, "no assignment was found, try to increase memory"
        fsc = FSC(self.quotient, memory_size, assignment)
        self.quotient.set_imperfect_memory_size(1)
        return fsc

    def run_simulation(self):
        
        self.simulated_model = SimulatedModel(self.quotient.pomdp)

        self.root = None

        # history = []
        accumulated_reward = 0
        action = None       # last action played
        fsc = None          # last FSC built
        for depth in range(self.simulation_horizon):

            observation = self.simulated_model.current_observation
            # observation_label = self.quotient.observation_labels[observation]
            # print("s: ", self.simulated_model.current_state, observation, observation_label)
            if self.simulated_model.state_is_absorbing[self.simulated_model.current_state]:
                break

            # run MCTS
            self.build_tree(action, observation, self.exploration_horizon)

            # resynthesize FSC
            fsc = self.synthesize(self.root)
            # fsc_state = fsc.play_history(history)
            fsc_state = 0
            
            # pick the best action
            action = self.pick_action_play(self.root, fsc, fsc_state)
            
            # play the action
            # history.append( (observation,action) )
            reward = self.simulated_model.state_action_reward(self.simulated_model.current_state, action, self.reward_name)
            accumulated_reward += reward
            # action_label = self.quotient.action_labels_at_observation[observation][action]
            # print("a: ", action, action_label)
            self.simulated_model.simulate_action(action)

        # logger.info("finished, accumulated reward: {}".format(accumulated_reward))
        return accumulated_reward

    
    def run(self):

        # assuming reward optimization without constraints
        assert len(self.quotient.specification.constraints) == 0
        opt = self.quotient.specification.optimality
        assert opt.reward
        self.reward_name = opt.formula.reward_name
        self.minimizing = opt.minimizing
        target_label = str(opt.formula.subformula.subformula)
        assert self.quotient.pomdp.labeling.contains_label(target_label),\
            "formula must contain reachability wrt a simple label"

        self.simulate_fsc = False
        self.use_fsc_to_play = False

        self.discount_factor = 1

        self.simulation_iterations = 1000
        self.simulation_horizon = 40
        # self.simulate_fsc = True
        
        self.exploration_iterations = 20
        self.exploration_horizon = 20

        self.exploration_constant_ucb = 10000
        # self.use_fsc_to_play = True

        self.total_decisions = 0
        self.actions_same = 0
        self.fsc_better = 0
        self.mcts_better = 0

        # random.seed(42)
        self.builder = stormpy.synthesis.SubPomdpBuilder(self.quotient.pomdp, self.reward_name, target_label)

        # run simulations
        import progressbar
        bar = progressbar.ProgressBar(maxval=self.simulation_iterations, \
            widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage(), progressbar.AdaptiveETA()])
        bar.start()

        simulation_values = []
        for simulation in range(self.simulation_iterations):
            simulation_value = self.run_simulation()
            # print(simulation_value)
            simulation_values.append(simulation_value)
            bar.update(simulation)

        bar.finish()

        simulation_value_avg = numpy.mean(simulation_values)
        # simulation_value_std = numpy.std(simulation_values)

        print("{} simulations: mean value = {}".format(self.simulation_iterations,simulation_value_avg))

        print("MCTS = FSC: {} / {}".format(self.actions_same, self.total_decisions))
        print("FSC is better: {} / {}".format(self.fsc_better, self.total_decisions))
        print("TS is better: {} / {}".format(self.mcts_better, self.total_decisions))


        
        