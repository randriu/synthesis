
import stormpy
import stormpy.pomdp
import math
import itertools
from collections import OrderedDict

from .statistic import Statistic

from ..sketch.jani import JaniUnfolder
from ..sketch.property import Property
from ..sketch.holes import *

from .models import MarkovChain,MDP

import logging
logger = logging.getLogger(__name__)


class QuotientContainer:

    sketch = None

    def __init__(self, sketch):
        self.sketch = sketch





class JaniQuotientContainer(QuotientContainer):
    
    def __init__(self, *args):
        super().__init__(*args)

        # construct jani program
        self.unfolder = JaniUnfolder(self.sketch)
        self.sketch.properties = self.unfolder.properties
        self.sketch.optimality_property = self.unfolder.optimality_property
        self.sketch.design_space.set_properties(self.sketch.properties)
        self.combination_coloring = self.unfolder.combination_coloring
        self.color_to_edge_indices = self.unfolder.color_to_edge_indices

        self._color_0_actions = None

        # build quotient MDP       
        self.quotient_mdp = stormpy.build_sparse_model_with_options(self.unfolder.jani_unfolded, MarkovChain.builder_options)


    def build(self, design_space):
        if design_space == self.sketch.design_space:
            return MDP(self.sketch, design_space, self.quotient_mdp)
        
        # must restrict the super-mdp
        
        # get colors relevant to this design space
        edge_0_indices = self.color_to_edge_indices.get(0)
        edge_indices = stormpy.FlatSet(edge_0_indices)
        for c in self.combination_coloring.subcolors(design_space):
            edge_indices.insert_set(self.color_to_edge_indices.get(c))

        # compute (and remember) color 0 actions
        co = self.quotient_mdp.choice_origins
        if self._color_0_actions is None:
            self._color_0_actions = stormpy.BitVector(self.quotient_mdp.nr_choices, False)
            for act_index in range(self.quotient_mdp.nr_choices):
                if co.get_edge_index_set(act_index).is_subset_of(edge_0_indices):
                    assert co.get_edge_index_set(act_index).is_subset_of(edge_indices)
                    self._color_0_actions.set(act_index)

        # select actions having relevant colors
        selected_actions = stormpy.BitVector(self._color_0_actions)
        for act_index in range(self.quotient_mdp.nr_choices):
            if selected_actions.get(act_index):
                continue
            # TODO many actions are always taken. We should preprocess these.
            if co.get_edge_index_set(act_index).is_subset_of(edge_indices):
                selected_actions.set(act_index)

        # construct the submodel
        keep_unreachable_states = False
        subsystem_options = stormpy.SubsystemBuilderOptions()
        subsystem_options.build_action_mapping = True
        # subsystem_options.build_state_mapping = True #+
        all_states = stormpy.BitVector(self.quotient_mdp.nr_states, True)
        submodel_construction = stormpy.construct_submodel(
            self.quotient_mdp, all_states, selected_actions, keep_unreachable_states, subsystem_options
        )
        mdp = submodel_construction.model
        choice_map = submodel_construction.new_to_old_action_mapping
        assert len(choice_map) == mdp.nr_choices, \
            f"mapping contains {len(choice_map)} actions, " \
            f"but model has {mdp.nr_choices} actions"
        assert mdp.has_choice_origins()
        if design_space.size == 1:
            assert mdp.nr_choices == mdp.nr_states

        # success
        return MDP(self.sketch, design_space, mdp, choice_map)

    @classmethod
    def prepare_split(self, mdp, mc_result, properties):
        assert not mdp.is_dtmc

        # identify the most inconsistent holes
        hole_selection = mdp.scheduler_selection(mc_result)
        hole_definitions = {hole:len(counts) for hole,counts in hole_selection.items()}        
        max_definitions = max([hole_definitions[hole] for hole in mdp.design_space.holes])
        inconsistent = [hole for hole in mdp.design_space.holes if hole_definitions[hole] == max_definitions]

        # from these holes, identify the one with the largest domain
        splitter = None
        hole_domains = {hole:len(mdp.design_space[hole]) for hole in inconsistent}
        max_domains = max([hole_domains[hole] for hole in inconsistent])
        splitters = [hole for hole in inconsistent if hole_domains[hole] == max_domains]
        splitter = splitters[0]
        
        # split
        options = mdp.design_space[splitter]
        half = len(options) // 2

        suboptions = [options[:half], options[half:]]
        design_subspaces = []
        for suboption in suboptions:
            hole_suboption = HoleOptions(mdp.design_space)
            hole_suboption[splitter] = suboption
            design_subspace = DesignSpace(hole_suboption)
            design_subspace.set_properties(properties)
            design_subspaces.append(design_subspace)

        return design_subspaces[0], design_subspaces[1]
       



    
class POMDPQuotientContainer(QuotientContainer):
    
    def __init__(self, *args):
        super().__init__(*args)
        self.memory_size = self.sketch.pomdp_memory_size

        # quotient POMDP stuff
        self.quotient_pomdp = None
        self.observations = None
        self.actions_at_observation = None

        # (unfolded) quotient MDP stuff
        self.quotient_mdp = None
        self.mdp_to_pomdp_state_map = None
        self.mdp_to_pomdp_observations = None
        self.mdp_to_pomdp_memory = None

        # state space associated with the quotient MDP
        self.holes_action = None
        self.holes_memory = None
        self.design_space = None

        # coloring
        self.combination_coloring = None
        self.action_colors = None
        
        # construct quotient POMDP
        MarkovChain.builder_options.set_build_choice_labels(True)
        self.quotient_pomdp = stormpy.build_sparse_model_with_options(self.sketch.prism, MarkovChain.builder_options)
        assert self.quotient_pomdp.labeling.get_states("overlap_guards").number_of_set_bits() == 0
        self.quotient_pomdp = stormpy.pomdp.make_canonic(self.quotient_pomdp)

        # extract observation labels
        self.observations = self.quotient_pomdp.nr_observations
        ov = self.quotient_pomdp.observation_valuations
        self.observation_labels = [ ov.get_string(obs) for obs in range(self.observations) ]
        print("observation labels: ", self.observation_labels)

        # compute actions available at each observation
        # ensure that states with the same observation have the same number of available actions
        # collect labels of actions available at each observation
        self.actions_at_observation = [0] * self.quotient_pomdp.nr_observations
        self.action_labels_at_observation = [[] for obs in range(self.quotient_pomdp.nr_observations)]
        for state in range(self.quotient_pomdp.nr_states):
            obs = self.quotient_pomdp.observations[state]
            # print("state = {}, obs = {}".format(state,self.observation_labels[obs]))
            if self.actions_at_observation[obs] != 0:
                assert self.actions_at_observation[obs] == self.quotient_pomdp.get_nr_available_actions(state)
                continue
            actions = self.quotient_pomdp.get_nr_available_actions(state)
            self.actions_at_observation[obs] = actions
            for offset in range(actions):
                choice = self.quotient_pomdp.get_choice_index(state,offset)
                labels = self.quotient_pomdp.choice_labeling.get_labels_of_choice(choice)
                self.action_labels_at_observation[obs].append(labels)
        # print("actions at observations: ", self.actions_at_observation)
        print("labels of actions at observations: ", self.action_labels_at_observation)


        # construct memory and unfold into quotient MDP
        memory = stormpy.pomdp.PomdpMemoryBuilder().build(stormpy.pomdp.PomdpMemoryPattern.full, self.memory_size)
        # pomdp.model = stormpy.pomdp.unfold_memory(pomdp.model, memory, add_memory_labels=True, keep_state_valuations=True)
        unfolder = stormpy.pomdp.ExplicitPomdpMemoryUnfolder(self.quotient_pomdp,memory)
        self.quotient_mdp = unfolder.transform()
        self.mdp_to_pomdp_state_map = unfolder.state_to_state()
        self.mdp_to_pomdp_memory = unfolder.state_to_memory()
        self.mdp_to_pomdp_observations = [
            self.quotient_pomdp.observations[self.mdp_to_pomdp_state_map[s]]
            for s in range(self.quotient_mdp.nr_states)
        ]

        # create holes for each observation-memory pair
        self.holes_action = dict()
        self.holes_memory = dict()
        for obs in range(self.observations):
            obs_label = self.observation_labels[obs]
            for mem in range(self.memory_size):
                string = "({},{})".format(obs_label,mem)
                hole_action = "A" + string
                hole_memory = "N" + string
                self.holes_action[(obs,mem)] = hole_action
                self.holes_memory[(obs,mem)] = hole_memory

        # create domains for each hole
        hole_options = HoleOptions()
        for obs in range(self.observations):
            for mem in range(self.memory_size):                
                hole_options[self.holes_action[(obs,mem)]] = list(range(self.actions_at_observation[obs]))
                hole_options[self.holes_memory[(obs,mem)]] = list(range(self.memory_size))
        self.design_space = DesignSpace(hole_options, self.sketch.properties)
        # print(self.design_space)

        # associate actions with hole combinations (colors)
        # TODO determine reachable holes ?
        self.combination_coloring = CombinationColoring(hole_options)
        self.action_colors = []

        for state in range(self.quotient_mdp.nr_states):
            obs = self.mdp_to_pomdp_observations[state]
            mem = self.mdp_to_pomdp_memory[state]
            
            hole_action = self.holes_action[(obs,mem)]
            hole_memory = self.holes_memory[(obs,mem)]
            relevant_holes = [hole_action, hole_memory]
            combinations = [
                range(len(hole_options[hole])) if hole in relevant_holes else [None]
                for hole in hole_options.holes
            ]
            for combination in itertools.product(*combinations):            
                color = self.combination_coloring.get_or_make_color(combination)
                self.action_colors.append(color)
            # print("hole options in state {} : {}x{}".format(state, len(hole_options[hole_action]), len(hole_options[hole_memory])))
            # print("actions in state {} : {}".format(state, self.model.get_nr_available_actions(state)))


        # print(self.combination_coloring)
        # print(self.action_colors)
        
        # x = self.quotient_pomdp
        # print(type(x), dir(x))
        # print("")
        # print("states: ", x.nr_states)

        # print("")
        # print("observations: ", self.origin.nr_observations)

        # print("state -> observation: ", self.origin.observations)

        # print("has observation valuation: ", x.has_observation_valuations())
        # ov = x.observation_valuations
        # print(type(ov), dir(ov))
        # for state in range(x.nr_observations):
        #     print(ov.get_string(state))

        # print("")
        # print("choices: ", self.origin.nr_choices)
        # print("actions: ", [self.origin.get_nr_available_actions(s) for s in range(self.origin.nr_states)])
        # print("nondet indices: ", self.origin.nondeterministic_choice_indices)

        # note: actions in each state are sorted (accoring to labels appearing
        # in the first state; therefore, we can refer to these actions using
        # indices that are consistent throughout the state space
        
        # print(self.origin.has_choice_origins())
        # print("has choice labeling: ", self.origin.has_choice_labeling())
        # l = self.origin.choice_labeling
        # print(type(l), dir(l))
        # for choice in range(self.origin.nr_choices):
        #     print(choice, l.get_labels_of_choice(choice))
        
        # print("\n>> transformation ...\n")

        
        # y = self.quotient_mdp
        # print("states: ", y.nr_states)
        # print("state map: ", self.mdp_to_pomdp_state_map)
        # print("observations: ", y.nr_observations)
        # print("state -> observation: ", self.model.observations)
        # print("has observation valuation: ", self.model.has_observation_valuations())
        # print("observation map: ", self.observation_map)
        # print("memory map: ", self.memory_map)
        # print("")
        # print("choices: ", self.model.nr_choices)
        # print("actions: ", [self.model.get_nr_available_actions(s) for s in range(self.model.nr_states)])

    def build(self, design_space):
        if design_space == self.sketch.design_space:
            return MDP(self.sketch, design_space, self.quotient_mdp)

        # must restrict the super-mdp
        
        # get colors relevant to this design space
        # TODO optimize this
        relevant_colors = self.combination_coloring.subcolors(design_space)
        relevant_colors.add(0)
        relevant_actions = [action for action,color in enumerate(self.action_colors) if color in relevant_colors]
        selected_actions = stormpy.BitVector(self.quotient_mdp.nr_choices)
        for action in relevant_actions:
            selected_actions.set(action)


        # construct the submodel
        keep_unreachable_states = False
        subsystem_options = stormpy.SubsystemBuilderOptions()
        subsystem_options.build_action_mapping = True
        # subsystem_options.build_state_mapping = True #+
        all_states = stormpy.BitVector(self.quotient_mdp.nr_states, True)
        submodel_construction = stormpy.construct_submodel(
            self.quotient_mdp, all_states, selected_actions, keep_unreachable_states, subsystem_options
        )
        mdp = submodel_construction.model
        choice_map = submodel_construction.new_to_old_action_mapping
        assert len(choice_map) == mdp.nr_choices, \
            f"mapping contains {len(choice_map)} actions, " \
            f"but model has {mdp.nr_choices} actions"
        # assert mdp.has_choice_origins()
        if design_space.size == 1:
            assert mdp.nr_choices == mdp.nr_states

        # success
        return MDP(self.sketch, design_space, mdp, choice_map)

    def prepare_split(self, mdp, mc_result, properties):
        assert not mdp.is_dtmc

        # identify the most inconsistent holes
        # TODO POMDP does not have choice origins, so we cannot apply scheduler
        inconsistent = [hole for hole in mdp.design_space.holes]
        
        # from these holes, identify the one with the largest domain
        splitter = None
        hole_domains = {hole:len(mdp.design_space[hole]) for hole in inconsistent}
        max_domains = max([hole_domains[hole] for hole in inconsistent])
        splitters = [hole for hole in inconsistent if hole_domains[hole] == max_domains]
        splitter = splitters[0]
        
        # split
        options = mdp.design_space[splitter]
        half = len(options) // 2

        suboptions = [options[:half], options[half:]]
        design_subspaces = []
        for suboption in suboptions:
            hole_suboption = HoleOptions(mdp.design_space)
            hole_suboption[splitter] = suboption
            design_subspace = DesignSpace(hole_suboption)
            design_subspace.set_properties(properties)
            design_subspaces.append(design_subspace)

        return design_subspaces[0], design_subspaces[1]

