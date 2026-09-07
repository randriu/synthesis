'''
Colored MDP representing a family of POMDPs: adds observation-awareness on top of FamilyColoredMdp.
'''

import payntbind

import paynt.colored_mdp
from paynt.family.colored_mdp import FamilyColoredMdp
from paynt.family.factory import FamilyColoredMdpFactory
import paynt.pomdp.fsc
import paynt.underlying_model.underlying_model

import logging
logger = logging.getLogger(__name__)


class SubPomdp:
    '''
    Simple container for a (sub-)POMDP created from the underlying model.
    '''
    def __init__(self, model, underlying_mdp_state_map, underlying_mdp_choice_map):
        # the Stormpy POMDP
        self.model = model
        # for each state of the POMDP, a state in the underlying model
        self.underlying_mdp_state_map = underlying_mdp_state_map
        # for each choice of the POMDP, a choice in the underlying model
        self.underlying_mdp_choice_map = underlying_mdp_choice_map


class PomdpFamilyColoredMdp(FamilyColoredMdp):

    feature_kind = "pomdp_family"

    def __init__(self, underlying_mdp, parameter_space, coloring, use_exact,
                 num_actions, action_labels, choice_to_action, state_action_choices, state_to_actions,
                 obs_evaluator, observation_to_actions):
        super().__init__(underlying_mdp, parameter_space, coloring, use_exact,
                          num_actions, action_labels, choice_to_action, state_action_choices, state_to_actions)
        self.obs_evaluator = obs_evaluator
        # for each observation, a list of actions (indices) available
        self.observation_to_actions = observation_to_actions
        # POMDP manager used for unfolding the memory model into the underlying POMDP
        self.fsc_unfolder = None

    @property
    def num_observations(self):
        return self.obs_evaluator.num_obs_classes

    @property
    def state_to_observation(self):
        return self.obs_evaluator.state_to_obs_class

    def observation_is_trivial(self, obs):
        return len(self.observation_to_actions[obs])==1

    def build_pomdp(self, parameter_space):
        ''' Construct the sub-POMDP from the given parameter assignment. '''
        assert parameter_space.size == 1, "expecting parameter space of size 1"
        choices = self.coloring.selectCompatibleChoices(parameter_space.native)
        mdp,state_map,choice_map = paynt.underlying_model.underlying_model.SubmodelBuilder.restrict(
            self.underlying_mdp, choices, self.subsystem_builder_options)
        pomdp = self.obs_evaluator.add_observations_to_submdp(mdp,state_map)
        return SubPomdp(pomdp,state_map,choice_map)

    def build_dtmc_sketch(self, fsc):
        '''
        Construct the family of DTMCs representing the execution of the given FSC in different environments.
        '''

        # create the product
        fsc.check(self.observation_to_actions)

        self.fsc_unfolder = payntbind.synthesis.FscUnfolder(
            self.underlying_mdp, self.state_to_observation, self.num_actions, self.choice_to_action
        )
        if isinstance(fsc,paynt.pomdp.fsc.Fsc):
            self.fsc_unfolder.applyFsc(fsc.transitions)
        elif isinstance(fsc,paynt.pomdp.fsc.FscFactored):
            self.fsc_unfolder.applyFscFactored(fsc.action_function, fsc.update_function)
        else:
            raise ValueError("unknown FSC class")
        product = self.fsc_unfolder.product
        product_choice_to_choice = self.fsc_unfolder.product_choice_to_choice

        # the product inherits the design space
        product_parameter_space = self.parameter_space.copy()

        # the choices of the product inherit colors of the underlying model
        product_choice_to_parameter_options = []
        underlying_num_choices = self.underlying_mdp.nr_choices
        choice_to_parameter_assignment = self.coloring.getChoiceToAssignment()
        for product_choice in range(product.nr_choices):
            choice = product_choice_to_choice[product_choice]
            if choice == underlying_num_choices:
                parameter_options = []
            else:
                parameter_options = [(parameter,option) for parameter,option in choice_to_parameter_assignment[choice]]
            product_choice_to_parameter_options.append(parameter_options)
        product_coloring = payntbind.synthesis.Coloring(product_parameter_space.native, product.nondeterministic_choice_indices, product_choice_to_parameter_options)

        dtmc_sketch = paynt.colored_mdp.ColoredMdp(product, product_parameter_space, product_coloring, use_exact=self.use_exact)
        return dtmc_sketch


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
