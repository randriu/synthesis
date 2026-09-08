'''
Constructs a DecPomdpColoredMdp by unfolding every agent's imperfect-information strategy into its own FSC
template of a given memory size. Like paynt.pomdp's factory, this supports re-unfolding at a larger memory
size after construction (DecPomdpSynthesizer increases it step by step), so the set_*_memory_size methods
are public entry points, not just __init__-time setup: each produces a fresh DecPomdpColoredMdp rather than
mutating the previous one in place, and the caller reassigns.
'''

import payntbind

import paynt.parameter_space.parameter_space
from paynt.pomdp.decpomdp.colored_mdp import DecPomdpColoredMdp

import logging
logger = logging.getLogger(__name__)


class DecPomdpColoredMdpFactory:

    def __init__(self, decpomdp_manager, task, use_exact=False):
        assert decpomdp_manager.num_agents > 1
        self.decpomdp_manager = decpomdp_manager
        self.task = task
        self.use_exact = use_exact

        # for each agent a (simplified) label for each observation
        self.agent_observation_labels = decpomdp_manager.agent_observation_labels
        # for each agent its action labels
        self.agent_action_labels = decpomdp_manager.agent_action_labels
        # number of agents in the model
        self.nr_agents = decpomdp_manager.num_agents
        # for each joint observation, the observation of each agent
        self.joint_observations = decpomdp_manager.joint_observations
        # for each state, its corresponding joint observation index
        self.state_joint_observation = decpomdp_manager.state_joint_observation
        # for each agent, the number of its observations
        self.nr_agent_observations = [len(observation) for observation in self.agent_observation_labels]
        # for each agent, the number of available actions at a given observation
        self.num_agent_actions_at_observation = decpomdp_manager.num_agent_actions_at_observation

        # mark perfectly observable states for each agent
        nr_states = decpomdp_manager.num_decpomdp_states()
        self.agent_observation_states = [[0 for obs in range(self.nr_agent_observations[agent])] for agent in range(self.nr_agents)]
        for state in range(nr_states):
            joint_observation = self.state_joint_observation[state]
            for agent in range(self.nr_agents):
                agent_obs = self.joint_observations[joint_observation][agent]
                self.agent_observation_states[agent][agent_obs] += 1

        # for each agent and each observation, the size of the memory allocated to it, and the current unfolding
        self.agent_observation_memory_size = [[] for _ in range(self.nr_agents)]
        self.current_memory_size = None
        self.colored_mdp = self.set_imperfect_memory_size(task.memory_size)

    def create_parameter_name(self, agent, obs, mem, is_action_parameter):
        category = "A" if is_action_parameter else "M"
        obs_label = self.agent_observation_labels[agent][obs]
        return "{}({},{},{})".format(category,agent,obs_label,mem)

    def set_manager_memory_vector(self):
        for agent, agent_memory in enumerate(self.agent_observation_memory_size):
            for obs, memory in enumerate(agent_memory):
                self.decpomdp_manager.set_agent_observation_memory_size(agent, obs, memory)

    def set_imperfect_memory_size(self, memory_size):
        ''' (Re-)unfold every agent's FSC template at the given memory size (imperfect observations only),
        producing a fresh DecPomdpColoredMdp -- callers reassign their reference (e.g. self.colored_mdp =
        factory.set_imperfect_memory_size(k)) rather than relying on in-place mutation. '''
        for agent in range(self.nr_agents):
            agent_memory = [memory_size if self.agent_observation_states[agent][obs] > 1 else 1 for obs in range(self.nr_agent_observations[agent])]
            self.agent_observation_memory_size[agent] = agent_memory
        self.set_manager_memory_vector()
        self.current_memory_size = memory_size
        self.colored_mdp = self._unfold_memory()
        return self.colored_mdp

    def set_agent_imperfect_memory_size(self, agent, memory_size):
        ''' Like set_imperfect_memory_size, but re-unfolds only the given agent's imperfect observations. '''
        assert agent in range(self.nr_agents), "given agent index is larger than number of agents"
        agent_memory = [memory_size if self.agent_observation_states[agent][obs] > 1 else 1 for obs in range(self.nr_agent_observations[agent])]
        self.agent_observation_memory_size[agent] = agent_memory
        self.set_manager_memory_vector()
        self.colored_mdp = self._unfold_memory()
        return self.colored_mdp

    def create_coloring(self, underlying_mdp):
        pm = self.decpomdp_manager
        parameter_space = paynt.parameter_space.parameter_space.ParameterSpace()

        for agent in range(self.nr_agents):
            for obs in range(self.nr_agent_observations[agent]):
                # action parameters
                num_actions = self.num_agent_actions_at_observation[agent][obs]
                if num_actions > 1:
                    option_labels = ["act_"+str(x) for x in range(num_actions)] # TODO adding labels here would be nice in the future
                    for mem in range(self.agent_observation_memory_size[agent][obs]):
                        name = self.create_parameter_name(agent,obs,mem,True)
                        parameter_space.add_parameter(name,option_labels)

                # memory parameters
                num_updates = pm.agent_max_successor_memory_size[agent][obs]
                if num_updates > 1:
                    option_labels = [str(x) for x in range(num_updates)]
                    for mem in range(self.agent_observation_memory_size[agent][obs]):
                        name = self.create_parameter_name(agent,obs,mem,False)
                        parameter_space.add_parameter(name,option_labels)

        # create the coloring
        assert pm.num_holes == parameter_space.num_parameters
        num_parameters = parameter_space.num_parameters
        agent_row_action_parameter = pm.agent_row_action_hole
        agent_row_action_option = pm.agent_row_action_option
        agent_row_memory_parameter = pm.agent_row_memory_hole
        agent_row_memory_option = pm.agent_row_memory_option
        choice_to_parameter_options = []
        for choice in range(underlying_mdp.nr_choices):
            parameter_options = []
            for agent in range(self.nr_agents):
                parameter = agent_row_action_parameter[agent][choice]
                if parameter != num_parameters:
                    parameter_options.append( (parameter,agent_row_action_option[agent][choice]) )
                parameter = agent_row_memory_parameter[agent][choice]
                if parameter != num_parameters:
                    parameter_options.append( (parameter,agent_row_memory_option[agent][choice]) )
            choice_to_parameter_options.append(parameter_options)
        return parameter_space, choice_to_parameter_options

    def _unfold_memory(self):
        underlying_mdp = self.decpomdp_manager.construct_quotient_mdp()
        logger.debug(f"constructed underlying MDP having {underlying_mdp.nr_states} states and {underlying_mdp.nr_choices} actions.")

        parameter_space, choice_to_parameter_options = self.create_coloring(underlying_mdp)
        coloring = payntbind.synthesis.Coloring(
            parameter_space.native, underlying_mdp.nondeterministic_choice_indices, choice_to_parameter_options)

        colored_mdp = DecPomdpColoredMdp(underlying_mdp, parameter_space, coloring, self.use_exact)
        return colored_mdp
