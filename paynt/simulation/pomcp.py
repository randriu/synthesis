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
    
    def get_next_action(self, last_action, current_observation, simulation_step):
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
        self.exploration_iterations = 10
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

    
    
    def reset_tree(self, last_action, current_observation):

        if self.root is None:
            # first call: create belief root corresponding to the initial state
            self.root = self.create_belief_from_state(self.simulated_model.initial_state)
            self.predict_values_at_belief(self.root,self.exploration_horizon)
        else:
            # check if action node has the belief corresponding to this observation
            action_node = self.root.action_nodes[last_action]
            if current_observation not in action_node.belief_nodes:
                # cannot re-use the sub-tree: use uniform belief over all states with the given observation
                # logger.info("observation {} never experienced in simulation, restarting with uniform belief... ".format(current_observation))
                self.root = self.create_empty_belief(current_observation)
                for state in range(self.pomdp.nr_states):
                    obs = self.pomdp.observations[state]
                    if obs == current_observation:
                        self.root.add(state)
                self.predict_values_at_belief(self.root,self.exploration_horizon)
            else:
                # can reuse the sub-tree
                self.root = action_node.belief_nodes[current_observation]

    def get_next_action(self, last_action, current_observation, simulation_step):
        self.reset_tree(last_action, current_observation)
        for _ in range(self.exploration_iterations):
            state = self.root.sample()
            self.explore(self.root, state, self.exploration_horizon)
        return self.pick_action_value(self.root)

        

class FSC:

    def __init__(self, num_nodes, num_observations):
        # self.num_nodes = num_nodes
        # self.num_observations = num_observations
        
        # gamma: NxZ -> Act
        self.action_function = [ [None]*num_observations for _ in range(num_nodes) ]
        # delta: NxZ -> N
        self.update_function = [ [None]*num_observations for _ in range(num_nodes) ]

        self.current_node = 0

    def decide(self, decision_map, node, observation):
        '''
        Make decision using decision_map based on the observation and memory
        node. decision_map is either self.action_function or
        self.update_function
        '''
        decision = decision_map[node][observation]
        if decision is None:
            # default to 0 node
            decision = decision_map[0][observation]
            if decision is None:
                # default to first decision
                decision = 0
        return decision

    def suggest_action(self, observation, node=None):
        if node is None:
            node = self.current_node
        return self.decide(self.action_function, node, observation)

    def suggest_update(self, observation, node=None):
        if node is None:
            node = self.current_node
        return self.decide(self.update_function, node, observation)

    def update_memory_node(self, observation):
        self.current_node = self.suggest_update(observation)


class ActionOracleSubpomdp(ActionOracleMcts):


    def __init__(self, simulated_model, discount_factor, relevant_horizon, specification, reward_name, target_label):
        super().__init__(simulated_model, discount_factor, relevant_horizon)
        self.specification = specification
        self.subpomdp_builder = stormpy.synthesis.SubPomdpBuilder(self.pomdp, reward_name, target_label)
        self.subpomdp_builder.set_discount_factor(discount_factor)
        self.fsc = None


    def predict_fsc_at_belief(self, belief_node, fsc):
        avg_path_reward = 0
        path_rewards = []
        for simulation in range(self.exploration_iterations * 10):
            rewards = []
            state = belief_node.sample()
            obs = belief_node.observation
            mem = fsc.current_node
            for _ in range(self.exploration_horizon):
                action = fsc.suggest_action(obs,mem)
                rewards.append(self.simulated_model.state_action_reward(state,action))
                mem = fsc.suggest_update(obs,mem)
                state = self.simulated_model.sample_successor(state,action)
                obs = self.simulated_model.state_observation(state)
            path_reward = self.simulated_model.discounted_reward(rewards, self.discount_factor)
            path_rewards.append(path_reward)
        return numpy.mean(path_rewards)


    def get_next_action(self, last_action, current_observation, simulation_step):

        if self.fsc is not None and self.root is not None:
            # update FSC state
            self.fsc.update_memory_node(self.root.observation)

        # move the tree root
        self.reset_tree(last_action, current_observation)

        # run MCTS
        for _ in range(self.exploration_iterations):
            state = self.root.sample()
            self.explore(self.root, state, self.exploration_horizon)
        action_mcts = self.pick_action_value(self.root)
        value_mcts = self.root.action_nodes[action_mcts].value

        if simulation_step % 10 == 0:
            # extract sub-POMDP from the tree
            print("\n\n")
            # print(f'running synthesis at step {simulation_step} with threshold {value_mcts}')
            self.fsc = self.synthesize(value_mcts)
        
        action_fsc = self.fsc.suggest_action(self.root.observation)

        action = action_mcts
        value_fsc = self.predict_fsc_at_belief(self.root, self.fsc)
        actions_differ = "x" if action_mcts != action_fsc else "o"
        print(f"{actions_differ} MCTS = {value_mcts}, FSC = {value_fsc}", action_mcts, action_fsc)
        if action_mcts != action_fsc:
            if value_mcts < value_fsc:
                print("choosing FSC action over MCTS")
                action = action_mcts
            

        return action_mcts


    def collect_relevant_states(self, initial_belief_node):

        # state_selection_strategy = "all states"
        state_selection_strategy = "all visited states"
        # state_selection_strategy = "top % of visited states"

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

        if state_selection_strategy == "all states":
            # collect all states
            for state in range(self.pomdp.nr_states):
                relevant_states_set.add(state)

        if state_selection_strategy == "all visited states":
            # collect all visited states
            for state in state_visits.keys():
                relevant_states_set.add(state)
        
        if state_selection_strategy == "top % of visited states":
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

    def construct_subpomdp(self, root):
        initial_distribution = root.distribution()
        relevant_states = self.collect_relevant_states(root)
        self.subpomdp_builder.set_relevant_states(relevant_states)
        frontier_states = self.subpomdp_builder.get_frontier_states()
        state_values = {}
        for state in frontier_states:
            state_values[state] = 0
        subpomdp = self.subpomdp_builder.restrict_pomdp(initial_distribution, state_values)
        return subpomdp

    def synthesize(self, starting_value):

        # looking for FSCs with this many memory nodes
        memory_size = 2

        # construct the subpomdp with the discount transformation already applied
        subpomdp = self.construct_subpomdp(self.root)

        num_treasures = 0
        rm = subpomdp.reward_models[self.simulated_model.reward_name]
        for state in range(subpomdp.nr_states):
            row0 = subpomdp.transition_matrix.get_row_group_start(state) 
            reward = rm.state_action_rewards[row0]
            if reward > 0:
                num_treasures += 1
        print(f"sub-POMDP contains {num_treasures} treasure(s)")

        # print(su.reward_models['rew'].state_action_rewards)
        # print(subpomdp.initial_states)

        # setting the specification threshold to accelerate the synthesis
        # self.specification.optimality.update_optimum(starting_value)

        # construct the coloring
        quotient = POMDPQuotientContainer(subpomdp, self.specification)
        quotient.set_imperfect_memory_size(memory_size)
        synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR(quotient)
        
        # synthesize the FSC
        assignment = synthesizer.synthesize()
        if assignment is None:
            logger.debug("no assignment was found, picking arbitrary assignment")
            assignment = quotient.design_space.pick_any()
        else:
            print("synthesized assignment with value ", self.specification.optimality.optimum)

        

        # note: this assignment is for the sub-POMDP, not for the original POMDP; however, the new sub-POMDP does not
        # store observation valuations, so the hole names will refer to the index observation; since the sub-POMDP uses
        # a fresh observation, the indices for old observation should coincide
        # print(assignment)
        fsc = FSC(memory_size, subpomdp.nr_observations)
        for hole in assignment:
            option = hole.options[0]
            is_action_hole, observation, node = quotient.decode_hole_name(hole.name)
            if is_action_hole:
                fsc.action_function[node][observation] = option
            else:
                fsc.update_function[node][observation] = option

        # simulate the choice of the initial state and make the corresponding step in the FSC
        action = fsc.suggest_action(self.pomdp.nr_observations)
        assert action == 0
        fsc.update_memory_node(self.pomdp.nr_observations)

        # fsc is now ready for simulation
        value_fsc = self.predict_fsc_at_belief(self.root, fsc)
        print(f"value at current belief: {value_fsc}")

        if abs(value_fsc - self.specification.optimality.optimum) > 1:

            exit()

        # resetting specification threshold for the subsequent syntheses
        self.specification.reset()

        return fsc






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

            if self.simulated_model.state_action_reward(self.simulated_model.current_state,0) > 0:
                print("*** found the treasure ***")

            if self.simulated_model.finished():
                print("simulation finished in absorbing state ", self.simulated_model.current_state)
                break
            action = action_oracle.get_next_action(last_action, self.simulated_model.state_observation(), simulation_step)
            reward = self.simulated_model.state_action_reward(self.simulated_model.current_state, action)
            accumulated_reward += discount_factor_to_k * reward
            discount_factor_to_k *= discount_factor
            self.simulated_model.simulate_action(action)
            last_action = action
        return accumulated_reward


    def run(self):

        random.seed(12)

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
        action_oracle = ActionOracleSubpomdp(self.simulated_model, discount_factor, relevant_horizon, self.specification, self.reward_name, self.target_label)

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


