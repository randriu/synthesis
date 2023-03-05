import stormpy

import paynt
from paynt.simulation.simulation import SimulatedModel
from paynt.quotient.quotient_pomdp import POMDPQuotientContainer

import logging
logger = logging.getLogger(__name__)

import collections
import math, numpy

import random


class FSC:

    def __init__(self, num_nodes, num_observations):
        # self.num_nodes = num_nodes
        # self.num_observations = num_observations
        
        # gamma: NxZ -> Act
        self.action_function = [ [None]*num_observations for _ in range(num_nodes) ]
        # delta: NxZ -> N
        self.update_function = [ [None]*num_observations for _ in range(num_nodes) ]

    @classmethod
    def from_hole_assignment(cls, quotient, num_nodes, assignment):
        assert not quotient.posterior_aware
        fsc = FSC(num_nodes,quotient.pomdp.nr_observations)
        for hole in assignment:
            option = hole.options[0]
            is_action_hole, observation, node = quotient.decode_hole_name(hole.name)
            if is_action_hole:
                fsc.action_function[node][observation] = option
            else:
                fsc.update_function[node][observation] = option
        return fsc

    def decide(self, decision_map, node, observation):
        '''
        Make decision using decision_map based on the observation and memory
        node. decision_map is either self.action_function or
        self.update_function
        '''
        decision = decision_map[node][observation]
        if decision is None:
            # default to 0 node
            decision = decision_map[0][node]
            if decision is None:
                # default to first decision
                decision = 0
        return decision

    def suggest_action(self, node, observation):
        return self.decide(self.action_function, node, observation)

    def suggest_update(self, node, observation):
        return self.decide(self.update_function, node, observation)
    





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
        self.pomdp = quotient.pomdp
        self.specification = quotient.specification
        self.quotient = quotient
        invalid_spec_msg = "expecting a single optimizing reward property"
        assert self.quotient.specification.is_single_property, invalid_spec_msg
        assert len(self.quotient.specification.constraints) == 0, invalid_spec_msg
        opt = self.quotient.specification.optimality
        assert opt.reward, invalid_spec_msg
        self.reward_name = opt.formula.reward_name
        self.minimizing = opt.minimizing
        self.target_label = str(opt.formula.subformula.subformula)
        assert self.quotient.pomdp.labeling.contains_label(self.target_label),\
            "formula must contain reachability wrt a simple label"

        # disable synthesis logging
        paynt.quotient.quotient_pomdp.logger.disabled = True
        paynt.quotient.property.logger.disabled = True
        paynt.synthesizer.synthesizer.logger.disabled = True


    def create_belief_node(self, observation):
        num_actions = self.quotient.actions_at_observation[observation]
        return BeliefNode(observation, num_actions)

    
    def predict_action_value(self, state, action, horizon):
        return self.simulated_model.state_action_rollout(state,action,horizon,self.discount_factor)

    def predict_state_value(self, state, horizon):
        num_actions = self.pomdp.get_nr_available_actions(state)
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
            rewards = []
            state = belief_node.sample()
            obs = belief_node.observation
            mem = 0
            for _ in range(self.exploration_horizon):
                action = fsc.suggest_action(mem,obs)
                print("fsc suggests ", action)
                print(" state {} has {} actions".format(state, self.quotient.pomdp.get_nr_available_actions(state)))
                rewards.append(self.simulated_model.state_action_reward(state,action))
                mem = fsc.suggest_update(mem,obs)
                state = self.simulated_model.sample_successor(state,action)
                obs = next_observation = self.simulated_model.state_observation(state)
            path_reward = self.simulated_model.discounted_reward(rewards, self.discount_factor)
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

    def pick_action_play(self, belief_node, fsc, fsc_state=0):
        action_evaluations = [
            action_node.evaluate(self.minimizing)
            for action,action_node in enumerate(belief_node.action_nodes)
        ]
        # print("action values: ", action_evaluations)
        self.total_decisions += 1
        best_action = self.best_action(action_evaluations)
        
        if self.use_fsc_to_play and fsc is not None:
            fsc_action = fsc.suggest_action(0,belief_node.observation)
            fsc_action_value = self.approximate_action_value_fsc(belief_node, fsc)

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

        action_reward = self.simulated_model.state_action_reward(state,action)


        next_state = self.simulated_model.sample_successor(state,action)
        next_observation = self.simulated_model.state_observation(next_state)

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

    
    def build_tree(self, root, action, observation, horizon):

        new_root = None
        
        if action is not None:
            # check if action node has the belief corresponding to this observation
            action_node = root.action_nodes[action]
            if observation not in action_node.belief_nodes:
                # logger.info("observation {} never experienced in simulation, restarting with uniform belief... ".format(observation))
                pass
            else:
                # can reuse the sub-tree
                new_root = action_node.belief_nodes[observation]

        if new_root is None:
            # cannot re-use the sub-tree: use uniform belief over all states
            # with the given observation
            new_root = self.create_belief_node(observation)
            for state in range(self.simulated_model.model.nr_states):
                obs = self.simulated_model.state_observation(state)
                if obs == observation:
                    new_root.add(state)
            self.predict_belief_values(new_root,horizon)

        # nothing to do if only 1 action is available
        if len(new_root.action_nodes) == 1:
            return new_root

        for _ in range(self.exploration_iterations):
            state = new_root.sample()
            self.explore(new_root, state, horizon)
        return new_root


    def collect_relevant_states(self, initial_belief_node):
        state_visits = [0 for state in range(self.pomdp.nr_states)]
        nodes = [initial_belief_node]
        while nodes:
            node = nodes.pop(-1)
            for state in node.particles:
                state_visits[state] += 1
            for action_node in node.action_nodes:
                for belief_node in action_node.belief_nodes.values():
                    nodes.append(belief_node)

        relevant_states = stormpy.storage.BitVector(self.pomdp.nr_states,False)
        for s,v in enumerate(state_visits):
            if v>0:
                relevant_states.set(s)

        # add states in the initial belief
        for state in initial_belief_node.particles:
            relevant_states.set(state)
        
        return relevant_states
    
    def synthesize(self, initial_belief_node):
        relevant_states = self.collect_relevant_states(initial_belief_node)
        self.subpomdp_builder.set_relevant_states(relevant_states)
        
        # approximate values in horizon states
        horizon_states = self.subpomdp_builder.get_horizon_states()
        # print(relevant_states)
        # print(horizon_states)
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

        subpomdp = self.subpomdp_builder.restrict_pomdp(initial_belief, horizon_values)

        self.specification.reset()
        quotient = POMDPQuotientContainer(subpomdp, self.specification)
        memory_size = paynt.quotient.quotient_pomdp.POMDPQuotientContainer.initial_memory_size
        quotient.set_imperfect_memory_size(memory_size)
        synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR(quotient)
        
        # synthesize the FSC
        assignment = synthesizer.synthesize()
        if assignment is None:
            logger.debug("no assignment was found")
            return None
        # note: this assignment is for the sub-POMDP, not for the original POMDP
        # however, since the new sub-POMDP uses a fresh observation, it should be OK
        return FSC.from_hole_assignment(quotient, memory_size, assignment)

    
    def pick_action(self, root, action, fsc_state, current_fsc):
        observation = self.simulated_model.state_observation()
        if self.simulate_fsc and self.use_optimal_fsc:
            action = self.optimal_fsc.suggest_action(fsc_state,observation)
            fsc_state = self.optimal_fsc.suggest_update(fsc_state,observation)
            return root, action, fsc_state, current_fsc
        
        root = self.build_tree(root, action, observation, self.exploration_horizon)

        if (self.simulate_fsc or self.use_fsc_to_play) and not self.use_optimal_fsc:
            new_fsc = self.synthesize(root)
            if new_fsc is not None:
                fsc_state = 0
                current_fsc = new_fsc
        
        if self.simulate_fsc:
            action = current_fsc.suggest_action(fsc_state, observation)
            fsc_state = current_fsc.suggest_update(fsc_state, observation)
            return root, action, fsc_state, current_fsc
        
        action = self.pick_action_play(root, current_fsc)
        return root, action, fsc_state, current_fsc

    
    def run_simulation(self):
        self.simulated_model.reset_simulation()

        accumulated_reward = 0
        root = None
        action = None
        fsc_state = 0
        current_fsc = None
        for depth in range(self.simulation_horizon):
            if self.simulated_model.finished():
                break
            # print("simulation ", depth)
            root, action, fsc_state, current_fsc = self.pick_action(root, action, fsc_state, current_fsc)
            accumulated_reward += self.simulated_model.state_action_reward(self.simulated_model.current_state, action)
            self.simulated_model.simulate_action(action)
        return accumulated_reward
    
    def run(self):

        # do not unfold the pomdp
        self.quotient.set_imperfect_memory_size(1)

        self.simulated_model = SimulatedModel(self.pomdp, self.reward_name)
        # SimulatedModel(self.quotient.pomdp).produce_samples()

        self.discount_factor = 1
        
        self.simulate_fsc = False
        self.use_optimal_fsc = False
        self.use_fsc_to_play = True
        
        self.simulation_iterations = 100
        self.simulation_horizon = 100
        
        self.exploration_iterations = 10
        self.exploration_horizon = 10

        self.exploration_constant_ucb = 10000

        self.total_decisions = 0
        self.actions_same = 0
        self.fsc_better = 0
        self.mcts_better = 0

        # random.seed(42)
        self.subpomdp_builder = stormpy.synthesis.SubPomdpBuilder(self.pomdp, self.reward_name, self.target_label)
        
        if self.use_optimal_fsc:
            memory_size = paynt.quotient.quotient_pomdp.POMDPQuotientContainer.initial_memory_size
            self.quotient.set_imperfect_memory_size(memory_size)
            synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR(self.quotient)
            assignment = synthesizer.synthesize()
            logger.info("synthesized solution with value {}".format(self.quotient.specification.optimality.optimum))
            self.optimal_fsc = FSC.from_hole_assignment(self.quotient, memory_size, assignment)
            self.quotient.set_imperfect_memory_size(1)


        # run simulations
        import progressbar
        bar = progressbar.ProgressBar(maxval=self.simulation_iterations, \
            widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage(), progressbar.AdaptiveETA()])
        bar.start()

        simulation_values = []
        for simulation_iteration in range(self.simulation_iterations):
            simulation_value = self.run_simulation()
            # print(simulation_value)
            simulation_values.append(simulation_value)
            bar.update(simulation_iteration)

        bar.finish()

        simulation_value_avg = numpy.mean(simulation_values)
        # simulation_value_std = numpy.std(simulation_values)

        print("{} simulations: mean value = {}".format(self.simulation_iterations,simulation_value_avg))

        print("MCTS = FSC: {} / {}".format(self.actions_same, self.total_decisions))
        print("FSC is better: {} / {}".format(self.fsc_better, self.total_decisions))
        print("MCTS is better: {} / {}".format(self.mcts_better, self.total_decisions))


        
        