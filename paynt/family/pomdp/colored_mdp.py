'''
Colored MDP representing a family of POMDPs: adds observation-awareness on top of FamilyColoredMdp.
'''

import payntbind

import paynt.colored_mdp
from paynt.family.colored_mdp import FamilyColoredMdp
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
