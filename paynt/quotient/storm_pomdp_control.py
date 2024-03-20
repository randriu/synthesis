import stormpy
import stormpy.pomdp
import payntbind
import paynt.quotient.pomdp

from ..quotient.models import MarkovChain
from ..utils.profiler import Timer

from os import makedirs

from threading import Thread
from time import sleep
import math

from queue import Queue

import logging
logger = logging.getLogger(__name__)


# class implementing the main components of the Storm integration for FSC synthesis for POMDPs
class StormPOMDPControl:

    latest_storm_result = None      # holds object representing the latest Storm result
    storm_bounds = None             # under-approximation value from Storm

    # PAYNT data and FSC export
    latest_paynt_result = None
    paynt_bounds = None
    paynt_export = []

    # parsed best result data dictionary (Starting with data from Storm)
    result_dict = {}
    result_dict_no_cutoffs = {}
    result_dict_paynt = {}
    memory_vector = {}

    # controller sizes
    belief_controller_size = None
    paynt_fsc_size = None

    is_storm_better = False

    pomdp = None                    # The original POMDP model
    quotient = None
    spec_formulas = None            # The specification to be checked
    storm_options = None
    get_result = None
    use_cutoffs = False
    unfold_strategy_storm = None

    # PAYNT/Storm iteration settings
    iteration_timeout = None
    paynt_timeout = None
    storm_timeout = None

    enhanced_saynt = None
    enhanced_saynt_threads = []
    storm_fsc_usage = {}
    total_fsc_used = 0
    use_uniform_obs_beliefs = True
    dynamic_thread_timeout = False

    storm_terminated = False

    s_queue = None

    saynt_timer = None
    export_fsc_storm = None
    export_fsc_paynt = None


    def __init__(self):
        pass

    def set_options(self,
        storm_options="cutoff", get_storm_result=None, iterative_storm=None, use_storm_cutoffs=False,
        unfold_strategy_storm="storm", prune_storm=False, export_fsc_storm=None, export_fsc_paynt=None, enhanced_saynt=None,
        saynt_overapprox = False
    ):
        self.storm_options = storm_options
        if get_storm_result is not None:
            self.get_result = get_storm_result
        if iterative_storm is not None:
            self.iteration_timeout, self.paynt_timeout, self.storm_timeout = iterative_storm
        self.use_cutoffs = use_storm_cutoffs
        self.unfold_strategy_storm = unfold_strategy_storm
        self.export_fsc_storm = export_fsc_storm
        self.export_fsc_paynt = export_fsc_paynt
        self.enhanced_saynt = enhanced_saynt
        self.saynt_overapprox = saynt_overapprox

        if self.saynt_overapprox:
            self.dynamic_thread_timeout = True

        self.incomplete_exploration = False
        if prune_storm:
            self.incomplete_exploration = True

        self.unfold_storm = True
        self.unfold_cutoff = False
        if unfold_strategy_storm == "paynt":
            self.unfold_storm = False
        elif unfold_strategy_storm == "cutoff":
            self.unfold_cutoff = True

    # create copy of the storm control with the same settings
    def copy(self):
        copy_storm_control = StormPOMDPControl()
        copy_storm_control.storm_options = self.storm_options
        copy_storm_control.use_cutoffs = self.use_cutoffs
        copy_storm_control.unfold_strategy_storm = self.unfold_strategy_storm
        copy_storm_control.incomplete_exploration = self.incomplete_exploration
        copy_storm_control.unfold_storm = self.unfold_storm
        copy_storm_control.unfold_cutoff = self.unfold_cutoff
        copy_storm_control.unfold_storm = self.unfold_storm
        copy_storm_control.unfold_cutoff = self.unfold_cutoff
        copy_storm_control.iteration_timeout = self.iteration_timeout

        return copy_storm_control


    def get_storm_result(self):
        self.run_storm_analysis()
        self.parse_results(self.quotient)
        self.update_data()

        if self.s_queue is not None:
            self.s_queue.put((self.result_dict, self.storm_bounds))

    # run Storm POMDP analysis for given model and specification
    # TODO: discuss Storm options
    def run_storm_analysis(self):
        # TODO rework options
        if self.storm_options == "cutoff":
            options = self.get_cutoff_options(100000)
        elif self.storm_options == "clip2":
            options = self.get_clip2_options()
        elif self.storm_options == "clip4":
            options = self.get_clip4_options()
        elif self.storm_options == "small":
            options = self.get_cutoff_options(100)
        elif self.storm_options == "2mil":
            options = self.get_cutoff_options(2000000)
        elif self.storm_options == "5mil":
            options = self.get_cutoff_options(5000000)
        elif self.storm_options == "10mil":
            options = self.get_cutoff_options(10000000)
        elif self.storm_options == "20mil":
            options = self.get_cutoff_options(20000000)
        elif self.storm_options == "30mil":
            options = self.get_cutoff_options(30000000)
        elif self.storm_options == "50mil":
            options = self.get_cutoff_options(50000000)
        elif self.storm_options == "refine":
            options = self.get_refine_options()
        elif self.storm_options == "overapp":
            options = self.get_overapp_options()
        else:
            logger.error("Incorrect option setting for Storm was found")
            exit()

        belmc = stormpy.pomdp.BeliefExplorationModelCheckerDouble(self.pomdp, options)

        logger.info("starting Storm POMDP analysis")
        storm_timer = Timer()
        storm_timer.start()
        result = belmc.check(self.spec_formulas[0], self.paynt_export)   # calls Storm
        storm_timer.stop()
        logger.info("Storm POMDP analysis completed")

        value = result.upper_bound if self.quotient.specification.optimality.minimizing else result.lower_bound
        size = self.get_belief_controller_size(result, self.paynt_fsc_size)

        if self.get_result is not None:
            # TODO not important for the paper but it would be nice to have correct FSC here as well
            
            if self.storm_options == "overapp":
                print(f'-----------Storm----------- \
                \nValue = {value} | Time elapsed = {round(storm_timer.read(),1)}s | FSC size = {size}\n', flush=True)
                #print(".....")
                #print(result.upper_bound)
                #print(result.lower_bound)
            else:
                print(f'-----------Storm----------- \
                \nValue = {value} | Time elapsed = {round(storm_timer.read(),1)}s | FSC size = {size}\n', flush=True)
            exit()

        print(f'-----------Storm----------- \
              \nValue = {value} | Time elapsed = {round(storm_timer.read(),1)}s | FSC size = {size}\n', flush=True)

        self.latest_storm_result = result
        if self.quotient.specification.optimality.minimizing:
            self.storm_bounds = self.latest_storm_result.upper_bound
        else:
            self.storm_bounds = self.latest_storm_result.lower_bound

    # setup interactive Storm belief model checker
    def interactive_storm_setup(self):
        global belmc    # needs to be global for threading to work correctly
        options = self.get_interactive_options()
        belmc = stormpy.pomdp.BeliefExplorationModelCheckerDouble(self.pomdp, options)

    # start interactive belief model checker, this function is called only once to start the storm thread. To resume Storm computation 'interactive_storm_resume' is used
    def interactive_storm_start(self, storm_timeout, enhanced=False):
        self.storm_thread = Thread(target=self.interactive_run, args=(belmc,))
        control_thread = Thread(target=self.interactive_control, args=(belmc, True, storm_timeout, enhanced))

        logger.info("Interactive Storm started")
        control_thread.start()
        self.storm_thread.start()

        control_thread.join()

        self.belief_explorer = belmc.get_interactive_belief_explorer()

    # resume interactive belief model checker, should be called only after belief model checker was previously started
    def interactive_storm_resume(self, storm_timeout, enhanced=False):
        control_thread = Thread(target=self.interactive_control, args=(belmc, False, storm_timeout, enhanced))

        logger.info("Interactive Storm resumed")
        control_thread.start()

        control_thread.join()

    # terminate interactive belief model checker
    def interactive_storm_terminate(self):
        belmc.terminate_unfolding()
        self.storm_thread.join()

    # this function represents the storm thread in SAYNT
    def interactive_run(self, belmc):
        logger.info("starting Storm POMDP analysis")
        result = belmc.check(self.spec_formulas[0], self.paynt_export)   # calls Storm

        # to get here Storm exploration has to end either by constructing finite belief MDP or by outside termination
        self.storm_terminated = True

        if result.induced_mc_from_scheduler is not None:
            value = result.upper_bound if self.quotient.specification.optimality.minimizing else result.lower_bound
            size = self.get_belief_controller_size(result, self.paynt_fsc_size)

            print(f'-----------Storm----------- \
              \nValue = {value} | Time elapsed = {round(self.saynt_timer.read(),1)}s | FSC size = {size}\n', flush=True)
            
            if self.export_fsc_storm is not None:
                makedirs(self.export_fsc_storm, exist_ok=True)
                with open(self.export_fsc_storm + "/storm.fsc", "w") as text_file:
                    print(result.induced_mc_from_scheduler.to_dot(), file=text_file)
                    text_file.close()

            self.latest_storm_result = result
            if self.quotient.specification.optimality.minimizing:
                self.storm_bounds = self.latest_storm_result.upper_bound
            else:
                self.storm_bounds = self.latest_storm_result.lower_bound
            self.parse_results(self.quotient)
            self.update_data()

        logger.info("Storm POMDP analysis completed")

    # ensures correct execution of one loop of Storm exploration
    def interactive_control(self, belmc, start, storm_timeout, enhanced=False):
        if belmc.has_converged():
            logger.info("Storm already terminated.")
            return

        # Update cut-off FSC values provided by PAYNT
        if not start:
            logger.info("Updating FSC values in Storm")
            self.belief_explorer.set_fsc_values(self.paynt_export, 0)
            belmc.continue_unfolding()

        # wait for Storm to start exploring
        while not belmc.is_exploring():
            if belmc.has_converged():
                break
            sleep(0.01)

        sleep(storm_timeout)
        if self.storm_terminated:
            return
        logger.info("Pausing Storm")
        if enhanced:
            belmc.pause_unfolding_for_cut_off_values()
        else:
            belmc.pause_unfolding()

        # wait for the result to be constructed from the explored belief MDP
        while not belmc.is_result_ready():
            sleep(1)

        result = belmc.get_interactive_result()

        if enhanced:
            self.beliefs = belmc.get_beliefs_from_exchange()
            self.belief_overapp_values = belmc.get_exchange_overapproximation_map()

        value = result.upper_bound if self.quotient.specification.optimality.minimizing else result.lower_bound
        size = self.get_belief_controller_size(result, self.paynt_fsc_size)

        print(f'-----------Storm----------- \
              \nValue = {value} | Time elapsed = {round(self.saynt_timer.read(),1)}s | FSC size = {size}\n', flush=True)
        
        if self.export_fsc_storm is not None:
            makedirs(self.export_fsc_storm, exist_ok=True)
            with open(self.export_fsc_storm + "/storm.fsc", "w") as text_file:
                print(result.induced_mc_from_scheduler.to_dot(), file=text_file)
                text_file.close()

        self.latest_storm_result = result
        if self.quotient.specification.optimality.minimizing:
            self.storm_bounds = self.latest_storm_result.upper_bound
        else:
            self.storm_bounds = self.latest_storm_result.lower_bound
        self.parse_results(self.quotient)
        self.update_data()

    ########
    # Different options for Storm below (would be nice to make this more succint)

    def get_cutoff_options(self, belief_states=100000):
        options = stormpy.pomdp.BeliefExplorationModelCheckerOptionsDouble(False, True)
        options.use_state_elimination_cutoff = False
        options.size_threshold_init = belief_states
        options.use_clipping = False
        return options

    def get_overapp_options(self, belief_states=20000000):
        options = stormpy.pomdp.BeliefExplorationModelCheckerOptionsDouble(True, False)
        options.use_state_elimination_cutoff = False
        options.size_threshold_init = belief_states
        options.use_clipping = False
        return options

    def get_refine_options(self, step_limit=0):
        options = stormpy.pomdp.BeliefExplorationModelCheckerOptionsDouble(False, True)
        options.use_state_elimination_cutoff = False
        options.size_threshold_init = 0
        options.size_threshold_factor = 2
        options.use_clipping = False
        options.gap_threshold_init = 0
        options.refine_precision = 0
        if step_limit > 0:
            options.refine_step_limit = step_limit
        options.refine = True
        return options

    def get_clip2_options(self):
        options = stormpy.pomdp.BeliefExplorationModelCheckerOptionsDouble(False, True)
        options.use_state_elimination_cutoff = False
        options.size_threshold_init = 0
        options.use_clipping = True
        options.clipping_grid_res = 2
        options.gap_threshold_init = 0
        return options

    def get_clip4_options(self):
        options = stormpy.pomdp.BeliefExplorationModelCheckerOptionsDouble(False, True)
        options.use_state_elimination_cutoff = False
        options.size_threshold_init = 0
        options.use_clipping = True
        options.clipping_grid_res = 4
        options.gap_threshold_init = 0
        return options

    def get_interactive_options(self):
        options = stormpy.pomdp.BeliefExplorationModelCheckerOptionsDouble(self.saynt_overapprox, True)
        options.use_state_elimination_cutoff = False
        options.size_threshold_init = 0
        options.resolution_init = 2
        options.skip_heuristic_schedulers = False
        options.interactive_unfolding = True
        options.gap_threshold_init = 0
        options.refine = False
        options.cut_zero_gap = False
        if self.storm_options == "clip2":
            options.use_clipping = True
            options.clipping_grid_res = 2
        elif self.storm_options == "clip4":
            options.use_clipping = True
            options.clipping_grid_res = 4
        return options
    
    # End of options
    ########

    # computes over-approximation for the given POMDP
    # this can be used to compute bounds for POMDP abstraction
    # TODO discuss the best options for this use case
    @staticmethod
    def storm_pomdp_analysis(model, formulas):
        options = stormpy.pomdp.BeliefExplorationModelCheckerOptionsDouble(True, False)
        options.use_state_elimination_cutoff = False
        options.size_threshold_init = 1000000
        options.use_clipping = False
        options.exploration_time_limit = 60
        belmc = stormpy.pomdp.BeliefExplorationModelCheckerDouble(model, options)

        result = belmc.check(formulas[0], [])   # calls Storm

        return result
    


    def create_thread_control(self, belief_info, belief_type, obs_option=True):
        if belief_type == "obs":
            if obs_option:
                obs_states = []
                for state in range(self.quotient.pomdp.nr_states):
                    if self.quotient.pomdp.observations[state] == belief_info:
                        obs_states.append(state)
                prob = 1/len(obs_states)
                initial_belief = {x:prob for x in obs_states}
            else:
                initial_belief = self.average_belief_data[belief_info]
        elif belief_type == "sup":
            states = list(belief_info)
            prob = 1/len(states)
            initial_belief = {x:prob for x in states}
        elif belief_type == "belief":
            initial_belief = self.beliefs[belief_info]
        elif belief_type == "custom":
            initial_belief = belief_info
        else:
            assert False, "wrong belief type"

        sub_pomdp = self.sub_pomdp_builder.start_from_belief(initial_belief)
        sub_pomdp_quotient = paynt.quotient.pomdp.PomdpQuotient(sub_pomdp, self.quotient.specification.copy())

        sub_pomdp_storm_control = self.copy()

        sub_pomdp_synthesizer = paynt.synthesizer.synthesizer_pomdp.SynthesizerPOMDP(sub_pomdp_quotient, "ar", sub_pomdp_storm_control)
        sub_pomdp_synthesizer.main_synthesizer = False

        sub_pomdp_thread = Thread(target=sub_pomdp_synthesizer.strategy_iterative_storm, args=(True, False))

        sub_pomdp_states_to_full = self.sub_pomdp_builder.state_sub_to_full

        if belief_type == "obs":
            belief_thread_type_label = "obs_" + str(belief_info)
        elif belief_type == "belief":
            belief_thread_type_label = "belief_" + str(belief_info)
        else:
            belief_thread_type_label = "custom"
            
        belief_thread_data = {"synthesizer": sub_pomdp_synthesizer, "thread": sub_pomdp_thread, "state_map": sub_pomdp_states_to_full, "active": True, "type": belief_thread_type_label}

        self.enhanced_saynt_threads.append(belief_thread_data)

        # create index for FSC in Storm
        thread_index = self.belief_explorer.add_fsc_values([])
        assert thread_index == len(self.enhanced_saynt_threads), "Newly created thread and its index in Storm are not matching"

        self.enhanced_saynt_threads[thread_index-1]["thread"].start()
        self.enhanced_saynt_threads[thread_index-1]["synthesizer"].interactive_queue.put("timeout")

    
    # parse the current Storm and PAYNT results if they are available
    def parse_results(self, quotient):
        if self.latest_storm_result is not None:
            self.parse_storm_result(quotient)
        else:
            self.result_dict = {}
            self.result_dict_no_cutoffs = {}

        if self.latest_paynt_result is not None:
            self.parse_paynt_result(quotient)
        else:
            self.result_dict_paynt = {}    

    # parse Storm results into a dictionary
    def parse_storm_result(self, quotient):
        # to make the code cleaner
        get_choice_label = self.latest_storm_result.induced_mc_from_scheduler.choice_labeling.get_labels_of_choice

        cutoff_epxloration = [x for x in range(len(self.latest_storm_result.cutoff_schedulers))]
        finite_mem = False

        result = {x:[] for x in range(quotient.observations)}
        result_no_cutoffs = {x:[] for x in range(quotient.observations)}

        self.storm_fsc_usage = {}
        
        for state in self.latest_storm_result.induced_mc_from_scheduler.states:
            # TODO what if there were no labels in the model?
            if get_choice_label(state.id) == set():
                continue

            # parse non cut-off states
            if 'cutoff' not in state.labels and 'clipping' not in state.labels:
                for label in state.labels:
                    # observation based on prism observables
                    if '[' in label:
                        observation = self.quotient.observation_labels.index(label)

                        index = -1

                        choice_label = list(get_choice_label(state.id))[0]
                        for i in range(len(quotient.action_labels_at_observation[int(observation)])):
                            if choice_label == quotient.action_labels_at_observation[int(observation)][i]:
                                index = i
                                break

                        if index >= 0 and index not in result[int(observation)]:
                            result[int(observation)].append(index)

                        if index >= 0 and index not in result_no_cutoffs[int(observation)]:
                            result_no_cutoffs[int(observation)].append(index)
                    # explicit observation index
                    elif 'obs_' in label:
                        _, observation = label.split('_')

                        index = -1
                        choice_label = list(get_choice_label(state.id))[0]
                        for i in range(len(quotient.action_labels_at_observation[int(observation)])):
                            if choice_label == quotient.action_labels_at_observation[int(observation)][i]:
                                index = i
                                break

                        if index >= 0 and index not in result[int(observation)]:
                            result[int(observation)].append(index)

                        if index >= 0 and index not in result_no_cutoffs[int(observation)]:
                            result_no_cutoffs[int(observation)].append(index)
                        
            # parse cut-off states
            else:
                for label in state.labels:
                    if 'finite_mem' in label:
                        fsc_index = int(label.split('_')[-1])
                        if fsc_index not in self.storm_fsc_usage.keys():
                            self.storm_fsc_usage[fsc_index] = 1
                            if fsc_index == 0:
                                finite_mem_dict = self.result_dict_paynt
                            else:
                                finite_mem_dict = self.enhanced_saynt_threads[fsc_index-1]["synthesizer"].storm_control.result_dict_paynt
                            for obs, actions in finite_mem_dict.items():
                                for action in actions:
                                    if action not in result_no_cutoffs[obs]:
                                        result_no_cutoffs[obs].append(action)
                                    if action not in result[obs]:
                                        result[obs].append(action)
                        else:
                            self.storm_fsc_usage[fsc_index] += 1
                        break
                else:
                    if len(cutoff_epxloration) == 0:
                        continue
                    
                    # obtain what cut-off scheduler was used
                    if 'sched_' in list(get_choice_label(state.id))[0]:
                        _, scheduler_index = list(get_choice_label(state.id))[0].split('_')
    
                        if int(scheduler_index) not in cutoff_epxloration:
                            continue
    
                        scheduler = self.latest_storm_result.cutoff_schedulers[int(scheduler_index)]
    
                        for state in range(quotient.pomdp.nr_states):
    
                            choice_string = str(scheduler.get_choice(state).get_choice())
                            actions = self.parse_choice_string(choice_string)
    
                            observation = quotient.pomdp.get_observation(state)
    
                            for action in actions:
                                if action not in result[observation]:
                                    result[observation].append(action)
    
                        cutoff_epxloration.remove(int(scheduler_index))

        # removing unrestricted observations
        observations = list(result.keys())
        for obs in observations:
            if len(result[obs]) == 0:
                del result[obs]

            if len(result_no_cutoffs[obs]) == 0:
                del result_no_cutoffs[obs]

        self.result_dict = result    
        self.result_dict_no_cutoffs = result_no_cutoffs
        self.total_fsc_used = sum(list(self.storm_fsc_usage.values()))


    def parse_belief_data(self):      
        obs_dict = {}
        support_dict = {}
        total_obs_belief_dict = {}

        for belief in self.beliefs.values():
            belief_obs = self.quotient.pomdp.get_observation(list(belief.keys())[0])
            if belief_obs not in obs_dict.keys():
                obs_dict[belief_obs] = 1
            else:
                obs_dict[belief_obs] += 1

            if belief_obs not in total_obs_belief_dict.keys():
                total_obs_belief_dict[belief_obs] = {}
                for state, probability in belief.items():
                    total_obs_belief_dict[belief_obs][state] = probability
            else:
                for state, probability in belief.items():
                    if state not in total_obs_belief_dict[belief_obs].keys():
                        total_obs_belief_dict[belief_obs][state] = probability
                    else:
                        total_obs_belief_dict[belief_obs][state] += probability

            support = tuple(list(belief.keys()))
            if support not in support_dict.keys():
                support_dict[support] = 1
            else:
                support_dict[support] += 1

        average_obs_belief_dict = {}
            
        for obs, total_dict in total_obs_belief_dict.items():
            total_value = sum(list(total_dict.values()))
            average_obs_belief_dict[obs] = {}
            for state, state_total_val in total_dict.items():
                average_obs_belief_dict[obs][state] = state_total_val / total_value

        percent_1 = round(len(self.beliefs)/100)

        sorted_obs = sorted(obs_dict, key=obs_dict.get)
        sorted_support = sorted(support_dict, key=support_dict.get)

        main_observation_list = [obs for obs in sorted_obs if obs_dict[obs] > percent_1]
        main_support_list = [sup for sup in sorted_support if support_dict[sup] > percent_1]

        residue_observation_list = [obs for obs in sorted_obs if obs not in main_observation_list]
        residue_support_list = [sup for sup in sorted_support if sup not in main_support_list]

        self.main_obs_belief_data = main_observation_list
        self.main_support_belief_data = main_support_list
        self.residue_obs_belief_data = residue_observation_list
        self.average_belief_data = average_obs_belief_dict


    def compute_belief_value(self, belief, obs, fsc_values=[]):
        best_value = None

        for values in fsc_values:
            if obs >= len(values):
                continue
            for index, mem_values in enumerate(values[obs]):
                vl = 0
                for state, prob in belief.items():
                    if not state in mem_values.keys():
                        break
                    vl += prob * mem_values[state]
                else:
                    if best_value is None:
                        best_value = vl
                    elif (self.quotient.specification.optimality.minimizing and best_value > vl) or (not(self.quotient.specification.optimality.minimizing) and best_value < vl):
                        best_value = vl
            
        return best_value
    

    def overapp_belief_value_analysis(self, number_of_beliefs):

        export_values = [x["synthesizer"].storm_control.paynt_export for x in self.enhanced_saynt_threads]
        export_values.append(self.paynt_export)

        analysed_beliefs = 0

        obs_differences = {}
        obs_count = {}
        belief_values_dif = {}

        for belief_id, belief in self.beliefs.items():
            if belief_id in self.belief_overapp_values.keys():
                analysed_beliefs += 1
                belief_obs = self.quotient.pomdp.get_observation(list(belief.keys())[0])
                belief_value = self.compute_belief_value(belief, belief_obs, export_values)
                belief_values_dif[belief_id] = abs(self.belief_overapp_values[belief_id] - belief_value)

                if belief_obs not in obs_differences.keys():
                    obs_count[belief_obs] = 1
                    obs_differences[belief_obs] = abs(self.belief_overapp_values[belief_id] - belief_value)
                else:
                    obs_count[belief_obs] += 1
                    obs_differences[belief_obs] += abs(self.belief_overapp_values[belief_id] - belief_value)

        obs_values = {obs_key:obs_dif/obs_count[obs_key] for obs_key, obs_dif in obs_differences.items()}
        sorted_obs_values = {k: v for k, v in sorted(obs_values.items(), key=lambda item: item[1], reverse=True)}

        sorted_belief_values_dif = {k: v for k, v in sorted(belief_values_dif.items(), key=lambda item: item[1], reverse=True)}

        obs_to_activate = []
        beliefs_to_activate = []

        if number_of_beliefs == 0:
            number_of_threads_to_activate = len(self.main_obs_belief_data)
            if number_of_threads_to_activate <= 4:
                number_of_threads_to_activate = 5
        else:
            number_of_threads_to_activate = number_of_beliefs - 1

        for obs in sorted_obs_values.keys():
            obs_to_activate.append(obs)
            number_of_threads_to_activate -= 1
            if number_of_threads_to_activate <= 2:
                break

        added_belief_obs = [self.quotient.pomdp.get_observation(list(self.beliefs[list(sorted_belief_values_dif.keys())[0]].keys())[0])]
        beliefs_to_activate.append(list(sorted_belief_values_dif.keys())[0])
        number_of_threads_to_activate -= 1

        for belief_id, _ in sorted_belief_values_dif.items():
            if number_of_threads_to_activate > 1 and belief_id not in beliefs_to_activate:
                added_belief_obs.append(self.quotient.pomdp.get_observation(list(self.beliefs[belief_id].keys())[0]))
                beliefs_to_activate.append(belief_id)
                number_of_threads_to_activate -= 1
                continue
            if self.quotient.pomdp.get_observation(list(self.beliefs[belief_id].keys())[0]) not in added_belief_obs:
                beliefs_to_activate.append(belief_id)
                break

        self.activate_threads(obs_to_activate, beliefs_to_activate)

        print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
        print(sorted_obs_values)
        my_iter = 0
        for belief_id, diff in sorted_belief_values_dif.items():
            print(belief_id, self.quotient.pomdp.get_observation(list(self.beliefs[belief_id].keys())[0]), diff)
            my_iter += 1
            if my_iter == 20:
                break
        print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
            

    # help function for cut-off parsing, returns list of actions for given choice_string
    # TODO bound to restrict some action if needed
    def parse_choice_string(self, choice_string, probability_bound=0):
        chars = '}{]['
        for c in chars:
            choice_string = choice_string.replace(c, '')
        
        choice_string = choice_string.strip(', ')

        choices = choice_string.split(',')

        result = []

        for choice in choices:
            probability, action = choice.split(':')
            # probability bound

            action = int(action.strip())
            
            result.append(action)

        return result

    # parse PAYNT result to a dictionart
    def parse_paynt_result(self, quotient):

        result = {x:[] for x in range(quotient.observations)}
        
        for hole in range(self.latest_paynt_result.num_holes):
            name = self.latest_paynt_result.hole_name(hole)
            if name.startswith('M'):
                continue
            name = name.strip('A()')
            obs = name.split(',')[0]
            if obs.isdigit():
                observation = int(obs)
            else:
                assert obs in self.quotient.observation_labels, f"observation labels {self.quotient.observation_labels} don't contain {obs} even though it's used in hole name {name}"
                observation = self.quotient.observation_labels.index(obs)

            option = self.latest_paynt_result.hole_options(hole)[0]
            if option not in result[observation]:
                result[observation].append(option)

        observations = list(result.keys())
        for obs in observations:
            if len(result[obs]) == 0:
                del result[obs]

        #logger.info("Result dictionary is based on result from PAYNT")
        self.result_dict_paynt = result

    # returns the main family that will be explored first
    # main family contains only the actions considered by respective FSC (most usually Storm result)
    def get_main_restricted_family(self, family, result_dict):

        if result_dict == {}:
            return family

        restricted_family = family.copy()
        # go through each observation of interest
        for obs in range(self.quotient.observations):
            for hole in self.quotient.observation_action_holes[obs]:

                if obs in result_dict.keys():
                    selected_actions = [action for action in family.hole_options(hole) if action in result_dict[obs]]
                else:
                    selected_actions = [family.hole_options(hole)[0]]

                if len(selected_actions) == 0:
                    return None

                restricted_family.hole_set_options(hole,selected_actions)

        logger.info("Main family based on data from Storm: reduced design space from {} to {}".format(family.size, restricted_family.size))

        return restricted_family


    # returns dictionary containing restrictions for easy creation of subfamilies
    # creating this restrictions list saves some memory compared to constructing all of the families
    # corresponding families are then created only when needed
    def get_subfamilies_restrictions(self, family, result_dict):

        if result_dict == {}:
            return {}

        subfamilies_restriction = []

        restricted_holes_list = []

        for observ in result_dict.keys():

            act_obs_holes = self.quotient.observation_action_holes[observ]
            restricted_holes_list.extend(act_obs_holes)

        for hole in restricted_holes_list:

            for obs_holes, index in zip(self.quotient.observation_action_holes, range(len(self.quotient.observation_action_holes))):
                if hole in obs_holes:
                    obs = index

            if len(result_dict[obs]) == self.quotient.actions_at_observation[obs]:
                continue

            restriction = [action for action in family.hole_options(hole) if action in result_dict[obs]]

            if len(restriction) == family.hole_num_options(hole):
                continue

            subfamilies_restriction.append({"hole": hole, "restriction": restriction})

        return subfamilies_restriction

    # constructs the families given by the restrictions list
    def get_subfamilies(self, restrictions, family):

        subfamilies = []

        for i in range(len(restrictions)):
            restricted_family = family.copy()

            actions = [action for action in family.hole_options(restrictions[i]["hole"]) if action not in restrictions[i]["restriction"]]
            if len(actions) == 0:
                actions = [family.hole_options(restrictions[i]["hole"])[0]]

            restricted_family.hole_set_options(restrictions[i]['hole'],actions)

            for j in range(i):
                restricted_family.hole_set_options(restrictions[j]['hole'],restrictions[j]["restriction"])

            subfamilies.append(restricted_family)

        return subfamilies

    # returns True if the current best FSC from Storm requires more memory
    # returns False otherwise
    def is_memory_needed(self):
        if len(self.memory_vector) == 0:
            return False

        memory_needed = False
        for obs in range(self.quotient.observations):
            if self.quotient.observation_memory_size[obs] < self.memory_vector[obs]:
                memory_needed = True
                break
        return memory_needed
    
    def deactivate_threads(self):
        for thread in self.enhanced_saynt_threads:
            thread["active"] = False

    def activate_threads(self, obs_threads, belief_threads):
        logger.info(f"activating observation threads: {obs_threads}")

        for obs in obs_threads:
            for thread in self.enhanced_saynt_threads:
                thread_type = thread["type"].split('_')
                thread_val = thread_type[1]
                thread_type = thread_type[0]
                if thread_type == "obs" and int(thread_val) == obs:
                    thread["active"] = True
                    break
            else:
                self.create_thread_control(obs, "obs", self.use_uniform_obs_beliefs)

        logger.info(f"activating belief threads: {belief_threads}")        
            
        for belief in belief_threads:
            for thread in self.enhanced_saynt_threads:
                thread_type = thread["type"].split('_')
                thread_val = thread_type[1]
                thread_type = thread_type[0]
                if thread_type == "belief" and int(thread_val) == belief:
                    thread["active"] = True
                    break
            else:
                self.create_thread_control(belief, "belief", self.use_uniform_obs_beliefs)



    # update all of the important data structures according to the current results
    def update_data(self):

        if self.paynt_bounds is None and self.storm_bounds is None:
            return

        if self.paynt_bounds is None:
            self.is_storm_better = True
        elif self.storm_bounds is None:
            self.is_storm_better = False
        else:
            if self.quotient.specification.optimality.minimizing:
                if self.paynt_bounds <= self.storm_bounds:
                    self.is_storm_better = False
                else:
                    self.is_storm_better = True
            else:
                if self.paynt_bounds >= self.storm_bounds:
                    self.is_storm_better = False
                else:
                    self.is_storm_better = True


        if self.unfold_strategy_storm in ["storm", "paynt"]:
            for obs in range(self.quotient.observations):
                if obs in self.result_dict_no_cutoffs.keys():
                    self.memory_vector[obs] = len(self.result_dict_no_cutoffs[obs])
                else:
                    self.memory_vector[obs] = 1
        else:
            for obs in range(self.quotient.observations):
                if obs in self.result_dict.keys():
                    self.memory_vector[obs] = len(self.result_dict[obs])
                else:
                    self.memory_vector[obs] = 1
    
    # Computes the size of the controller for belief MC
    # if it uses FSC cutoffs assignment should be provided
    # FORMULA: E + 2*T + size(Fc)
    # E - number of non-frontier states (non cutoff states)
    # T - number of transitions
    # Fc - used cut-off schedulers
    def get_belief_controller_size(self, storm_result, paynt_fsc_size=None):

        belief_mc = storm_result.induced_mc_from_scheduler

        non_frontier_states = 0
        uses_fsc = False
        used_randomized_schedulers = []

        fsc_size = 0
        randomized_schedulers_size = 0

        for state in belief_mc.states:
            if 'cutoff' not in state.labels:
                non_frontier_states += 1
            elif 'finite_mem' in state.labels and not uses_fsc:
                uses_fsc = True
            else:
                for label in state.labels:
                    if 'sched_' in label:
                        _, scheduler_index = label.split('_')
                        if int(scheduler_index) in used_randomized_schedulers:
                            continue
                        used_randomized_schedulers.append(int(scheduler_index))

        if uses_fsc:
            # Compute the size of FSC
            if paynt_fsc_size:
                fsc_size = paynt_fsc_size

        for index in used_randomized_schedulers:
            observation_actions = {x:[] for x in range(self.quotient.observations)}
            rand_scheduler = storm_result.cutoff_schedulers[index]
            for state in range(self.quotient.pomdp.nr_states):
                choice_string = str(rand_scheduler.get_choice(state).get_choice())
                actions = self.parse_choice_string(choice_string)
                observation = self.quotient.pomdp.get_observation(state)
                for action in actions:
                    if action not in observation_actions[observation]:
                        observation_actions[observation].append(action)
            randomized_schedulers_size += sum(list([len(support) for support in observation_actions.values()])) * 3

        result_size = non_frontier_states + belief_mc.nr_transitions + fsc_size + randomized_schedulers_size

        return result_size
