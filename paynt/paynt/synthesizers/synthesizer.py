import stormpy

import math
import itertools
from collections import OrderedDict

from .statistic import Statistic
from .models import MarkovChain, DTMC, MDP
from .quotient import JaniQuotientContainer, POMDPQuotientContainer

from ..sketch.holes import HoleOptions,DesignSpace

import logging
logger = logging.getLogger(__name__)

from stormpy.synthesis import dtmc_from_mdp

class Synthesizer:
    def __init__(self, sketch):
        MarkovChain.initialize(sketch.properties, sketch.optimality_property)

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
        if sketch.is_pomdp:
            self.quotient_container = POMDPQuotientContainer(sketch)
        else:
            self.quotient_container = JaniQuotientContainer(sketch)
        
        self.stat = Statistic(sketch, self.method_name)

    @property
    def method_name(self):
        return "AR"

    def run(self):
        self.stat.start()
        self.stat.super_mdp_size = self.quotient_container.quotient_mdp.nr_states

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
                # all UNSAT
                self.stat.pruned(family.size)
                continue
            
            if feasible == None:
                # undecided: split wrt first undecided result
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
            opt_bounds,optimum,improving_assignment,can_improve = mdp.check_optimality(self.optimality_property)
            if optimum is not None:
                self.optimality_property.update_optimum(optimum)
                satisfying_assignment = improving_assignment
            if can_improve:
                subfamily1, subfamily2 = self.quotient_container.prepare_split(mdp, opt_bounds, properties)
                families.append(subfamily1)
                families.append(subfamily2)

        # FIXME POMDP hack: replace hole valuations with corresponding action labels & print a table
        print("design space: ", self.sketch.design_space)
        print("design space size: ", self.sketch.design_space.size)
        if self.sketch.is_pomdp and satisfying_assignment is not None:

            pomdp = self.quotient_container.pomdp

            # collect labels of actions available at each observation
            action_labels_at_observation = [[] for obs in range(pomdp.nr_observations)]
            for state in range(pomdp.nr_states):
                obs = pomdp.observations[state]
                if action_labels_at_observation[obs] != []:
                    continue
                actions = pomdp.get_nr_available_actions(state)
                for offset in range(actions):
                    choice = pomdp.get_choice_index(state,offset)
                    labels = pomdp.choice_labeling.get_labels_of_choice(choice)
                    action_labels_at_observation[obs].append(labels)
            # print("labels of actions at observations: ", self.action_labels_at_observation)
            
            # satisfying_assignment_renamed = HoleOptions()
            # for hole_index,options in satisfying_assignment.items():
            #     hole_name = self.quotient_container.hole_names[hole_index]
            #     satisfying_assignment_renamed[hole_name] = options
            # satisfying_assignment = satisfying_assignment_renamed

            for obs in range(self.quotient_container.pomdp.nr_observations):
                at_obs = action_labels_at_observation[obs]
                for mem in range(self.quotient_container.full_memory_size):
                    hole = self.quotient_container.holes_action[(obs,mem)]
                    options = satisfying_assignment[hole]
                    satisfying_assignment[hole] = [at_obs[index] for index in options]

        self.stat.finished(satisfying_assignment)







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




