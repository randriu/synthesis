import stormpy
import payntbind

import paynt
import paynt.quotient.quotient

import logging
logger = logging.getLogger(__name__)


class DecPomdpQuotient(paynt.quotient.quotient.Quotient):

    def __init__(self, decpomdp_manager, specification):
        super().__init__(specification = specification)

        self.initial_memory_size = 2; #TODO Must take this from paynt

        assert decpomdp_manager.num_agents > 1

        self.decpomdp_manager = decpomdp_manager

        self.agent_observation_labels = decpomdp_manager.agent_observation_labels
        # # print("self.agent_observation_labels",self.agent_observation_labels)

        self.agent_action_labels = decpomdp_manager.agent_action_labels
        print("self.agent_action_labels",self.agent_action_labels)

        self.joint_actions = decpomdp_manager.joint_actions
        print("self.joint_actions",self.joint_actions)


        self.transition_matrix = decpomdp_manager.transition_matrix
        print("self.transition_matrix",self.transition_matrix)

        self.nr_agents = decpomdp_manager.num_agents
        # # print("self.nr_agents",self.nr_agents)

        # for each joint observation contains observation of each agent
        self.joint_observations = decpomdp_manager.joint_observations
        # print("self.joint_observations",self.joint_observations)

        self.row_joint_action = decpomdp_manager.row_joint_action
        # print("self.row_joint_action",self.row_joint_action)

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

        # self.transition_matrix_dpomdp = decpomdp_manager.transition_matrix
        # print("self.transition_matrix_dpomdp",self.transition_matrix_dpomdp)


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














        # logger.info(f"dec-POMDP has {self.decpomdp_manager.num_agents} agents")
        # self.decpomdp_manager.set_global_memory_size(1) #must be power of the number n and exponent must be number of egents
        # self.quotient = self.decpomdp_manager.construct_quotient_mdp()
        # print("MDP has {} states".format(self.quotient.nr_states))
        print("transition matrix: ", self.quotient_mdp.transition_matrix)
        # logger.debug("nothing to do, aborting.....")
        # exit()
        

        

    def create_hole_name(self,agent, obs, mem, is_action_hole):
        category = "A" if is_action_hole else "M"
        obs_label = self.agent_observation_labels[agent][obs]
        return "{}({},{},{})".format(category,agent,obs_label,mem)

    def set_imperfect_memory_size(self, memory_size):
        ''' Set given memory size only to imperfect observations. '''
        self.agent_observation_memory_size = [0] * self.nr_agents
        for agent in range(self.nr_agents): 
            agent_obs_mem_size = [memory_size for obs in range(self.nr_agent_observations[agent])]
            agent_obs_mem_size[-1:] = [1] # this is for discount state
            self.agent_observation_memory_size[agent] = agent_obs_mem_size
        # print("self.observation_memory_size",self.observation_memory_size)

        self.set_manager_memory_vector()
        self.unfold_memory()

    def set_manager_memory_vector(self):
        mem = pow( self.initial_memory_size , self.nr_agents) 
        # logger.debug(f"memory of every state of quotient mdp was set to  {mem}.")
        self.decpomdp_manager.set_global_memory_size(mem)

    def unfold_memory(self):
        
        # reset attributes
        self.quotient_mdp = None
        self.coloring = None
        self.state_to_holes = None
        self.hole_option_to_actions = None
        
        self.observation_action_holes = None
        self.observation_memory_holes = None
        self.is_action_hole = None
        
       
        self.quotient_mdp = self.decpomdp_manager.construct_quotient_mdp()
        self.choice_destinations = payntbind.synthesis.computeChoiceDestinations(self.quotient_mdp)
        # logger.debug(f"constructed quotient MDP having {self.quotient_mdp.nr_states} states and {self.quotient_mdp.nr_choices} actions.")

        family, choice_to_hole_options = self.create_coloring()
       

        self.coloring = payntbind.synthesis.Coloring(family.family, self.quotient_mdp.nondeterministic_choice_indices, choice_to_hole_options)
        self.state_to_holes = self.coloring.getStateToHoles().copy()

        # to each hole-option pair a list of actions colored by this combination
        self.hole_option_to_actions = [[] for hole in range(family.num_holes)]
        for hole in range(family.num_holes):
            self.hole_option_to_actions[hole] = [[] for option in family.hole_options(hole)]
        for choice in range(self.quotient_mdp.nr_choices):
            for hole,option in choice_to_hole_options[choice]:
                # print("option",option)
                # print("hole",hole)
                self.hole_option_to_actions[hole][option].append(choice)

        self.design_space = paynt.family.family.DesignSpace(family)
        # print("self.design_space ",self.design_space )

    def create_coloring(self):

        # short aliases
        pm = self.decpomdp_manager
        mdp = self.quotient_mdp

        # create holes
        all_holes = paynt.family.family.Family()
        self.observation_action_holes = []
        self.observation_memory_holes = []
        self.is_action_hole = []

        for agent in range(self.nr_agents): 
            for obs in range(self.nr_agent_observations[agent]):
                
                # action holes
                hole_indices = []
                num_actions = self.nr_agent_actions_at_observation[agent][obs]
                if num_actions > 1:
                    option_labels = [str(labels) for labels in self.agent_labels_actions_at_observation[agent][obs]]
                    for mem in range(self.agent_observation_memory_size[agent][obs]):
                        hole_indices.append(all_holes.num_holes)
                        name = self.create_hole_name(agent,obs,mem,True)
                        all_holes.add_hole(name,option_labels)
                        self.is_action_hole.append(True)
                self.observation_action_holes.append(hole_indices)

                # memory holes
                hole_indices = []
                num_updates = pow(pm.max_successor_memory_size[obs], 1 / self.nr_agents)
                if num_updates > 1:
                    option_labels = [str(x) for x in range(int(num_updates))]
                    for mem in range(self.agent_observation_memory_size[agent][obs]):
                        name = self.create_hole_name(agent,obs,mem,False)
                        hole_indices.append(all_holes.num_holes)
                        all_holes.add_hole(name,option_labels)
                        self.is_action_hole.append(False)
                    self.observation_memory_holes.append(hole_indices)


        # create the coloring
        choice_to_hole_options = []
        
        for action in range(mdp.nr_choices):
            hole_options = []
            for agent in range(self.nr_agents): 
                h = pm.row_action_hole[agent][action]
                if h != pm.num_holes:
                    hole_options.append( (h,pm.row_action_option[agent][action]) )
                h = pm.row_memory_hole[agent][action]
                if h != pm.num_holes:
                    hole_options.append( (h,pm.row_memory_option[agent][action]) )
            choice_to_hole_options.append(hole_options)
        # logger.info(f"choice_to_hole_options is: {choice_to_hole_options}")
        # logger.info(f"pm.row_action_hole is: {pm.row_action_hole}")
        print("all_holes",all_holes)
        print("choice_to_hole_options",choice_to_hole_options)

        return all_holes, choice_to_hole_options