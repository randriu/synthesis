import stormpy
from .statistic import Statistic
from .models import MarkovChain, DTMC, MDP

from .quotient import QuotientContainer
from .quotient_pomdp import POMDPQuotientContainer

from .synthesizer import SynthesizerAR, SynthesizerHybrid

from ..profiler import Timer,Profiler

from ..sketch.holes import Holes,DesignSpace

import math
from collections import defaultdict

import logging
logger = logging.getLogger(__name__)


class SynthesizerPOMDP():

    def __init__(self, sketch, method):
        assert sketch.is_pomdp
        self.sketch = sketch
        self.synthesizer = None
        if method == "ar":
            self.synthesizer = SynthesizerAR
        elif method == "hybrid":
            self.synthesizer = SynthesizerHybrid
        self.total_iters = 0
        Profiler.initialize()

    def print_stats(self):
        pass
    
    def synthesize(self, family, print_stats = True):
        self.sketch.quotient.discarded = 0
        synthesizer = self.synthesizer(self.sketch)
        family.property_indices = self.sketch.design_space.property_indices
        assignment = synthesizer.synthesize(family)
        if print_stats:
            synthesizer.print_stats()
        print(assignment)
        self.total_iters += synthesizer.stat.iterations_mdp
        return assignment


    def strategy_full(self):
        self.sketch.quotient.pomdp_manager.set_memory_size(Sketch.pomdp_memory_size)
        self.sketch.quotient.unfold_memory()
        self.synthesize(self.sketch.design_space)

    
    def strategy_iterative(self):
        mem_size = POMDPQuotientContainer.pomdp_memory_size
        while True:
        # for x in range(2):
            logger.info("Synthesizing optimal k={} controller ...".format(mem_size) )
            self.sketch.quotient.pomdp_manager.set_memory_size(mem_size)
            self.sketch.quotient.unfold_memory()
            self.synthesize(self.sketch.design_space)
            mem_size += 1

    
    def solve_mdp(self, family):

        # solve quotient MDP
        self.sketch.quotient.build(family)
        mdp = family.mdp
        spec = mdp.check_specification(self.sketch.specification)

        hole_scores = {}
        all_results = spec.constraints_result.results.copy()
        if spec.optimality_result is not None:
            all_results.append(spec.optimality_result)
        # print([res.primary_scores for res in all_results])

        for index,res in enumerate(all_results):
            for hole,score in res.primary_scores.items():
                hole_score = hole_scores.get(hole,0)
                hole_scores[hole] = hole_score + score



        result = spec.optimality_result
        selection = result.primary_selection
        choice_values = result.primary_choice_values
        expected_visits = result.primary_expected_visits
        # scores = result.primary_scores
        scores = hole_scores

        return mdp, spec, selection, choice_values, expected_visits, scores

    
    def strategy_expected(self):


        # assuming optimality
        assert self.sketch.specification.optimality is not None

        # for each observation will contain a set of observed action inconsistencies
        action_inconsistencies = [set() for obs in range(self.sketch.quotient.observations)]
        # for each observation (that doesn't have action inconsistencies) will
        # contain a set of observed memory inconsistencies
        memory_inconsistencies = [set() for obs in range(self.sketch.quotient.observations)]

        # start with k=1
        self.sketch.quotient.pomdp_manager.set_memory_size(1)
        memory_injections = 0
        best_assignment = None
        fsc_synthesis_timer = Timer()
        fsc_synthesis_timer.start()

        while True:
        # for iteration in range(4):

            # print(self.sketch.quotient.observation_labels)
            
            print("\n------------------------------------------------------------\n")

            # print(action_inconsistencies)
            # print(memory_inconsistencies)

            # construct the quotient
            self.sketch.quotient.unfold_memory()
            
            # use inconsistencies to break symmetry
            family = self.sketch.quotient.break_symmetry_3(self.sketch.design_space, action_inconsistencies, memory_inconsistencies)
            # family = self.sketch.design_space

            # solve MDP that corresponds to this restricted family
            mdp,spec,selection,choice_values,expected_visits,hole_scores = self.solve_mdp(family)
            # print(expected_visits)
            
            # check whether that primary direction was not enough ?
            if not spec.optimality_result.can_improve:
                logger.info("Optimum matches the upper bound of a symmetry-free MDP.")
                break
            
            # synthesize optimal assignment
            synthesized_assignment = self.synthesize(family)
           
            # identify hole that we want to improve
            selected_hole = None
            selected_options = None
            if synthesized_assignment is not None:
                # synthesized solution exists: hole of interest is the one where
                # the fully-observable improves upon the synthesized action
                # the most
                best_assignment = synthesized_assignment

                # for each state of the sub-MDP, compute potential state improvement
                state_improvement = [None] * mdp.states
                scheduler = spec.optimality_result.primary.result.scheduler
                for state in range(mdp.states):
                    # nothing to do if the state is not labeled by any hole
                    quotient_state = mdp.quotient_state_map[state]
                    holes = self.sketch.quotient.state_to_holes[quotient_state]
                    if not holes:
                        continue
                    hole = list(holes)[0]
                    
                    # get choice obtained by the MDP model checker
                    choice_0 = mdp.model.transition_matrix.get_row_group_start(state)
                    mdp_choice = scheduler.get_choice(state).get_deterministic_choice()
                    mdp_choice = choice_0 + mdp_choice
                    
                    # get choice implied by the synthesizer
                    syn_option = synthesized_assignment[hole].options[0]
                    nci = mdp.model.nondeterministic_choice_indices
                    for choice in range(nci[state],nci[state+1]):
                        choice_global = mdp.quotient_choice_map[choice]
                        choice_color = self.sketch.quotient.action_to_hole_options[choice_global]
                        if choice_color == {hole:syn_option}:
                            syn_choice = choice
                            break
                    
                    # estimate improvement
                    mdp_value = choice_values[mdp_choice]
                    syn_value = choice_values[syn_choice]
                    improvement = abs(syn_value - mdp_value)
                    
                    state_improvement[state] = improvement

                # had there been no new assignment, the hole of interest will
                # be the one with the maximum score in the symmetry-free MDP

                # map improvements in states of this sub-MDP to states of the quotient
                quotient_state_improvement = [None] * self.sketch.quotient.quotient_mdp.nr_states
                for state in range(mdp.states):
                    quotient_state_improvement[mdp.quotient_state_map[state]] = state_improvement[state]

                # extract DTMC corresponding to the synthesized solution
                dtmc = self.sketch.quotient.build_chain(synthesized_assignment)

                # compute expected visits for this dtmc
                dtmc_visits = stormpy.synthesis.compute_expected_number_of_visits(MarkovChain.environment, dtmc.model).get_values()
                dtmc_visits = list(dtmc_visits)

                # handle infinity- and zero-visits
                if self.sketch.specification.optimality.minimizing:
                    dtmc_visits = QuotientContainer.make_vector_defined(dtmc_visits)
                else:
                    dtmc_visits = [ value if value != math.inf else 0 for value in dtmc_visits]

                # weight state improvements with expected visits
                # aggregate these weighted improvements by holes
                hole_differences = [0] * family.num_holes
                hole_states_affected = [0] * family.num_holes
                for state in range(dtmc.states):
                    quotient_state = dtmc.quotient_state_map[state]
                    improvement = quotient_state_improvement[quotient_state]
                    if improvement is None:
                        continue

                    weighted_improvement = improvement * dtmc_visits[state]
                    assert not math.isnan(weighted_improvement), "{}*{} = nan".format(improvement,dtmc_visits[state])
                    hole = list(self.sketch.quotient.state_to_holes[quotient_state])[0]
                    hole_differences[hole] += weighted_improvement
                    hole_states_affected[hole] += 1

                hole_differences_avg = [0] * family.num_holes
                for hole in family.hole_indices:
                    if hole_states_affected[hole] != 0:
                        hole_differences_avg[hole] = hole_differences[hole] / hole_states_affected[hole]
                all_scores = {hole:hole_differences_avg[hole] for hole in family.hole_indices}
                nonzero_scores = {h:v for h,v in all_scores.items() if v>0}
                if len(nonzero_scores) > 0:
                    hole_scores = nonzero_scores
                else:
                    hole_scores = all_scores

            max_score = max(hole_scores.values())
            if max_score > 0:
                hole_scores = {h:v for h,v in hole_scores.items() if v / max_score > 0.01 }
            with_max_score = [hole for hole in hole_scores if hole_scores[hole] == max_score]
            selected_hole = with_max_score[0]
            # selected_hole = holes_to_inject[0]
            selected_options = selection[selected_hole]
            
            print()
            print("hole scores: ", hole_scores)
            print("selected hole: ", selected_hole)
            print("hole has options: ", selected_options)

            # identify observation having this hole
            for obs in range(self.sketch.quotient.observations):
                if selected_hole in self.sketch.quotient.obs_to_holes[obs]:
                    selected_observation = obs
                    break

            if len(selected_options) > 1:
                # identify whether this hole is inconsistent in actions or updates
                actions,updates = self.sketch.quotient.sift_actions_and_updates(selected_hole, selected_options)
                if len(actions) > 1:
                    # action inconsistency
                    action_inconsistencies[obs] |= actions
                else:
                    memory_inconsistencies[obs] |= updates
            
            # print status
            opt = "-"
            if self.sketch.specification.optimality.optimum is not None:
                opt = round(self.sketch.specification.optimality.optimum,3)
            elapsed = round(fsc_synthesis_timer.read(),1)
            logger.info("FSC synthesis: elapsed {} s, opt = {}, injections: {}.".format(elapsed, opt, memory_injections))
            logger.info("FSC: {}".format(best_assignment))

            # inject memory and continue
            self.sketch.quotient.pomdp_manager.inject_memory(selected_observation)
            memory_injections += 1
            logger.info("Injected memory into observation {}.".format(selected_observation))


    def run(self):
        # self.strategy_full()
        self.strategy_iterative()
        # self.strategy_expected()





