import stormpy
import payntbind

import paynt
import paynt.quotient.quotient

import logging
logger = logging.getLogger(__name__)


class DecPomdpQuotient(paynt.quotient.quotient.Quotient):

    def __init__(self, decpomdp_manager, specification):
        super().__init__(specification = specification)

        self.initial_memory_size = 4; #TODO Must take this from paynt

        assert decpomdp_manager.num_agents > 1

        self.decpomdp_manager = decpomdp_manager

        self.agent_observation_labels = decpomdp_manager.agent_observation_labels
        # # print("self.agent_observation_labels",self.agent_observation_labels)

        self.agent_action_labels = decpomdp_manager.agent_action_labels
        # # print("self.agent_action_labels",self.agent_action_labels)

        self.joint_actions = decpomdp_manager.joint_actions
        # # print("self.joint_actions",self.joint_actions)


        # self.transition_matrix = decpomdp_manager.transition_matrix
        # # print("self.transition_matrix",self.transition_matrix[4])

        self.nr_agents = decpomdp_manager.num_agents
        # # print("self.nr_agents",self.nr_agents)

        # for each joint observation contains observation of each agent
        self.joint_observations = decpomdp_manager.joint_observations
        # print("self.joint_observations",self.joint_observations)

        self.row_joint_action = decpomdp_manager.row_joint_action
        # # print("self.row_joint_action",self.row_joint_action)

        self.nr_states = len(self.row_joint_action)
        # # print("self.nr_states",self.nr_states)

        # self.nr_joint_actions = len(self.joint_actions)
        # # print("self.nr_joint_actions",self.nr_joint_actions)

        self.nr_joint_observations = len(self.joint_observations)
        # # print("self.nr_joint_observations",self.nr_joint_observations)

        self.state_joint_observation = decpomdp_manager.state_joint_observation
        # # print("self.state_joint_observation",self.state_joint_observation)

        self.nr_agent_observations = [len(observation) for observation in self.agent_observation_labels]
        # # print("self.nr_agent_observations",self.nr_agent_observations)

        # self.num_rows = decpomdp_manager.num_rows()
        # # print("self.num_rows",self.num_rows)

        # self. = decpomdp_manager.
        # print("self.",self.)

        # self. = decpomdp_manager.
        # print("self.",self.)


        # for each aget: for each state contains observation
        self.agent_state_observation = [0] * self.nr_agents
        for agent in range(self.nr_agents): 
            observations_for_state = [0] * self.nr_states
            for state in range(self.nr_states):
                observation = self.state_joint_observation[state]
                observations_for_state[state] = self.joint_observations[observation][agent]
            self.agent_state_observation[agent] = observations_for_state
        # print("self.agent_state_observation",self.agent_state_observation)

        # # # compute joint actions available at each observation
        # # self.joint_actions_at_observation = [0] * len(self.joint_observations)
        # # for state in range(self.nr_states):
        # #     obs = self.state_joint_observation[state]
        # #     if self.joint_actions_at_observation[obs] != 0:
        # #         continue
        # #     self.joint_actions_at_observation[obs] = len(self.row_joint_action[state])
        # # print("self.joint_actions_at_observation",self.joint_actions_at_observation)

        # # assign joint observations to agent observations
        self.joint_observations_to_agent_observation = [0] * self.nr_agents
        for agent in range(self.nr_agents): 
            agent_observations = [0] * len(self.joint_observations)
            for state in range(self.nr_states):
                obs = self.state_joint_observation[state]
                if agent_observations[obs] != 0:
                    continue
                agent_observations[obs] = self.agent_state_observation[agent][state]
            self.joint_observations_to_agent_observation[agent] = agent_observations
        # print("self.joint_observations_to_agent_observation",self.joint_observations_to_agent_observation)


        # # compute number of actions available at each agent observation for each agent 
        self.nr_agent_actions_at_observation = [0] * self.nr_agents
        for agent in range(self.nr_agents): 
            labels = [0] * self.nr_agent_observations[agent]
            for state in range(self.nr_states):
                obs = self.agent_state_observation[agent][state]
                # print("obs",obs)
                if labels[obs] != 0:
                    continue
                actions = self.row_joint_action[state]
                labels[obs] = len(list(set(map(lambda x: self.joint_actions[x][agent] , actions))))
            self.nr_agent_actions_at_observation[agent] = labels
        # print("self.nr_agent_actions_at_observation",self.nr_agent_actions_at_observation)

        # get labels of actions available at each observation for each agent 
        self.agent_labels_actions_at_observation = [0] * self.nr_agents
        for agent in range(self.nr_agents): 
            labels = [0] * self.nr_agent_observations[agent]
            for state in range(self.nr_states):
                obs = self.agent_state_observation[agent][state]
                if labels[obs] != 0:
                    continue
                actions = self.row_joint_action[state]
                labels[obs] = list(set(map(lambda x: self.agent_action_labels[agent][self.joint_actions[x][agent]] , actions)))
            self.agent_labels_actions_at_observation[agent] = labels

        # print("self.agent_labels_actions_at_observation",self.agent_labels_actions_at_observation)


        # do initial unfolding
        
        self.set_imperfect_memory_size(self.initial_memory_size)














        logger.info(f"dec-POMDP has {self.decpomdp_manager.num_agents} agents")
        self.decpomdp_manager.set_global_memory_size(4) #must be power of the number n and exponent must be number of egents
        self.quotient = self.decpomdp_manager.construct_quotient_mdp()
        print("MDP has {} states".format(self.quotient.nr_states))
        print("transitions from state 1: ", self.quotient.transition_matrix.get_row(1))
        logger.debug("nothing to do, aborting.....")
        exit()
        

        

    def create_hole_name(self,agent, obs, mem, is_action_hole):
        category = "A" if is_action_hole else "M"
        obs_label = self.agent_observation_labels[agent][obs]
        return "{}({},{},{})".format(category,agent,obs_label,mem)

    def set_imperfect_memory_size(self, memory_size):
        ''' Set given memory size only to imperfect observations. '''
        self.observation_memory_size = [0] * self.nr_agents
        for agent in range(self.nr_agents): 
            agent_obs_mem_size = [memory_size for obs in range(self.nr_agent_observations[agent])]
            agent_obs_mem_size[-1:] = [1] # this is for discount state
            self.observation_memory_size[agent] = agent_obs_mem_size
        # print("self.observation_memory_size",self.observation_memory_size)

        self.set_manager_memory_vector()
        # self.unfold_memory()

    def set_manager_memory_vector(self):
        mem = pow( self.initial_memory_size , self.nr_agents) 
        self.decpomdp_manager.set_global_memory_size(mem)