import paynt.synthesizer.synthesizer_ar
from paynt.pomdp.saynt.control import StormPOMDPControl

from time import sleep

import logging
logger = logging.getLogger(__name__)

# Abstraction Refinement + Storm splitting
class SynthesizerARStorm(paynt.synthesizer.synthesizer_ar.SynthesizerAR):

    # parameter space exploration order: True = DFS, False = BFS
    exploration_order_dfs = True

    # buffer containing parameter subspaces to be checked after the main restricted parameter space
    parameter_subspaces_buffer = None

    main_parameter_space = None

    # if True, Storm over-approximation will be run to help with parameter-space pruning
    storm_pruning = False

    storm_control = None
    s_queue = None

    saynt_timer = None

    @property
    def method_name(self):
        return "AR"

    # performs splitting of the parameter space according to Storm result
    # main parameter spaces contain only those actions that were considered by best found Storm FSC
    def storm_split(self, parameter_spaces):
        parameter_subspaces = []
        main_parameter_spaces = []

        # split each parameter space in the current buffer into a main parameter space and corresponding subspaces
        for parameter_space in parameter_spaces:
            if self.storm_control.use_cutoffs:
                result_dict = self.storm_control.result_dict
            else:
                result_dict = self.storm_control.result_dict_no_cutoffs
            main_p = self.storm_control.get_main_restricted_parameter_space(parameter_space, result_dict)
            if main_p is None:
                parameter_subspaces.append(parameter_space)
                continue

            main_parameter_spaces.append(main_p)
            parameter_subspace_restrictions = self.storm_control.get_parameter_subspaces_restrictions(parameter_space, result_dict)
            parameter_subspaces_p = self.storm_control.get_parameter_subspaces(parameter_subspace_restrictions, parameter_space)
            parameter_subspaces.extend(parameter_subspaces_p)

        logger.info(f"State after Storm splitting: Main parameter spaces - {len(main_parameter_spaces)}, Parameter subspaces - {len(parameter_subspaces)}")

        # if there are no main parameter spaces we don't have to prioritize search
        if len(main_parameter_spaces) == 0:
            main_parameter_spaces = parameter_subspaces
            parameter_subspaces = []

        return main_parameter_spaces, parameter_subspaces




    def verify_parameter_space(self, parameter_space):
        self.colored_mdp.build(parameter_space)
        self.check_specification(parameter_space)

        if parameter_space.analysis_result.improving_value is not None:
            if self.saynt_timer is not None:
                print(f'-----------PAYNT----------- \
                    \nValue = {parameter_space.analysis_result.improving_value} | Time elapsed = {round(self.saynt_timer.read(),1)}s | FSC size = {self.colored_mdp.policy_size(parameter_space.analysis_result.improving_assignment)}\n', flush=True)
            else:
                self.stat.new_fsc_found(parameter_space.analysis_result.improving_value, parameter_space.analysis_result.improving_assignment, self.colored_mdp.policy_size(parameter_space.analysis_result.improving_assignment))
            self.task.specification.optimality.update_optimum(parameter_space.analysis_result.improving_value)

        # storm pruning runs Storm POMDP over-approximation analysis and on the sub-POMDP given by a parameter space
        # this serves as a better abstraction for pruning, however is much more computationally intensive
        if self.task.specification.optimality.optimum and parameter_space.analysis_result.can_improve and self.storm_pruning:

            parameter_space_pomdp = self.colored_mdp.get_parameter_space_pomdp(parameter_space.mdp)

            storm_res = StormPOMDPControl.storm_pomdp_analysis(parameter_space_pomdp, self.task.specification.stormpy_formulae())

            # compare computed bounds to the current optimum to see if the parameter space can be pruned
            if self.task.specification.optimality.minimizing:
                if self.task.specification.optimality.optimum <= storm_res.lower_bound:
                    parameter_space.analysis_result.can_improve = False
                    logger.info(f"Used Storm result to prune a parameter space with Storm value: {storm_res.lower_bound} compared to current optimum {self.task.specification.optimality.optimum}. Underlying MDP value: {res.optimality_result.primary.value}")
            else:
                if self.task.specification.optimality.optimum >= storm_res.upper_bound:
                    parameter_space.analysis_result.can_improve = False
                    logger.info(f"Used Storm result to prune a parameter space with Storm value: {storm_res.upper_bound} compared to current optimum {self.task.specification.optimality.optimum}. Underlying MDP value: {res.optimality_result.primary.value}")



    def synthesize_one(self, parameter_space):

        self.best_assignment = None

        if self.main_parameter_space is not None:
            parameter_space = self.main_parameter_space

        parameter_spaces = [parameter_space]

        while parameter_spaces:

            # check whether PAYNT should be paused
            if self.s_queue is not None:
                # if the queue is non empty, pause for PAYNT was requested
                if not self.s_queue.empty():
                    if self.best_assignment is not None:
                        self.storm_control.latest_paynt_result = self.best_assignment
                        self.storm_control.paynt_export = self.colored_mdp.extract_policy(self.best_assignment, self.task.specification)
                        self.storm_control.paynt_bounds = self.task.specification.optimality.optimum
                        self.storm_control.paynt_fsc_size = self.colored_mdp.policy_size(self.storm_control.latest_paynt_result)
                        self.storm_control.latest_paynt_result_fsc = self.colored_mdp.assignment_to_fsc(self.storm_control.latest_paynt_result)
                        self.storm_control.update_data()
                    logger.info("Pausing synthesis")
                    self.s_queue.get()
                    self.stat.synthesis_timer.stop()
                    # check for the signal that PAYNT can be resumed or terminated
                    while self.s_queue.empty():
                        sleep(1)
                    status = self.s_queue.get()
                    if status == "resume":
                        logger.info("Resuming synthesis")
                        if self.storm_control.is_storm_better:
                            # if the result found by Storm is better and needs more memory end the current synthesis and add memory
                            if self.storm_control.is_memory_needed():
                                logger.info("Additional memory needed")
                                return self.best_assignment
                            else:
                                logger.info("Applying parameter-space split according to Storm results")
                                parameter_spaces, self.parameter_subspaces_buffer = self.storm_split(parameter_spaces)
                        # if Storm's result is not better continue with the synthesis normally
                        else:
                            logger.info("PAYNT's value is better. Prioritizing synthesis results")
                        self.stat.synthesis_timer.start()

                    elif status == "terminate":
                        logger.info("Terminating controller synthesis")
                        return self.best_assignment

            if SynthesizerARStorm.exploration_order_dfs:
                parameter_space = parameter_spaces.pop(-1)
            else:
                parameter_space = parameter_spaces.pop(0)

            # simulate sequential
            parameter_space.parent_info = None

            self.verify_parameter_space(parameter_space)
            if parameter_space.analysis_result.improving_assignment is not None:
                self.best_assignment = parameter_space.analysis_result.improving_assignment
            # parameter space can be pruned
            if parameter_space.analysis_result.can_improve == False:
                self.explore(parameter_space)
                # if there are no more parameter spaces in the main buffer continue the exploration in the subspaces
                if not parameter_spaces and self.parameter_subspaces_buffer:
                    logger.info("Main parameter space synthesis done")
                    logger.info(f"Parameter subspaces buffer contains: {len(self.parameter_subspaces_buffer)} parameter spaces")
                    parameter_spaces = self.parameter_subspaces_buffer
                    self.parameter_subspaces_buffer = []
                continue

            # undecided
            parameter_subspaces = self.split_undecided_space(parameter_space)
            parameter_spaces = parameter_spaces + parameter_subspaces

        return self.best_assignment
