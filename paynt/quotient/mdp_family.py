import payntbind

import paynt.family.family
import paynt.quotient.quotient
import paynt.models.models

import json

import logging
logger = logging.getLogger(__name__)


class MdpFamilyQuotient(paynt.quotient.quotient.Quotient):

    @staticmethod
    def map_state_action_to_choices(mdp, num_actions, choice_to_action):
        state_action_choices = []
        for state in range(mdp.nr_states):
            action_choices = [[] for action in range(num_actions)]
            for choice in mdp.transition_matrix.get_rows_for_group(state):
                action = choice_to_action[choice]
                action_choices[action].append(choice)
            state_action_choices.append(action_choices)
        return state_action_choices

    @staticmethod
    def map_state_to_available_actions(state_action_choices):
        state_to_actions = []
        for state,action_choices in enumerate(state_action_choices):
            available_actions = []
            for action,choices in enumerate(action_choices):
                if choices:
                    available_actions.append(action)
            state_to_actions.append(available_actions)
        return state_to_actions

    
    def __init__(self, quotient_mdp, family, coloring, specification):
        super().__init__(quotient_mdp = quotient_mdp, family = family, coloring = coloring, specification = specification)

        # number of distinct actions in the quotient
        self.num_actions = None
        # a list of action labels
        self.action_labels = None
        # for each choice of the quotient, the executed action
        self.choice_to_action = None
        # for each state of the quotient and for each action, a list of choices that execute this action
        self.state_action_choices = None
        # for each state of the quotient, a list of available actions
        self.state_to_actions = None

        self.action_labels,self.choice_to_action = payntbind.synthesis.extractActionLabels(quotient_mdp)
        self.num_actions = len(self.action_labels)
        self.state_action_choices = MdpFamilyQuotient.map_state_action_to_choices(
            self.quotient_mdp, self.num_actions, self.choice_to_action)
        self.state_to_actions = MdpFamilyQuotient.map_state_to_available_actions(self.state_action_choices)

    def empty_policy(self):
        return self.empty_scheduler()

    def scheduler_to_policy(self, scheduler, mdp):
        state_to_choice = self.scheduler_to_state_to_choice(mdp,scheduler)
        policy = self.empty_policy()
        for state in range(self.quotient_mdp.nr_states):
            choice = state_to_choice[state]
            if choice is not None:
                policy[state] = self.choice_to_action[choice]
        return policy

    def policy_to_state_valuation_actions(self, policy):
        '''
        Create a representation for a policy that associated action labels with state valuations. States with only
        one available action are omitted.
        '''
        policy,_ = policy
        sv = self.quotient_mdp.state_valuations
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

    
    def fix_and_apply_policy_to_family(self, family, policy):
        '''
        Apply policy to the quotient MDP for the given family. Every undefined action in a policy is set to an arbitrary
        one. Upon constructing the MDP, reset unused actions in a policy to None.
        :returns fixed policy
        :returns the resulting MDP
        '''
        policy = [action if action is not None else self.state_to_actions[state][0] for state,action in enumerate(policy)]
        policy_choices = []
        for state,action in enumerate(policy):
            policy_choices += self.state_action_choices[state][action]
        choices = payntbind.synthesis.policyToChoicesForFamily(policy_choices, family.selected_choices)

        # build MDP and keep only reachable states in policy
        mdp = self.build_from_choice_mask(choices)
        policy_fixed = self.empty_policy()
        for state in mdp.quotient_state_map:
            policy_fixed[state] = policy[state]

        mask = [state for state,action in enumerate(policy_fixed) if action is not None]
        policy_fixed = (policy_fixed,mask)
        return policy_fixed,mdp
    

    def apply_policy_to_family(self, family, policy):
        policy_choices = []
        for state,action in enumerate(policy):
            if action is None:
                for choice in self.state_action_choices[state]:
                    policy_choices += choice
            else:
                policy_choices += self.state_action_choices[state][action]
        choices = payntbind.synthesis.policyToChoicesForFamily(policy_choices, family.selected_choices)

        mdp = self.build_from_choice_mask(choices)

        return mdp

    
    def assert_mdp_is_deterministic(self, mdp, family):
        if mdp.is_deterministic:
            return
        
        logger.error(f"applied policy to a singleton family {family} and obtained MDP with nondeterminism")
        for state in range(mdp.model.nr_states):

            choices = mdp.model.transition_matrix.get_rows_for_group(state)
            if len(choices)>1:
                quotient_state = mdp.quotient_state_map[state]
                quotient_choices = [mdp.quotient_choice_map[choice] for choice in choices]
                state_str = self.quotient_mdp.state_valuations.get_string(quotient_state)
                state_str = state_str.replace(" ","")
                state_str = state_str.replace("\t","")
                actions_str = [self.action_labels[self.choice_to_action[choice]] for choice in quotient_choices]
                logger.error(f"the following state {state_str} has multiple actions {actions_str}")
        logger.error("aborting...")
        exit(1)
        

    def build_game_abstraction_solver(self, prop):
        target_label = prop.get_target_label()
        precision = paynt.verification.property.Property.model_checking_precision
        solver = payntbind.synthesis.GameAbstractionSolver(
            self.quotient_mdp, len(self.action_labels), self.choice_to_action, prop.formula, prop.maximizing, target_label, precision
        )
        return solver

    def build_assignment(self, family):
        assert family.size == 1, "expecting family of size 1"
        choices = self.coloring.selectCompatibleChoices(family.family)
        model,state_map,choice_map = self.restrict_quotient(choices)
        return paynt.models.models.SubMdp(model,state_map,choice_map)
