import paynt.quotient
import paynt.quotient.fsc
import stormpy
import stormpy.pomdp
import payntbind

import paynt.utils.timer

from os import makedirs

from threading import Thread
from time import sleep

import logging
logger = logging.getLogger(__name__)


# class implementing the main components of the Storm integration for FSC synthesis for POMDPs
class StormPOMDPControl:

    def __init__(self):
        self.latest_storm_result = None      # holds object representing the latest Storm result
        self.storm_bounds = None             # under-approximation value from Storm

        self.saynt_fsc = None                # holds the FSC synthesized using SAYNT

        # PAYNT data and FSC export
        self.latest_paynt_result = None      # holds the synthesised assignment
        self.latest_paynt_result_fsc = None  # holds the FSC built from assignment
        self.paynt_bounds = None
        self.paynt_export = []

        # parsed best result data dictionary (Starting with data from Storm)
        self.result_dict = {}
        self.result_dict_no_cutoffs = {}
        self.result_dict_paynt = {}
        self.memory_vector = {}

        # controller sizes
        self.belief_controller_size = None
        self.paynt_fsc_size = None

        self.is_storm_better = False

        self.pomdp = None                    # The original POMDP model
        self.quotient = None
        self.spec_formulas = None            # The specification to be checked
        self.storm_options = None
        self.get_result = None
        self.use_cutoffs = False
        self.unfold_strategy_storm = None

        # PAYNT/Storm iteration settings
        self.iteration_timeout = None
        self.paynt_timeout = None
        self.storm_timeout = None

        self.storm_terminated = False

        self.s_queue = None

        self.saynt_timer = None

    def set_options(self,
        storm_options, get_storm_result, iterative_storm, use_storm_cutoffs,
        unfold_strategy_storm, prune_storm
    ):
        self.storm_options = storm_options
        if get_storm_result is not None:
            self.get_result = get_storm_result
        if iterative_storm is not None:
            self.iteration_timeout, self.paynt_timeout, self.storm_timeout = iterative_storm
        self.use_cutoffs = use_storm_cutoffs
        self.unfold_strategy_storm = unfold_strategy_storm

        self.incomplete_exploration = False
        if prune_storm:
            self.incomplete_exploration = True

        self.unfold_storm = True
        self.unfold_cutoff = False
        if unfold_strategy_storm == "paynt":
            self.unfold_storm = False
        elif unfold_strategy_storm == "cutoff":
            self.unfold_cutoff = True

    def get_storm_result(self):
        self.run_storm_analysis()
        self.parse_results(self.quotient)
        self.update_data()

        if self.s_queue is not None:
            self.s_queue.put((self.result_dict, self.storm_bounds))

    def store_storm_result(self, result):
        self.latest_storm_result = result
        if self.quotient.specification.optimality.minimizing:
            self.storm_bounds = self.latest_storm_result.upper_bound
        else:
            self.storm_bounds = self.latest_storm_result.lower_bound

        if (self.storm_control.iteration_timeout is not None) or (self.storm_control.get_result is not None):
            self.saynt_fsc = self.belief_controller_to_fsc(self.latest_storm_result, self.latest_paynt_result_fsc)

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
        storm_timer = paynt.utils.timer.Timer()
        storm_timer.start()
        result = belmc.check(self.spec_formulas[0], self.paynt_export)   # calls Storm
        storm_timer.stop()
        logger.info("Storm POMDP analysis completed")

        value = result.upper_bound if self.quotient.specification.optimality.minimizing else result.lower_bound
        self.belief_controller_size = self.get_belief_controller_size(result, self.paynt_fsc_size)

        print(f'-----------Storm-----------')
        print(f'Value = {value} | Time elapsed = {round(storm_timer.read(),1)}s | FSC size = {self.belief_controller_size}', flush=True)
        if self.get_result is not None:
            # TODO not important for the paper but it would be nice to have correct FSC here as well
            if self.storm_options == "overapp":
                #print(".....")
                #print(result.upper_bound)
                #print(result.lower_bound)
                pass
            # else:
                # print(f'FSC (dot) = {result.induced_mc_from_scheduler.to_dot()}\n', flush=True)

        # print(f'\nFSC (dot) = {result.induced_mc_from_scheduler.to_dot()}\n', flush=True)

        self.store_storm_result(result)

    # setup interactive Storm belief model checker
    def interactive_storm_setup(self):
        global belmc    # needs to be global for threading to work correctly
        options = self.get_interactive_options()
        belmc = stormpy.pomdp.BeliefExplorationModelCheckerDouble(self.pomdp, options)

    # start interactive belief model checker, this function is called only once to start the storm thread. To resume Storm computation 'interactive_storm_resume' is used
    def interactive_storm_start(self, storm_timeout):
        self.storm_thread = Thread(target=self.interactive_run, args=(belmc,))
        control_thread = Thread(target=self.interactive_control, args=(belmc, True, storm_timeout,))

        logger.info("Interactive Storm started")
        control_thread.start()
        self.storm_thread.start()

        control_thread.join()

    # resume interactive belief model checker, should be called only after belief model checker was previously started
    def interactive_storm_resume(self, storm_timeout):
        control_thread = Thread(target=self.interactive_control, args=(belmc, False, storm_timeout,))

        if self.storm_terminated:
            logger.info("Storm already terminated")
            return
        
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

            self.store_storm_result(result)
            self.parse_results(self.quotient)
            self.update_data()

        logger.info("Storm POMDP analysis completed")

    # ensures correct execution of one loop of Storm exploration
    def interactive_control(self, belmc, start, storm_timeout):
        if belmc.has_converged():
            logger.info("Storm already terminated.")
            return

        # Update cut-off FSC values provided by PAYNT
        if not start:
            logger.info("Updating FSC values in Storm")
            belmc.set_fsc_values(self.paynt_export)
            belmc.continue_unfolding()

        # wait for Storm to start exploring
        while not belmc.is_exploring():
            if belmc.has_converged():
                break
            sleep(1)

        sleep(storm_timeout)
        if self.storm_terminated:
            logger.info("Storm terminated")
            return
        logger.info("Pausing Storm")
        belmc.pause_unfolding()

        # wait for the result to be constructed from the explored belief MDP
        while not belmc.is_result_ready():
            sleep(1)

        result = belmc.get_interactive_result()

        value = result.upper_bound if self.quotient.specification.optimality.minimizing else result.lower_bound
        size = self.get_belief_controller_size(result, self.paynt_fsc_size)

        print(f'-----------Storm----------- \
              \nValue = {value} | Time elapsed = {round(self.saynt_timer.read(),1)}s | FSC size = {size}\n', flush=True)

        self.store_storm_result(result)
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
        options = stormpy.pomdp.BeliefExplorationModelCheckerOptionsDouble(False, True)
        options.use_state_elimination_cutoff = False
        options.size_threshold_init = 0
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

        cutoff_epxloration = list(range(len(self.latest_storm_result.cutoff_schedulers)))
        finite_mem = False

        result = {x:[] for x in range(quotient.observations)}
        result_no_cutoffs = {x:[] for x in range(quotient.observations)}
        
        for state in self.latest_storm_result.induced_mc_from_scheduler.states:
            # TODO what if there were no labels in the model?
            if get_choice_label(state.id) == set():
                continue

            # parse non cut-off states
            if 'cutoff' not in state.labels and 'clipping' not in state.labels:
                for label in state.labels:
                    observation = None
                    if '[' in label:
                        # observation based on prism observables
                        observation = self.quotient.observation_labels.index(label)
                    elif 'obs_' in label:
                        # explicit observation index
                        _,observation = label.split('_')
                    if observation is not None:
                        observation = int(observation)
                        choice_label = list(get_choice_label(state.id))[0]
                        for index,action_label in enumerate(quotient.action_labels_at_observation[observation]):
                            if choice_label == action_label:
                                if index not in result[observation]:
                                    result[observation].append(index)
                                if index not in result_no_cutoffs[observation]:
                                    result_no_cutoffs[observation].append(index)
                                break
                        

            # parse cut-off states
            else:
                for label in state.labels:
                    if 'finite_mem' in label and not finite_mem:
                        finite_mem = True
                        self.parse_paynt_result(self.quotient)
                        for obs,actions in self.result_dict_paynt.items():
                            for action in actions:
                                if action not in result_no_cutoffs[obs]:
                                    result_no_cutoffs[obs].append(action)
                                if action not in result[obs]:
                                    result[obs].append(action)
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

        logger.info("Main family based on data from Storm: reduced design space from {} to {}".format(family.size_or_order, restricted_family.size_or_order))

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

        for i,restriction in enumerate(restrictions):
            restricted_family = family.copy()

            actions = [action for action in family.hole_options(restriction["hole"]) if action not in restriction["restriction"]]
            if len(actions) == 0:
                actions = [family.hole_options(restriction["hole"])[0]]

            restricted_family.hole_set_options(restriction['hole'],actions)

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

    def belief_controller_to_fsc(self, storm_result, paynt_fsc=None):

        belief_mc = storm_result.induced_mc_from_scheduler

        uses_fsc = False
        used_randomized_schedulers = {}
        paynt_cutoff_states = 0

        for state in belief_mc.states:
            for label in state.labels:
                if 'finite_mem' in label:
                    uses_fsc = True
                    paynt_cutoff_states += 1
                    continue
                elif 'sched_' in label:
                    _, scheduler_index = label.split('_')
                    if int(scheduler_index) in used_randomized_schedulers.keys():
                        continue
                    used_randomized_schedulers[int(scheduler_index)] = state.id
                    continue

        fsc_nodes = belief_mc.nr_states - paynt_cutoff_states + 1 # +1 for new initial node

        fsc_node = 1
        belief_mc_nodes_map = []
        for state in belief_mc.states:
            for label in state.labels:
                if 'finite_mem' in label:
                    belief_mc_nodes_map.append(None)
                    break
            else:
                belief_mc_nodes_map.append(fsc_node)
                fsc_node += 1

        assert fsc_nodes-1 == len([x for x in belief_mc_nodes_map if x is not None]), f"{fsc_nodes-1} != {len([x for x in belief_mc_nodes_map if x is not None])}"

        if uses_fsc:
            fsc_nodes += paynt_fsc.num_nodes
            first_fsc_node = belief_mc.nr_states - paynt_cutoff_states + 1

        result_fsc = paynt.quotient.fsc.FSC(fsc_nodes, self.quotient.observations, is_deterministic=False)

        action_labels = set()
        for labels in self.quotient.action_labels_at_observation:
            action_labels.update(labels)
        action_labels = list(action_labels)
        result_fsc.action_labels = action_labels

        result_fsc.observation_labels = self.quotient.observation_labels

        if paynt_fsc is not None and uses_fsc:
            paynt_fsc.make_stochastic()
            paynt_fsc_num_nodes = paynt_fsc.num_nodes
            paynt_fsc_action_function = paynt_fsc.action_function
            paynt_fsc_update_function = paynt_fsc.update_function
            new_fsc_update_function = []
            
            for node in range(paynt_fsc_num_nodes):
                new_fsc_update_function.append([])
                for obs in range(self.quotient.observations):
                    new_fsc_update_function[node].append({list(paynt_fsc_update_function[node][obs].keys())[0]+first_fsc_node:1.0})

            for node in range(paynt_fsc_num_nodes):
                result_fsc.action_function[node+first_fsc_node] = paynt_fsc_action_function[node]
                result_fsc.update_function[node+first_fsc_node] = new_fsc_update_function[node]
        
        # create the initial node
        init_belief_state = belief_mc.initial_states[0]
        actions = list(belief_mc.choice_labeling.get_labels_of_choice(init_belief_state))
        assert len(actions) == 1, "Belief MC has multiple labels for one action"
        action = actions[0]
        for label in belief_mc.labeling.get_labels_of_state(init_belief_state):
            succ_observation = None
            fsc_switch = None
            cutoff_switch = None
            for label in belief_mc.labeling.get_labels_of_state(init_belief_state):
                if '[' in label:
                    # observation based on prism observables
                    succ_observation = self.quotient.observation_labels.index(label)
                elif 'obs_' in label:
                    # explicit observation index
                    _,succ_observation = label.split('_')
                elif 'finite_mem' in label:
                    fsc_switch = int(label.split('_')[-1])
                if 'sched_' in label:
                    cutoff_switch = int(label.split('_')[1])
                if succ_observation is not None:
                    succ_observation = int(succ_observation)
            assert not((fsc_switch is not None) and (cutoff_switch is not None)), "Belief MC state has both FSC and Storm cutoff scheduler"
            assert succ_observation is not None, "Belief MC state has no observation"
            if fsc_switch is not None:
                result_fsc.action_function[0][succ_observation] = result_fsc.action_function[first_fsc_node+fsc_switch][succ_observation]
                result_fsc.update_function[0][succ_observation] = result_fsc.update_function[first_fsc_node+fsc_switch][succ_observation]
            elif cutoff_switch is not None:
                scheduler = storm_result.cutoff_schedulers[cutoff_switch]
                cutoff_node_id = belief_mc_nodes_map[used_randomized_schedulers[cutoff_switch]]
                for pomdp_state in range(self.quotient.pomdp.nr_states):
                    obs_index = self.quotient.pomdp.get_observation(pomdp_state)
                    if obs_index != succ_observation:
                        continue
                    choice = scheduler.get_choice(pomdp_state).get_choice().__str__()
                    choice = choice.replace('{','').replace('}','').replace('[','').replace(']','').replace(' ','').split(',')
                    for c in choice[:-1]:
                        prob, cutoff_action = c.split(':')
                        action_label = self.quotient.action_labels_at_observation[succ_observation][int(cutoff_action)]
                        action_index = result_fsc.action_labels.index(action_label)
                        if result_fsc.action_function[node_id][succ_observation] is None:
                            result_fsc.action_function[node_id][succ_observation] = {action_index:float(prob)}
                        else:
                            result_fsc.action_function[node_id][succ_observation][action_index] = float(prob)
                    break
                result_fsc.update_function[0][succ_observation] = {cutoff_node_id: 1.0}
            else:
                if action == "loop":
                    result_fsc.action_function[0][succ_observation] = {0: 1.0}
                else:
                    result_fsc.action_function[0][succ_observation] = {result_fsc.action_labels.index(action): 1.0}
                result_fsc.update_function[0][succ_observation] = {belief_mc_nodes_map[init_belief_state]: 1.0}

        for state in belief_mc.states:
            node_id = belief_mc_nodes_map[state.id]
            if node_id is None:
                continue
            elif 'cutoff' in state.labels: # Storm cutoff schedulers
                for label in state.labels:
                    if 'sched_' in label:
                        _, scheduler_index = label.split('_')
                        break
                else:
                    continue
                scheduler = storm_result.cutoff_schedulers[int(scheduler_index)]
                for obs in range(self.quotient.observations):
                    result_fsc.update_function[node_id][obs] = {node_id: 1.0}
                processed_obs = []
                for pomdp_state in range(self.quotient.pomdp.nr_states):
                    obs_index = self.quotient.pomdp.get_observation(pomdp_state)
                    if obs_index in processed_obs:
                        continue
                    processed_obs.append(obs_index)
                    choice = scheduler.get_choice(pomdp_state).get_choice().__str__()
                    choice = choice.replace('{','').replace('}','').replace('[','').replace(']','').replace(' ','').split(',')
                    for c in choice[:-1]:
                        prob, action = c.split(':')
                        action = int(action)
                        action_label = self.quotient.action_labels_at_observation[obs_index][action]
                        action_index = result_fsc.action_labels.index(action_label)
                        if result_fsc.action_function[node_id][obs_index] is None:
                            result_fsc.action_function[node_id][obs_index] = {action_index:float(prob)}
                        else:
                            result_fsc.action_function[node_id][obs_index][action_index] = float(prob)
            elif '__extra' in state.labels or 'target' in state.labels: # basically target states so just loop with everything
                for obs in range(self.quotient.observations):
                    first_action_in_obs = self.quotient.action_labels_at_observation[obs][0] # this ensures the looping action is available
                    result_fsc.action_function[node_id][obs] = {action_labels.index(first_action_in_obs):1.0}
                    result_fsc.update_function[node_id][obs] = {node_id: 1.0}
            else: # normal belief mc states
                successors = []
                for transition in belief_mc.transition_matrix.row_iter(state.id, state.id):
                    successors.append(transition.column)
                for succ in successors:
                    actions = list(belief_mc.choice_labeling.get_labels_of_choice(succ))
                    assert len(actions) == 1, "Belief MC has multiple labels for one action"
                    action = actions[0]
                    succ_observation = None
                    fsc_switch = None
                    cutoff_switch = None
                    for label in belief_mc.labeling.get_labels_of_state(succ):
                        if '[' in label:
                            # observation based on prism observables
                            succ_observation = self.quotient.observation_labels.index(label)
                        elif 'obs_' in label:
                            # explicit observation index
                            _,succ_observation = label.split('_')
                        elif 'finite_mem' in label:
                            fsc_switch = int(label.split('_')[-1])
                        if 'sched_' in label:
                            cutoff_switch = int(label.split('_')[1])
                        if succ_observation is not None:
                            succ_observation = int(succ_observation)
                    assert not((fsc_switch is not None) and (cutoff_switch is not None)), "Belief MC state has both FSC and Storm cutoff scheduler"
                    assert succ_observation is not None, "Belief MC state has no observation"
                    if fsc_switch is not None:
                        result_fsc.action_function[node_id][succ_observation] = result_fsc.action_function[first_fsc_node+fsc_switch][succ_observation]
                        result_fsc.update_function[node_id][succ_observation] = result_fsc.update_function[first_fsc_node+fsc_switch][succ_observation]
                    elif cutoff_switch is not None:
                        scheduler = storm_result.cutoff_schedulers[cutoff_switch]
                        cutoff_node_id = belief_mc_nodes_map[used_randomized_schedulers[cutoff_switch]]
                        for pomdp_state in range(self.quotient.pomdp.nr_states):
                            obs_index = self.quotient.pomdp.get_observation(pomdp_state)
                            if obs_index != succ_observation:
                                continue
                            choice = scheduler.get_choice(pomdp_state).get_choice().__str__()
                            choice = choice.replace('{','').replace('}','').replace('[','').replace(']','').replace(' ','').split(',')
                            for c in choice[:-1]:
                                prob, cutoff_action = c.split(':')
                                action_label = self.quotient.action_labels_at_observation[succ_observation][int(cutoff_action)]
                                action_index = result_fsc.action_labels.index(action_label)
                                if result_fsc.action_function[node_id][succ_observation] is None:
                                    result_fsc.action_function[node_id][succ_observation] = {action_index:float(prob)}
                                else:
                                    result_fsc.action_function[node_id][succ_observation][action_index] = float(prob)
                            break
                        result_fsc.update_function[node_id][succ_observation] = {cutoff_node_id: 1.0}
                    else:
                        if action == "loop":
                            first_action_in_obs = self.quotient.action_labels_at_observation[succ_observation][0] # this ensures the looping action is available
                            result_fsc.action_function[node_id][succ_observation] = {action_labels.index(first_action_in_obs): 1.0}
                        else:
                            result_fsc.action_function[node_id][succ_observation] = {result_fsc.action_labels.index(action): 1.0}
                        result_fsc.update_function[node_id][succ_observation] = {belief_mc_nodes_map[succ]: 1.0}

        logger.info(f"constructed FSC with {result_fsc.num_nodes} nodes")

        return result_fsc


    
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
