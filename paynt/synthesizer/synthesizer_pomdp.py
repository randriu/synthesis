import stormpy
import payntbind

from .statistic import Statistic
import paynt.synthesizer.synthesizer_ar
from .synthesizer_ar_storm import SynthesizerARStorm
from .synthesizer_hybrid import SynthesizerHybrid
from .synthesizer_multicore_ar import SynthesizerMultiCoreAR

import paynt.quotient.quotient
import paynt.quotient.pomdp
from ..utils.profiler import Timer

import paynt.verification.property

import math
from collections import defaultdict

from threading import Thread
from queue import Queue
import time

import logging
logger = logging.getLogger(__name__)


class SynthesizerPOMDP:

    # If true explore only the main family
    incomplete_exploration = False

    def __init__(self, quotient, method, storm_control):
        self.quotient = quotient
        self.use_storm = False
        self.synthesizer = None
        if method == "ar":
            self.synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR
        elif method == "ar_multicore":
            self.synthesizer = SynthesizerMultiCoreAR
        elif method == "hybrid":
            self.synthesizer = SynthesizerHybrid
        self.total_iters = 0

        self.storm_control = None
        self.main_synthesizer = True

        if storm_control is not None:
            self.use_storm = True
            self.storm_control = storm_control
            self.storm_control.quotient = self.quotient
            self.storm_control.pomdp = self.quotient.pomdp
            self.storm_control.spec_formulas = self.quotient.specification.stormpy_formulae()
            self.synthesis_terminate = False
            self.synthesizer = SynthesizerARStorm       # SAYNT only works with abstraction refinement
            self.saynt_timer = Timer()
            self.interactive_queue = Queue()
            if self.storm_control.iteration_timeout is not None:
                self.storm_control.saynt_timer = self.saynt_timer
            if self.storm_control.enhanced_saynt is not None:
                self.storm_control.sub_pomdp_builder = payntbind.synthesis.SubPomdpBuilder(self.quotient.pomdp)

    def synthesize(self, family, print_stats=True, main_family=None, subfamilies=None):
        if self.storm_control is not None:
            synthesizer = self.synthesizer(self.quotient, subfamilies_buffer=subfamilies, main_family=main_family, storm_control=self.storm_control, s_queue=self.interactive_queue, saynt_timer=self.saynt_timer, main_thread=self.main_synthesizer)
        else:
            synthesizer = self.synthesizer(self.quotient)
        family.constraint_indices = self.quotient.design_space.constraint_indices
        assignment = synthesizer.synthesize(family, keep_optimum=True, print_stats=print_stats)
        if synthesizer.stat.iterations_mdp is not None:
            self.total_iters += synthesizer.stat.iterations_mdp
        return assignment

    # iterative strategy using Storm analysis to enhance the synthesis
    def strategy_iterative_storm(self, unfold_imperfect_only, unfold_storm=True):
        '''
        @param unfold_imperfect_only if True, only imperfect observations will be unfolded
        '''
        mem_size = paynt.quotient.pomdp.PomdpQuotient.initial_memory_size

        while True:
        # for x in range(2):
            
            paynt.quotient.pomdp.PomdpQuotient.current_family_index = mem_size

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
                            if self.storm_control.unfold_cutoff:
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
                    if self.storm_control.incomplete_exploration == True:
                        subfamily_restrictions = []
                    else:
                        subfamily_restrictions = self.storm_control.get_subfamilies_restrictions(family, self.storm_control.result_dict)
                # only consider the induced DTMC actions without cut-off states
                else:
                    main_family = self.storm_control.get_main_restricted_family(family, self.storm_control.result_dict_no_cutoffs)
                    if self.storm_control.incomplete_exploration == True:
                        subfamily_restrictions = []
                    else:
                        subfamily_restrictions = self.storm_control.get_subfamilies_restrictions(family, self.storm_control.result_dict_no_cutoffs)

                subfamilies = self.storm_control.get_subfamilies(subfamily_restrictions, family)
            # if PAYNT is better continue normally
            else:
                main_family = family
                subfamilies = []

            assignment = self.synthesize(family, subfamilies=subfamilies, main_family=main_family)

            if assignment is not None:
                self.storm_control.latest_paynt_result = assignment
                self.storm_control.paynt_export = self.quotient.extract_policy(assignment)
                self.storm_control.paynt_bounds = self.quotient.specification.optimality.optimum
                self.storm_control.paynt_fsc_size = self.quotient.policy_size(self.storm_control.latest_paynt_result)

            self.storm_control.update_data()

            logger.info(f"Terminate: {self.synthesis_terminate}")
            if self.synthesis_terminate:
                break

            mem_size += 1
            
            #break

    # main SAYNT loop
    def iterative_storm_loop(self, timeout, paynt_timeout, storm_timeout, iteration_limit=0):
        self.storm_control.interactive_storm_setup()
        iteration = 1
        paynt_thread = Thread(target=self.strategy_iterative_storm, args=(True, self.storm_control.unfold_storm))

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


    # enhanced SAYNT loop
    def enhanced_iterative_storm_loop(self, timeout, paynt_timeout, storm_timeout, number_of_beliefs=0, iteration_limit=0):
        self.storm_control.interactive_storm_setup()
        iteration = 1
        paynt_thread = Thread(target=self.strategy_iterative_storm, args=(True, self.storm_control.unfold_storm))

        iteration_timeout = time.time() + timeout

        self.saynt_timer.start()

        while True:
            if iteration == 1:
                self.storm_control.interactive_storm_start(storm_timeout, True)
                self.storm_control.parse_belief_data()

                self.storm_control.belief_explorer.add_fsc_values(self.storm_control.paynt_export)

                if False:
                    obs = self.quotient.observation_labels.index("[goal=0\t& in=1\t& out=0\t& switch=0]")
                    obs_states = []
                    
                    for state in self.quotient.pomdp.states:
                        state_obs = self.quotient.pomdp.get_observation(state)
                        if state_obs == obs:
                            obs_states.append(state.id)

                    for state in obs_states:
                        self.storm_control.create_thread_control({state: 1}, "custom", self.storm_control.use_uniform_obs_beliefs)

                else:
                    if number_of_beliefs == 0:
                        beliefs_remaining = len(self.storm_control.main_obs_belief_data)
                        # beliefs_remaining = len(self.storm_control.main_support_belief_data)
                    else:
                        beliefs_remaining = number_of_beliefs - 1
                    if beliefs_remaining != 0:
                        for index, belief_type_data in enumerate([self.storm_control.main_obs_belief_data, self.storm_control.residue_obs_belief_data]):
                        # for index, belief_type_data in enumerate([self.storm_control.main_support_belief_data]):
                            index_type = "obs" if index in [0,1] else "sup"
                            # index_type = "sup"
                            for obs_or_sup in belief_type_data:
                                self.storm_control.create_thread_control(obs_or_sup, index_type, self.storm_control.use_uniform_obs_beliefs)
                                beliefs_remaining -= 1
                                if beliefs_remaining == 0:
                                    break
                            if beliefs_remaining == 0:
                                break

                number_of_threads = len(self.storm_control.enhanced_saynt_threads)
                logger.info(f"{number_of_threads} threads for enhanced SAYNT created")
                active_beliefs = len([True for x in self.storm_control.enhanced_saynt_threads if x["active"]]) + 1
                logger.info(f"number of currently active threads: {active_beliefs}")
                logger.info(f"new synthesis time per thread: {paynt_timeout/active_beliefs}s")
                
                paynt_thread.start()

                logger.info("Timeout for PAYNT started")
                time.sleep(paynt_timeout/active_beliefs)
                self.interactive_queue.put("timeout")

                while not self.interactive_queue.empty():
                    time.sleep(0.5)

                self.storm_control.belief_explorer.set_fsc_values(self.storm_control.paynt_export, 0)

                for index, belief_thread in enumerate(self.storm_control.enhanced_saynt_threads):
                    if belief_thread["active"]:
                        logger.info(f'starting synthesis for {belief_thread["type"]}')
                        belief_thread["synthesizer"].interactive_queue.put("resume")
                        time.sleep(paynt_timeout/active_beliefs)
                        belief_thread["synthesizer"].interactive_queue.put("timeout")
                        while not belief_thread["synthesizer"].interactive_queue.empty():
                            time.sleep(0.5)

                        export_full = []
                        for mem_export in belief_thread["synthesizer"].storm_control.paynt_export:
                            one_memory = []
                            for val_export in mem_export:
                                full_pomdp_values = {belief_thread["state_map"][mem_export]:val for mem_export, val in val_export.items()}
                                one_memory.append(full_pomdp_values)
                            export_full.append(one_memory)

                        self.storm_control.belief_explorer.set_fsc_values(export_full, index+1)
            else:
                self.storm_control.interactive_storm_resume(storm_timeout)
                self.storm_control.parse_belief_data()

                if self.storm_control.dynamic_thread_timeout:
                    if self.storm_control.saynt_overapprox:
                        self.storm_control.deactivate_threads()
                        self.storm_control.overapp_belief_value_analysis(number_of_beliefs)
                    else:
                        # TODO some other dynamic timeout method
                        pass

                logger.info(f"{len(self.storm_control.enhanced_saynt_threads) - number_of_threads} new threads for enhanced SAYNT created")
                logger.info(f"total number of created threads: {len(self.storm_control.enhanced_saynt_threads)}")
                number_of_threads = len(self.storm_control.enhanced_saynt_threads)
                active_beliefs = len([True for x in self.storm_control.enhanced_saynt_threads if x["active"]]) + 1
                logger.info(f"number of currently active threads: {active_beliefs}")
                logger.info(f"new synthesis time per thread: {paynt_timeout/active_beliefs}s")

                self.interactive_queue.put("resume")
                time.sleep(paynt_timeout/active_beliefs)
                self.interactive_queue.put("timeout")

                while not self.interactive_queue.empty():
                    time.sleep(0.5)

                for index, belief_thread in enumerate(self.storm_control.enhanced_saynt_threads):
                    if belief_thread["active"]:
                        logger.info(f'starting synthesis for {belief_thread["type"]}')
                        belief_thread["synthesizer"].interactive_queue.put("resume")
                        time.sleep(paynt_timeout/active_beliefs)
                        belief_thread["synthesizer"].interactive_queue.put("timeout")
                        while not belief_thread["synthesizer"].interactive_queue.empty():
                            time.sleep(0.5)

                        export_full = []
                        for mem_export in belief_thread["synthesizer"].storm_control.paynt_export:
                            one_memory = []
                            for val_export in mem_export:
                                full_pomdp_values = {belief_thread["state_map"][mem_export]:val for mem_export, val in val_export.items()}
                                one_memory.append(full_pomdp_values)
                            export_full.append(one_memory)

                        self.storm_control.belief_explorer.set_fsc_values(export_full, index+1)

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

            print(f"used FSCs: {self.storm_control.storm_fsc_usage}")
            print(f"FSCs used count: {self.storm_control.total_fsc_used}")

            if time.time() > iteration_timeout or iteration == iteration_limit:
                break

            iteration += 1

        for belief_thread in self.storm_control.enhanced_saynt_threads:
            belief_thread["synthesizer"].interactive_queue.put("terminate")
            belief_thread["synthesizer"].synthesis_terminate = True
            belief_thread["thread"].join()

        self.interactive_queue.put("terminate")
        self.synthesis_terminate = True
        paynt_thread.join()

        self.storm_control.interactive_storm_terminate()

        self.saynt_timer.stop()




    # run PAYNT POMDP synthesis with a given timeout
    def run_synthesis_timeout(self, timeout):
        paynt_thread = Thread(target=self.strategy_iterative_storm, args=(True, False))
        iteration_timeout = time.time() + timeout
        paynt_thread.start()

        while True:
            if time.time() > iteration_timeout:
                break

            time.sleep(0.1)

        self.interactive_queue.put("pause")
        self.interactive_queue.put("terminate")
        self.synthesis_terminate = True
        paynt_thread.join()


    # PAYNT POMDP synthesis that uses pre-computed results from Storm as guide
    def strategy_storm(self, unfold_imperfect_only, unfold_storm=True):
        '''
        @param unfold_imperfect_only if True, only imperfect observations will be unfolded
        '''
        mem_size = paynt.quotient.pomdp.PomdpQuotient.initial_memory_size

        while True:
        # for x in range(2):

            if self.storm_control.is_storm_better == False:
                self.storm_control.parse_results(self.quotient)
            
            paynt.quotient.pomdp.PomdpQuotient.current_family_index = mem_size

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
                            if self.storm_control.unfold_cutoff:
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
                    if self.storm_control.incomplete_exploration == True:
                        subfamily_restrictions = []
                    else:
                        subfamily_restrictions = self.storm_control.get_subfamilies_restrictions(family, self.storm_control.result_dict)
                # only consider the induced DTMC actions without cut-off states
                else:
                    main_family = self.storm_control.get_main_restricted_family(family, self.storm_control.result_dict_no_cutoffs)
                    if self.storm_control.incomplete_exploration == True:
                        subfamily_restrictions = []
                    else:
                        subfamily_restrictions = self.storm_control.get_subfamilies_restrictions(family, self.storm_control.result_dict_no_cutoffs)

                subfamilies = self.storm_control.get_subfamilies(subfamily_restrictions, family)
            # if PAYNT is better continue normally
            else:
                main_family = family
                subfamilies = []

            assignment = self.synthesize(family, subfamilies=subfamilies, main_family=main_family)

            if assignment is not None:
                self.storm_control.latest_paynt_result = assignment
                self.storm_control.paynt_export = self.quotient.extract_policy(assignment)
                self.storm_control.paynt_bounds = self.quotient.specification.optimality.optimum


            self.storm_control.update_data()

            mem_size += 1
            
            #break


    def strategy_iterative(self, unfold_imperfect_only, max_memory=None):
        '''
        @param unfold_imperfect_only if True, only imperfect observations will be unfolded
        '''
        mem_size = paynt.quotient.pomdp.PomdpQuotient.initial_memory_size
        opt = self.quotient.specification.optimality.optimum
        while True:
            
            logger.info("Synthesizing optimal k={} controller ...".format(mem_size) )
            if unfold_imperfect_only:
                self.quotient.set_imperfect_memory_size(mem_size)
            else:
                self.quotient.set_global_memory_size(mem_size)
            
            self.synthesize(self.quotient.design_space)

            opt_old = opt
            opt = self.quotient.specification.optimality.optimum

            # finish if optimum has not been improved
            # if opt_old == opt and opt is not None:
            #     break
            mem_size += 1

            if max_memory is not None and mem_size > max_memory:
                break

            #break
    
    def solve_mdp(self, family):

        # solve quotient MDP
        self.quotient.build(family)
        spec = self.quotient.check_specification_for_mdp(family.mdp, family.constraint_indices)

        # nothing more to do if optimality cannot be improved
        if not spec.optimality_result.can_improve:
            return family.mdp, spec, None, None, None, None

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
        
        choice_values = result.primary_choice_values
        expected_visits = result.primary_expected_visits
        # scores = result.primary_scores
        scores = hole_scores

        return family.mdp, spec, selection, choice_values, expected_visits, scores

    
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
            choice_to_assignment = self.quotient.coloring.getChoiceToAssignment()
            state_to_holes = self.quotient.coloring.getStateToHoles()
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
                    holes = state_to_holes[quotient_state]
                    if not holes:
                        continue
                    hole = list(holes)[0]
                    
                    # get choice obtained by the MDP model checker
                    choice_0 = mdp.model.transition_matrix.get_row_group_start(state)
                    mdp_choice = scheduler.get_choice(state).get_deterministic_choice()
                    mdp_choice = choice_0 + mdp_choice
                    
                    # get choice implied by the synthesizer
                    syn_option = synthesized_assignment.hole_options(hole)[0]
                    nci = mdp.model.nondeterministic_choice_indices
                    for choice in range(nci[state],nci[state+1]):
                        choice_global = mdp.quotient_choice_map[choice]
                        assignment = choice_to_assignment[choice_global]
                        choice_color = {hole:option for hole,option in assignment}
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
                dtmc = self.quotient.build_assignment(synthesized_assignment)

                # compute expected visits for this dtmc
                dtmc_visits = paynt.verification.property.Property.compute_expected_visits(dtmc)

                # handle infinity- and zero-visits
                if self.quotient.specification.optimality.minimizing:
                    dtmc_visits = paynt.quotient.quotient.Quotient.make_vector_defined(dtmc_visits)
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
                    hole = list(state_to_holes[quotient_state])[0]
                    hole_differences[hole] += weighted_improvement
                    hole_states_affected[hole] += 1

                hole_differences_avg = [0] * family.num_holes
                for hole in range(family.num_holes):
                    if hole_states_affected[hole] != 0:
                        hole_differences_avg[hole] = hole_differences[hole] / hole_states_affected[hole]
                all_scores = {hole:hole_differences_avg[hole] for hole in range(family.num_holes)}
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
                


    def run(self, optimum_threshold=None, export_evaluation=None):
        # choose the synthesis strategy:
        if self.use_storm:
            logger.info("Storm POMDP option enabled")
            logger.info("Storm settings: iterative - {}, get_storm_result - {}, storm_options - {}, prune_storm - {}, unfold_strategy - {}, use_storm_cutoffs - {}, enhanced_saynt - {}, saynt_overapprox - {}".format(
                        (self.storm_control.iteration_timeout, self.storm_control.paynt_timeout, self.storm_control.storm_timeout), self.storm_control.get_result,
                        self.storm_control.storm_options, self.storm_control.incomplete_exploration, (self.storm_control.unfold_storm, self.storm_control.unfold_cutoff), self.storm_control.use_cutoffs, self.storm_control.enhanced_saynt, self.storm_control.saynt_overapprox
            ))
            # start SAYNT
            if self.storm_control.iteration_timeout is not None:
                if self.storm_control.enhanced_saynt is None:
                    self.iterative_storm_loop(timeout=self.storm_control.iteration_timeout, 
                                            paynt_timeout=self.storm_control.paynt_timeout, 
                                            storm_timeout=self.storm_control.storm_timeout, 
                                            iteration_limit=0)
                else:
                    self.enhanced_iterative_storm_loop(timeout=self.storm_control.iteration_timeout, 
                                            paynt_timeout=self.storm_control.paynt_timeout, 
                                            storm_timeout=self.storm_control.storm_timeout, 
                                            number_of_beliefs=self.storm_control.enhanced_saynt,
                                            iteration_limit=0)
            # run PAYNT for a time given by 'self.storm_control.get_result' and then run Storm using the best computed FSC at cut-offs
            elif self.storm_control.get_result is not None:
                if self.storm_control.get_result:
                    self.run_synthesis_timeout(self.storm_control.get_result)
                self.storm_control.run_storm_analysis()
            # run Storm and then use the obtained result to enhance PAYNT synthesis
            else:
                self.storm_control.get_storm_result()
                self.strategy_storm(unfold_imperfect_only=True, unfold_storm=self.storm_control.unfold_storm)

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


        





