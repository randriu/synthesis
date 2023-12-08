import stormpy
import stormpy.synthesis

import paynt.quotient.quotient

import collections

import logging
logger = logging.getLogger(__name__)


class MdpFamilyQuotientContainer(paynt.quotient.quotient.QuotientContainer):

    @staticmethod
    def extract_choice_labels(mdp):
        '''
        :param mdp having a canonic choice labeling (exactly 1 label for each choice)
        :return a list of action labels
        :return for each row, its action
        :return for each state, a list of actions associated with the rows of this state
        '''
        assert mdp.has_choice_labeling, "MDP does not have a choice labeling"
        action_labels = list(mdp.choice_labeling.get_labels())
        # sorting because get_labels() is not deterministic
        action_labels = sorted(action_labels)
        label_to_action = {label:index for index,label in enumerate(action_labels)}
        
        choice_to_action = [None] * mdp.nr_choices
        for state in range(mdp.nr_states):
            for choice in mdp.transition_matrix.get_rows_for_group(state):
                label = list(mdp.choice_labeling.get_labels_of_choice(choice))[0]
                action = label_to_action[label]
                choice_to_action[choice] = action

        return action_labels,choice_to_action

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

    @staticmethod
    def compute_choice_destinations(mdp):
        choice_destinations = []
        for choice in range(mdp.nr_choices):
            destinations = []
            for entry in mdp.transition_matrix.get_row(choice):
                destinations.append(entry.column)
            choice_destinations.append(destinations)
        return choice_destinations

        
    def __init__(self, quotient_mdp, coloring, specification):
        super().__init__(quotient_mdp = quotient_mdp, coloring = coloring, specification = specification)

        self.design_space = paynt.quotient.holes.DesignSpace(coloring.holes)

        # a list of action labels
        self.action_labels = None
        # for each choice of the quotient, the executed action
        self.choice_to_action = None
        # for each state of the quotient and for each action, a list of choices that execute this action
        self.state_action_choices = None
        # for each state of the quotient, a list of available actions
        self.state_to_actions = None
        # for each choice of the quotient, a list of its state-destinations
        self.choice_destinations = None

        self.action_labels,self.choice_to_action = MdpFamilyQuotientContainer.extract_choice_labels(self.quotient_mdp)
        self.state_action_choices = MdpFamilyQuotientContainer.map_state_action_to_choices(
            self.quotient_mdp, self.num_actions, self.choice_to_action)
        self.state_to_actions = MdpFamilyQuotientContainer.map_state_to_available_actions(self.state_action_choices)
        self.choice_destinations = MdpFamilyQuotientContainer.compute_choice_destinations(self.quotient_mdp)
    
    
    @property
    def num_actions(self):
        return len(self.action_labels)


    def keep_reachable_choices(self, choice_mask, mdp=None, choice_destinations=None):
        if mdp is None:
            mdp = self.quotient_mdp
        if choice_destinations is None:
            choice_destinations = self.choice_destinations
        state_visited = [False]*mdp.nr_states
        initial_state = list(mdp.initial_states)[0]
        state_visited[initial_state] = True
        state_queue = [initial_state]
        tm = mdp.transition_matrix
        choice_mask_reachable = stormpy.BitVector(mdp.nr_choices,False)
        while state_queue:
            state = state_queue.pop()
            for choice in mdp.transition_matrix.get_rows_for_group(state):
                if not choice_mask[choice]:
                    continue
                choice_mask_reachable.set(choice,True)
                for dst in choice_destinations[choice]:
                    if not state_visited[dst]:
                        state_visited[dst] = True
                        state_queue.append(dst)
        return choice_mask_reachable
    
    
    
    def choices_to_hole_selection(self, choice_mask):
        hole_selection = [set() for hole_index in self.design_space.hole_indices]
        for choice in choice_mask:
            choice_options = self.coloring.action_to_hole_options[choice]
            for hole_index,option in choice_options.items():
                hole_selection[hole_index].add(option)
        hole_selection = [list(options) for options in hole_selection]
        return hole_selection

    def empty_policy(self):
        return [None] * self.quotient_mdp.nr_states

    def scheduler_to_policy(self, scheduler, mdp):            
        policy = self.empty_policy()
        nci = mdp.model.nondeterministic_choice_indices.copy()
        for state in range(mdp.model.nr_states):
            state_choice = scheduler.get_choice(state).get_deterministic_choice()
            choice = nci[state] + state_choice
            quotient_choice = mdp.quotient_choice_map[choice]
            action = self.choice_to_action[quotient_choice]
            quotient_state = mdp.quotient_state_map[state]
            policy[quotient_state] = action
        return policy


    def fix_policy_for_family(self, family, policy):
        '''
        Apply policy to the quotient MDP for the given family. If a state is reached for which policy does not define
        an action, pick an arbitrary one.
        :return fixed policy
        :return choice mask from which Q-MDP x policy can be constructed
        '''
        
        choice_mask = stormpy.BitVector(self.quotient_mdp.nr_choices,False)
        policy_fixed = self.empty_policy()

        initial_state = list(self.quotient_mdp.initial_states)[0]
        tm = self.quotient_mdp.transition_matrix
        
        state_visited = stormpy.BitVector(self.quotient_mdp.nr_states,False)
        state_visited.set(initial_state,True)
        state_queue = [initial_state]
        while state_queue:
            state = state_queue.pop()
            action = policy[state]
            if action is None:
                action = self.state_to_actions[state][0]
            policy_fixed[state] = action
            for choice in self.state_action_choices[state][action]:
                if not family.selected_actions_bv[choice]:
                    continue
                choice_mask.set(choice,True)
                for dst in self.choice_destinations[choice]:
                    if not state_visited[dst]:
                        state_visited.set(dst,True)
                        state_queue.append(dst)
        return policy_fixed,choice_mask

    
    def apply_policy_to_family(self, family, policy):
        _,choice_mask = self.fix_policy_for_family(family,policy)
        return self.build_from_choice_mask(choice_mask)


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
        solver = stormpy.synthesis.GameAbstractionSolver(
            self.quotient_mdp, len(self.action_labels), self.choice_to_action, target_label
        )
        return solver

    