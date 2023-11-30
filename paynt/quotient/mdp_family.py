import stormpy
import stormpy.synthesis

import paynt.quotient.holes
import paynt.quotient.models
import paynt.quotient.quotient
import paynt.verification.property_result

import logging
logger = logging.getLogger(__name__)


class MdpFamilyQuotientContainer(paynt.quotient.quotient.QuotientContainer):

    @classmethod
    def extract_choice_labels(cls, mdp):
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
        state_to_actions = []
        tm = mdp.transition_matrix
        for state in range(mdp.nr_states):
            state_choice_label_indices = set()
            for choice in range(tm.get_row_group_start(state),tm.get_row_group_end(state)):
                label = list(mdp.choice_labeling.get_labels_of_choice(choice))[0]
                action = label_to_action[label]
                choice_to_action[choice] = action
                state_choice_label_indices.add(action)
            state_to_actions.append(list(state_choice_label_indices))

        return action_labels,choice_to_action,state_to_actions

    
    def __init__(self, quotient_mdp, coloring, specification):
        super().__init__(quotient_mdp = quotient_mdp, coloring = coloring, specification = specification)
        self.design_space = paynt.quotient.holes.DesignSpace(coloring.holes)

        self.action_labels,self.choice_to_action,self.state_to_actions = \
            MdpFamilyQuotientContainer.extract_choice_labels(self.quotient_mdp)

        self.choice_destinations = self.compute_choice_destinations(self.quotient_mdp)
        self.state_action_choices = self.compute_state_action_choices(self.quotient_mdp, self.num_actions, self.choice_to_action)

    
    @property
    def num_actions(self):
        return len(self.action_labels)


    def compute_state_action_choices(self, mdp, num_actions, choice_to_action):
        state_action_choices = []
        tm = mdp.transition_matrix
        for state in range(mdp.nr_states):
            action_choices = [[] for action in range(num_actions)]
            for choice in range(tm.get_row_group_start(state),tm.get_row_group_end(state)):
                action = choice_to_action[choice]
                action_choices[action].append(choice)
            state_action_choices.append(action_choices)
        return state_action_choices

    def compute_choice_destinations(self, mdp):
        choice_destinations = []
        tm = mdp.transition_matrix
        for choice in range(mdp.nr_choices):
            destinations = []
            for entry in tm.get_row(choice):
                destinations.append(entry.column)
            choice_destinations.append(destinations)
        return choice_destinations


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
            for choice in range(tm.get_row_group_start(state),tm.get_row_group_end(state)):
                if not choice_mask[choice]:
                    continue
                choice_mask_reachable.set(choice,True)
                for dst in choice_destinations[choice]:
                    if not state_visited[dst]:
                        state_visited[dst] = True
                        state_queue.append(dst)
        return choice_mask_reachable
    
    
    def choices_to_policy(self, choice_mask):
        policy = [self.num_actions] * self.quotient_mdp.nr_states
        tm = self.quotient_mdp.transition_matrix
        for state in range(self.quotient_mdp.nr_states):
            for choice in range(tm.get_row_group_start(state),tm.get_row_group_end(state)):
                if choice_mask[choice]:
                    assert policy[state] == self.num_actions
                    policy[state] = self.choice_to_action[choice]
        return policy

    
    def choices_to_hole_selection(self, choice_mask):
        hole_selection = [set() for hole_index in self.design_space.hole_indices]
        for choice in choice_mask:
            choice_options = self.coloring.action_to_hole_options[choice]
            for hole_index,option in choice_options.items():
                if hole_index == 0:
                    print(0, option)
                hole_selection[hole_index].add(option)
        hole_selection = [list(options) for options in hole_selection]
        return hole_selection


    def fix_policy_for_family(self, family, policy):
        '''
        Apply policy to the quotient MDP for the given family. If a state is reached for which policy does not define
        an action, pick an arbitrary one.
        :return fixed policy
        :return choice mask from which Q-MDP x policy can be constructed
        '''
        invalid_action = self.num_actions
        
        choice_mask = stormpy.BitVector(self.quotient_mdp.nr_choices,False)
        policy_fixed = [invalid_action] * self.quotient_mdp.nr_states

        initial_state = list(self.quotient_mdp.initial_states)[0]
        tm = self.quotient_mdp.transition_matrix
        
        state_visited = stormpy.BitVector(self.quotient_mdp.nr_states,False)
        state_visited.set(initial_state,True)
        state_queue = [initial_state]
        while state_queue:
            state = state_queue.pop()
            action = policy[state]
            if action == invalid_action:
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


    
    def build_game_abstraction_solver(self, prop):
        target_label = str(prop.formula.subformula.subformula)
        solver = stormpy.synthesis.GameAbstractionSolver(
            self.quotient_mdp, len(self.action_labels), self.choice_to_action, target_label
        )
        return solver
