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

# --- simulation parameters ---
simulation_iterations = 100
discount_factor = 0.9
precision = 1e-1

# action_oracle_type = "random"
# action_oracle_type = "mcts"
action_oracle_type = "fsc"


# --- MCTS parameters ---
exploration_iterations = 20
exploration_constant_ucb = 10000
mcts_rollouts = True


# --- FSC parameters ---
only_synthesis = False

fsc_recomputation_frequency = 10
fsc_rollouts = False
fsc_use_cache = True
memory_size = 2

# observation_selection = "all observations"
observation_selection = "visited observations"

# action_selection = "only MCTS"
# action_selection = "only FSC"
action_selection = "MCTS or FSC"


class Maze:
    
    def __init__(self, pomdp):
        # get state coordinates, get max coordinates
        self.pomdp = pomdp
        self.state_x = []
        self.state_y = []
        for state in range(self.num_states):
            json = pomdp.state_valuations.get_json(state)
            self.state_x.append(int(json["x"]))
            self.state_y.append(int(json["y"]))
        
        # store maze structure
        self.maze = []
        for x in range(self.max_x+1):
            x_column = [" " for y in range(self.max_y+1)]
            self.maze.append(x_column)
        for state in range(pomdp.nr_states):
            x,y = self.xy(state)
            self.maze[x][y] = "."

        # identify init & checkpoints
        for state in range(pomdp.nr_states):
            obs = pomdp.observations[state]
            json = pomdp.observation_valuations.get_json(obs)
            if json["treasure"] == 1:
                x,y = self.xy(state)
                self.maze[x][y] = "t"

        for state in pomdp.initial_states:
            x,y = self.xy(state)
            self.maze[x][y] = "i"

    @property
    def num_states(self):
        return self.pomdp.nr_states

    @property
    def max_x(self):
        return max(self.state_x)

    @property
    def max_y(self):
        return max(self.state_y)
    
    def xy(self, state):
        x = self.state_x[state]
        y = self.state_y[state]
        return x,y

    def to_string(self, maze):
        s = ""
        for y in range(self.max_y,-1,-1):
            for x in range(0,self.max_x+1):
                s += maze[x][y]
            s += "\n"
        return s

    def __str__(self):
        return self.to_string(self.maze)

    def print(self):
        print(self)
        
    def print_relevant(self, relevant_states):
        maze = []
        for x in range(self.max_x+1):
            x_column = [self.maze[x][y] for y in range(self.max_y+1)]
            maze.append(x_column)
        for state in relevant_states:
            x,y = self.xy(state)
            maze[x][y] = "x"
        print(self.to_string(maze))

    
        

class ActionOracleRandom:
    def __init__(self, pomcp):
        self.pomcp = pomcp

    @property
    def pomdp(self):
        return self.pomcp.pomdp

    @property
    def discount_factor(self):
        return self.pomcp.discount_factor

    @property
    def simulated_model(self):
        return self.pomcp.simulated_model

    def reset(self):
        pass # left intentionally blank
    
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


class ActionOracleMcts(ActionOracleRandom):
    
    def __init__(self, pomcp):
        super().__init__(pomcp)
        
        # MCTS parameters
        self.exploration_iterations = exploration_iterations
        self.exploration_horizon = self.pomcp.effective_horizon
        self.exploration_constant_ucb = exploration_constant_ucb

        self.actions_at_observation = [0] * self.pomdp.nr_observations
        for state in range(self.pomdp.nr_states):
            obs = self.pomdp.observations[state]
            num_actions = self.pomdp.get_nr_available_actions(state)
            self.actions_at_observation[obs] = num_actions

    
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
            # MCTS rollouts
            value = 0
            if mcts_rollouts:
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


    def __init__(self, pomcp):
        super().__init__(pomcp)
        self.subpomdp_builder = stormpy.synthesis.SubPomdpBuilder(self.pomdp, self.pomcp.reward_name, self.pomcp.target_label)
        self.subpomdp_builder.set_discount_factor(self.discount_factor)
        self.fsc = None

        self.num_decisions = 0
        self.decisions_same = 0
        self.decisions_different = 0
        self.decisions_mcts = 0
        self.decisions_fsc = 0

        # collect labels of actions available at each observation
        self.action_labels_at_observation = [None for obs in range(self.pomdp.nr_observations)]
        for state in range(self.pomdp.nr_states):
            obs = self.pomdp.observations[state]
            if self.action_labels_at_observation[obs] is not None:
                continue
            actions = self.pomdp.get_nr_available_actions(state)
            self.action_labels_at_observation[obs] = []
            for offset in range(actions):
                choice = self.pomdp.get_choice_index(state,offset)
                labels = self.pomdp.choice_labeling.get_labels_of_choice(choice)
                self.action_labels_at_observation[obs].append(str(labels))


    def reset(self):
        super().reset()
        self.cache_reset()

    def construct_trivial_policy_values(self):
        return collections.defaultdict(int)
    
    def cache_reset(self):
        ''' Fill state-memory-action cache with zeroes. '''
        if not fsc_use_cache:
            return
        self.policy_values = []
        trivial_values = self.construct_trivial_policy_values()
        self.policy_values.append(trivial_values)
        

    def cache_update(self, quotient, assignment):
        ''' Use assignment and the corresponding FSC to update the state-memory-action cache. '''
        if not fsc_use_cache:
            return
        
        # model check the DTMC induced by this assignment to get state valuations
        dtmc = quotient.build_chain(assignment)
        mc_result = dtmc.check_specification(quotient.specification)
        dtmc_state_values = mc_result.optimality_result.result.get_values()

        policy_values = [self.construct_trivial_policy_values() for memory in range(memory_size)]

        # map states of a DTMC to states of its quotient to states of a sub-POMDP to states of the POMDP
        for state_dtmc,value in enumerate(dtmc_state_values):
            if value < 1e-4:
                continue
            quotient_state = dtmc.quotient_state_map[state_dtmc]
            subpomdp_state = quotient.pomdp_manager.state_prototype[quotient_state]
            pomdp_state = self.subpomdp_builder.state_sub_to_full[subpomdp_state]
            memory = quotient.pomdp_manager.state_memory[quotient_state]
            policy_values[memory][pomdp_state] = value

        self.policy_values += policy_values
        # print(len(self.policy_values))

    def cache_apply(self, quotient):
        ''' Modify rewards of the frontier states. '''
        if not fsc_use_cache:
            return

        # for each frontier observation, pick exactly 1 policy
        frontier_states = self.subpomdp_builder.frontier_states
        frontier_map = {}
        for state in frontier_states:
            obs = self.pomdp.observations[state]
            if obs not in frontier_map:
                frontier_map[obs] = []
            frontier_map[obs].append(state)

        state_values = {}
        num_policies = len(self.policy_values)
        for obs,states in frontier_map.items():
            assert states
            best_policy = 0
            best_score = sum([self.policy_values[0][state] for state in states])
            for policy in range(1,num_policies):
                score = sum([self.policy_values[policy][state] for state in states])
                if score > best_score:
                    best_policy = policy
                    best_score = score
            for state in states:
                state_values[state] = self.policy_values[best_policy][state]

        tm = quotient.quotient_mdp.transition_matrix
        state_action_rewards = quotient.quotient_mdp.reward_models[self.simulated_model.reward_name].state_action_rewards
        for quotient_state in range(quotient.quotient_mdp.nr_states):
            subpomdp_state = quotient.pomdp_manager.state_prototype[quotient_state]
            pomdp_state = self.subpomdp_builder.state_sub_to_full[subpomdp_state]
            if pomdp_state not in frontier_states:
                continue
            value = state_values[pomdp_state]
            if value == 0:
                continue
            row = quotient.quotient_mdp.get_choice_index(quotient_state,0)
            immediate_reward = state_action_rewards[tm.get_row_group_start(quotient_state)]
            print("{} -> {}".format(immediate_reward,value))
            for choice in range (tm.get_row_group_start(quotient_state),tm.get_row_group_start(quotient_state+1)):
                state_action_rewards[choice] = value


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
            # update FSC state using new observation
            self.fsc.update_memory_node(self.root.observation)

        # move the tree root
        self.reset_tree(last_action, current_observation)

        # run MCTS
        for _ in range(self.exploration_iterations):
            state = self.root.sample()
            self.explore(self.root, state, self.exploration_horizon)
        action_mcts = self.pick_action_value(self.root)
        value_mcts = self.root.action_nodes[action_mcts].value

        if simulation_step % fsc_recomputation_frequency == 0:
            # extract sub-POMDP from the tree
            # print("\n")
            self.fsc = self.synthesize(value_mcts)
        
        action_fsc = self.fsc.suggest_action(self.root.observation)

        self.num_decisions += 1

        best_action = action_mcts
        value_fsc = self.predict_fsc_at_belief(self.root, self.fsc)
        actions_differ = "x" if action_mcts != action_fsc else "o"
        # print(f"{actions_differ} MCTS = {value_mcts}, FSC = {value_fsc}", action_mcts, action_fsc)
        if action_mcts == action_fsc:
            self.decisions_same += 1
        else:
            self.decisions_different += 1
            if value_mcts > value_fsc:
                self.decisions_mcts += 1
            else:
                self.decisions_fsc += 1
                best_action = action_fsc
                # print("choosing FSC action over MCTS")
            

        if action_selection == "only MCTS":
            return action_mcts
        if action_selection == "only FSC":
            return action_fsc
        if action_selection == "MCTS or FSC":
            return best_action


    def collect_relevant_observations(self, initial_belief_node):
        ''' Collect observations relevant to the tree starting in the provided node. '''
        relevant_observations = stormpy.storage.BitVector(self.pomdp.nr_observations,False)
        
        if observation_selection == "all observations":
            for obs in range(self.pomdp.nr_observations):
                relevant_observations.set(obs,True)

        if observation_selection == "visited observations":
            # traverse the MC tree
            nodes = [initial_belief_node]
            while nodes:
                node = nodes.pop(-1)
                relevant_observations.set(node.observation,True)
                for action_node in node.action_nodes:
                    for belief_node in action_node.belief_nodes.values():
                        nodes.append(belief_node)

        assert relevant_observations[initial_belief_node.observation]
        return relevant_observations



    def construct_subpomdp_quotient(self, root, specification):
        # construct the subpomdp with the discount transformation already applied
        relevant_observations = self.collect_relevant_observations(root)
        initial_distribution = root.distribution()
        self.subpomdp_builder.set_relevant_observations(relevant_observations, initial_distribution)
        subpomdp = self.subpomdp_builder.restrict_pomdp(initial_distribution)

        # show relevant cells
        # self.pomcp.maze.print_relevant(self.subpomdp_builder.relevant_states)

        # unfold the sub-POMDP
        quotient = POMDPQuotientContainer(subpomdp, specification)
        quotient.set_imperfect_memory_size(memory_size)
        self.cache_apply(quotient)

        return quotient

    def assignment_to_fsc(self, quotient, assignment):
        # translate the hole assignment to the FSC
        # note: this assignment is for the sub-POMDP, not for the original POMDP; however, the new sub-POMDP does not
        # store observation valuations, so the hole names will refer to the index observation; since the sub-POMDP uses
        # a fresh observation, the indices for old observation should coincide
        num_observations_subpomdp = self.pomdp.nr_observations + 1

        # however, the quotient for the sub-POMDP made it canonic, i.e. rearranged its actions; thus, we need to
        # interpret the assignment using choice labels
        fsc = FSC(memory_size, num_observations_subpomdp)
        for hole in assignment:
            option = hole.options[0]
            option_label = hole.option_labels[option]
            is_action_hole, observation, node = quotient.decode_hole_name(hole.name)
            if is_action_hole:
                # find the index of the action that has this option label
                action_set = False
                for action,label in enumerate(self.action_labels_at_observation[observation]):
                    if label == option_label:
                        fsc.action_function[node][observation] = action
                        action_set = True
                        break
                assert action_set
            else:
                fsc.update_function[node][observation] = option

        return fsc
    
    def analyze_subpomdp(self, root, specification):
        
        # construct the sub-POMDP, unfold and color it
        quotient = self.construct_subpomdp_quotient(root, specification)

        # synthesize the FSC for this sub-POMDP
        synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR(quotient)
        assignment = synthesizer.synthesize()
        if assignment is None:
            logger.debug("no assignment was found, picking arbitrary assignment")
            assignment = quotient.design_space.pick_any()
        else:
            # print("synthesized assignment with value ", specification.optimality.optimum)
            pass

        fsc = self.assignment_to_fsc(quotient,assignment)
        self.cache_update(quotient,assignment)

        return fsc

    def synthesize(self, starting_value):

        # warm synthesis start
        # self.pomcp.specification.optimality.update_optimum(starting_value)

        # synthesize an FSC using states from the MC tree
        fsc = self.analyze_subpomdp(self.root, self.pomcp.specification)
        
        # simulate the choice of the initial state and make the corresponding step in the FSC
        action = fsc.suggest_action(self.pomdp.nr_observations)
        assert action == 0
        fsc.update_memory_node(self.pomdp.nr_observations)

        # double-check the FSC value
        value_fsc = self.predict_fsc_at_belief(self.root, fsc)
        if abs(value_fsc - self.pomcp.specification.optimality.optimum) > 0.01:
            # print(f"value at current belief: {value_fsc}")
            pass
            # exit()

        # resetting specification threshold for the subsequent syntheses
        self.pomcp.specification.reset()

        return fsc






class POMCP:
    
    def __init__(self, quotient):
        self.pomdp = quotient.pomdp
        self.specification = quotient.specification
        self.discount_factor = discount_factor # PARAM
        
        invalid_spec_msg = "expecting a single maximizing reward property"
        assert self.specification.is_single_property, invalid_spec_msg
        assert len(self.specification.constraints) == 0, invalid_spec_msg
        opt = self.specification.optimality
        assert opt.reward, invalid_spec_msg
        assert opt.maximizing, invalid_spec_msg
        
        self.reward_name = opt.formula.reward_name
        self.max_reward = max(self.pomdp.get_reward_model(self.reward_name).state_action_rewards)
        self.target_label = str(opt.formula.subformula.subformula)
        assert self.pomdp.labeling.contains_label(self.target_label),\
            "formula must contain reachability wrt a simple label"

        self.simulated_model = SimulatedModel(self.pomdp, self.reward_name)
        self.effective_horizon = None
        if discount_factor < 1:
            # max horizon is ln(eps*(1-d)/Rmax) / ln(d)
            self.effective_horizon = math.floor(
                math.log(precision*(1-discount_factor) / self.max_reward) /
                math.log(discount_factor)
                )
        print("effective horizon for discount factor {} and precision {} is {}".format(
            discount_factor,precision,self.effective_horizon
        ))

        if only_synthesis:
            subpomdp_builder = stormpy.synthesis.SubPomdpBuilder(self.pomdp, self.reward_name, self.target_label)
            subpomdp_builder.set_discount_factor(discount_factor)
            relevant_observations = stormpy.storage.BitVector(self.pomdp.nr_observations,True)
            initial_distribution = {self.simulated_model.initial_state : 1}
            subpomdp_builder.set_relevant_observations(relevant_observations, initial_distribution)
            subpomdp = subpomdp_builder.restrict_pomdp(initial_distribution)
            quotient = POMDPQuotientContainer(subpomdp, self.specification)
            quotient.set_imperfect_memory_size(memory_size)
            synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR(quotient)
            assignment = synthesizer.synthesize()
            print("synthesized assignment with value ", self.specification.optimality.optimum)
            exit()

        # disable synthesis logging
        paynt.quotient.quotient_pomdp.logger.disabled = True
        paynt.quotient.property.logger.disabled = True
        paynt.synthesizer.synthesizer.logger.disabled = True


    def run_simulation(self, simulation_horizon, action_oracle):
        self.simulated_model.reset()
        action_oracle.reset()

        last_action = None
        accumulated_reward = 0
        discount_factor_to_k = 1
        for simulation_step in range(simulation_horizon):

            if self.simulated_model.finished():
                # print("simulation finished in absorbing state ", self.simulated_model.current_state)
                break
            action = action_oracle.get_next_action(last_action, self.simulated_model.state_observation(), simulation_step)
            reward = self.simulated_model.state_action_reward(self.simulated_model.current_state, action)
            accumulated_reward += discount_factor_to_k * reward
            discount_factor_to_k *= discount_factor
            self.simulated_model.simulate_action(action)
            last_action = action
        return accumulated_reward


    

    def run(self):

        # random.seed(6)

        self.maze = Maze(self.pomdp)
        self.maze.print()

        # action oracle
        if action_oracle_type == "random":
            action_oracle = ActionOracleRandom(self)
        if action_oracle_type == "mcts":
            action_oracle = ActionOracleMcts(self)
        if action_oracle_type == "fsc":
            action_oracle = ActionOracleSubpomdp(self)

        # run simulations
        simulation_horizon = self.effective_horizon
        import progressbar
        bar = progressbar.ProgressBar(maxval=simulation_iterations, \
            widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage(), progressbar.AdaptiveETA()])
        bar.start()
        simulation_values = []
        for simulation_iteration in range(simulation_iterations):
            simulation_value = self.run_simulation(simulation_horizon, action_oracle)
            simulation_values.append(simulation_value)
            bar.update(simulation_iteration)
        bar.finish()

        simulation_value_avg = numpy.mean(simulation_values)
        # simulation_value_std = numpy.std(simulation_values)

        print("{} simulations: mean value = {}".format(simulation_iterations,simulation_value_avg))

        if isinstance(action_oracle, ActionOracleSubpomdp):
            print("total ({}) = same ({}) + different ({})".format(action_oracle.num_decisions, action_oracle.decisions_same, action_oracle.decisions_different))
            print("different ({}) = mcts ({}) + fsc ({})".format(action_oracle.decisions_different, action_oracle.decisions_mcts, action_oracle.decisions_fsc))


