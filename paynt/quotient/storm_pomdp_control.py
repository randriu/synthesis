import stormpy
import stormpy.synthesis
import stormpy.pomdp

from ..quotient.models import MarkovChain


from threading import Thread
from time import sleep


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

    storm_terminated = False

    s_queue = None

    def __init__(self):
        pass

    def get_storm_result(self):
        self.run_storm_analysis()
        self.parse_results(self.quotient)
        self.update_data()

        #print(self.result_dict)
        #print(self.storm_bounds)

        if self.s_queue is not None:
            self.s_queue.put((self.result_dict, self.storm_bounds))

    # run Storm POMDP analysis for given model and specification
    # TODO: discuss Storm options
    def run_storm_analysis(self):
        if self.storm_options == "cutoff":
            options = self.get_cutoff_options(100000)
        elif self.storm_options == "clip2":
            options = self.get_clip2_options()
        elif self.storm_options == "clip4":
            options = self.get_clip4_options()
        elif self.storm_options == "small":
            options = self.get_cutoff_options(1000)
        elif self.storm_options == "refine":
            options = self.get_refine_options()
        elif self.storm_options == "overapp":
            options = self.get_overapp_options()
        else:
            logger.error("Incorrect option setting for Storm was found")
            exit()

        belmc = stormpy.pomdp.BeliefExplorationModelCheckerDouble(self.pomdp, options)

        #self.paynt_export = []
        #print(self.paynt_export)

        logger.info("starting Storm POMDP analysis")
        result = belmc.check(self.spec_formulas[0], self.paynt_export)   # calls Storm
        logger.info("Storm POMDP analysis completed")

        if self.get_result is not None:
            print(result.induced_mc_from_scheduler)
            print(result.lower_bound)
            print(result.upper_bound)
            exit()

        # debug
        print(result.induced_mc_from_scheduler)
        print(result.lower_bound)
        print(result.upper_bound)
        #print(result.cutoff_schedulers[1])
        #for sc in result.cutoff_schedulers:
        #    print(sc)

        self.latest_storm_result = result


    def interactive_storm_setup(self):
        global belmc
        #belmc = stormpy.pomdp.pomdp.create_interactive_mc(MarkovChain.environment, self.pomdp, False)
        options = self.get_interactive_options()
        belmc = stormpy.pomdp.BeliefExplorationModelCheckerDouble(self.pomdp, options)

    def interactive_storm_start(self, storm_timeout):
        self.storm_thread = Thread(target=self.interactive_run, args=(belmc,))
        control_thread = Thread(target=self.interactive_control, args=(belmc, True, storm_timeout,))

        logger.info("Interactive Storm started")
        control_thread.start()
        self.storm_thread.start()

        control_thread.join()

        self.belief_explorer = belmc.get_interactive_belief_explorer()


    def interactive_storm_resume(self, storm_timeout):
        control_thread = Thread(target=self.interactive_control, args=(belmc, False, storm_timeout,))

        logger.info("Interactive Storm resumed")
        control_thread.start()

        control_thread.join()

    def interactive_storm_terminate(self):
        belmc.terminate_unfolding()

    def interactive_run(self, belmc):
        logger.info("starting Storm POMDP analysis")
        result = belmc.check(self.spec_formulas[0], self.paynt_export)   # calls Storm

        self.storm_terminated = True

        if result.induced_mc_from_scheduler is not None:
            # debug
            print(result.induced_mc_from_scheduler)
            print(result.lower_bound)
            print(result.upper_bound)
            #print(result.cutoff_schedulers[1])
            #for sc in result.cutoff_schedulers:
            #    print(sc)

            self.latest_storm_result = result
            self.parse_results(self.quotient)
            self.update_data()

        logger.info("Storm POMDP analysis completed")

    def interactive_control(self, belmc, start, storm_timeout):
        if self.storm_terminated:
            logger.info("Storm already terminated.")
            return

        if belmc.get_status() == 4:
            logger.info("Storm terminated by exploring whole belief space.")
            return
        if not start:
            logger.info("Updating FSC values in Storm")
            #explorer = belmc.get_interactive_belief_explorer()
            self.belief_explorer.set_fsc_values(self.paynt_export)
            belmc.continue_unfolding()

        while not belmc.is_exploring():
            if belmc.get_status() == 4:
                logger.info("Storm terminated by exploring whole belief space.")
                return
            sleep(1)

        sleep(storm_timeout)
        if self.storm_terminated:
            return
        logger.info("Pausing Storm")
        belmc.pause_unfolding()

        while not belmc.is_result_ready():
            if belmc.get_status() == 4:
                logger.info("Storm terminated by exploring whole belief space.")
                return
            sleep(2)

        result = belmc.get_interactive_result()

        # debug
        #print(result.induced_mc_from_scheduler)
        print(result.lower_bound)
        print(result.upper_bound)
        #print(result.cutoff_schedulers[1])
        #for sc in result.cutoff_schedulers:
        #    print(sc)

        self.latest_storm_result = result
        self.parse_results(self.quotient)
        self.update_data()

        #print(self.result_dict)
        #print(self.result_dict_no_cutoffs)
        #print(self.is_storm_better)



    def get_cutoff_options(self, belief_states=100000):
        options = stormpy.pomdp.BeliefExplorationModelCheckerOptionsDouble(False, True)
        options.use_explicit_cutoff = True
        options.size_threshold_init = belief_states
        options.use_grid_clipping = False
        return options

    def get_overapp_options(self, belief_states=100000):
        options = stormpy.pomdp.BeliefExplorationModelCheckerOptionsDouble(True, False)
        options.use_explicit_cutoff = True
        options.size_threshold_init = belief_states
        options.use_grid_clipping = False
        return options

    def get_refine_options(self, step_limit=0):
        options = stormpy.pomdp.BeliefExplorationModelCheckerOptionsDouble(False, True)
        options.use_explicit_cutoff = True
        options.size_threshold_init = 0
        options.size_threshold_factor = 2
        options.use_grid_clipping = False
        options.gap_threshold_init = 0
        options.refine_precision = 0
        if step_limit > 0:
            options.refine_step_limit = step_limit
        options.refine = True
        return options

    def get_clip2_options(self):
        options = stormpy.pomdp.BeliefExplorationModelCheckerOptionsDouble(False, True)
        options.use_explicit_cutoff = True
        options.size_threshold_init = 0
        #options.size_threshold_factor = 2
        options.use_grid_clipping = True
        #options.exploration_time_limit = 1
        #options.clipping_threshold_init = 1
        options.clipping_grid_res = 2
        options.gap_threshold_init = 0
        #options.refine_precision = 0
        #options.refine = True
        #options.exploration_heuristic =
        #options.preproc_minmax_method = stormpy.MinMaxMethod.policy_iteration
        return options

    def get_clip4_options(self):
        options = stormpy.pomdp.BeliefExplorationModelCheckerOptionsDouble(False, True)
        options.use_explicit_cutoff = True
        options.size_threshold_init = 0
        #options.size_threshold_factor = 2
        options.use_grid_clipping = True
        #options.exploration_time_limit = 1
        #options.clipping_threshold_init = 1
        options.clipping_grid_res = 4
        options.gap_threshold_init = 0
        #options.refine_precision = 0
        #options.refine = True
        #options.exploration_heuristic =
        #options.preproc_minmax_method = stormpy.MinMaxMethod.policy_iteration
        return options

    def get_interactive_options(self):
        options = stormpy.pomdp.BeliefExplorationModelCheckerOptionsDouble(False, True)
        options.use_explicit_cutoff = True
        options.size_threshold_init = 0
        options.skip_heuristic_schedulers = False
        options.interactive_unfolding = True
        options.gap_threshold_init = 0
        options.refine = False
        options.cut_zero_gap = False
        if self.storm_options == "clip2":
            options.use_grid_clipping = True
            options.clipping_grid_res = 2
        elif self.storm_options == "clip4":
            options.use_grid_clipping = True
            options.clipping_grid_res = 4
        return options

    # Over-approximation
    @staticmethod
    def storm_pomdp_analysis(model, formulas):
        options = stormpy.pomdp.BeliefExplorationModelCheckerOptionsDouble(True, False)
        options.use_explicit_cutoff = True
        options.size_threshold_init = 1000000
        options.use_grid_clipping = False
        options.exploration_time_limit = 60
        belmc = stormpy.pomdp.BeliefExplorationModelCheckerDouble(model, options)

        #logger.info("starting Storm POMDP analysis")
        result = belmc.check(formulas[0], [])   # calls Storm
        #logger.info("Storm POMDP analysis completed")

        # debug
        #print(result.lower_bound)
        #print(result.upper_bound)

        return result

    # Probably not neccessary with the introduction of paynt result dict
    def parse_result(self, quotient):
        if self.is_storm_better and self.latest_storm_result is not None:
            self.parse_storm_result(quotient)
        else:
            if self.latest_paynt_result is not None:
                self.parse_paynt_result(quotient)
            else:
                self.result_dict = {}
                self.result_dict_paynt = {}
            self.result_dict_no_cutoffs = self.result_dict

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

    def join_results(self, use_cutoffs=True):
        if use_cutoffs:
            for obs in range(self.quotient.observations):
                if obs in self.result_dict.keys():
                    if obs in self.result_dict_paynt.keys():
                        for action in self.result_dict_paynt[obs]:
                            if action not in self.result_dict[obs]:
                                self.result_dict[obs].append(action)
                else:
                    if obs in self.result_dict_paynt.keys():
                        self.result_dict[obs] = self.result_dict_paynt[obs]

        

    # parse Storm results into a dictionary
    def parse_storm_result(self, quotient):
        # to make the code cleaner
        get_choice_label = self.latest_storm_result.induced_mc_from_scheduler.choice_labeling.get_labels_of_choice

        cutoff_epxloration = [x for x in range(len(self.latest_storm_result.cutoff_schedulers))]
        finite_mem = False

        result = {x:[] for x in range(quotient.observations)}
        result_no_cutoffs = {x:[] for x in range(quotient.observations)}
        
        for state in self.latest_storm_result.induced_mc_from_scheduler.states:
            # debug
            #print(state.id, state.labels, get_choice_label(state.id))

            # TODO what if there were no labels in the model?
            if get_choice_label(state.id) == set():
                continue

            # parse non cut-off states
            if 'cutoff' not in state.labels and 'clipping' not in state.labels:
                for label in state.labels:
                    if '[' in label:
                        simplified_label = self.quotient.simplify_label(label)
                        observation = self.quotient.observation_labels.index(simplified_label)

                        index = -1

                        for i in range(len(quotient.action_labels_at_observation[int(observation)])):
                            if list(get_choice_label(state.id))[0] in quotient.action_labels_at_observation[int(observation)][i]:
                                index = i
                                break

                        if index >= 0 and index not in result[int(observation)]:
                            result[int(observation)].append(index)

                        if index >= 0 and index not in result_no_cutoffs[int(observation)]:
                            result_no_cutoffs[int(observation)].append(index)
                    elif 'obs_' in label:
                        _, observation = label.split('_')

                        index = -1

                        for i in range(len(quotient.action_labels_at_observation[int(observation)])):
                            if list(get_choice_label(state.id))[0] in quotient.action_labels_at_observation[int(observation)][i]:
                                index = i
                                break

                        if index >= 0 and index not in result[int(observation)]:
                            result[int(observation)].append(index)

                        if index >= 0 and index not in result_no_cutoffs[int(observation)]:
                            result_no_cutoffs[int(observation)].append(index)
                        
            # parse cut-off states
            else:
                if 'finite_mem' in state.labels and not finite_mem:
                    finite_mem = True
                    self.parse_paynt_result(self.quotient)
                    for obs, actions in self.result_dict_paynt.items():
                        for action in actions:
                            if action not in result_no_cutoffs[obs]:
                                result_no_cutoffs[obs].append(action)
                            if action not in result[obs]:
                                result[obs].append(action)
                else:
                    if len(cutoff_epxloration) == 0:
                        continue
    
                    # debug
                    #print(cutoff_epxloration)
    
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

        if quotient.specification.optimality.minimizing:
            self.storm_bounds = self.latest_storm_result.upper_bound
        else:
            self.storm_bounds = self.latest_storm_result.lower_bound

        #logger.info("Result dictionary is based on result from Storm")
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

    def parse_paynt_result(self, quotient):

        result = {x:[] for x in range(quotient.observations)}
        
        for hole in self.latest_paynt_result:
            if hole.name.startswith('M'):
                continue
            name = hole.name.strip('A()')
            obs = name.split(',')[0]
            observation = self.quotient.observation_labels.index(obs)

            if hole.options[0] not in result[observation]:
                result[observation].append(hole.options[0])

        observations = list(result.keys())
        for obs in observations:
            if len(result[obs]) == 0:
                del result[obs]

        #logger.info("Result dictionary is based on result from PAYNT")
        self.result_dict_paynt = result


    # returns the main family that will be explored first
    def get_main_restricted_family(self, family, quotient, use_cutoffs=True):

        if not self.is_storm_better:
            result_dict = self.result_dict_paynt
        elif use_cutoffs:
            result_dict = self.result_dict
        else:
            result_dict = self.result_dict_no_cutoffs

        if result_dict == {}:
            return family

        # go through each observation of interest
        restricted_family = family.copy()
        for obs in range(quotient.observations):
      
            num_actions = quotient.actions_at_observation[obs]
            num_updates = quotient.pomdp_manager.max_successor_memory_size[obs]

            act_obs_holes = quotient.observation_action_holes[obs]
            mem_obs_holes = quotient.observation_memory_holes[obs]
            act_num_holes = len(act_obs_holes)
            mem_num_holes = len(mem_obs_holes)

            if act_num_holes == 0:
                continue

            all_actions = [action for action in range(num_actions)]
            selected_actions = [all_actions.copy() for _ in act_obs_holes]
            
            #all_updates = [update for update in range(num_updates)]
            #selected_updates = [all_updates.copy() for _ in mem_obs_holes]

            # Action restriction
            if obs not in result_dict.keys():
                selected_actions = [[0] for _ in act_obs_holes]
            else:
                selected_actions = [result_dict[obs] for _ in act_obs_holes]

            selected_updates = [[0] for hole in mem_obs_holes]

            # Apply action restrictions
            for index in range(act_num_holes):
                hole = act_obs_holes[index]
                actions = selected_actions[index]
                options = []
                for action in actions:
                    if action not in restricted_family[hole].options:
                        continue
                    options.append(action)
                if len(options) == 0:
                    options = [0]
                restricted_family[hole].assume_options(options)

            # Apply memory restrictions
            #for index in range(mem_num_holes):
            #    hole = mem_obs_holes[index]
            #    updates = selected_updates[index]
            #    options = []
            #    for update in updates:
            #        options.append(update)
            #    restricted_family[hole].assume_options(options)

        #print(restricted_family)
        logger.info("Main family based on data from Storm: reduced design space from {} to {}".format(family.size, restricted_family.size))

        return restricted_family

    def get_main_restricted_family_new(self, family, result_dict):

        if result_dict == {}:
            return family

        # go through each observation of interest
        restricted_family = family.copy()
        for obs in range(self.quotient.observations):
            for hole in self.quotient.observation_action_holes[obs]:

                if obs in result_dict.keys():
                    selected_actions = [action for action in family[hole].options if action in result_dict[obs]]
                else:
                    selected_actions = [family[hole].options[0]]

                if len(selected_actions) == 0:
                    return None

                restricted_family[hole].assume_options(selected_actions)

        #print(restricted_family)
        logger.info("Main family based on data from Storm: reduced design space from {} to {}".format(family.size, restricted_family.size))

        return restricted_family


    # returns dictionary containing restrictions for easy creation of subfamilies
    def get_subfamilies_restrictions(self, family, result_dict):

        if result_dict == {}:
            return {}

        subfamilies_restriction = []

        restricted_holes_list = []

        for observ in result_dict.keys():

            act_obs_holes = self.quotient.observation_action_holes[observ]
            restricted_holes_list.extend(act_obs_holes)
        
        #explored_hole_list = []

        # debug
        #subfamilies_size = 0

        for hole in restricted_holes_list:

            for obs_holes, index in zip(self.quotient.observation_action_holes, range(len(self.quotient.observation_action_holes))):
                if hole in obs_holes:
                    obs = index

            if len(result_dict[obs]) == self.quotient.actions_at_observation[obs]:
                continue

            restriction = [action for action in family[hole].options if action in result_dict[obs]]

            if len(restriction) == len(family[hole].options):
                continue

            subfamilies_restriction.append({"hole": hole, "restriction": restriction})

            # debug
            #print(obs, subfamily.size, subfamily)
            #subfamilies_size += subfamily.size

        # debug
        #print(subfamilies_size)

        return subfamilies_restriction



    # returns dictionary containing restrictions for easy creation of subfamilies
    # BROKEN NOW !!!!!!!!!!!!!!!!!
    # def get_subfamilies_restrictions_symmetry_breaking(self, quotient, use_cutoffs=True):

        # if use_cutoffs or not(self.is_storm_better):
            # result_dict = self.result_dict
        # else:
            # result_dict = self.result_dict_no_cutoffs

        # subfamilies = []

        # for obs in result_dict.keys():

            # if len(result_dict[obs]) == quotient.actions_at_observation[obs]:
                # continue

            # subfamilies.append({"holes": quotient.observation_action_holes[obs], "restriction": result_dict[obs]})

            # # debug
            # #print(obs, subfamily.size, subfamily)
            # #subfamilies_size += subfamily.size

        # # debug
        # #print(subfamilies_size)

        # return subfamilies


    def get_subfamilies_dict(self, restrictions, family):

        if len(restrictions) == 0:
            return []

        subfamilies = []

        for i in range(len(restrictions)):
            subfamily = []
            for j in range(i+1):
                if i != j:
                    subfamily.append(restrictions[j])
                else:
                    actions = [action for action in family[restrictions[j]["hole"]].options if action not in restrictions[j]["restriction"]]
                    subfamily.append({"hole": restrictions[j]["hole"], "restriction": actions})

            subfamilies.append(subfamily)

        for subfamily in subfamilies:
            holes = [x["hole"] for x in subfamily]

            for obs in range(self.quotient.observations):
                num_actions = self.quotient.actions_at_observation[obs]
                act_obs_holes = self.quotient.observation_action_holes[obs]
                for index in range(len(act_obs_holes)):
                    hole = act_obs_holes[index]
                    restriction = []
                    if hole not in holes:
                        for action in range(num_actions):
                            if action in family[hole].options:
                                restriction.append(action)
                    subfamily.append({"hole": hole, "restriction": restriction})

        return subfamilies

    def get_subfamilies(self, restrictions, family):

        subfamilies = []

        for i in range(len(restrictions)):
            restricted_family = family.copy()

            actions = [action for action in family[restrictions[i]["hole"]].options if action not in restrictions[i]["restriction"]]
            if len(actions) == 0:
                actions = [family[restrictions[i]["hole"]].options[0]]

            restricted_family[restrictions[i]['hole']].assume_options(actions)

            for j in range(i):
                restricted_family[restrictions[j]['hole']].assume_options(restrictions[j]["restriction"])

            subfamilies.append(restricted_family)

        return subfamilies

    def is_memory_needed(self):
        if len(self.memory_vector) == 0:
            return False

        memory_needed = False
        for obs in range(self.quotient.observations):
            if self.quotient.observation_memory_size[obs] < self.memory_vector[obs]:
                memory_needed = True
                break
        return memory_needed


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
                    


