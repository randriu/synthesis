import stormpy
import stormpy.synthesis
import stormpy.pomdp

import math
import re
import itertools
from collections import OrderedDict

from .statistic import Statistic

from ..sketch.jani import JaniUnfolder
from ..sketch.property import Property
from ..sketch.holes import Hole,Holes,DesignSpace,CombinationColoring

from ..profiler import Profiler

from .models import MarkovChain,MDP,DTMC

import logging
logger = logging.getLogger(__name__)


class QuotientContainer:

    sketch = None

    def __init__(self, sketch):
        self.sketch = sketch
        
        self.quotient_mdp = None

        self.default_actions = None        
        self.action_to_hole_options = None

    def build(self, design_space):
        if design_space == self.sketch.design_space:
            # quotient needed
            return MDP(self.quotient_mdp, design_space, self)
        
        # must restrict the quotient
        selected_actions = stormpy.BitVector(self.default_actions)
        for act_index in range(self.quotient_mdp.nr_choices):
            if selected_actions.get(act_index):
                continue
            hole_options = self.action_to_hole_options[act_index]
            if design_space.includes(hole_options):
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
        model = submodel_construction.model
        choice_map = submodel_construction.new_to_old_action_mapping
        assert len(choice_map) == model.nr_choices
        
        if design_space.size == 1:
            assert model.nr_choices == model.nr_states
            return DTMC(model) 

        # success
        return MDP(model, design_space, self, choice_map)

    def scheduler_selection(self, mdp, scheduler):
        assert scheduler.memoryless
        assert scheduler.deterministic
        
        selection = [set() for hole_index in mdp.design_space.hole_indices]
        for state in range(mdp.states):
            offset = scheduler.get_choice(state).get_deterministic_choice()
            choice = mdp.model.get_choice_index(state,offset)
            choice = mdp.quotient_choice_map[choice]

            hole_option = self.action_to_hole_options[choice]
            for hole_index,option in hole_option.items():
                selection[hole_index].add(option)

        selection = [list(options) for options in selection]
        return selection

    def scheduler_selection_difference(self, mdp, result):
        # for each choice, compute a scalar product of choice probabilities and destination results
        tm = mdp.model.transition_matrix
        choice_value = stormpy.synthesis.multiply_with_vector(tm,result.get_values())
        
        # get scheduler selection, filter inconsistent assignments
        selection = self.scheduler_selection(mdp, result.scheduler)        
        inconsistent_assignments = {hole_index:options for hole_index,options in enumerate(selection) if len(options)>1}

        # for each hole, compute its difference sum and a number of affected states
        hole_difference_sum = {hole_index: 0 for hole_index in inconsistent_assignments}
        hole_states_affected = {hole_index: 0 for hole_index in inconsistent_assignments}

        for state in range(mdp.states):

            # for this state, compute for each inconsistent hole the difference in choice value between respective options
            hole_min = {hole_index: None for hole_index in inconsistent_assignments}
            hole_max = {hole_index: None for hole_index in inconsistent_assignments}

            for choice in range(tm.get_row_group_start(state),tm.get_row_group_end(state)):
                
                value = choice_value[choice]
                choice_global = mdp.quotient_choice_map[choice]
                if self.default_actions.get(choice_global):
                    continue
                
                # collect holes in which this action is inconsistent
                choice_options = self.action_to_hole_options[choice_global]
                inconsistent_holes = []
                for hole_index,option in choice_options.items():
                    inconsistent_options = inconsistent_assignments.get(hole_index,set())
                    if option in inconsistent_options:
                        inconsistent_holes.append(hole_index)

                for hole_index in inconsistent_holes:
                    current_min = hole_min[hole_index]
                    if current_min is None or value < current_min:
                        hole_min[hole_index] = value
                    current_max = hole_max[hole_index]
                    if current_max is None or value > current_min:
                        hole_max[hole_index] = value

            for hole_index,min_value in hole_min.items():
                if min_value is None:
                    continue
                max_value = hole_max[hole_index]
                difference = max_value - min_value
                hole_difference_sum[hole_index] += difference
                hole_states_affected[hole_index] += 1

        # aggregate
        inconsistent_differences = {
            hole_index: (hole_difference_sum[hole_index] / hole_states_affected[hole_index])
            for hole_index in inconsistent_assignments
            }
        inconsistent_differences = [inconsistent_differences[hole_index] if hole_index in inconsistent_differences else 0 for hole_index in mdp.design_space.hole_indices]

        return selection, inconsistent_differences

    def scheduler_consistent(self, mdp, result):
        '''
        Get hole assignment induced by this scheduler and fill undefined
        holes by some option from the design space of this mdp.
        :return hole assignment
        :return whether the scheduler is consistent
        '''
        scheduler = result.scheduler
        selection = self.scheduler_selection(mdp, scheduler)
        consistent = True
        for hole_index in mdp.design_space.hole_indices:
            options = selection[hole_index]
            if len(options) > 1:
                consistent = False
            if options == []:
                selection[hole_index] = [mdp.design_space[hole_index].options[0]]
        return selection,consistent

    

    def suboptions_half(self, mdp, splitter):
        options = mdp.design_space[splitter].options
        half = len(options) // 2
        suboptions = [options[:half], options[half:]]
        return suboptions

    def suboptions_unique(self, mdp, splitter, used_options):
        suboptions = [[option] for option in used_options]
        index = 0
        for option in mdp.design_space[splitter].options:
            if option in used_options:
                continue
            suboptions[index].append(option)
            index = (index + 1) % len(suboptions)
        return suboptions
        # return self.suboptions_half(mdp, splitter)

    def holes_with_max_score(self, hole_score):
        max_score = max(hole_score)
        with_max_score = [hole_index for hole_index in range(len(hole_score)) if hole_score[hole_index] == max_score]
        return with_max_score

    def most_inconsistent_holes(self, scheduler_assignment):
        num_definitions = [len(options) for options in scheduler_assignment]
        most_inconsistent = self.holes_with_max_score(num_definitions) 
        return most_inconsistent

    
    def prepare_split(self, mdp, results, properties):
        assert not mdp.is_dtmc

        result_primary,result_secondary = results
        scheduler = result_primary.scheduler

        Profiler.start("scheduler_selection")
        # identify the most inconsistent holes
        # hole_assignments = self.scheduler_selection(mdp, scheduler)
        # inconsistent = self.most_inconsistent_holes(hole_assignments)
        # hole_sizes = [mdp.design_space[hole_index].size if hole_index in inconsistent else 0 for hole_index in mdp.design_space.hole_indices]
        # splitters = self.holes_with_max_score(hole_sizes)

        hole_assignments,inconsistent_differences = self.scheduler_selection_difference(mdp, result_primary)
        splitters = self.holes_with_max_score(inconsistent_differences)

        splitter = splitters[0]
        Profiler.start("synthesis")
        
        # self.splitter_frequency[splitter] += 1
        # if sum(self.splitter_frequency) % 100 == 0:
        #     for obs in range(self.pomdp.nr_observations):
        #         action_freq = [self.splitter_frequency[hole_index] for hole_index in self.pomdp_manager.action_holes[obs]]
        #         memory_freq = [self.splitter_frequency[hole_index] for hole_index in self.pomdp_manager.memory_holes[obs]]
        #         print("{}: {} & {}".format(obs,action_freq,memory_freq))
        
        # split
        # suboptions = self.suboptions_half(mdp, splitter)
        suboptions = self.suboptions_unique(mdp, splitter, hole_assignments[splitter])

        # construct corresponding design subspaces
        design_subspaces = []
        for suboption in suboptions:
            design_subspace = mdp.design_space.assume_hole_suboptions(splitter, suboption)
            design_subspaces.append(design_subspace)
        return design_subspaces



class JaniQuotientContainer(QuotientContainer):
    
    def __init__(self, *args):
        super().__init__(*args)

        # unfold jani program
        unfolder = JaniUnfolder(self.sketch)
        self.sketch.properties = unfolder.properties
        self.sketch.optimality_property = unfolder.optimality_property
        self.sketch.design_space.set_properties(self.sketch.properties)

        # build quotient MDP       
        edge_to_hole_options = unfolder.edge_to_hole_options
        self.quotient_mdp = stormpy.build_sparse_model_with_options(unfolder.jani_unfolded, MarkovChain.builder_options)

        # associate each action of a quotient MDP with hole options
        # remember default actions (actions taken in each hole assignment)
        # TODO handle overlapping colors
        num_choices = self.quotient_mdp.nr_choices

        self.default_actions = stormpy.BitVector(num_choices, False)
        self.action_to_hole_options = []
        tm = self.quotient_mdp.transition_matrix
        for choice in range(num_choices):
            edges = self.quotient_mdp.choice_origins.get_edge_index_set(choice)            
            hole_options = {}
            for edge in edges:
                combination = edge_to_hole_options.get(edge, None)
                if combination is None:
                    continue
                for hole_index,option in combination.items():
                    options = hole_options.get(hole_index,set())
                    options.add(option)
                    hole_options[hole_index] = options

            for hole_index,options in hole_options.items():
                assert len(options) == 1
            hole_options = {hole_index:list(options)[0] for hole_index,options in hole_options.items()}

            self.action_to_hole_options.append(hole_options)
            if len(hole_options) == 0:
                self.default_actions.set(choice)

        self.splitter_frequency = [0] * self.sketch.design_space.num_holes


    
class POMDPQuotientContainer(QuotientContainer):

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
        self.action_to_hole_options = None
        self.default_actions = None

        # construct quotient POMDP
        MarkovChain.builder_options.set_build_choice_labels(True)
        self.pomdp = stormpy.build_sparse_model_with_options(self.sketch.prism, MarkovChain.builder_options)
        assert self.pomdp.labeling.get_states("overlap_guards").number_of_set_bits() == 0
        self.pomdp = stormpy.pomdp.make_canonic(self.pomdp)
        # ^ this also asserts that states with the same observation have the same number of available actions
        print("observations: ", self.pomdp.observations)

        # extract observation labels
        ov = self.pomdp.observation_valuations
        self.observation_labels = [ov.get_string(obs) for obs in range(self.pomdp.nr_observations)]
        self.observation_labels = [self.process_label(label) for label in self.observation_labels]
        print("observation labels: ", self.observation_labels)

        # compute actions available at each observation
        self.actions_at_observation = [0] * self.pomdp.nr_observations
        for state in range(self.pomdp.nr_states):
            obs = self.pomdp.observations[state]
            if self.actions_at_observation[obs] != 0:
                continue
            self.actions_at_observation[obs] = self.pomdp.get_nr_available_actions(state)
        print("actions at observations: ", self.actions_at_observation)

        # collect labels of actions available at each observation
        self.action_labels_at_observation = [[] for obs in range(self.pomdp.nr_observations)]
        for state in range(self.pomdp.nr_states):
            obs = self.pomdp.observations[state]
            if self.action_labels_at_observation[obs] != []:
                continue
            actions = self.pomdp.get_nr_available_actions(state)
            for offset in range(actions):
                choice = self.pomdp.get_choice_index(state,offset)
                labels = self.pomdp.choice_labeling.get_labels_of_choice(choice)
                self.action_labels_at_observation[obs].append(labels)
        # print("labels of actions at observations: ", self.action_labels_at_observation)

        self.pomdp_manager = stormpy.synthesis.PomdpManager(self.pomdp)

    def process_label(self,label):
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

    def suggest_injection(self):
        max_splits_value = max(self.splitter_frequency)
        hole_index = self.splitter_frequency.index(max_splits_value)
        pm = self.pomdp_manager
        for obs in range(self.pomdp.nr_observations):
            if hole_index in pm.action_holes[obs] or hole_index in pm.memory_holes[obs]:
                return obs
        assert(False)


    def unfoldPartialMemory(self):

        pomdp = self.pomdp
        pm = self.pomdp_manager

        self.quotient_mdp = pm.construct_mdp()
        mdp = self.quotient_mdp
        # print("MDP states: ", mdp.nr_states)
        # print("MDP rows: ", mdp.nr_choices)

        print("# of observations:" , pomdp.nr_observations)
        print("# of holes: ", pm.num_holes)
        print("action holes: ", pm.action_holes)
        print("memory holes: ", pm.memory_holes)
        print("hole options: ", pm.hole_options)
        print("", flush=True)

        # create holes
        holes = Holes()
        for hole_index in range(pm.num_holes):
            holes.append(None)

        # create action holes
        for obs,hole_indices in enumerate(pm.action_holes):
            obs_label = self.observation_labels[obs]
            action_labels = self.action_labels_at_observation[obs]
            for mem,hole_index in enumerate(hole_indices):
                name = "A({},{})".format(obs_label,mem)
                options = list(range(pm.hole_options[hole_index]))
                option_labels = [str(labels) for labels in action_labels]
                hole = Hole(name, options, option_labels)
                holes[hole_index] = hole

        # create memory holes
        for obs,hole_indices in enumerate(pm.memory_holes):
            obs_label = self.observation_labels[obs]
            for mem,hole_index in enumerate(hole_indices):
                name = "M({},{})".format(obs_label,mem)
                options = list(range(pm.hole_options[hole_index]))
                option_labels = [str(o) for o in options]
                hole = Hole(name, options, option_labels)
                holes[hole_index] = hole

        # create domains for each hole
        self.design_space = DesignSpace(holes, self.sketch.properties)
        self.sketch.design_space = self.design_space
        # print("design space: ", self.design_space)

        # associate actions with hole combinations (colors)
        self.combination_coloring = CombinationColoring(holes)
        self.action_to_hole_options = []
        num_choices = mdp.nr_choices

        self.default_actions = stormpy.BitVector(num_choices, False)
        
        for row in range(num_choices):
            relevant_holes = {}
            action_hole = pm.row_action_hole[row]
            if action_hole != pm.num_holes:
                relevant_holes[action_hole] = pm.row_action_option[row]
            memory_hole = pm.row_memory_hole[row]
            if memory_hole != pm.num_holes:
                relevant_holes[memory_hole] = pm.row_memory_option[row]
            if not relevant_holes:
                self.action_to_hole_options.append({})
                self.default_actions.set(row)
                continue

            self.action_to_hole_options.append(relevant_holes)

        self.splitter_frequency = [0] * self.design_space.num_holes


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
        self.holes_action = []
        self.holes_memory = []
        hole_index = 0
        holes = Holes()

        for obs in range(self.pomdp.nr_observations):
            obs_label = self.observation_labels[obs]
            obs_actions = self.actions_at_observation[obs]
            action_labels = self.action_labels_at_observation[obs]

            self.holes_action.append([])
            self.holes_memory.append([])
            for mem in range(memory_size):
                string = "({},{})".format(obs_label,mem)

                # create action hole
                name = "A" + string
                options = list(range(obs_actions))
                option_labels = [str(labels) for labels in action_labels]
                hole = Hole(name,options,option_labels)
                self.holes_action[obs].append(holes.num_holes)
                holes.append(hole)

                # create memory hole
                name = "M" + string
                options = list(range(memory_size))
                option_labels = [str(o) for o in options]
                hole = Hole(name,options,option_labels)
                self.holes_memory[obs].append(holes.num_holes)
                holes.append(hole)


        self.design_space = DesignSpace(holes, self.sketch.properties)
        self.sketch.design_space = self.design_space
        
        # associate actions with hole combinations (colors)
        # TODO determine reachable holes ?
        self.combination_coloring = CombinationColoring(holes)
        self.action_to_colors = []
        num_choices = self.quotient_mdp.nr_choices
        self.color_0_actions = stormpy.BitVector(num_choices, False)
        
        for state in range(self.quotient_mdp.nr_states):
            obs = self.mdp_to_pomdp_observations[state]
            mem = self.mdp_to_pomdp_memory[state]
            
            action_hole_index = self.holes_action[obs][mem]
            memory_hole_index = self.holes_memory[obs][mem]
            relevant_hole_indices = [action_hole_index, memory_hole_index]
            combinations = [
                hole.options if hole_index in relevant_hole_indices else [None]
                for hole_index,hole in enumerate(self.design_space)
            ]
            for combination in itertools.product(*combinations):            
                color = self.combination_coloring.get_or_make_color(combination)
                self.action_to_colors.append({color})
            # print("hole options in state {} : {}x{}".format(state, len(hole_options[hole_action]), len(hole_options[hole_memory])))
            # print("actions in state {} : {}".format(state, self.model.get_nr_available_actions(state)))

        self.splitter_frequency = [0] * self.design_space.num_holes

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