import stormpy

from .holes import Hole,Holes

import logging
logger = logging.getLogger(__name__)


class MdpColoring:
    ''' Labeling of actions of an MDP with hole options. '''

    def __init__(self, mdp, holes, action_to_hole_options):

        # reference to the quotient MDP
        self.mdp = mdp
        # design space
        self.holes = holes
        # for each choice of the quotient MDP contains a set of hole-option labelings
        self.action_to_hole_options = action_to_hole_options

        # bitvector of quotient MDP choices not labeled by any hole
        self.default_actions = None
        # for each state of the quotient MDP, a set of holes associated with the actions in this state
        self.state_to_holes = None
        # whether each state is marked by at most one hole
        self.coloring_is_simple = None
        # to each hole-option pair a list of actions colored by this combination
        self.hole_option_to_actions = None

        # compute default actions
        self.default_actions = stormpy.BitVector(self.mdp.nr_choices, False)
        for choice in range(self.mdp.nr_choices):
            if not self.action_to_hole_options[choice]:
                self.default_actions.set(choice)

        # collect relevant holes in states
        tm = self.mdp.transition_matrix
        self.state_to_holes = []
        for state in range(self.mdp.nr_states):
            relevant_holes = set()
            for action in range(tm.get_row_group_start(state),tm.get_row_group_end(state)):
                relevant_holes.update(set(self.action_to_hole_options[action].keys()))
            self.state_to_holes.append(relevant_holes)

        self.coloring_is_simple = all([
            len(self.state_to_holes[state])<=1
            for state in range(self.mdp.nr_states)
        ])
        
        # construct reverse coloring
        self.hole_option_to_actions = [[] for hole in self.holes]
        for hole_index,hole in enumerate(self.holes):
            self.hole_option_to_actions[hole_index] = [[] for option in hole.options]
        for action in range(self.mdp.nr_choices):
            for hole_index,option in self.action_to_hole_options[action].items():
                self.hole_option_to_actions[hole_index][option].append(action)


    def __str__(self):
        return str(self.action_to_hole_options)
    

    
    def select_actions(self, family):
        '''
        Select non-default actions relevant in the provided design space.
        @return  a bitvector of all selected actions
        '''


        hole_selected_actions = None
        selected_actions = None

        if not self.coloring_is_simple:

            if family.parent_info is None:
                # select from the super-quotient
                selected_actions = []
                for action in range(self.mdp.nr_choices):
                    if self.default_actions[action]:
                        continue
                    hole_options = self.action_to_hole_options[action]
                    if family.includes(hole_options):
                        selected_actions.append(action)
            else:
                # filter each action in the parent wrt newly restricted design space
                parent_actions = family.parent_info.selected_actions
                selected_actions = []
                for action in parent_actions:
                    hole_options = self.action_to_hole_options[action]
                    # if family.includes(hole_options):
                    if family.parent_info.splitter not in hole_options or family.includes(hole_options):
                        selected_actions.append(action)
        else:
            if family.parent_info is None:
                hole_selected_actions = []
                for hole_index,hole in enumerate(family):
                    hole_actions = []
                    for option in hole.options:
                        hole_actions += self.hole_option_to_actions[hole_index][option]
                    hole_selected_actions.append(hole_actions)

            else:
                hole_selected_actions = family.parent_info.hole_selected_actions.copy()
                splitter = family.parent_info.splitter
                splitter_actions = []
                for option in family[splitter].options:
                    splitter_actions += self.hole_option_to_actions[splitter][option]
                hole_selected_actions[splitter] = splitter_actions

            selected_actions = []
            for actions in hole_selected_actions:
                selected_actions += actions

        # construct bitvector of selected actions
        selected_actions_bv = stormpy.synthesis.construct_selection(self.default_actions, selected_actions)
        
        return hole_selected_actions,selected_actions,selected_actions_bv
