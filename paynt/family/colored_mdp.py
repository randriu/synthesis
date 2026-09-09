'''
Colored MDP representing a family of MDPs: parameters select which concrete environment instance
(rather than which FSC/policy structure) is in effect.
'''

import payntbind

import paynt.colored_mdp
import paynt.underlying_model.underlying_model
import paynt.specification.property

import json

import logging
logger = logging.getLogger(__name__)


class FamilyColoredMdp(paynt.colored_mdp.ColoredMdp):

    feature_kind = "family"

    def __init__(self, underlying_mdp, parameter_space, coloring, use_exact,
                 num_actions, action_labels, choice_to_action, state_action_choices, state_to_actions):
        super().__init__(underlying_mdp, parameter_space, coloring, use_exact)
        # number of distinct actions in the underlying MDP
        self.num_actions = num_actions
        # a list of action labels
        self.action_labels = action_labels
        # for each choice of the underlying MDP, the executed action
        self.choice_to_action = choice_to_action
        # for each state of the underlying MDP and for each action, a list of choices that execute this action
        self.state_action_choices = state_action_choices
        # for each state of the underlying MDP, a list of available actions
        self.state_to_actions = state_to_actions

    def build_assignment(self, parameter_space):
        '''
        Overrides ColoredMdp.build_assignment: fixing every parameter (i.e. picking one member of the
        parameter_space) does not fix the agent's policy -- that is separate, handled by apply_policy_to_parameter_space --
        so the resulting model can still be nondeterministic and must not be converted to a DTMC.
        '''
        assert parameter_space.size == 1, "expecting parameter_space of size 1"
        choices = self.coloring.selectCompatibleChoices(parameter_space.native)
        model, state_map, choice_map = paynt.underlying_model.underlying_model.SubmodelBuilder.restrict(
            self.underlying_mdp, choices, self.subsystem_builder_options)
        return paynt.underlying_model.underlying_model.SubMdp(model, state_map, choice_map)

    def empty_policy(self):
        return paynt.underlying_model.underlying_model.ModelIndex.empty_scheduler(self.underlying_mdp)

    def scheduler_to_policy(self, scheduler, mdp):
        state_to_choice = paynt.underlying_model.underlying_model.ModelIndex.scheduler_to_state_to_choice(
            self.underlying_mdp, self.choice_destinations, mdp, scheduler)
        policy = self.empty_policy()
        for state in range(self.underlying_mdp.nr_states):
            choice = state_to_choice[state]
            if choice is not None:
                policy[state] = self.choice_to_action[choice]
        return policy

    def policy_to_state_valuation_actions(self, policy):
        '''
        Create a representation for a policy that associates action labels with state valuations. States with only
        one available action are omitted.
        '''
        policy,_ = policy
        sv = self.underlying_mdp.state_valuations
        state_valuation_to_action = []
        for state,action in enumerate(policy):
            if action is None:
                continue
            if len(self.state_to_actions[state])==1:
                continue
            # get action label
            action = self.action_labels[action]
            if action == "empty_label":
                continue

            # get state valuation
            valuation_jani = json.loads(str(sv.get_json(state)))
            valuation = {}
            for variable,value in valuation_jani.items():
                if "_loc_prism2jani_" in variable:
                    continue
                valuation[variable] = value

            state_valuation_to_action.append( (valuation,action) )

        # omit variables that are assigned to the same value
        default_valuation,_ = state_valuation_to_action[0]
        irrelevant_variables = set(default_valuation)
        for valuation,_ in state_valuation_to_action[1:]:
            for variable in list(irrelevant_variables):
                if valuation[variable] != default_valuation[variable]:
                    irrelevant_variables.remove(variable)
        state_valuation_to_action = [
            ({variable:value for variable,value in valuation.items() if variable not in irrelevant_variables},action)
            for valuation,action in state_valuation_to_action
        ]
        return state_valuation_to_action

    def policy_to_json(self, state_valuation_to_action, dt_control=False):
        '''
        :param state_valuation_to_action: a list of tuples (valuation,action) where valuation is a dictionary of variable
        :param dt_control: if True, outputs JSON in the format expected by the DT control tool,
                otherwise simpler format is used
        '''
        json_whole = []
        for index, valuation_action in enumerate(state_valuation_to_action):
            if dt_control:
                json_unit = {}
                valuation, action = valuation_action
                json_unit["c"] = [{"origin": {"action-label": action}}]
                json_unit["s"] = valuation
                json_whole.append(json_unit)
            else:
                json_whole.append(valuation_action)

        return json_whole

    def fix_and_apply_policy_to_parameter_space(self, selected_choices, policy):
        '''
        Apply policy to the underlying MDP restricted to selected_choices. Every undefined action in a policy
        is set to an arbitrary one. Upon constructing the MDP, reset unused actions in a policy to None.
        :param selected_choices the compatible-choices bitmask to restrict the policy to -- passed explicitly
            (not a parameter_space) since callers may want to verify against a snapshot taken at an earlier
            point (e.g. before postprocessing widened a node's parameter_space via parameter_set_options)
        :returns fixed policy
        :returns the resulting MDP
        '''
        policy = [action if action is not None else self.state_to_actions[state][0] for state,action in enumerate(policy)]
        policy_choices = []
        for state,action in enumerate(policy):
            policy_choices += self.state_action_choices[state][action]
        choices = payntbind.synthesis.policyToChoicesForFamily(policy_choices, selected_choices)

        # build MDP and keep only reachable states in policy
        mdp = paynt.underlying_model.underlying_model.SubmodelBuilder.build_submdp(
            self.underlying_mdp, choices, self.subsystem_builder_options)
        policy_fixed = self.empty_policy()
        for state in mdp.underlying_mdp_state_map:
            policy_fixed[state] = policy[state]

        mask = [state for state,action in enumerate(policy_fixed) if action is not None]
        policy_fixed = (policy_fixed,mask)
        return policy_fixed,mdp

    def apply_policy_to_parameter_space(self, selected_choices, policy):
        policy_choices = []
        for state,action in enumerate(policy):
            if action is None:
                for choice in self.state_action_choices[state]:
                    policy_choices += choice
            else:
                policy_choices += self.state_action_choices[state][action]
        choices = payntbind.synthesis.policyToChoicesForFamily(policy_choices, selected_choices)

        mdp = paynt.underlying_model.underlying_model.SubmodelBuilder.build_submdp(
            self.underlying_mdp, choices, self.subsystem_builder_options)

        return mdp

    def assert_mdp_is_deterministic(self, mdp, parameter_space):
        if mdp.is_deterministic:
            return

        logger.error(f"applied policy to a singleton parameter assignment {parameter_space} and obtained MDP with nondeterminism")
        for state in range(mdp.model.nr_states):

            choices = mdp.model.transition_matrix.get_rows_for_group(state)
            if len(choices)>1:
                underlying_mdp_state = mdp.underlying_mdp_state_map[state]
                underlying_mdp_choices = [mdp.underlying_mdp_choice_map[choice] for choice in choices]
                state_str = self.underlying_mdp.state_valuations.get_string(underlying_mdp_state)
                state_str = state_str.replace(" ","")
                state_str = state_str.replace("\t","")
                actions_str = [self.action_labels[self.choice_to_action[choice]] for choice in underlying_mdp_choices]
                logger.error(f"the following state {state_str} has multiple actions {actions_str}")
        logger.error("aborting...")
        exit(1)

    def build_game_abstraction_solver(self, prop):
        target_label = prop.get_target_label()
        precision = paynt.specification.property.Property.model_checking_precision
        solver = payntbind.synthesis.GameAbstractionSolver(
            self.underlying_mdp, len(self.action_labels), self.choice_to_action, prop.formula, prop.maximizing, target_label, precision
        )
        return solver
