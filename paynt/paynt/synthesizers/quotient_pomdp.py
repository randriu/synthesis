import stormpy
import stormpy.synthesis
import stormpy.pomdp

from .models import MarkovChain,MDP,DTMC
from ..sketch.holes import Hole,Holes,DesignSpace
from .quotient import QuotientContainer
from. coloring import MdpColoring

from ..profiler import Profiler

import math
import re

import logging
logger = logging.getLogger(__name__)


class POMDPQuotientContainer(QuotientContainer):

    # implicit size for POMDP unfolding
    initial_memory_size = 1

    # TODO
    current_family_index = None

    # if True, action-memory hole pairs will be merged into a single hole
    # use_simplified_coloring = False
    use_simplified_coloring = True
    
    def __init__(self, *args):
        super().__init__(*args)

        # default quotient attributes
        self.quotient_mdp = None
        self.coloring = None

        # attributes associated with a (folded) POMDP

        # default POMDP model
        self.pomdp = None
        # a (simplified) label for each observation
        self.observation_labels = None
        # number of actions available at each observation
        self.actions_at_observation = None
        # action labels corresponding to ^
        self.action_labels_at_observation = None
        # for each observation, a prototype of an action hole
        self.action_hole_prototypes = None
        # for each observation, number of states associated with it
        self.observation_states = None
        
        # attributes associated with an unfolded quotient MDP
        
        # number of memory states allocated to each observation
        self.observation_memory_size = None
        # Storm POMDP manager
        self.pomdp_manager = None
        # for each observation, a prototype of a memory hole
        self.memory_hole_prototypes = None
        # for each observation, a list of action holes
        self.observation_action_holes = None
        # for each observation, a list of memory holes
        self.observation_memory_holes = None
        # for each hole, an indication whether this is an action or a memory hole
        self.is_action_hole = None

        # construct the quotient POMDP
        self.pomdp = self.sketch.explicit_quotient
        self.pomdp = stormpy.pomdp.make_canonic(self.pomdp)
        # ^ this also asserts that states with the same observation have the
        # same number and the same order of available actions

        logger.info(f"Constructed POMDP having {self.observations} observations.")
        
        # extract observation labels
        if self.pomdp.has_observation_valuations():
            ov = self.pomdp.observation_valuations
            self.observation_labels = [ov.get_string(obs) for obs in range(self.observations)]
            self.observation_labels = [self.simplify_label(label) for label in self.observation_labels]
        else:
            self.observation_labels = list(range(self.observations))
        logger.debug(f"Observation labels: {self.observation_labels}")

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

        # construct action hole prototypes
        self.action_hole_prototypes = [None] * self.observations
        for obs in range(self.observations):
            num_actions = self.actions_at_observation[obs]
            if num_actions <= 1:
                continue
            name = self.create_hole_name(obs,mem="*",action_hole=True)
            options = list(range(num_actions))
            option_labels = [str(labels) for labels in self.action_labels_at_observation[obs]]
            hole = Hole(name, options, option_labels)
            self.action_hole_prototypes[obs] = hole

        # mark perfect observations
        self.observation_states = [0 for obs in range(self.observations)]
        for state in range(self.pomdp.nr_states):
            obs = self.pomdp.observations[state]
            self.observation_states[obs] += 1

        # initialize POMDP manager
        self.pomdp_manager = stormpy.synthesis.PomdpManager(self.pomdp)
        # do initial unfolding
        self.set_imperfect_memory_size(POMDPQuotientContainer.initial_memory_size)
        # self.set_global_memory_size(POMDPQuotientContainer.initial_memory_size)
        
        

    
    @property
    def observations(self):
        return self.pomdp.nr_observations

    def create_hole_name(self, obs, mem, action_hole):
        category = "A" if action_hole else "M"
        obs_label = self.observation_labels[obs]
        return "{}({},{})".format(category,obs_label,mem)
    
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

    def set_manager_memory_vector(self):
        for obs in range(self.observations):
            mem = self.observation_memory_size[obs]
            self.pomdp_manager.set_observation_memory_size(obs,mem)

    def set_global_memory_size(self, memory_size):
        self.observation_memory_size = [memory_size] * self.observations
        self.set_manager_memory_vector()
        self.unfold_memory()

    def set_imperfect_memory_size(self, memory_size):
        ''' Set given memory size only to imperfect observations. '''
        self.observation_memory_size = [
            memory_size if self.observation_states[obs]>1 else 1
            for obs in range(self.observations)
        ]
        self.set_manager_memory_vector()
        self.unfold_memory()
    
    def increase_memory_size(self, obs):
        self.observation_memory_size[obs] += 1
        self.set_manager_memory_vector()
        self.unfold_memory()

    
    def design_space_counter(self):
        ds = self.sketch.design_space.copy()
        print("ds: ", ds)
        for obs in range(self.observations):
            print(self.observation_memory_holes[obs])
            for mem,hole in enumerate(self.observation_memory_holes[obs]):
                print(ds[hole])
                new_options = [mem]
                if mem < max(ds[hole].options):
                    new_options += [mem+1]
                print(new_options)
                ds[hole].assume_options(new_options)
                print(ds[hole])
                print()
        self.sketch.set_design_space(ds)


    # def family_observation_index(self, family, obs):

    #     # collect all actions and all memory updates
    #     # actions = set()
    #     # for hole in self.observation_action_holes[obs]:
    #     #     actions.update(family[hole].options)
    #     updates = set()
    #     for hole in self.observation_memory_holes[obs]:
    #         updates.update(family[hole].options)
    #     return len(updates)
    #     # return max(len(actions),len(updates))
        
    # def family_index(self,family):

    #     # get reachable holes
    #     reachable_choices = [
    #         family.mdp.quotient_choice_map[choice]
    #         for choice in range(family.mdp.choices)
    #     ]
    #     reachable_holes = set()
    #     for choice in reachable_choices:
    #         choice_holes = self.coloring.action_to_hole_options[choice].keys()
    #         reachable_holes.update(choice_holes)

    #     # in each observation, count how many action/memory holes are reachable;
    #     # observation index is then the maximum number of action OR memory holes
    #     # associated with this observation
    #     obs_indices = []
    #     for obs in range(self.observations):
    #         reachable_action_holes = [
    #             hole for hole in self.observation_action_holes[obs]
    #             if hole in reachable_holes
    #         ]
    #         reachable_memory_holes = [
    #             hole for hole in self.observation_memory_holes[obs]
    #             if hole in reachable_holes
    #         ]
    #         obs_index = max(len(reachable_action_holes),len(reachable_memory_holes))
    #         obs_indices.append(obs_index)

    #     # family index is the maximum observation index
    #     return max(obs_indices)

    # def split(self,family):

    #     if POMDPQuotientContainer.current_family_index == 1:
    #         return super().split(family)

    #     # split hole having number of options equal to the current family index
    #     splitter = None
    #     for obs in range(self.observations):
    #         for hole in self.observation_memory_holes[obs]:
    #             if len(family[hole].options) == POMDPQuotientContainer.current_family_index:
    #                 splitter = hole
    #     print(splitter)
    #     exit()

    
    def unfold_memory(self):
        
        # reset attributes
        self.quotient_mdp = None
        self.coloring = None
        self.memory_hole_prototypes = None
        
        self.observation_action_holes = None
        self.observation_memory_holes = None
        self.is_action_hole = None
        
        # use manager to unfold POMDP
        logger.debug(
            "Unfolding POMDP using the following memory allocation vector: {} ..."
            .format(self.observation_memory_size))
        self.quotient_mdp = self.pomdp_manager.construct_mdp()

        # short aliases
        pm = self.pomdp_manager
        pomdp = self.pomdp
        mdp = self.quotient_mdp

        logger.debug(f"Constructed quotient MDP having {mdp.nr_states} states and {mdp.nr_choices} actions.")

        # detect which observations now involve memory updates
        self.memory_hole_prototypes = [None] * self.observations
        for obs in range(self.observations):
            num_updates = pm.max_successor_memory_size[obs]
            if num_updates <= 1:
                continue
            name = self.create_hole_name(obs,mem="*",action_hole=False)
            options = list(range(num_updates))
            option_labels = [str(x) for x in range(num_updates)]
            hole = Hole(name,options,option_labels)
            self.memory_hole_prototypes[obs] = hole

        # create holes
        all_holes = Holes()
        self.observation_action_holes = []
        self.observation_memory_holes = []
        self.is_action_hole = []

        for obs in range(self.observations):
            
            # action holes
            holes = []
            prototype = self.action_hole_prototypes[obs]
            if prototype is not None:
                for mem in range(self.observation_memory_size[obs]):
                    hole = prototype.copy()
                    hole.name = self.create_hole_name(obs,mem,True)
                    holes.append(all_holes.num_holes)
                    all_holes.append(hole)
                    self.is_action_hole.append(True)
            self.observation_action_holes.append(holes)

            # memory holes
            holes = []
            prototype = self.memory_hole_prototypes[obs]
            if prototype is not None:
                for mem in range(self.observation_memory_size[obs]):
                    hole = prototype.copy()
                    hole.name = self.create_hole_name(obs,mem,False)
                    holes.append(all_holes.num_holes)
                    all_holes.append(hole)
                    self.is_action_hole.append(False)
            self.observation_memory_holes.append(holes)

        # create the coloring
        action_to_hole_options = []
        for action in range(mdp.nr_choices):
            hole_options = {}
            h = pm.row_action_hole[action]
            if h != pm.num_holes:
                hole_options[h] = pm.row_action_option[action]
            h = pm.row_memory_hole[action]
            if h != pm.num_holes:
                hole_options[h] = pm.row_memory_option[action] 
            action_to_hole_options.append(hole_options)
        self.coloring = MdpColoring(self.quotient_mdp, all_holes, action_to_hole_options)
        
        # finalize the design space
        self.sketch.set_design_space(DesignSpace(all_holes))

        # the design space is ready
        if not self.use_simplified_coloring:
            return
        
        # store old coloring
        self.design_space_old = self.sketch.design_space
        self.coloring_old = self.coloring
        # replace with simplified one
        design_space_new,self.coloring,self.obs_to_holes,self.hole_pair_map = self.simplify_coloring()
        self.sketch.set_design_space(design_space_new)


    def simplify_coloring(self):

        # merge action-memory holes in the same obs-mem pair
        obs_to_holes = [[] for obs in range(self.observations)]

        # for each action-memory hole pair, a mapping of its option pairs to new options
        hole_pair_map = {}

        all_holes = Holes()
        for obs in range(self.observations):

            ah = self.action_hole_prototypes[obs]
            mh = self.memory_hole_prototypes[obs]
            
            if ah is not None and mh is None:
                # only action holes
                for old_hole_index in self.observation_action_holes[obs]:
                    old_hole = self.sketch.design_space[old_hole_index]
                    new_hole_index = all_holes.num_holes
                    new_hole = old_hole.copy()
                    hole_pair_map[old_hole_index] = new_hole_index
                    all_holes.append(new_hole)
                    obs_to_holes[obs].append(new_hole_index)

            if ah is None and mh is not None:
                # only memory holes
                for old_hole_index in self.observation_memory_holes[obs]:
                    old_hole = self.sketch.design_space[old_hole_index]
                    new_hole_index = all_holes.num_holes
                    hole_pair_map[old_hole_index] = new_hole_index
                    new_hole = old_hole.copy()
                    all_holes.append(new_hole)
                    obs_to_holes[obs].append(new_hole_index)

            if ah is not None and mh is not None:
                # both types of holes
                for mem in range(self.observation_memory_size[obs]):
                    action_hole_index = self.observation_action_holes[obs][mem]
                    memory_hole_index = self.observation_memory_holes[obs][mem]

                    action_hole = self.sketch.design_space[action_hole_index]
                    memory_hole = self.sketch.design_space[memory_hole_index]

                    name = "AM({},{})".format(self.observation_labels[obs],mem)

                    option_dict = {}
                    options = []
                    option_labels = []
                    for action_option in ah.options:
                        for memory_option in mh.options:
                            option_label = ah.option_labels[action_option] + "+" + mh.option_labels[memory_option]
                            option_labels.append(option_label)

                            option_dict[(action_option,memory_option)] = len(options)
                            options.append(len(options))

                    new_hole_index = all_holes.num_holes
                    obs_to_holes[obs].append(new_hole_index)
                    hole = Hole(name, options, option_labels)
                    hole_pair_map[(action_hole_index,memory_hole_index)] = (new_hole_index,option_dict)
                    all_holes.append(hole)

        # modify the coloring
        action_to_hole_options = self.coloring.action_to_hole_options.copy()
        for action in range(self.quotient_mdp.nr_choices):
            hole_options_old = self.coloring.action_to_hole_options[action]
            if len(hole_options_old) == 0:
                continue

            if len(hole_options_old) == 1:
                old_index = next(iter(hole_options_old.keys()))
                new_index = hole_pair_map[old_index]
                new_option = hole_options_old[old_index]
                action_to_hole_options[action] = {new_index : new_option}
                continue

            # 2 holes
            indices = list(hole_options_old.keys())
            ah_index = indices[0]
            mh_index = indices[1]

            ah_option = hole_options_old[ah_index]
            mh_option = hole_options_old[mh_index]

            new_hole,new_map = hole_pair_map[(ah_index,mh_index)]
            new_hole_options = {new_hole: new_map[(ah_option,mh_option)]}
            action_to_hole_options[action] = new_hole_options

        design_space_new = DesignSpace(all_holes)
        coloring_new = MdpColoring(self.quotient_mdp, all_holes, action_to_hole_options)

        return design_space_new, coloring_new, obs_to_holes, hole_pair_map



    

    
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
            edges_0 = self.coloring.hole_option_to_actions[hole_index][options[0]]
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
                    choice_global = self.coloring.hole_option_to_actions[hole_index][option][choice_index]
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

    
    
    def sift_actions_and_updates(self, obs, hole, options):
        actions = set()
        updates = set()
        num_updates = self.pomdp_manager.max_successor_memory_size[obs]
        for option in options:
            actions.add(option // num_updates)
            updates.add(option %  num_updates)
        return actions,updates

    def break_symmetry_uai(self, family, action_inconsistencies, memory_inconsistencies):
        
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

