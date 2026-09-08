'''
Constructs a PomdpFamilyColoredMdp: like FamilyColoredMdpFactory, but tracks observation classes so that
policy decisions can be tied together across environment variants that look the same to the agent.
'''

from paynt.family.factory import FamilyColoredMdpFactory
from paynt.family.pomdp.colored_mdp import PomdpFamilyColoredMdp

import logging
logger = logging.getLogger(__name__)


class PomdpFamilyColoredMdpFactory(FamilyColoredMdpFactory):

    def __init__(self, underlying_mdp, parameter_space, coloring, task, obs_evaluator, use_exact=False):
        self.obs_evaluator = obs_evaluator
        super().__init__(underlying_mdp, parameter_space, coloring, task, use_exact=use_exact)

    def unfold_scheduler_memory(self, underlying_mdp, parameter_space, coloring):
        unfolded_mdp, parameter_space, new_coloring = super().unfold_scheduler_memory(underlying_mdp, parameter_space, coloring)
        # memory was unfolded, so obs_evaluator must be updated to match the unfolded state space
        prototype_states = list(self.memory_unfolder.state_prototype)
        state_to_obs_class = list(self.obs_evaluator.state_to_obs_class)
        new_obs_classes_map = [state_to_obs_class[prototype_states[state]] for state in range(unfolded_mdp.nr_states)]
        self.obs_evaluator.state_to_obs_class = new_obs_classes_map
        return unfolded_mdp, parameter_space, new_coloring

    def _construct_colored_mdp(self):
        # identify actions available at each observation
        observation_to_actions = [None] * self.obs_evaluator.num_obs_classes
        state_to_observation = self.obs_evaluator.state_to_obs_class
        for state,available_actions in enumerate(self.state_to_actions):
            obs = state_to_observation[state]
            if observation_to_actions[obs] is not None:
                assert observation_to_actions[obs] == available_actions,\
                    f"two states in observation class {obs} differ in available actions"
                continue
            observation_to_actions[obs] = available_actions

        return PomdpFamilyColoredMdp(
            self.underlying_mdp, self.parameter_space, self.coloring, self.use_exact,
            self.num_actions, self.action_labels, self.choice_to_action, self.state_action_choices, self.state_to_actions,
            self.obs_evaluator, observation_to_actions)
