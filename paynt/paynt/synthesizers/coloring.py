import stormpy

from ..sketch.holes import Hole,Holes

from ..profiler import Profiler

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
        self.simple_coloring = None
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

        self.simple_coloring = all([
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

    
    # def simplify_coloring(self):
    #     assert False
    #     print(self.action_to_hole_options)
        
    #     # merge action-memory holes in the same obs-mem pair
    #     # WARNING: in general, this is not safe -- apply only to POMDPs
    #     pairs_to_merge = [
    #         self.state_to_holes[state]
    #         for state in range(self.quotient_mdp.nr_states)
    #         if len(self.state_to_holes[state]) > 1
    #     ]
    #     pairs_to_merge = set([frozenset(x) for x in pairs_to_merge])
    #     pairs_to_merge = [list(x) for x in pairs_to_merge]

    #     hole_merged = [False for hole in holes]
    #     for pair in pairs_to_merge:
    #         for hole_index in pair:
    #             hole_merged[hole_index] = True
        
    #     print(pairs_to_merge)
    #     print(hole_merged)

    #     hole_new_to_old = []
    #     hole_old_to_new = [None for hole in holes]

    #     # copy unmerged holes
    #     holes_new = Holes()
    #     for hole_index,hole in enumerate(holes):
    #         if not hole_merged[hole_index]:
    #             hole_old_to_new[hole_index] = len(holes_new)
    #             hole_new_to_old.append([hole_index])
    #             holes_new.append(hole.copy())

    #     # merge holes
    #     for pair in pairs_to_merge:
    #         hole_new_to_old.append(pair)
    #         for hole_index in pair:
    #             hole_old_to_new[hole_index] = len(holes_new)

    #         ah_index = pair[0]
    #         mh_index = pair[1]
    #         ah = holes[ah_index]
    #         mh = holes[mh_index]

    #         # merge holes
    #         name = ah.name + "+" + mh.name
    #         options = list(range(ah.size * mh.size))
    #         option_labels = []
    #         for action in ah.option_labels:
    #             for update in mh.option_labels:
    #                 option_labels.append(action + "+" + update)
    #         hole = Hole(name,options,option_labels)
    #         holes_new.append(hole)

    #     action_to_hole_options_new = []
    #     for action in range(self.quotient_mdp.nr_choices):
    #         old_hole_options = self.action_to_hole_options[action]
    #         old_hole_options = [(hole,option) for hole,option in old_hole_options.items()]
    #         new_hole_options = {}
    #         if len(old_hole_options) == 1:
    #             old_hole_index,option = old_hole_options[0]
    #             new_hole_options = {hole_old_to_new[old_hole_index]:option}
    #         if len(old_hole_options) == 2:
    #             ah_index,ah_option = old_hole_options[0]
    #             mh_index,mh_option = old_hole_options[1]
    #             new_hole_index = hole_old_to_new[ah_index]
    #             option = ah_option * holes[mh_index].size + mh_option
    #             new_hole_options = {new_hole_index:option}

    #         action_to_hole_options_new.append(new_hole_options)

    #     print(action_to_hole_options_new)

    #     print(holes_new)
    #     exit()

    
    def select_actions(self, family):
        ''' Select non-default actions relevant in the provided design space. '''
        Profiler.start("coloring::select_actions")


        hole_selected_actions = None
        selected_actions = None

        if not self.simple_coloring:
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
        
        Profiler.resume()
        return hole_selected_actions,selected_actions,selected_actions_bv
