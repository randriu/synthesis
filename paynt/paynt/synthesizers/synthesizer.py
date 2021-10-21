
import stormpy
import stormpy.pomdp
import math
import itertools
from collections import OrderedDict

from .statistic import Statistic

from ..sketch import *

from .edge_coloring import EdgeColoring

import logging
logger = logging.getLogger(__name__)


class MarkovChain:

    # options for the construction of chains
    builder_options = None
    # model checking environment (method & precision)
    environment = None

    @classmethod
    def initialize(cls, sketch):

        # builder options
        mc_formulae = [p.formula for p in sketch.properties]
        if sketch.optimality_property is not None:
            mc_formulae.append(sketch.optimality_property.formula)
        cls.builder_options = stormpy.BuilderOptions(mc_formulae)
        cls.builder_options.set_build_with_choice_origins(True)
        cls.builder_options.set_build_state_valuations(True)
        cls.builder_options.set_add_overlapping_guards_label()
    
        # model checking environment
        cls.environment = stormpy.Environment()
        cls.environment.solver_environment.minmax_solver_environment.precision = stormpy.Rational(1e-5)
        cls.set_solver_method(stormpy.MinMaxMethod.policy_iteration) # default for DTMCs

    @classmethod
    def set_solver_method(cls, method):
        cls.environment.solver_environment.minmax_solver_environment.method = method
    
    def __init__(self, sketch):
        self.sketch = sketch

    def build(self, program):
        self.model = stormpy.build_sparse_model_with_options(program, MarkovChain.builder_options)
        assert self.model.labeling.get_states("overlap_guards").number_of_set_bits() == 0

    @property
    def states(self):
        return self.model.nr_states

    @property
    def is_dtmc(self):
        return self.model.nr_choices == self.model.nr_states

    @property
    def initial_state(self):
        return self.model.initial_states[0]

    def at_initial_state(self, array):
        return array.at(self.initial_state)


class DTMC(MarkovChain):

    def __init__(self, sketch, assignment):
        super().__init__(sketch)
        program = sketch.restrict(assignment)
        self.build(program)

    # model check dtmc against a property, return
    # (1) whether the property was satisfied
    # (2) value in the initial state
    def analyze_property(self, prop):
        mc_result = stormpy.model_checking(
            self.model, prop.formula, only_initial_states=False, extract_scheduler=False, environment=self.environment
        )
        return prop.satisfied(value), self.at_initial_state(mc_result)

    # check multiple properties, return False as soon as any one is violated
    def check_properties(self, properties):
        for p in properties:
            sat,_ = self.analyze_property(p)
            if not sat:
                return False
        return True

    # check all properties, return unsatisfiable ones
    def check_properties_all(self, properties):
        unsat_properties = []
        for p in properties:
            sat,_ = self.analyze_property(p)
            if not sat:
                unsat_properties.append(p)
        return unsat_properties

    # model check optimality property, return
    # (1) whether the property was satisfied
    # (2) whether the optimal value was improved
    def check_optimality(self, prop):
        sat,value = self.analyze_property(prop)
        improved = prop.update_optimum(value)
        return sat,improved


class MDP(MarkovChain):

    def __init__(self, sketch, design_space, model, quotient_choice_map = None):
        super().__init__(sketch)
        self.design_space = design_space
        self.model = model
        self.quotient_choice_map = quotient_choice_map
        self.design_subspaces = None

    def analyze_property(self, prop, alt = False):
        '''
        Model check MDP against property.
        :param alt if True, alternative direction will be checked
        :return bounds on satisfiability
        '''
        if self.is_dtmc:
            self.set_solver_method(stormpy.MinMaxMethod.policy_iteration)
        else:
            self.set_solver_method(stormpy.MinMaxMethod.value_iteration)
        formula = prop.formula if not alt else prop.formula_alt
        bounds = stormpy.model_checking(
            self.model, formula, only_initial_states=False,
            extract_scheduler=(not self.is_dtmc), environment=self.environment
        )
        return bounds

    def check_property(self, prop):
        '''
        Model check the underlying quotient MDP against a given formula. Return:
        (1) feasibility: SAT = True, UNSAT = False, undecided = None
        (2) bounds on the primary direction
        (3) bounds on the secondary direction
        '''

        # check primary direction
        bounds_primary = self.analyze_property(prop)
        result_primary = self.at_initial_state(bounds_primary)
        if self.is_dtmc:
            feasible = prop.decided(result_primary,result_primary)
            return feasible,bounds_primary,bounds_primary

        # do we need to check secodary direction?
        if prop.minimizing:
            absolute_min = result_primary
            absolute_max = math.inf
        else:
            absolute_min = -math.inf
            absolute_max = result_primary
        feasible = prop.decided(absolute_min,absolute_max)
        bounds_secondary = None
        if feasible is None:
            # primary direction is not sufficient
            bounds_secondary = self.analyze_property(prop, alt = True)
            result_secondary = self.at_initial_state(bounds_secondary)
            if prop.minimizing:
                absolute_max = result_secondary
            else:
                absolute_min = result_secondary
            feasible = prop.decided(absolute_min,absolute_max)

        return feasible, bounds_primary, bounds_secondary

    def check_properties(self, properties):
        ''' check all properties, return
        (1) satisfiability (True/False/None)
        (2) list of undecided properties
        (3) list of bounds for undecided properties
        '''
        undecided_properties = []
        undecided_bounds = []
        for prop in properties:
            feasible,bounds_primary,bounds_secondary = self.check_property(prop)
            if feasible == False:
                return False, None, None
            if feasible == None:
                undecided_properties.append(prop)
                undecided_bounds.append(bounds_primary)
        feasibility = True if undecided_properties == [] else None
        return feasibility, undecided_properties, undecided_bounds

    def check_optimality(self, prop):
        ''' model check optimality property, return
        (1) bounds in primary direction
        (2) whether the optimal value was improved
        (3) improving assignment if (2) holds
        (4) whether the optimal value (wrt eps) can be improved by refining the
            design space
        '''
        
        # check property
        feasible,bounds_primary,bounds_secondary = self.check_property(prop)
        if feasible == False:
            return bounds_primary,False,None,False
        if feasible == None:
            return bounds_primary,False,None,True

        # all SAT
        # check if primary result is tight
        assignment_primary = self.scheduler_assignment(bounds_primary)
        result_primary_tight = assignment_primary.size == 1
        
        # tight primary result is the best result in this family
        if result_primary_tight:
            improving_assignment = assignment_primary
            result_primary = self.at_initial_state(bounds_primary)
            improved = prop.update_optimum(result_primary)
            assert improved
            return bounds_primary,improved,improving_assignment,False
        
        # use secondary result as new optimum
        result_secondary = self.at_initial_state(bounds_secondary)
        improved = prop.update_optimum(result_secondary)
        assert improved
        improving_assignment = self.design_space.pick_any()
        return bounds_primary,improved,improving_assignment,True

    def scheduler_selection(self, result):
        scheduler = result.scheduler
        assert scheduler.memoryless
        assert scheduler.deterministic        
        
        # apply scheduler
        dtmc = self.model.apply_scheduler(scheduler, drop_unreachable_states=False)
        assert dtmc.has_choice_origins()

        # map states actions to a color
        state_act_to_color = OrderedDict()
        for state in dtmc.states:
            action_index = state.id
            assert len(state.actions) == 1    
            state_act_to_color[action_index] = []
            for e in dtmc.choice_origins.get_edge_index_set(action_index):
                color = self.sketch.choice_origin_to_color[e]
                if color != 0:
                    state_act_to_color[action_index].append([color])
        # print(state_act_to_color)
        
        # map states to hole assignments in this state
        color_map = OrderedDict()
        for state, act_to_colors in state_act_to_color.items():
            color_map[state] = self.sketch.edge_coloring.get_hole_assignments(act_to_colors)
        # print(color_map)
        
        # count all hole assignments
        selected_hole_option_map = dict()
        for state, hole_option_map in color_map.items():
            for hole, option_selection_map in hole_option_map.items():
                e = selected_hole_option_map.get(hole, dict())
                for o in option_selection_map:
                    former_count = e.get(o, 0)
                    e[o] = former_count + 1
                selected_hole_option_map[hole] = e
        # print(selected_hole_option_map)

        # fix undefined hole selections
        selection = OrderedDict()
        for hole in self.design_space.holes:
            if hole not in selected_hole_option_map:
                selected_hole_option_map[hole] = {0:1};


        return selected_hole_option_map

    def scheduler_assignment(self, result):
        if self.is_dtmc:
            return self.design_space.pick_any()

        # extract scheduler selection
        selection = self.scheduler_selection(result)

        # collect positive hole assignments
        assignment = HoleOptions()
        for hole in self.sketch.design_space.holes:
            option_counts = selection[hole]
            selected_options = [index for index in option_counts.keys()  if option_counts[index]>0 ]
            assignment[hole] = [self.sketch.design_space[hole][index] for index in selected_options]

        return assignment






class Synthesizer:
    def __init__(self, sketch):
        MarkovChain.initialize(sketch)

        self.sketch = sketch
        self.design_space = sketch.design_space
        self.properties = sketch.properties
        self.optimality_property = sketch.optimality_property

        self.stat = Statistic(sketch, self.method_name)

    @property
    def method_name(self):
        return "1-by-1"
    
    @property
    def has_optimality(self):
        return self.optimality_property is not None

    def print_stats(self, short_summary = False):
        print(self.stat.get_summary(short_summary))

    def run(self):
        assert not sketch.prism.model_type == stormpy.storage.PrismModelType.POMDP, "1-by-1 method does not support POMDP"
        self.stat.start()
        satisfying_assignment = None
        for hole_combination in self.design_space.all_hole_combinations():
            assignment = self.design_space.construct_assignment(hole_combination)
            dtmc = DTMC(self.sketch, assignment)
            self.stat.iteration_dtmc(dtmc.states)
            constraints_sat = dtmc.check_properties(self.properties)
            self.stat.pruned(1)
            if not constraints_sat:
                continue
            if not self.has_optimality:
                satisfying_assignment = assignment
                break
            _,improved = dtmc.check_optimality(self.optimality_property)
            if improved:
                satisfying_assignment = assignment

        self.stat.finished(satisfying_assignment)


class SynthesizerAR(Synthesizer):
    
    def __init__(self, sketch):
        super().__init__(sketch)
        if sketch.prism.model_type == stormpy.storage.PrismModelType.POMDP:
            self.quotient_container = POMDPQuotientContainer(sketch)
            self.sketch.design_space = self.quotient_container.design_space
            self.stat = Statistic(sketch, self.method_name)
        else:
            sketch.construct_jani()
            self.quotient_container = MDPQuotientContainer(sketch)

    @property
    def method_name(self):
        return "AR"

    def run(self):
        self.stat.start()
        print(self.stat.remaining)
        # exit()

        # initiate AR loop
        satisfying_assignment = None
        families = [self.sketch.design_space]
        while families:
            family = families.pop(-1)
            # logger.debug("analyzing family {}".format(family))
            mdp = self.quotient_container.build(family)
            self.stat.iteration_mdp(mdp.states)
            feasible,undecided_properties,undecided_bounds = mdp.check_properties(family.properties)
            properties = undecided_properties
            if feasible == False:
                # logger.debug("AR: family is UNSAT")
                self.stat.pruned(family.size)
                continue
            
            if feasible == None:
                # logger.debug("AR: family is undecided")
                assert len(undecided_bounds) > 0
                subfamily1, subfamily2 = self.quotient_container.prepare_split(mdp, undecided_bounds[0], properties)
                families.append(subfamily1)
                families.append(subfamily2)
                continue

            # all SAT
            # logger.debug("AR: family is SAT")
            if not self.has_optimality:
                # found feasible solution
                logger.debug("AR: found feasible family")
                satisfying_assignment = family.pick_any()
                break
            
            # must check optimality
            opt_bounds,improved,improving_assignment,can_improve = mdp.check_optimality(self.optimality_property)
            if improved:
                satisfying_assignment = improving_assignment
            if can_improve:
                subfamily1, subfamily2 = self.quotient_container.prepare_split(mdp, opt_bounds, properties)
                families.append(subfamily1)
                families.append(subfamily2)

        # FIXME POMDP hack: replace hole valuations with corresponding action labels
        print("design space: ", self.sketch.design_space)
        print("design space size: ", self.sketch.design_space.size)
        if satisfying_assignment is not None and self.sketch.prism.model_type == stormpy.storage.PrismModelType.POMDP:
            for obs in range(self.quotient_container.observations):
                at_obs = self.quotient_container.action_labels_at_observation[obs]
                for mem in range(self.quotient_container.memory_size):
                    hole = self.quotient_container.holes_action[(obs,mem)]
                    options = satisfying_assignment[hole]
                    satisfying_assignment[hole] = [at_obs[index] for index in options]
        self.stat.finished(satisfying_assignment)



class QuotientContainer:

    sketch = None

    def __init__(self, sketch):
        self.sketch = sketch


    

class MDPQuotientContainer(QuotientContainer):
    
    def __init__(self, *args):
        super().__init__(*args)

        self._color_0_actions = None

        # build quotient MDP
        self.quotient_mdp = None
        mc_formulae = [p.formula for p in self.sketch.properties]
        if self.sketch.optimality_property is not None:
            mc_formulae.append(self.sketch.optimality_property.formula)
        
        self.quotient_mdp = stormpy.build_sparse_model_with_options(self.sketch.jani_unfolded, MarkovChain.builder_options)


    def build(self, design_space):
        if design_space == self.sketch.design_space:
            return MDP(self.sketch, design_space, self.quotient_mdp)
        
        # must restrict the super-mdp
        
        # index the suboptions
        indexed_suboptions = OrderedDict()
        for hole,values in design_space.items():
            indexed_suboptions[hole] = []
            for v in values:
                for index, ref in enumerate(self.sketch.design_space[hole]):
                    if ref == v:
                        indexed_suboptions[hole].append(index)
    
        # get colors relevant to this design space
        edge_0_indices = self.sketch.color_to_edge_indices.get(0)
        edge_indices = stormpy.FlatSet(edge_0_indices)
        for c in self.sketch.edge_coloring.subcolors(indexed_suboptions):
            edge_indices.insert_set(self.sketch.color_to_edge_indices.get(c))

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
        self.edge_coloring = None
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
        self.edge_coloring = EdgeColoring(hole_options)
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
                color = self.edge_coloring.get_or_make_color(combination)
                self.action_colors.append(color)
            # print("hole options in state {} : {}x{}".format(state, len(hole_options[hole_action]), len(hole_options[hole_memory])))
            # print("actions in state {} : {}".format(state, self.model.get_nr_available_actions(state)))


        # print(self.edge_coloring)
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
        
        # index the suboptions
        indexed_suboptions = OrderedDict()
        for hole,values in design_space.items():
            indexed_suboptions[hole] = []
            for v in values:
                for index, ref in enumerate(self.sketch.design_space[hole]):
                    if ref == v:
                        indexed_suboptions[hole].append(index)

        # get colors relevant to this design space
        # TODO optimize this
        relevant_colors = self.edge_coloring.subcolors(indexed_suboptions)
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










class SynthesizerCEGIS(Synthesizer):
    @property
    def method_name(self):
        return "CEGIS"
    
    def run(self):

        satisfying_assignment = None
        self.design_space.z3_initialize()
        self.design_space.z3_encode()

        assignment = self.design_space.pick_assignment()
        while assignment is not None:
            dtmc = DTMC(self.sketch, assignment)
            unsat_properties = dtmc.check_properties_all(self.properties)
            sat_opt,improved = dtmc.check_optimality(self.optimality_property)
            # TODO
            if sat:
                if not self.has_optimality:
                    satisfying_assignment = assignment
                    break
                if improved:
                    satisfying_assignment = assignment

            self.design_space.exclude_assignment(assignment, [index for index in range(len(self.design_space.holes))])
            assignment = self.design_space.pick_assignment()

        self.stat.finished(satisfying_assignment)








    

    












class Family:

    
    def __init__(self, parent=None, design_space=None):
        '''
        Construct a family. Each family is either a superfamily represented by
        a Family._quotient_mdp or a (proper) subfamily that is constructed on
        demand via Family._quotient_container.consider_subset(). Subfamilies
        inherit formulae of interest from their parents.
        '''
        self.design_space = Family.sketch.design_space.copy() if parent is None else design_space
        self.mdp = Family._quotient_mdp if parent is None else None
        self.choice_map = [i for i in range(Family._quotient_mdp.nr_choices)] if parent is None else None
    
        self.design_space.z3_encode()

        # a family that has never been MDP-analyzed is not ready to be split
        self.bounds = [None] * len(self.property_indices)  # assigned when analysis is initiated

        self.suboptions = None
        self.member_assignment = None


class FamilyHybrid(Family):
    ''' Family adopted for CEGAR-CEGIS analysis. '''

    # TODO: more efficient state-hole mapping?

    _choice_to_hole_indices = {}

    def __init__(self, *args):
        super().__init__(*args)

        self._state_to_hole_indices = None  # evaluated on demand

        # dtmc corresponding to the constructed assignment
        self.dtmc = None
        self.dtmc_state_map = None

    def initialize(*args):
        Family.initialize(*args)

        # map edges of a quotient container to hole indices
        jani = Family._quotient_container.jani_program
        _edge_to_hole_indices = dict()
        for aut_index, aut in enumerate(jani.automata):
            for edge_index, edge in enumerate(aut.edges):
                if edge.color == 0:
                    continue
                index = jani.encode_automaton_and_edge_index(aut_index, edge_index)
                assignment = Family._quotient_container.edge_coloring.get_hole_assignment(edge.color)
                hole_indices = [index for index, value in enumerate(assignment) if value is not None]
                _edge_to_hole_indices[index] = hole_indices

        # map actions of a quotient MDP to hole indices
        FamilyHybrid._choice_to_hole_indices = []
        choice_origins = Family._quotient_mdp.choice_origins
        matrix = Family._quotient_mdp.transition_matrix
        for state in range(Family._quotient_mdp.nr_states):
            for choice_index in range(matrix.get_row_group_start(state), matrix.get_row_group_end(state)):
                choice_hole_indices = set()
                for index in choice_origins.get_edge_index_set(choice_index):
                    hole_indices = _edge_to_hole_indices.get(index, set())
                    choice_hole_indices.update(hole_indices)
                FamilyHybrid._choice_to_hole_indices.append(choice_hole_indices)

    def split(self):
        assert self.split_ready
        return FamilyHybrid(self, self.suboptions[0]), FamilyHybrid(self, self.suboptions[1])

    @property
    def state_to_hole_indices(self):
        '''
        Identify holes relevant to the states of the MDP and store only significant ones.
        '''
        # if someone (i.e., CEGIS) asks for state indices, the model should already be analyzed
        assert self.constructed and self.analyzed

        # lazy evaluation
        if self._state_to_hole_indices is not None:
            return self._state_to_hole_indices

        
        # logger.debug("Constructing state-holes mapping via edge-holes mapping.")

        self._state_to_hole_indices = []
        matrix = self.mdp.transition_matrix
        for state in range(self.mdp.nr_states):
            state_hole_indices = set()
            for choice_index in range(matrix.get_row_group_start(state), matrix.get_row_group_end(state)):
                state_hole_indices.update(FamilyHybrid._choice_to_hole_indices[self.choice_map[choice_index]])
            state_hole_indices = set(
                [index for index in state_hole_indices if len(self.design_space[Family.sketch.design_space.holes[index]]) > 1]
            )
            self._state_to_hole_indices.append(state_hole_indices)

        return self._state_to_hole_indices

    @property
    def state_to_hole_indices_choices(self):
        '''
        Identify holes relevant to the states of the MDP and store only significant ones.
        '''
        # if someone (i.e., CEGIS) asks for state indices, the model should already be analyzed
        assert self.constructed and self.analyzed

        # lazy evaluation
        if self._state_to_hole_indices is not None:
            return self._state_to_hole_indices

        Profiler.start("is - MDP holes (choices)")
        logger.debug("Constructing state-holes mapping via choice-holes mapping.")

        self._state_to_hole_indices = []
        matrix = self.mdp.transition_matrix
        for state in range(self.mdp.nr_states):
            state_hole_indices = set()
            for choice_index in range(matrix.get_row_group_start(state), matrix.get_row_group_end(state)):
                quotient_choice_index = self.choice_map[choice_index]
                choice_hole_indices = FamilyHybrid._choice_to_hole_indices[quotient_choice_index]
                state_hole_indices.update(choice_hole_indices)
            state_hole_indices = set(
                [index for index in state_hole_indices if len(self.options[Family.hole_list[index]]) > 1])
            self._state_to_hole_indices.append(state_hole_indices)
        Profiler.stop()
        return self._state_to_hole_indices

    def pick_member(self):
        # pick hole assignment

        self.pick_assignment()
        if self.member_assignment is not None:

            # collect edges relevant for this assignment
            indexed_assignment = Family.sketch.design_space.index_map(self.member_assignment)
            subcolors = Family._quotient_container.edge_coloring.subcolors(indexed_assignment)
            collected_edge_indices = stormpy.FlatSet(
                Family._quotient_container.color_to_edge_indices.get(0, stormpy.FlatSet())
            )
            for c in subcolors:
                collected_edge_indices.insert_set(Family._quotient_container.color_to_edge_indices.get(c))

            # construct the DTMC by exploring the quotient MDP for this subfamily
            self.dtmc, self.dtmc_state_map = stormpy.synthesis.dtmc_from_mdp(self.mdp, collected_edge_indices)
            logger.debug(f"Constructed DTMC of size {self.dtmc.nr_states}.")

            # assert absence of deadlocks or overlapping guards
            # assert self.dtmc.labeling.get_states("deadlock").number_of_set_bits() == 0
            assert self.dtmc.labeling.get_states("overlap_guards").number_of_set_bits() == 0
            assert len(self.dtmc.initial_states) == 1  # to avoid ambiguity

        # success
        return self.member_assignment

    def exclude_member(self, conflicts):
        '''
        Exclude the subfamily induced by the selected assignment and a set of conflicts.
        '''
        assert self.member_assignment is not None

        for conflict in conflicts:
            counterexample_clauses = dict()
            for var, hole in Family._solver_meta_vars.items():
                if Family._hole_indices[hole] in conflict:
                    option_index = Family._hole_option_indices[hole][self.member_assignment[hole][0]]
                    counterexample_clauses[hole] = (var == option_index)
                else:
                    all_options = [var == Family._hole_option_indices[hole][option] for option in self.options[hole]]
                    counterexample_clauses[hole] = z3.Or(all_options)
            counterexample_encoding = z3.Not(z3.And(list(counterexample_clauses.values())))
            Family._solver.add(counterexample_encoding)
        self.member_assignment = None

    def analyze_member(self, formula_index):
        assert self.dtmc is not None
        result = stormpy.model_checking(self.dtmc, Family.formulae[formula_index].formula)
        value = result.at(self.dtmc.initial_states[0])
        satisfied = Family.formulae[formula_index].satisfied(value)
        return satisfied, value

    def print_member(self):
        print("> DTMC info:")
        dtmc = self.dtmc
        tm = dtmc.transition_matrix
        for state in range(dtmc.nr_states):
            row = tm.get_row(state)
            print("> ", str(row))

# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------

# ----- Adaptivity ----- #
# idea: switch between cegar/cegis, allocate more time to the more efficient method

class StageControl:
    # switching
    def __init__(self):
        self.stage_timer = Timer()
        # cegar/cegis stats
        self.stage_time_cegar, self.stage_pruned_cegar, self.stage_time_cegis, self.stage_pruned_cegis = 0, 0, 0, 0
        # multiplier to derive time allocated for cegis; =1 is fair, <1 favours cegar, >1 favours cegis
        self.cegis_allocated_time_factor = 1.0
        # start with AR
        self.stage_cegar = True
        self.cegis_allocated_time = 0

    def start(self, request_stage_cegar):
        self.stage_cegar = request_stage_cegar
        self.stage_timer.reset()
        self.stage_timer.start()

    def step(self, models_pruned):
        '''Performs a stage step, returns True if the method switch took place'''

        # record pruned models
        self.stage_pruned_cegar += models_pruned / self.models_total if self.stage_cegar else 0
        self.stage_pruned_cegis += models_pruned / self.models_total if not self.stage_cegar else 0

        # in cegis mode, allow cegis another stage step if some time remains
        if not self.stage_cegar and self.stage_timer.read() < self.cegis_allocated_time:
            return False

        # stage is finished: record time
        self.stage_timer.stop()
        current_time = self.stage_timer.read()
        if self.stage_cegar:
            # cegar stage over: allocate time for cegis and switch
            self.stage_time_cegar += current_time
            self.cegis_allocated_time = current_time * self.cegis_allocated_time_factor
            self.stage_start(request_stage_cegar=False)
            return True

        # cegis stage over
        self.stage_time_cegis += current_time

        # calculate average success rate, adjust cegis time allocation factor
        success_rate_cegar = self.stage_pruned_cegar / self.stage_time_cegar
        success_rate_cegis = self.stage_pruned_cegis / self.stage_time_cegis
        if self.stage_pruned_cegar == 0 or self.stage_pruned_cegis == 0:
            cegar_dominance = 1
        else:
            cegar_dominance = success_rate_cegar / success_rate_cegis
        cegis_dominance = 1 / cegar_dominance
        self.cegis_allocated_time_factor = cegis_dominance

        # switch back to cegar
        self.start(request_stage_cegar=True)
        return True



class SynthesizerHybrid(Synthesizer):
    
    def __init__(self, sketch):
        super().__init__(sketch)

        sketch.construct_jani()
        sketch.design_space.z3_initialize()
        
        self.stage_control = StageControl()

        # ar family stack
        self.families = []


    @property
    def method_name(self):
        return "hybrid"


    def analyze_family_cegis(self, family):
        return None
        '''
        Analyse a family against selected formulae using precomputed MDP data
        to construct generalized counterexamples.
        '''

        # TODO preprocess only formulae of interest

        logger.debug(f"CEGIS: analyzing family {family.design_space} of size {family.design_space.size}.")

        assert family.constructed
        assert family.analyzed

        # list of relevant holes (open constants) in this subfamily
        relevant_holes = [hole for hole in family.design_space.holes if len(family.hole_options[hole]) > 1]

        # prepare counterexample generator
        logger.debug("CEGIS: preprocessing quotient MDP")
        raw_formulae = [f.property.raw_formula for f in Family.formulae]
        counterexample_generator = stormpy.synthesis.SynthesisCounterexample(
            family.mdp, len(Family.sketch.design_space.holes), family.state_to_hole_indices, raw_formulae, family.bounds
        )
        

        # process family members
        assignment = family.pick_member()

        while assignment is not None:
            logger.debug(f"CEGIS: picked family member: {assignment}.")

            # collect indices of violated formulae
            violated_formulae_indices = []
            for formula_index in family.formulae_indices:
                # logger.debug(f"CEGIS: model checking DTMC against formula with index {formula_index}.")
                sat, result = family.analyze_member(formula_index)
                logger.debug(f"Formula {formula_index} is {'SAT' if sat else 'UNSAT'}")
                if not sat:
                    print(formula_index, result)
                    violated_formulae_indices.append(formula_index)
                formula = Family.formulae[formula_index]
                if sat and formula.optimality:
                    formula.improve_threshold(result)
                    counterexample_generator.replace_formula_threshold(
                        formula_index, formula.threshold, family.bounds[formula_index]
                    )
            # exit()
            if not violated_formulae_indices:
                return True


            # some formulae were UNSAT: construct counterexamples
            counterexample_generator.prepare_dtmc(family.dtmc, family.dtmc_state_map)
            
            conflicts = []
            for formula_index in violated_formulae_indices:
                # logger.debug(f"CEGIS: constructing CE for formula with index {formula_index}.")
                conflict_indices = counterexample_generator.construct_conflict(formula_index)
                # conflict = counterexample_generator.construct(formula_index, self.use_nontrivial_bounds)
                conflict_holes = [Family.hole_list[index] for index in conflict_indices]
                generalized_count = len(Family.hole_list) - len(conflict_holes)
                logger.debug(
                    f"CEGIS: found conflict involving {conflict_holes} (generalized {generalized_count} holes)."
                )
                conflicts.append(conflict_indices)
                print(formula_index, flush=True)
                # exit()

            exit()
            family.exclude_member(conflicts)

            # pick next member
            Profiler.start("is - pick DTMC")
            assignment = family.pick_member()
            Profiler.stop()

            # record stage
            if self.stage_control.step(0):
                # switch requested
                Profiler.add_ce_stats(counterexample_generator.stats)
                return None

        # full family pruned
        logger.debug("CEGIS: no more family members.")
        Profiler.add_ce_stats(counterexample_generator.stats)
        return False

    def run(self):
        
        # initialize family description
        logger.debug("Constructing quotient MDP of the superfamily.")
        self.models_total = self.sketch.design_space.size

        # FamilyHybrid.initialize(self.sketch)

        qmdp = MDP(self.sketch)
        # exit()

        # get the first family to analyze
        
        family = FamilyHybrid()
        family.construct()
        satisfying_assignment = None

        # CEGAR the superfamily
        self.stage_control.stage_start(request_stage_cegar=True)
        feasible, optimal_value = family.analyze()
        exit()

        self.stage_step(0)


        # initiate CEGAR-CEGIS loop (first phase: CEGIS) 
        self.families = [family]
        logger.debug("Initiating CEGAR--CEGIS loop")
        while self.families:
            logger.debug(f"Current number of families: {len(self.families)}")

            # pick a family
            family = self.families.pop(-1)
            if not self.stage_cegar:
                # CEGIS
                feasible = self.analyze_family_cegis(family)
                exit()
                if feasible and isinstance(feasible, bool):
                    logger.debug("CEGIS: some is SAT.")
                    satisfying_assignment = family.member_assignment
                    break
                elif not feasible and isinstance(feasible, bool):
                    logger.debug("CEGIS: all UNSAT.")
                    self.stage_step(family.size)
                    continue
                else:  # feasible is None:
                    # stage interrupted: leave the family to cegar
                    # note: phase was switched implicitly
                    logger.debug("CEGIS: stage interrupted.")
                    self.families.append(family)
                    continue
            else:  # CEGAR
                assert family.split_ready

                # family has already been analysed: discard the parent and refine
                logger.debug("Splitting the family.")
                subfamily_left, subfamily_right = family.split()
                subfamilies = [subfamily_left, subfamily_right]
                logger.debug(
                    f"Constructed two subfamilies of size {subfamily_left.size} and {subfamily_right.size}."
                )

                # analyze both subfamilies
                models_pruned = 0
                for subfamily in subfamilies:
                    self.iterations_cegar += 1
                    logger.debug(f"CEGAR: iteration {self.iterations_cegar}.")
                    subfamily.construct()
                    Profiler.start("ar - MDP model checking")
                    feasible, optimal_value = subfamily.analyze()
                    Profiler.stop()
                    if feasible and isinstance(feasible, bool):
                        logger.debug("CEGAR: all SAT.")
                        satisfying_assignment = subfamily.member_assignment
                        if optimal_value is not None:
                            self._check_optimal_property(
                                subfamily, satisfying_assignment, cex_generator=None, optimal_value=optimal_value
                            )
                        elif satisfying_assignment is not None and self._optimality_setting is None:
                            break
                    elif not feasible and isinstance(feasible, bool):
                        logger.debug("CEGAR: all UNSAT.")
                        models_pruned += subfamily.size
                        continue
                    else:  # feasible is None:
                        logger.debug("CEGAR: undecided.")
                        self.families.append(subfamily)
                        continue
                self.stage_step(models_pruned)

        if PRINT_PROFILING:
            Profiler.print()

        if self.input_has_optimality_property() and self._optimal_value is not None:
            assert not self.families
            logger.info(f"Found optimal assignment: {self._optimal_value}")
            return self._optimal_assignment, self._optimal_value
        elif satisfying_assignment is not None:
            logger.info(f"Found satisfying assignment: {readable_assignment(satisfying_assignment)}")
            return satisfying_assignment, None
        else:
            logger.info("No more options.")
            return None, None




