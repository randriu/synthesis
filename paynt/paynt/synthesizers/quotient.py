import stormpy
import stormpy.synthesis
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
        
        self.quotient_mdp = None
        self.combination_coloring = None
        self.action_to_colors = None
        self.color_0_actions = None

    def build(self, design_space):
        if design_space == self.sketch.design_space:
            # quotient needed
            return MDP(self.sketch, design_space, self.quotient_mdp, self)
        
        # must restrict the quotient
        # get actions having colors associated this design space
        relevant_colors = self.combination_coloring.subcolors(design_space)
        selected_actions = stormpy.BitVector(self.color_0_actions)
        for act_index in range(self.quotient_mdp.nr_choices):
            if selected_actions.get(act_index):
                continue
            if self.action_to_colors[act_index].issubset(relevant_colors):
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
        assert len(choice_map) == mdp.nr_choices
        if design_space.size == 1:
            assert mdp.nr_choices == mdp.nr_states

        # success
        return MDP(self.sketch, design_space, mdp, self, choice_map)

    def scheduler_colors(self, mdp, scheduler):
        ''' Get all colors involved in the choices of this scheduler. '''
        colors = set()
        for state in range(mdp.states):
            offset = scheduler.get_choice(state).get_deterministic_choice()
            choice = mdp.model.get_choice_index(state,offset)
            if mdp.quotient_choice_map is not None:
                choice = mdp.quotient_choice_map[choice]
            choice_colors = self.action_to_colors[choice]
            colors.update(choice_colors)
        return colors

    def scheduler_selection(self, mdp, scheduler):
        ''' Get hole assignments used in this scheduler. '''
        assert scheduler.memoryless
        assert scheduler.deterministic

        # collect colors of selected actions
        colors = self.scheduler_colors(mdp, scheduler)
        
        # translate colors to hole assignments
        selection = self.combination_coloring.get_hole_assignments(colors)
        return selection

    def scheduler_consistent(self, mdp, scheduler):
        '''
        Get hole assignment induced by this scheduler and fill undefined
        holes by some option from the design space of this mdp.
        :return hole assignment
        :return whether the scheduler is consistent
        '''
        selection = self.scheduler_selection(mdp, scheduler)
        consistent = True
        for hole in mdp.design_space.holes:
            options = selection[hole]
            if len(options) > 1:
                consistent = False
            if options == []:
                selection[hole] = [mdp.design_space[hole][0]]
        return selection,consistent

    def prepare_split(self, mdp, mc_result, properties):
        assert not mdp.is_dtmc

        # identify the most inconsistent holes
        hole_assignments = self.scheduler_selection(mdp, mc_result.scheduler)
        hole_definitions = {hole:len(options) for hole,options in hole_assignments.items()}
        max_definitions = max([hole_definitions[hole] for hole in mdp.design_space.holes])
        inconsistent = [hole for hole in mdp.design_space.holes if hole_definitions[hole] == max_definitions]
        # inconsistent = [hole for hole in mdp.design_space.holes]

        # from these holes, identify the one with the largest domain
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
            design_subspace = DesignSpace(mdp.design_space)
            design_subspace[splitter] = suboption
            design_subspace.set_properties(properties)
            design_subspaces.append(design_subspace)

        return design_subspaces[0], design_subspaces[1]


    def test_family(self, family, optimality_property):
        pass

        # family["A([o=1],0)"] = [0]
        # # family["A([o=1],1)"] = [0]
        # print(family)

        # mdp = self.build(family)
        # result = mdp.analyze_property(optimality_property)
        # at_init = mdp.at_initial_state(result)
        # print(" MDP min: ", at_init)

        # assignment,_ = self.scheduler_consistent(mdp,result.scheduler)
        # assignment = HoleOptions(assignment)
        # # print(assignment)

        # mdp = self.build(assignment)
        # result2 = mdp.analyze_property(optimality_property)
        # at_init2 = mdp.at_initial_state(result2)

        # print("DTMC min: ", at_init2)

        # exit()





class JaniQuotientContainer(QuotientContainer):
    
    def __init__(self, *args):
        super().__init__(*args)

        # unfold jani program
        unfolder = JaniUnfolder(self.sketch)
        self.sketch.properties = unfolder.properties
        self.sketch.optimality_property = unfolder.optimality_property
        self.sketch.design_space.set_properties(self.sketch.properties)
        self.combination_coloring = unfolder.combination_coloring

        # build quotient MDP       
        self.quotient_mdp = stormpy.build_sparse_model_with_options(unfolder.jani_unfolded, MarkovChain.builder_options)

        # associate action of a quotient MDP with a set of colors
        # remember color-0 actions
        num_choices = self.quotient_mdp.nr_choices
        self.action_to_colors = []
        self.color_0_actions = stormpy.BitVector(num_choices, False)
        for act_index in range(num_choices):
            edges = self.quotient_mdp.choice_origins.get_edge_index_set(act_index)
            colors = {unfolder.edge_to_color[edge] for edge in edges}
            if colors == {0}:
                self.color_0_actions.set(act_index)
            self.action_to_colors.append(colors)

    
class POMDPQuotientContainer(QuotientContainer):

    full_memory_size = 2
    
    def __init__(self, *args):
        super().__init__(*args)
        
        # quotient POMDP stuff
        self.pomdp = None
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
        self.action_to_colors = None

        # construct quotient POMDP
        MarkovChain.builder_options.set_build_choice_labels(True)
        self.pomdp = stormpy.build_sparse_model_with_options(self.sketch.prism, MarkovChain.builder_options)
        assert self.pomdp.labeling.get_states("overlap_guards").number_of_set_bits() == 0
        self.pomdp = stormpy.pomdp.make_canonic(self.pomdp)
        # ^ this also asserts that states with the same observation have the same number of available actions
        print("observations: ", self.pomdp.observations)


        # extract observation labels
        ov = self.pomdp.observation_valuations
        self.observation_labels = [ ov.get_string(obs) for obs in range(self.pomdp.nr_observations) ]
        print("observation labels: ", self.observation_labels)

        # compute actions available at each observation
        self.actions_at_observation = [0] * self.pomdp.nr_observations
        for state in range(self.pomdp.nr_states):
            obs = self.pomdp.observations[state]
            if self.actions_at_observation[obs] != 0:
                continue
            self.actions_at_observation[obs] = self.pomdp.get_nr_available_actions(state)
        print("actions at observations: ", self.actions_at_observation)

        self.unfoldFullMemory(POMDPQuotientContainer.full_memory_size)

        # self.pomdp_manager = stormpy.synthesis.PomdpManager(self.pomdp)
        # self.pomdp_manager.inject_memory(0)
        # self.pomdp_manager.inject_memory(4)
        # self.pomdp_manager.inject_memory_all()
        # self.pomdp_manager.inject_memory_all()
        # self.pomdp_manager.inject_memory(0)
        # self.unfoldPartialMemory()


    def unfoldPartialMemory(self):

        pomdp = self.pomdp
        pm = self.pomdp_manager

        self.quotient_mdp = pm.construct_mdp()
        mdp = self.quotient_mdp
        print(mdp.nr_states)
        print(mdp.nr_choices)

        print("# holes: ", pm.num_holes)
        print("action holes: ", pm.action_holes)
        print("memory holes: ", pm.memory_holes)
        print("hole options: ", pm.hole_options)
        print("row -> action hole: ", pm.row_action_hole)
        print("row -> action option: ", pm.row_action_option)
        print("row -> memory hole: ", pm.row_memory_hole)
        print("row -> memory option: ", pm.row_memory_option)

        # create holes names
        self.hole_names = [""] * pm.num_holes
        for obs,hole_indices in enumerate(pm.action_holes):
            obs_label = self.observation_labels[obs]
            for mem,hole_index in enumerate(hole_indices):
                self.hole_names[hole_index] = "A({},{})".format(obs_label,mem)
        for obs,hole_indices in enumerate(pm.memory_holes):
            obs_label = self.observation_labels[obs]
            for mem,hole_index in enumerate(hole_indices):
                self.hole_names[hole_index] = "N({},{})".format(obs_label,mem)
        print(self.hole_names)

        # create domains for each hole
        hole_options = HoleOptions()
        for hole_index in range(pm.num_holes):
            hole_options[hole_index] = list(range(pm.hole_options[hole_index]))
        self.design_space = DesignSpace(hole_options, self.sketch.properties)
        self.sketch.design_space = self.design_space
        print(self.design_space)

        # associate actions with hole combinations (colors)
        self.combination_coloring = CombinationColoring(hole_options)
        self.action_to_colors = []
        num_choices = mdp.nr_choices
        self.color_0_actions = stormpy.BitVector(num_choices, False)
        
        for row in range(num_choices):
            relevant_holes = {}
            action_hole = pm.row_action_hole[row]
            if action_hole != pm.num_holes:
                relevant_holes[action_hole] = pm.row_action_option[row]
            memory_hole = pm.row_memory_hole[row]
            if memory_hole != pm.num_holes:
                relevant_holes[memory_hole] = pm.row_memory_option[row]
            if not relevant_holes:
                self.color_0_actions.set(row)
                self.action_to_colors.append({0})
                continue

            combination = tuple(
                relevant_holes[hole] if hole in relevant_holes else None
                for hole in hole_options.holes
            )
            color = self.combination_coloring.get_or_make_color(combination)
            self.action_to_colors.append({color})


    def unfoldFullMemory(self, memory_size):

        # construct memory model and unfold it into quotient MDP
        memory = stormpy.pomdp.PomdpMemoryBuilder().build(stormpy.pomdp.PomdpMemoryPattern.full, memory_size)
        # pomdp.model = stormpy.pomdp.unfold_memory(pomdp.model, memory, add_memory_labels=True, keep_state_valuations=True)
        unfolder = stormpy.synthesis.ExplicitPomdpMemoryUnfolder(self.pomdp,memory)
        self.quotient_mdp = unfolder.transform()
        self.mdp_to_pomdp_state_map = unfolder.state_to_state()
        self.mdp_to_pomdp_memory = unfolder.state_to_memory()
        self.mdp_to_pomdp_observations = [
            self.pomdp.observations[self.mdp_to_pomdp_state_map[s]]
            for s in range(self.quotient_mdp.nr_states)
        ]

        # create holes for each observation-memory pair
        self.holes_action = dict()
        self.holes_memory = dict()
        for obs in range(self.pomdp.nr_observations):
            obs_label = self.observation_labels[obs]
            for mem in range(memory_size):
                string = "({},{})".format(obs_label,mem)
                hole_action = "A" + string
                hole_memory = "N" + string
                self.holes_action[(obs,mem)] = hole_action
                self.holes_memory[(obs,mem)] = hole_memory

        # create domains for each hole
        hole_options = HoleOptions()
        for obs in range(self.pomdp.nr_observations):
            for mem in range(memory_size):                
                hole_options[self.holes_action[(obs,mem)]] = list(range(self.actions_at_observation[obs]))
                hole_options[self.holes_memory[(obs,mem)]] = list(range(memory_size))
        self.design_space = DesignSpace(hole_options, self.sketch.properties)
        self.sketch.design_space = self.design_space
        # print(self.design_space)

        # associate actions with hole combinations (colors)
        # TODO determine reachable holes ?
        self.combination_coloring = CombinationColoring(hole_options)
        self.action_to_colors = []
        num_choices = self.quotient_mdp.nr_choices
        self.color_0_actions = stormpy.BitVector(num_choices, False)
        
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
                self.action_to_colors.append({color})
            # print("hole options in state {} : {}x{}".format(state, len(hole_options[hole_action]), len(hole_options[hole_memory])))
            # print("actions in state {} : {}".format(state, self.model.get_nr_available_actions(state)))


        # print(self.combination_coloring)
        # print(self.action_colors)
        
        # print("has observation valuation: ", x.has_observation_valuations())
        # ov = x.observation_valuations
        # print(type(ov), dir(ov))
        # for state in range(x.nr_observations):
        #     print(ov.get_string(state))

        # print("")
        # print("choices: ", self.origin.nr_choices)
        # print("actions: ", [self.origin.get_nr_available_actions(s) for s in range(self.origin.nr_states)])

        # print(self.origin.has_choice_origins())
        # print("has choice labeling: ", self.origin.has_choice_labeling())
        # l = self.origin.choice_labeling
        # print(type(l), dir(l))
        # for choice in range(self.origin.nr_choices):
        #     print(choice, l.get_labels_of_choice(choice))