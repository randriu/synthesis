import stormpy
import stormpy.synthesis
import stormpy.pomdp

import math
import re
import itertools

from .statistic import Statistic

from ..sketch.jani import JaniUnfolder
from ..sketch.holes import Hole,Holes,DesignSpace

from .synthesizer import Synthesizer

from .quotient import QuotientContainer

from ..profiler import Profiler

from .models import MarkovChain,MDP,DTMC

import logging
logger = logging.getLogger(__name__)

class POMDPQuotientContainer(QuotientContainer):

    # implicit size for POMDP unfolding
    pomdp_memory_size = 1
    
    def __init__(self, *args):
        super().__init__(*args)

        # default quotient attributes
        self.quotient_mdp = None
        self.action_to_hole_options = None
        self.default_actions = None
        self.state_to_holes = None

        # POMDP attributes
        self.pomdp = None
        self.observation_labels = None
        self.actions_at_observation = None
        self.action_labels_at_observation = None

        # (unfolded) quotient MDP attributes
        self.pomdp_manager = None
        
        # for each observation, a list of holes
        self.obs_to_holes = []
        # number of distinct actions associated with this hole
        self.hole_num_actions = None
        # number of distinct memory updates associated with this hole
        self.hole_num_updates = None

        
        # construct quotient POMDP
        if not self.sketch.is_explicit:
            MarkovChain.builder_options.set_build_choice_labels(True)
            self.pomdp = stormpy.build_sparse_model_with_options(self.sketch.prism, MarkovChain.builder_options)
            MarkovChain.builder_options.set_build_choice_labels(False)
            assert self.pomdp.labeling.get_states("overlap_guards").number_of_set_bits() == 0
        else:
            self.pomdp = self.sketch.explicit_model
        self.pomdp = stormpy.pomdp.make_canonic(self.pomdp)
        # ^ this also asserts that states with the same observation have the same number of available actions

        logger.info(f"Constructed POMDP having {self.observations} observations.")
        
        # extract observation labels
        if self.pomdp.has_observation_valuations():
            ov = self.pomdp.observation_valuations
            self.observation_labels = [ov.get_string(obs) for obs in range(self.observations)]
            self.observation_labels = [self.simplify_label(label) for label in self.observation_labels]
        else:
            self.observation_labels = list(range(self.observations))

        # compute actions available at each observation
        self.actions_at_observation = [0] * self.observations
        for state in range(self.pomdp.nr_states):
            obs = self.pomdp.observations[state]
            if self.actions_at_observation[obs] != 0:
                continue
            self.actions_at_observation[obs] = self.pomdp.get_nr_available_actions(state)

        # collect labels of actions available at each observation
        self.action_labels_at_observation = [[] for obs in range(self.observations)]
        for state in range(self.pomdp.nr_states):
            obs = self.pomdp.observations[state]
            if self.action_labels_at_observation[obs] != []:
                continue
            actions = self.pomdp.get_nr_available_actions(state)
            for offset in range(actions):
                choice = self.pomdp.get_choice_index(state,offset)
                labels = self.pomdp.choice_labeling.get_labels_of_choice(choice)
                self.action_labels_at_observation[obs].append(labels)

        # initialize POMDP manager
        self.pomdp_manager = stormpy.synthesis.PomdpManager(self.pomdp)

    
    @property
    def observations(self):
        return self.pomdp.nr_observations

    def simplify_label(self,label):
        label = re.sub(r"\s+", "", label)
        label = label[1:-1]

        output = "[";
        first = True
        for p in label.split("&"):
            if not p.endswith("=0"):
                if first:
                    first = False
                else:
                    output += " & "
                output += p
        output += "]"
        return output

    def unfold_memory(self):
        
        # reset basic attributes
        self.quotient_mdp = None
        self.action_to_hole_options = None
        self.default_actions = None
        self.state_to_holes = None

        # reset family attributes
        self.obs_to_holes = []
        self.hole_num_actions = None
        self.hole_num_updates = None
        
        # unfold MDP using manager
        self.quotient_mdp = self.pomdp_manager.construct_mdp()
        logger.debug(f"Constructed quotient MDP having {self.quotient_mdp.nr_states} states and {self.quotient_mdp.nr_choices} actions.")

        # short aliases
        pm = self.pomdp_manager
        pomdp = self.pomdp
        mdp = self.quotient_mdp

        # create holes
        holes = Holes()
        self.obs_to_holes = []
        self.hole_num_actions = []
        self.hole_num_updates = []

        for obs in range(self.observations):
            ah = pm.action_holes[obs]
            mh = pm.memory_holes[obs]

            obs_label = self.observation_labels[obs]
            num_actions = self.actions_at_observation[obs]
            num_updates = pm.max_successor_memory_size[obs]
            action_labels = self.action_labels_at_observation[obs]
            action_labels_str = [str(labels) for labels in action_labels]
            memory_labels_str = [str(o) for o in range(num_updates)]

            assert len(ah) == 0 or len(mh) == 0 or len(ah) == len(mh)

            obs_holes = []
            if len(ah) == 0 and len(mh) == 0:
                # no holes
                pass

            elif len(mh) == 0:
                # only action holes
                for mem,old_hole_index in enumerate(ah):

                    name = "A({},{})".format(obs_label,mem)
                    options = list(range(num_actions))
                    hole = Hole(name, options, action_labels_str)

                    obs_holes.append(holes.num_holes)
                    holes.append(hole)
                    self.hole_num_actions.append(num_actions)
                    self.hole_num_updates.append(num_updates)
            
            elif len(ah) == 0:
                # only memory holes
                for mem,old_hole_index in enumerate(mh):
                    name = "M({},{})".format(obs_label,mem)
                    options = list(range(num_updates))
                    memory_labels_str = [str(o) for o in options]
                    hole = Hole(name, options, memory_labels_str)

                    obs_holes.append(holes.num_holes)
                    holes.append(hole)
                    self.hole_num_actions.append(num_actions)
                    self.hole_num_updates.append(num_updates)

            else:
                # pairs of action-memory holes - merge into a single hole
                for mem,action_hole in enumerate(ah):
                    memory_hole = mh[mem]

                    name = "AM({},{})".format(obs_label,mem)
                    
                    num_options = num_actions * num_updates
                    options = list(range(num_options))

                    option_labels = []
                    for action_option in range(num_actions):
                        for memory_option in range(num_updates):
                            option_label = action_labels_str[action_option] + "+" + memory_labels_str[memory_option]
                            option_labels.append(option_label)

                    hole = Hole(name, options, option_labels)
                    obs_holes.append(holes.num_holes)
                    holes.append(hole)
                    self.hole_num_actions.append(num_actions)
                    self.hole_num_updates.append(num_updates)

            self.obs_to_holes.append(obs_holes)

        # associate actions with hole combinations (explicit)
        self.action_to_hole_options = []
        num_choices = mdp.nr_choices

        # reverse mapping
        self.hole_option_to_actions = [[] for hole in holes]
        for hole_index,hole in enumerate(holes):
            self.hole_option_to_actions[hole_index] = [[] for option in hole.options]

        state_prototype = list(pm.state_prototype)
        state_memory = list(pm.state_memory)
        tm = mdp.transition_matrix
        for state in range(mdp.nr_states):
            pomdp_state = state_prototype[state]
            obs = pomdp.observations[pomdp_state]
            obs_holes = self.obs_to_holes[obs]
            if not obs_holes:
                self.action_to_hole_options.append({})
                continue

            mem = state_memory[state]
            hole_index = obs_holes[mem]

            option = 0
            for row in range(tm.get_row_group_start(state),tm.get_row_group_end(state)):
                self.action_to_hole_options.append({hole_index:option})
                self.hole_option_to_actions[hole_index][option].append(row)
                option += 1

        self.compute_default_actions()
        self.compute_state_to_holes()

        # sanity check
        for state in range(mdp.nr_states):
            assert len(self.state_to_holes[state]) <= 1

        # find hole for 
        # for hole in holes:
        #     if hole.name in ["AM([d=1 & l=1],0)", "AM([d=1 & l=1],1)", "AM([d=1 & l=1],2)"]:
        #         hole.options = hole.options[9:]
        #     if hole.name in ["AM([d=1 & r=1],0)", "AM([d=1 & r=1],1)", "AM([d=1 & r=1],2)"]:
        #         hole.options = hole.options[3:6]
        #     if hole.name in ["AM([d=1 & l=1 & r=1],0)", "AM([d=1 & l=1 & r=1],1)", "AM([d=1 & l=1 & r=1],2)"]:
        #         hole.options = hole.options[6:9]
            
        
        self.sketch.design_space = DesignSpace(holes)
        self.sketch.design_space.property_indices = self.sketch.specification.all_constraint_indices()


    def select_actions(self, family):

        Profiler.start("quotient::select_actions")

        assert family is not None

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
        return hole_selected_actions, None, selected_actions_bv

    
    def estimate_scheduler_difference(self, mdp, inconsistent_assignments, choice_values, expected_visits):

        # create inverse map
        # TODO optimize this for multiple properties
        if mdp.quotient_to_restricted_action_map is None:
            quotient_to_restricted_action_map = [None] * self.quotient_mdp.nr_choices
            for action in range(mdp.choices):
                quotient_to_restricted_action_map[mdp.quotient_choice_map[action]] = action

        # for each hole, compute its difference sum and a number of affected states
        inconsistent_differences = {}
        for hole_index,options in inconsistent_assignments.items():
            difference_sum = 0
            states_affected = 0
            edges_0 = self.hole_option_to_actions[hole_index][options[0]]
            for choice_index,_ in enumerate(edges_0):

                choice_0_global = edges_0[choice_index]
                choice_0 = quotient_to_restricted_action_map[choice_0_global]
                if choice_0 is None:
                    continue
                
                source_state = mdp.choice_to_state[choice_0]
                source_state_visits = expected_visits[source_state]
                # assert source_state_visits != 0
                if source_state_visits == 0:
                    continue

                state_values = []
                for option in options:
                    choice_global = self.hole_option_to_actions[hole_index][option][choice_index]
                    choice = quotient_to_restricted_action_map[choice_global]
                    choice_value = choice_values[choice]
                    state_values.append(choice_value)

                min_value = min(state_values)
                max_value = max(state_values)
                difference = (max_value - min_value) * source_state_visits
                assert not math.isnan(difference)
                difference_sum += difference
                states_affected += 1
            
            if states_affected == 0:
                hole_score = 0
            else:
                hole_score = difference_sum / states_affected
            inconsistent_differences[hole_index] = hole_score

        return inconsistent_differences

    
    def break_symmetry(self, family, action_inconsistencies):

        # mark observations having multiple actions and multiple holes, where it makes sense to break symmetry
        obs_with_multiple_holes = { obs for obs,holes in enumerate(self.obs_holes) if len(holes) > 1 }
        if len(obs_with_multiple_holes) == 0:
            return family

        # go through each observation of interest and break symmetry
        restricted_family = family.copy()
        for obs in obs_with_multiple_holes:
            obs_holes = self.obs_to_holes[obs]

            if obs in action_inconsistencies:
                # use inconsistencies to break symmetries
                actions = action_inconsistencies[obs]
            else:
                # remove actions one by one
                actions = list(range(self.hole_num_actions[obs]))
            
            for action_index,hole_index in enumerate(obs_holes):
                action = actions[action_index % len(actions)]
            
                # remove action from options
                options = [option for option in family[hole_index].options if option // quo.hole_num_updates[hole_index] != action]
                restricted_family[hole_index].assume_options(options)
        # logger.debug("Symmetry breaking: reduced design space from {} to {}".format(family.size, restricted_family.size))
        
        return restricted_family

    def break_symmetry_2(self, family, selection):

        # options that are left in the hole
        selection = [ options.copy() for options in selection ]

        # for each observation round-robin inconsistencies from the holes

        options_removed = [[] for hole in selection ]
        
        for obs in range(self.sketch.quotient.observations):
            obs_holes = self.sketch.quotient.obs_to_holes[obs]
            if len(obs_holes) <= 1:
                continue
            
            # count all different assignments in these holes
            option_count = [0] * family[obs_holes[0]].size
            for hole in obs_holes:
                for option in selection[hole]:
                    option_count[option] += 1

            # go through each hole and try to remove duplicates
            while True:
                changed = False
                for hole in obs_holes:
                    can_remove = [option for option in selection[hole] if option_count[option] > 1]
                    if not can_remove:
                        continue
                    option = can_remove[0]
                    selection[hole].remove(option)
                    options_removed[hole].append(option)
                    option_count[option] -= 1
                    changed = True
                if not changed:
                    break

        # remove selected options from the family
        restricted_family = family.copy()
        for hole,removed in enumerate(options_removed):
            new_options = [ option for option in family[hole].options if option not in removed ]
            restricted_family[hole].assume_options(new_options)
        
        logger.debug("Symmetry breaking: reduced design space from {} to {}".format(family.size, restricted_family.size))
        return restricted_family

    def sift_actions_and_updates(self, hole, options):
        actions = set()
        updates = set()
        num_updates = self.hole_num_updates[hole]
        for option in options:
            actions.add(option // num_updates)
            updates.add(option %  num_updates)
        return actions,updates

    def disable_action(self, family, hole, action):
        num_actions = self.hole_num_actions(hole)
        num_updates = self.hole_num_updates(hole)
        to_remove = [ (action * num_updates + update) for update in range(num_updates)]
        new_options = [ option for option in family[hole].options if option not in to_remove ]
        family.assume_hole_options(hole, new_options)

    
    def break_symmetry_3(self, family, action_inconsistencies, memory_inconsistencies):
        
        # go through each observation of interest and break symmetry
        restricted_family = family.copy()
        for obs in range(self.observations):
            
            num_actions = self.actions_at_observation[obs]
            num_updates = self.pomdp_manager.max_successor_memory_size[obs]

            obs_holes = self.obs_to_holes[obs]
            num_holes = len(obs_holes)


            all_actions = [action for action in range(num_actions)]
            selected_actions = [all_actions.copy() for hole in obs_holes]
            
            all_updates = [update for update in range(num_updates)]
            selected_updates = [all_updates.copy() for hole in obs_holes]

            inconsistencies = list(action_inconsistencies[obs])
            num_inc = len(inconsistencies)
            if num_inc > 1:
                # action inconsistency: allocate inconsistent actions between holes
                ignored_actions = [action for action in all_actions if action not in inconsistencies]
                selected_actions = [ignored_actions.copy() for hole in obs_holes]
                for index in range(max(num_holes,num_inc)):
                    selected_actions[index % num_holes].append(inconsistencies[index % num_inc])
            else:
                inconsistencies = list(memory_inconsistencies[obs])
                num_inc = len(inconsistencies)
                if num_inc > 1:
                    # memory inconsistency: distribute inconsistent updates between holes
                    ignored_updates = [update for update in all_updates if update not in inconsistencies]
                    selected_updates = [ignored_updates.copy() for hole in obs_holes]
                    for index in range(max(num_holes,num_inc)):
                        selected_updates[index % num_holes].append(inconsistencies[index % num_inc])

            # create options for each hole
            for index in range(num_holes):
                hole = obs_holes[index]
                actions = selected_actions[index]
                updates = selected_updates[index]
                options = []
                for action in actions:
                    for update in updates:
                        options.append(action * num_updates + update)
                restricted_family[hole].assume_options(options)

        # print(restricted_family)
        logger.debug("Symmetry breaking: reduced design space from {} to {}".format(family.size, restricted_family.size))

        return restricted_family

