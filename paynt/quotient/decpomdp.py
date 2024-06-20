import stormpy
import payntbind

import paynt
import paynt.quotient.quotient

import logging
logger = logging.getLogger(__name__)

class DecPomdpQuotient(paynt.quotient.quotient.Quotient):

    # implicit initial FSC size
    initial_memory_size = 1

    def __init__(self, decpomdp_manager, specification):
        super().__init__(specification = specification)

        assert decpomdp_manager.num_agents > 1

        self.decpomdp_manager = decpomdp_manager

        # for each agent a (simplified) label for each observation
        self.agent_observation_labels = decpomdp_manager.agent_observation_labels
        # for each agent its action labels
        self.agent_action_labels = decpomdp_manager.agent_action_labels
        # number of agent in the model
        self.nr_agents = decpomdp_manager.num_agents
        # for each joint observation contains observation of each agent
        self.joint_observations = decpomdp_manager.joint_observations
        # for each state its corresponding joint observation index
        self.state_joint_observation = decpomdp_manager.state_joint_observation
        # for each agent the number of its observations
        self.nr_agent_observations = [len(observation) for observation in self.agent_observation_labels]
        # number of states in the dec-pomdp model
        self.nr_states = decpomdp_manager.num_decpomdp_states()
        # for each agent number of states with the given observation
        self.agent_observation_states = None
        # for each agent and each observation the size of the memory, this is used to set the memory in the quotient
        self.agent_observation_memory_size = [[] for _ in range(self.nr_agents)]
        # for each agent the number of available actions at given observation
        self.num_agent_actions_at_observation = decpomdp_manager.num_agent_actions_at_observation

        # for each hole, an indication whether this is an action or a memory hole
        self.is_action_hole = None

        # mark perfectly observable states for each agent
        self.agent_observation_states = [[0 for obs in range(self.nr_agent_observations[agent])] for agent in range(self.nr_agents)]
        for state in range(self.nr_states):
            joint_observation = self.state_joint_observation[state]
            for agent in range(self.nr_agents):
                agent_obs = self.joint_observations[joint_observation][agent]
                self.agent_observation_states[agent][agent_obs] += 1
                
        # do initial unfolding
        self.set_imperfect_memory_size(DecPomdpQuotient.initial_memory_size)
        

    def create_hole_name(self, agent, obs, mem, is_action_hole):
        category = "A" if is_action_hole else "M"
        obs_label = self.agent_observation_labels[agent][obs]
        return "{}({},{},{})".format(category,agent,obs_label,mem)

    def set_imperfect_memory_size(self, memory_size):
        ''' Set given memory size only to imperfect observations. '''
        for agent in range(self.nr_agents):
            agent_memory = [memory_size if self.agent_observation_states[agent][obs] > 1 else 1 for obs in range(self.nr_agent_observations[agent])]
            self.agent_observation_memory_size[agent] = agent_memory

        self.set_manager_memory_vector()
        self.unfold_memory()

    def set_agent_imperfect_memory_size(self, agent, memory_size):
        ''' Set given memory size only to imperfect observations of given agent. '''
        assert agent in range(self.nr_agents), "given agent index is larger than number of agents"

        agent_memory = [memory_size if self.agent_observation_states[agent][obs] > 1 else 1 for obs in range(self.nr_agent_observations[agent])]
        self.agent_observation_memory_size[agent] = agent_memory

        self.set_manager_memory_vector()
        self.unfold_memory()

    def set_manager_memory_vector(self):
        for agent, agent_memory in enumerate(self.agent_observation_memory_size):
            for obs, memory in enumerate(agent_memory):
                self.decpomdp_manager.set_agent_observation_memory_size(agent, obs, memory)
            

    def substitute_suffix(self, string, delimiter, replacer):
        '''Subsitute the suffix behind the last delimiter.'''
        output_string = string.split(delimiter)
        output_string[-1] = str(replacer)
        output_string = delimiter.join(output_string)
        return output_string

    def unfold_memory(self):
        
        # reset attributes
        self.quotient_mdp = None
        self.coloring = None
        self.hole_option_to_actions = None
        
        self.is_action_hole = None
        
        self.quotient_mdp = self.decpomdp_manager.construct_quotient_mdp()
        self.choice_destinations = payntbind.synthesis.computeChoiceDestinations(self.quotient_mdp)
        logger.debug(f"constructed quotient MDP having {self.quotient_mdp.nr_states} states and {self.quotient_mdp.nr_choices} actions.")

        family, choice_to_hole_options = self.create_coloring()
       
        self.coloring = payntbind.synthesis.Coloring(family.family, self.quotient_mdp.nondeterministic_choice_indices, choice_to_hole_options)

        # to each hole-option pair a list of actions colored by this combination
        self.hole_option_to_actions = [[] for hole in range(family.num_holes)]
        for hole in range(family.num_holes):
            self.hole_option_to_actions[hole] = [[] for option in family.hole_options(hole)]
        for choice in range(self.quotient_mdp.nr_choices):
            for hole,option in choice_to_hole_options[choice]:
                self.hole_option_to_actions[hole][option].append(choice)

        self.design_space = paynt.family.family.DesignSpace(family)


    def create_coloring(self):
        # short aliases
        pm = self.decpomdp_manager

        # create holes
        family = paynt.family.family.Family()
        self.is_action_hole = []

        for agent in range(self.nr_agents):
            for obs in range(self.nr_agent_observations[agent]):
                
                # action holes
                hole_indices = []
                num_actions = self.num_agent_actions_at_observation[agent][obs]
                if num_actions > 1:
                    option_labels = ["act_"+str(x) for x in range(num_actions)] # TODO adding labels here would be nice in the future
                    for mem in range(self.agent_observation_memory_size[agent][obs]):
                        hole_indices.append(family.num_holes)
                        name = self.create_hole_name(agent,obs,mem,True)
                        family.add_hole(name,option_labels)
                        self.is_action_hole.append(True)

                # memory holes
                hole_indices = []
                num_updates = pm.agent_max_successor_memory_size[agent][obs]
                if num_updates > 1:
                    option_labels = [str(x) for x in range(num_updates)]
                    for mem in range(self.agent_observation_memory_size[agent][obs]):
                        name = self.create_hole_name(agent,obs,mem,False)
                        hole_indices.append(family.num_holes)
                        family.add_hole(name,option_labels)
                        self.is_action_hole.append(False)

        # create the coloring
        assert pm.num_holes == family.num_holes
        num_holes = family.num_holes
        agent_row_action_hole = pm.agent_row_action_hole
        agent_row_action_option = pm.agent_row_action_option
        agent_row_memory_hole = pm.agent_row_memory_hole
        agent_row_memory_option = pm.agent_row_memory_option
        choice_to_hole_options = []
        for choice in range(self.quotient_mdp.nr_choices):
            hole_options = []
            for agent in range(self.nr_agents): 
                hole = agent_row_action_hole[agent][choice]
                if hole != num_holes:
                    hole_options.append( (hole,agent_row_action_option[agent][choice]) )
                hole = agent_row_memory_hole[agent][choice]
                if hole != num_holes:
                    hole_options.append( (hole,agent_row_memory_option[agent][choice]) )
            choice_to_hole_options.append(hole_options)
        return family, choice_to_hole_options
    

    def scheduler_selection(self, mdp, scheduler, coloring=None):
        ''' Get hole options involved in the scheduler selection. '''
        assert scheduler.memoryless and scheduler.deterministic
        return super().scheduler_selection(mdp,scheduler,coloring) 

    def estimate_scheduler_difference(self, mdp, quotient_choice_map, inconsistent_assignments, choice_values, expected_visits=None):
        return super().estimate_scheduler_difference(mdp, quotient_choice_map, inconsistent_assignments, choice_values, expected_visits)