import stormpy

from .statistic import Statistic
from .synthesizer_ar import SynthesizerAR
from .synthesizer_ar_storm import SynthesizerARStorm
from .synthesizer_hybrid import SynthesizerHybrid
from .synthesizer_multicore_ar import SynthesizerMultiCoreAR

from ..quotient.holes import Holes,DesignSpace
from ..quotient.models import MarkovChain, DTMC, MDP
from ..quotient.quotient import QuotientContainer
from ..quotient.quotient_pomdp import POMDPQuotientContainer
from ..utils.profiler import Timer

import paynt.verification.property

import math
from collections import defaultdict

from threading import Thread
from queue import Queue
import time

import logging
logger = logging.getLogger(__name__)


class HoleTree:

    def __init__(self, options):
        self.nodes = [options]

    def __str__(self):
        return ",".join([str(x) for x in self.nodes])

    def split(self, mem, inconsistent_options):

        old_options = self.nodes[mem]
        
        # create child holes
        children = []
        for option in inconsistent_options:
            child_options = old_options.copy()
            child_options.remove(option)
            children.append(child_options)

        # store child nodes
        self.nodes[mem] = children[0]
        new_indices = []
        for child in children[1:]:
            new_indices.append(len(self.nodes))
            self.nodes.append(child)

        return new_indices

    def update_memory_updates(self, mem, new_indices):
        for index,options in enumerate(self.nodes):
            if mem in options:
                options.extend(new_indices)



class SynthesizerPOMDP:

    # If true explore only the main family
    incomplete_exploration = False

    def __init__(self, quotient, method, storm_control):
        self.quotient = quotient
        self.use_storm = False
        self.synthesizer = None
        if method == "ar":
            self.synthesizer = SynthesizerAR
        elif method == "ar_multicore":
            self.synthesizer = SynthesizerMultiCoreAR
        elif method == "hybrid":
            self.synthesizer = SynthesizerHybrid
        self.total_iters = 0

        if storm_control is not None:
            self.use_storm = True
            self.unfold_storm = True
            self.unfold_cutoff = False
            self.storm_control = storm_control
            self.storm_control.quotient = self.quotient
            self.storm_control.pomdp = self.quotient.pomdp
            self.storm_control.spec_formulas = self.quotient.specification.stormpy_formulae()
            self.synthesis_terminate = False
            self.synthesizer = SynthesizerARStorm       # SAYNT only works with abstraction refinement
            if self.storm_control.iteration_timeout is not None:
                self.saynt_timer = Timer()
                self.synthesizer.saynt_timer = self.saynt_timer
                self.storm_control.saynt_timer = self.saynt_timer

    def print_stats(self):
        pass
    
    def synthesize(self, family, print_stats = True):
        self.quotient.discarded = 0
        synthesizer = self.synthesizer(self.quotient)
        family.constraint_indices = self.quotient.design_space.constraint_indices
        assignment = synthesizer.synthesize(family)
        if print_stats:
            synthesizer.print_stats()
        self.total_iters += synthesizer.stat.iterations_mdp

        # Print extract list for every iteration optimum
        # if assignment:
        #     extracted_result = self.quotient.extract_policy(assignment)
        #     print(extracted_result)

        return assignment

    # iterative strategy using Storm analysis to enhance the synthesis
    def strategy_iterative_storm(self, unfold_imperfect_only, unfold_storm=True):
        '''
        @param unfold_imperfect_only if True, only imperfect observations will be unfolded
        '''
        mem_size = POMDPQuotientContainer.initial_memory_size

        self.synthesizer.storm_control = self.storm_control

        while True:
        # for x in range(2):
            
            POMDPQuotientContainer.current_family_index = mem_size

            # unfold memory according to the best result
            if unfold_storm:
                if mem_size > 1:
                    obs_memory_dict = {}
                    if self.storm_control.is_storm_better:
                        # Storm's result is better and it needs memory
                        if self.storm_control.is_memory_needed():
                            obs_memory_dict = self.storm_control.memory_vector
                            logger.info(f'Added memory nodes for observation based on Storm data')
                        else:
                            # consider the cut-off schedulers actions when updating memory
                            if self.unfold_cutoff:
                                for obs in range(self.quotient.observations):
                                    if obs in self.storm_control.result_dict:
                                        obs_memory_dict[obs] = self.quotient.observation_memory_size[obs] + 1
                                    else:
                                        obs_memory_dict[obs] = self.quotient.observation_memory_size[obs]
                            # only consider the induced DTMC without cut-off states
                            else:
                                for obs in range(self.quotient.observations):
                                    if obs in self.storm_control.result_dict_no_cutoffs:
                                        obs_memory_dict[obs] = self.quotient.observation_memory_size[obs] + 1
                                    else:
                                        obs_memory_dict[obs] = self.quotient.observation_memory_size[obs]
                            logger.info(f'Added memory nodes for observation based on Storm data')
                    else:
                        for obs in range(self.quotient.observations):
                            if self.quotient.observation_states[obs]>1:
                                obs_memory_dict[obs] = self.quotient.observation_memory_size[obs] + 1
                            else:
                                obs_memory_dict[obs] = 1
                        logger.info(f'Increase memory in all imperfect observation')
                    self.quotient.set_memory_from_dict(obs_memory_dict)
            else:
                logger.info("Synthesizing optimal k={} controller ...".format(mem_size) )
                if unfold_imperfect_only:
                    self.quotient.set_imperfect_memory_size(mem_size)
                else:
                    self.quotient.set_global_memory_size(mem_size)

            family = self.quotient.design_space

            # if Storm's result is better, use it to obtain main family that considers only the important actions
            if self.storm_control.is_storm_better:
                # consider the cut-off schedulers actions
                if self.storm_control.use_cutoffs:
                    main_family = self.storm_control.get_main_restricted_family(family, self.storm_control.result_dict)
                    if self.incomplete_exploration == True:
                        subfamily_restrictions = []
                    else:
                        subfamily_restrictions = self.storm_control.get_subfamilies_restrictions(family, self.storm_control.result_dict)
                # only consider the induced DTMC actions without cut-off states
                else:
                    main_family = self.storm_control.get_main_restricted_family(family, self.storm_control.result_dict_no_cutoffs)
                    if self.incomplete_exploration == True:
                        subfamily_restrictions = []
                    else:
                        subfamily_restrictions = self.storm_control.get_subfamilies_restrictions(family, self.storm_control.result_dict_no_cutoffs)

                subfamilies = self.storm_control.get_subfamilies(subfamily_restrictions, family)
            # if PAYNT is better continue normally
            else:
                main_family = family
                subfamilies = []

            self.synthesizer.subfamilies_buffer = subfamilies
            self.synthesizer.unresticted_family = family

            assignment = self.synthesize(main_family)

            if assignment is not None:
                self.storm_control.latest_paynt_result = assignment
                self.storm_control.paynt_export = self.quotient.extract_policy(assignment)
                self.storm_control.paynt_bounds = self.quotient.specification.optimality.optimum
                self.storm_control.paynt_fsc_size = self.quotient.policy_size(self.storm_control.latest_paynt_result)

            self.storm_control.update_data()

            if self.synthesis_terminate:
                break

            mem_size += 1
            
            #break

    # main SAYNT loop
    def iterative_storm_loop(self, timeout, paynt_timeout, storm_timeout, iteration_limit=0):
        self.interactive_queue = Queue()
        self.synthesizer.s_queue = self.interactive_queue
        self.storm_control.interactive_storm_setup()
        iteration = 1
        paynt_thread = Thread(target=self.strategy_iterative_storm, args=(True, self.unfold_storm))

        iteration_timeout = time.time() + timeout

        self.saynt_timer.start()
        while True:
            if iteration == 1:
                paynt_thread.start()
            else:
                self.interactive_queue.put("resume")

            logger.info("Timeout for PAYNT started")

            time.sleep(paynt_timeout)
            self.interactive_queue.put("timeout")

            while not self.interactive_queue.empty():
                time.sleep(0.1)

            if iteration == 1:
                self.storm_control.interactive_storm_start(storm_timeout)
            else:
                self.storm_control.interactive_storm_resume(storm_timeout)

            # compute sizes of controllers
            self.storm_control.belief_controller_size = self.storm_control.get_belief_controller_size(self.storm_control.latest_storm_result, self.storm_control.paynt_fsc_size)

            print("\n------------------------------------\n")
            print("PAYNT results: ")
            print(self.storm_control.paynt_bounds)
            print("controller size: {}".format(self.storm_control.paynt_fsc_size))

            print()

            print("Storm results: ")
            print(self.storm_control.storm_bounds)
            print("controller size: {}".format(self.storm_control.belief_controller_size))
            print("\n------------------------------------\n")

            if time.time() > iteration_timeout or iteration == iteration_limit:
                break

            iteration += 1

        self.interactive_queue.put("terminate")
        self.synthesis_terminate = True
        paynt_thread.join()

        self.storm_control.interactive_storm_terminate()

        self.saynt_timer.stop()

    # run PAYNT POMDP synthesis with a given timeout
    def run_synthesis_timeout(self, timeout):
        self.interactive_queue = Queue()
        self.synthesizer.s_queue = self.interactive_queue
        paynt_thread = Thread(target=self.strategy_iterative_storm, args=(True, False))
        iteration_timeout = time.time() + timeout
        paynt_thread.start()

        while True:
            if time.time() > iteration_timeout:
                break

            time.sleep(1)

        self.interactive_queue.put("pause")
        self.interactive_queue.put("terminate")
        self.synthesis_terminate = True
        paynt_thread.join()


    # PAYNT POMDP synthesis that uses pre-computed results from Storm as guide
    def strategy_storm(self, unfold_imperfect_only, unfold_storm=True):
        '''
        @param unfold_imperfect_only if True, only imperfect observations will be unfolded
        '''
        mem_size = POMDPQuotientContainer.initial_memory_size

        self.synthesizer.storm_control = self.storm_control

        while True:
        # for x in range(2):

            if self.storm_control.is_storm_better == False:
                self.storm_control.parse_result(self.quotient)
            
            POMDPQuotientContainer.current_family_index = mem_size

            # unfold memory according to the best result
            if unfold_storm:
                if mem_size > 1:
                    obs_memory_dict = {}
                    if self.storm_control.is_storm_better:
                        if self.storm_control.is_memory_needed():
                            obs_memory_dict = self.storm_control.memory_vector
                            logger.info(f'Added memory nodes for observation based on Storm data')
                        else:
                            # consider the cut-off schedulers actions when updating memory
                            if self.unfold_cutoff:
                                for obs in range(self.quotient.observations):
                                    if obs in self.storm_control.result_dict:
                                        obs_memory_dict[obs] = self.quotient.observation_memory_size[obs] + 1
                                    else:
                                        obs_memory_dict[obs] = self.quotient.observation_memory_size[obs]
                            # only consider the induced DTMC without cut-off states
                            else:
                                for obs in range(self.quotient.observations):
                                    if obs in self.storm_control.result_dict_no_cutoffs:
                                        obs_memory_dict[obs] = self.quotient.observation_memory_size[obs] + 1
                                    else:
                                        obs_memory_dict[obs] = self.quotient.observation_memory_size[obs]
                            logger.info(f'Added memory nodes for observation based on Storm data')
                    else:
                        for obs in range(self.quotient.observations):
                            if self.quotient.observation_states[obs]>1:
                                obs_memory_dict[obs] = self.quotient.observation_memory_size[obs] + 1
                            else:
                                obs_memory_dict[obs] = 1
                        logger.info(f'Increase memory in all imperfect observation')
                    self.quotient.set_memory_from_dict(obs_memory_dict)
            else:
                logger.info("Synthesizing optimal k={} controller ...".format(mem_size) )
                if unfold_imperfect_only:
                    self.quotient.set_imperfect_memory_size(mem_size)
                else:
                    self.quotient.set_global_memory_size(mem_size)

            family = self.quotient.design_space

            # if Storm's result is better, use it to obtain main family that considers only the important actions
            if self.storm_control.is_storm_better:
                # consider the cut-off schedulers actions
                if self.storm_control.use_cutoffs:
                    main_family = self.storm_control.get_main_restricted_family(family, self.storm_control.result_dict)
                    if self.incomplete_exploration == True:
                        subfamily_restrictions = []
                    else:
                        subfamily_restrictions = self.storm_control.get_subfamilies_restrictions(family, self.storm_control.result_dict)
                # only consider the induced DTMC actions without cut-off states
                else:
                    main_family = self.storm_control.get_main_restricted_family(family, self.storm_control.result_dict_no_cutoffs)
                    if self.incomplete_exploration == True:
                        subfamily_restrictions = []
                    else:
                        subfamily_restrictions = self.storm_control.get_subfamilies_restrictions(family, self.storm_control.result_dict_no_cutoffs)

                subfamilies = self.storm_control.get_subfamilies(subfamily_restrictions, family)
            # if PAYNT is better continue normally
            else:
                main_family = family
                subfamilies = []

            self.synthesizer.subfamilies_buffer = subfamilies
            self.synthesizer.unresticted_family = family

            assignment = self.synthesize(main_family)

            if assignment is not None:
                self.storm_control.latest_paynt_result = assignment
                self.storm_control.paynt_export = self.quotient.extract_policy(assignment)
                self.storm_control.paynt_bounds = self.quotient.specification.optimality.optimum


            self.storm_control.update_data()

            mem_size += 1
            
            #break


    def strategy_iterative(self, unfold_imperfect_only):
        '''
        @param unfold_imperfect_only if True, only imperfect observations will be unfolded
        '''
        mem_size = POMDPQuotientContainer.initial_memory_size
        opt = self.quotient.specification.optimality.optimum
        while True:
            
            logger.info("Synthesizing optimal k={} controller ...".format(mem_size) )
            if unfold_imperfect_only:
                self.quotient.set_imperfect_memory_size(mem_size)
            else:
                self.quotient.set_global_memory_size(mem_size)
            
            # self.quotient.design_space_counter()
            self.synthesize(self.quotient.design_space)

            opt_old = opt
            opt = self.quotient.specification.optimality.optimum

            # finish if optimum has not been improved
            # if opt_old == opt and opt is not None:
            #     break
            mem_size += 1

            #break
    
    def solve_mdp(self, family):

        # solve quotient MDP
        self.quotient.build(family)
        mdp = family.mdp
        spec = mdp.check_specification(self.quotient.specification, short_evaluation=True)

        # nothing more to do if optimality cannot be improved
        if not spec.optimality_result.can_improve:
            return mdp, spec, None, None, None, None

        # hole scores = sum of scores wrt individual formulae
        hole_scores = {}
        all_results = spec.constraints_result.results.copy()
        if spec.optimality_result is not None:
            all_results.append(spec.optimality_result)
        for index,res in enumerate(all_results):
            for hole,score in res.primary_scores.items():
                hole_score = hole_scores.get(hole,0)
                hole_scores[hole] = hole_score + score

        result = spec.optimality_result
        selection = result.primary_selection
        
        # print()
        # print()
        # # print(dir())
        # print(mdp.states)
        # scheduler = result.primary.result.scheduler
        # print(self.quotient.coloring.state_to_holes)
        # print(spec.optimality_result.primary_scores)
        # p = spec.optimality_result.primary.result
        # for state in range(mdp.states):
        #     print(state)
        #     local_choice = scheduler.get_choice(state).get_deterministic_choice()
        #     global_choice = mdp.model.get_choice_index(state,local_choice)
        #     row = mdp.model.transition_matrix.get_row(global_choice)
        #     print("scheduler choice: {}/{}".format(local_choice,global_choice))
        #     quotient_choice = mdp.quotient_choice_map[global_choice]
        #     print("choice colors: ", self.quotient.coloring.action_to_hole_options[quotient_choice])
        #     print("matrix row: ", row)
        #     quotient_state = mdp.quotient_state_map[state]
        #     relevant_holes = self.quotient.coloring.state_to_holes[quotient_state]
        #     obs = None
        #     for hole in relevant_holes:
        #         for obs in range(self.quotient.observations):
        #             action_holes = self.quotient.observation_action_holes[obs]
        #             if hole in action_holes:
        #                 selected_obs = obs
        #                 selected_mem = action_holes.index(hole)
        #                 hole_is_action = True
        #                 break
        #             memory_holes = self.quotient.observation_memory_holes[obs]
        #             if hole in memory_holes:
        #                 selected_obs = obs
        #                 selected_mem = memory_holes.index(hole)
        #                 hole_is_action = False
        #                 break
        #         print("hole corresponds to observation ({},{}) [{}]".format(selected_obs,selected_mem,hole_is_action))
        #     # print("relevant holes: ", self.quotient.)
        #     print(p.get_values()[state])
        #     print()
        #     # print(prototype_state)
        # print()
        # print()
        
        
        choice_values = result.primary_choice_values
        expected_visits = result.primary_expected_visits
        # scores = result.primary_scores
        scores = hole_scores

        return mdp, spec, selection, choice_values, expected_visits, scores

    
    def strategy_expected(self):

        # assuming optimality
        assert self.quotient.specification.optimality is not None

        num_obs = self.quotient.observations
        observation_successors = self.quotient.pomdp_manager.observation_successors

        # for each observation, create a root of an action hole tree
        action_hole_trees = [None] * num_obs
        memory_hole_trees = [None] * num_obs
        for obs in range(num_obs):
            ah = self.quotient.action_hole_prototypes[obs]
            if ah is not None:
                action_hole_trees[obs] = HoleTree(ah.options)
            memory_hole_trees[obs] = HoleTree([0])

        # start with k=1
        best_assignment = None
        fsc_synthesis_timer = Timer()
        fsc_synthesis_timer.start()

        # while True:
        for iteration in range(3):

            print("\n------------------------------------------------------------\n")

            print([str(tree) for tree in action_hole_trees])
            print([str(tree) for tree in memory_hole_trees])
            
            # construct and solve the quotient
            family = self.quotient.design_space
            mdp,spec,selection,choice_values,expected_visits,hole_scores = self.solve_mdp(family)
            
            # check whether that primary direction was not enough ?
            if not spec.optimality_result.can_improve:
                logger.info("Optimum matches the upper bound of a symmetry-free MDP.")
                break
            
            # synthesize optimal assignment
            synthesized_assignment = self.synthesize(family)

            # print status
            opt = "-"
            if self.quotient.specification.optimality.optimum is not None:
                opt = round(self.quotient.specification.optimality.optimum,3)
            elapsed = round(fsc_synthesis_timer.read(),1)
            memory_injections = sum(self.quotient.observation_memory_size) - num_obs
            logger.info("FSC synthesis: elapsed {} s, opt = {}, injections: {}.".format(elapsed, opt, memory_injections))
            logger.info("FSC: {}".format(best_assignment))
           
            # identify hole that we want to improve
            selected_hole = None
            selected_options = None
            if synthesized_assignment is not None:
                # remember the solution
                best_assignment = synthesized_assignment

                # synthesized solution exists: hole of interest is the one where
                # the fully-observable improves upon the synthesized action
                # the most

                # # for each state of the sub-MDP, compute potential state improvement
                # state_improvement = [None] * mdp.states
                # scheduler = spec.optimality_result.primary.result.scheduler
                # for state in range(mdp.states):
                #     # nothing to do if the state is not labeled by any hole
                #     quotient_state = mdp.quotient_state_map[state]
                #     holes = self.quotient.coloring.state_to_holes[quotient_state]
                #     if not holes:
                #         continue
                #     hole = list(holes)[0]
                    
                #     # get choice obtained by the MDP model checker
                #     choice_0 = mdp.model.transition_matrix.get_row_group_start(state)
                #     mdp_choice = scheduler.get_choice(state).get_deterministic_choice()
                #     mdp_choice = choice_0 + mdp_choice
                    
                #     # get choice implied by the synthesizer
                #     syn_option = synthesized_assignment[hole].options[0]
                #     nci = mdp.model.nondeterministic_choice_indices
                #     for choice in range(nci[state],nci[state+1]):
                #         choice_global = mdp.quotient_choice_map[choice]
                #         choice_color = self.quotient.coloring.action_to_hole_options[choice_global]
                #         if choice_color == {hole:syn_option}:
                #             syn_choice = choice
                #             break
                    
                #     # estimate improvement
                #     mdp_value = choice_values[mdp_choice]
                #     syn_value = choice_values[syn_choice]
                #     improvement = abs(syn_value - mdp_value)
                    
                #     state_improvement[state] = improvement

                # # had there been no new assignment, the hole of interest will
                # # be the one with the maximum score in the symmetry-free MDP

                # # map improvements in states of this sub-MDP to states of the quotient
                # quotient_state_improvement = [None] * self.quotient.quotient_mdp.nr_states
                # for state in range(mdp.states):
                #     quotient_state_improvement[mdp.quotient_state_map[state]] = state_improvement[state]

                # # extract DTMC corresponding to the synthesized solution
                # dtmc = self.quotient.build_chain(synthesized_assignment)

                # # compute expected visits for this dtmc
                # dtmc_visits = stormpy.compute_expected_number_of_visits(MarkovChain.environment, dtmc.model).get_values()
                # dtmc_visits = list(dtmc_visits)

                # # handle infinity- and zero-visits
                # if self.quotient.specification.optimality.minimizing:
                #     dtmc_visits = QuotientContainer.make_vector_defined(dtmc_visits)
                # else:
                #     dtmc_visits = [ value if value != math.inf else 0 for value in dtmc_visits]

                # # weight state improvements with expected visits
                # # aggregate these weighted improvements by holes
                # hole_differences = [0] * family.num_holes
                # hole_states_affected = [0] * family.num_holes
                # for state in range(dtmc.states):
                #     quotient_state = dtmc.quotient_state_map[state]
                #     improvement = quotient_state_improvement[quotient_state]
                #     if improvement is None:
                #         continue

                #     weighted_improvement = improvement * dtmc_visits[state]
                #     assert not math.isnan(weighted_improvement), "{}*{} = nan".format(improvement,dtmc_visits[state])
                #     hole = list(self.quotient.coloring.state_to_holes[quotient_state])[0]
                #     hole_differences[hole] += weighted_improvement
                #     hole_states_affected[hole] += 1

                # hole_differences_avg = [0] * family.num_holes
                # for hole in family.hole_indices:
                #     if hole_states_affected[hole] != 0:
                #         hole_differences_avg[hole] = hole_differences[hole] / hole_states_affected[hole]
                # all_scores = {hole:hole_differences_avg[hole] for hole in family.hole_indices}
                # nonzero_scores = {h:v for h,v in all_scores.items() if v>0}
                # if len(nonzero_scores) > 0:
                #     hole_scores = nonzero_scores
                # else:
                #     hole_scores = all_scores

            max_score = max(hole_scores.values())
            if max_score > 0:
                hole_scores = {h:v for h,v in hole_scores.items() if v / max_score > 0.01 }
            with_max_score = [hole for hole in hole_scores if hole_scores[hole] == max_score]
            selected_hole = with_max_score[0]
            # selected_hole = holes_to_inject[0]
            selected_options = selection[selected_hole]

            # identify observation having this hole
            for obs in range(self.quotient.observations):
                action_holes = self.quotient.observation_action_holes[obs]
                if selected_hole in action_holes:
                    selected_obs = obs
                    selected_mem = action_holes.index(selected_hole)
                    hole_is_action = True
                    break
                memory_holes = self.quotient.observation_memory_holes[obs]
                if selected_hole in memory_holes:
                    selected_obs = obs
                    selected_mem = memory_holes.index(selected_hole)
                    hole_is_action = False
                    break


            print()
            hole_scores_printable = {self.quotient.design_space[hole].name : score for hole,score in hole_scores.items()} 
            print("hole scores: ", hole_scores)
            print("hole scores (printable): ", hole_scores_printable)
            print("selected hole: {}, ({})".format(selected_hole, family[selected_hole]))
            print("hole corresponds to observation ({},{}) [{}]".format(selected_obs,selected_mem,hole_is_action))
            print("hole is inconsistent in options: ", selected_options)
            assert len(selected_options) > 1
            
            # split hole option and break symmetry
            if hole_is_action:
                new_indices = action_hole_trees[selected_obs].split(selected_mem,selected_options)
            else:
                assert None
                new_indices = memory_hole_trees[selected_obs].split(selected_mem,selected_options)
            print("new indices: ", new_indices)

            
            # increase memory size in the selected observation to reflect all inconsistencies
            # detect which observation were affected by this increase
            old_successor_size = self.quotient.pomdp_manager.max_successor_memory_size
            for x in range(len(selected_options)-1):
                self.quotient.increase_memory_size(selected_obs)
            new_successor_size = self.quotient.pomdp_manager.max_successor_memory_size
            affected_obs = []

            for obs in range(num_obs):
                if new_successor_size[obs] > old_successor_size[obs]:
                    affected_obs.append(obs)
            print("observations affected by injection: ", affected_obs)

            # update memory nodes
            for obs in affected_obs:
                memory_hole_trees[obs].update_memory_updates(selected_mem,new_indices)

            print([str(tree) for tree in action_hole_trees])
            print([str(tree) for tree in memory_hole_trees])
            
            # inject memory
            
            print()
            logger.info(">>>Injected memory into observation {}.".format(selected_obs))

            # reconstruct design space using the history of symmetry breakings
            
            restricted_family = self.quotient.design_space.copy()
            for obs in range(num_obs):

                action_holes = self.quotient.observation_action_holes[obs]
                if len(action_holes) > 0:
                    tree = action_hole_trees[obs]
                    for index,options in enumerate(tree.nodes):
                        restricted_family[action_holes[index]].assume_options(options)

                memory_holes = self.quotient.observation_memory_holes[obs]
                if len(memory_holes) > 0:
                    tree = memory_hole_trees[obs]
                    for index,options in enumerate(tree.nodes):
                        restricted_family[memory_holes[index]].assume_options(options)

            print(restricted_family)
            logger.debug("Symmetry breaking: reduced design space from {} to {}".format(self.quotient.design_space.size, restricted_family.size))
            self.quotient.design_space = restricted_family


    def strategy_expected_uai(self):


        # assuming optimality
        assert self.quotient.specification.optimality is not None

        # for each observation will contain a set of observed action inconsistencies
        action_inconsistencies = [set() for obs in range(self.quotient.observations)]
        # for each observation (that doesn't have action inconsistencies) will
        # contain a set of observed memory inconsistencies
        memory_inconsistencies = [set() for obs in range(self.quotient.observations)]

        # start with k=1
        self.quotient.set_global_memory_size(1)
        memory_injections = 0
        best_assignment = None
        fsc_synthesis_timer = Timer()
        fsc_synthesis_timer.start()

        while True:
        # for iteration in range(4):

            # print(self.quotient.observation_labels)
            
            print("\n------------------------------------------------------------\n")

            # print(action_inconsistencies)
            # print(memory_inconsistencies)

            # construct the quotient
            # self.quotient.unfold_memory()
            
            # use inconsistencies to break symmetry
            family = self.quotient.break_symmetry_uai(self.quotient.design_space, action_inconsistencies, memory_inconsistencies)
            # family = self.quotient.design_space

            # solve MDP that corresponds to this restricted family
            mdp,spec,selection,choice_values,expected_visits,hole_scores = self.solve_mdp(family)
            # print(expected_visits)
            
            # check whether that primary direction was not enough ?
            if not spec.optimality_result.can_improve:
                logger.info("Optimum matches the upper bound of the observation-free MDP.")
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
                    holes = self.quotient.coloring.state_to_holes[quotient_state]
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
                        choice_color = self.quotient.coloring.action_to_hole_options[choice_global]
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
                quotient_state_improvement = [None] * self.quotient.quotient_mdp.nr_states
                for state in range(mdp.states):
                    quotient_state_improvement[mdp.quotient_state_map[state]] = state_improvement[state]

                # extract DTMC corresponding to the synthesized solution
                dtmc = self.quotient.build_chain(synthesized_assignment)

                # compute expected visits for this dtmc
                dtmc_visits = stormpy.compute_expected_number_of_visits(paynt.verification.property.Property.environment, dtmc.model).get_values()
                dtmc_visits = list(dtmc_visits)

                # handle infinity- and zero-visits
                if self.quotient.specification.optimality.minimizing:
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
                    hole = list(self.quotient.coloring.state_to_holes[quotient_state])[0]
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
            for obs in range(self.quotient.observations):
                if selected_hole in self.quotient.obs_to_holes[obs]:
                    selected_observation = obs
                    break

            if len(selected_options) > 1:
                # identify whether this hole is inconsistent in actions or updates
                actions,updates = self.quotient.sift_actions_and_updates(selected_observation, selected_hole, selected_options)
                if len(actions) > 1:
                    # action inconsistency
                    action_inconsistencies[obs] |= actions
                else:
                    memory_inconsistencies[obs] |= updates
            
            # print status
            opt = "-"
            if self.quotient.specification.optimality.optimum is not None:
                opt = round(self.quotient.specification.optimality.optimum,3)
            elapsed = round(fsc_synthesis_timer.read(),1)
            logger.info("FSC synthesis: elapsed {} s, opt = {}, injections: {}.".format(elapsed, opt, memory_injections))
            # logger.info("FSC synthesis: assignment: {}".format(best_assignment))

            # inject memory and continue
            logger.info("Injecting memory into observation {} ...".format(selected_observation))
            self.quotient.increase_memory_size(selected_observation)
            memory_injections += 1
                


    def run(self):
        # choose the synthesis strategy:
        if self.use_storm:
            logger.info("Storm POMDP option enabled")
            logger.info("Storm settings: iterative - {}, get_storm_result - {}, storm_options - {}, prune_storm - {}, unfold_strategy - {}, use_storm_cutoffs - {}".format(
                        (self.storm_control.iteration_timeout, self.storm_control.paynt_timeout, self.storm_control.storm_timeout), self.storm_control.get_result,
                        self.storm_control.storm_options, self.incomplete_exploration, (self.unfold_storm, self.unfold_cutoff), self.storm_control.use_cutoffs
            ))
            # start SAYNT
            if self.storm_control.iteration_timeout is not None:
                self.iterative_storm_loop(timeout=self.storm_control.iteration_timeout, 
                                          paynt_timeout=self.storm_control.paynt_timeout, 
                                          storm_timeout=self.storm_control.storm_timeout, 
                                          iteration_limit=0)
            # run PAYNT for a time given by 'self.storm_control.get_result' and then run Storm using the best computed FSC at cut-offs
            elif self.storm_control.get_result is not None:
                if self.storm_control.get_result:
                    self.run_synthesis_timeout(self.storm_control.get_result)
                self.storm_control.run_storm_analysis()
            # run Storm and then use the obtained result to enhance PAYNT synthesis
            else:
                self.storm_control.get_storm_result()
                self.strategy_storm(unfold_imperfect_only=True, unfold_storm=self.unfold_storm)

            print("\n------------------------------------\n")
            print("PAYNT results: ")
            print(self.storm_control.paynt_bounds)
            print("controller size: {}".format(self.storm_control.paynt_fsc_size))

            print()

            print("Storm results: ")
            print(self.storm_control.storm_bounds)
            print("controller size: {}".format(self.storm_control.belief_controller_size))
            print("\n------------------------------------\n")
        # Pure PAYNT POMDP synthesis
        else:
            # self.strategy_expected_uai()
            # self.strategy_iterative(unfold_imperfect_only=False)
            self.strategy_iterative(unfold_imperfect_only=True)


        





