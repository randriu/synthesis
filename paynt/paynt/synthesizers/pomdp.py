import stormpy
from .statistic import Statistic
from .models import MarkovChain, DTMC, MDP
from .quotient import QuotientContainer,POMDPQuotientContainer
from .synthesizer import SynthesizerAR, SynthesizerHybrid

from ..profiler import Timer,Profiler

from ..sketch.holes import Holes,DesignSpace

import math
from collections import defaultdict

import logging
logger = logging.getLogger(__name__)


class SynthesizerPOMDP():

    # whether action holes will be restricted before synthesis
    # break_action_symmetry = False
    break_action_symmetry = True

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
        self.total_iters += synthesizer.stat.iterations_mdp
        return assignment


    def solve_mdp(self, family):

        # solve quotient MDP
        self.sketch.quotient.build(family)
        mdp = family.mdp
        spec = mdp.check_specification(self.sketch.specification)

        selection = spec.optimality_result.primary_selection
        choice_values = spec.optimality_result.primary_choice_values
        expected_visits = spec.optimality_result.primary_expected_visits
        scores = spec.optimality_result.primary_scores
        
        return mdp, spec, selection, choice_values, expected_visits, scores


    
    def strategy_expected(self):

        # assuming optimality
        assert self.sketch.specification.optimality is not None

        # start with k=1
        self.sketch.quotient.pomdp_manager.set_memory_size(1)

        for iteration in range(50):
            
            print("\n------------------------------------------------------------\n")
            
            # construct the quotient
            self.sketch.quotient.unfold_memory()
            
            # solve quotient MDP
            mdp,spec,selection,mdp_choice_values,mdp_visits,_ = self.solve_mdp(self.sketch.design_space)
            mdp_matrix = mdp.model.transition_matrix
            scheduler = spec.optimality_result.primary.result.scheduler
            mdp_choices = scheduler.compute_action_support(mdp.model.nondeterministic_choice_indices)

            # ? assuming that primary direction was not enough ?
            assert spec.optimality_result.feasibility is None
            
            # use inconsistencies in selection to break symmetry
            family = self.sketch.quotient.break_symmetry_2(self.sketch.design_space, selection)
            
            # synthesize optimal assignment
            synthesized_assignment = self.synthesize(family)
           
            if synthesized_assignment is None:
                # no new assignment: identify observation of interest based
                # only on the (symmetry-free) MDP

                # solve MDP corresponding to the restricted family
                ns_mdp,ns_spec,_,_,_,ns_scores = self.solve_mdp(family)
                print(ns_scores)
                
                # map hole scores to observations
                obs_scores = {}
                for obs in range(self.sketch.quotient.observations):
                    score_sum = 0
                    for hole in self.sketch.quotient.obs_to_holes[obs]:
                        score_sum += ns_scores.get(hole,0)
                    if score_sum > 0:
                        obs_scores[obs] = score_sum

                
                max_score = max(obs_scores.values())
                with_max_score = [obs for obs in obs_scores if obs_scores[obs] == max_score]
                selected_observation = with_max_score[0]

                print("hole scores: ", ns_scores)
                print("observation score: ", obs_score)
                print("selected observation: ", selected_observation)

                self.sketch.quotient.pomdp_manager.inject_memory(selected_observation)
                continue

            # use the synthesized solution to identify observation of interest

            # compute choices induced by this assignment
            _,_,synthesized_choices = self.sketch.quotient.select_actions(synthesized_assignment)
            
            # compare both choices state-wise
            state_improvement = [0] * mdp.states
            nci = mdp.model.nondeterministic_choice_indices
            for state in range(mdp.states):
                mdp_choice = None
                syn_choice = None
                for choice in range(nci[state],nci[state+1]):
                    if mdp_choices.get(choice):
                        assert mdp_choice is None
                        mdp_choice = choice
                    if synthesized_choices.get(choice):
                        assert syn_choice is None
                        syn_choice = choice
                assert mdp_choice is not None and syn_choice is not None
                pomdp_state = self.sketch.quotient.pomdp_manager.state_prototype[state]
                obs = self.sketch.quotient.pomdp.observations[pomdp_state]
                
                if mdp_choice == syn_choice:
                    continue
                mdp_value = mdp_choice_values[mdp_choice]
                syn_value = mdp_choice_values[syn_choice]
                improvement = abs(mdp_value - syn_value)

                # weight state improvement with the expected number of visits
                state_improvement[state] = mdp_visits[state] * improvement
                assert not math.isnan(state_improvement[state])

            # for each observation, compute average (potential) improvement across all of its states
            obs_sum = [0] * self.sketch.quotient.observations
            obs_cnt = [0] * self.sketch.quotient.observations
            for state in range(mdp.states):
                pomdp_state = self.sketch.quotient.pomdp_manager.state_prototype[state]
                obs = self.sketch.quotient.pomdp.observations[pomdp_state]
                obs_sum[obs] += state_improvement[state]
                obs_cnt[obs] += 1
            obs_avg = [obs_sum[obs] / obs_cnt[obs] for obs in range(self.sketch.quotient.observations)]
            selected_observation = obs_avg.index(max(obs_avg))
            obs_score = {obs:score for obs,score in enumerate(obs_avg) if score > 0}
            print()
            # print("observation labels: ", self.sketch.quotient.observation_labels)
            print("observation score: ", obs_score)
            print("selected observation: ", selected_observation)

            self.sketch.quotient.pomdp_manager.inject_memory(selected_observation)
        


    def strategy_full(self):
        self.sketch.quotient.pomdp_manager.set_memory_size(3)
        self.sketch.quotient.unfold_memory()
        self.synthesize()

    def run(self):
        # self.strategy_full()
        self.strategy_expected()





