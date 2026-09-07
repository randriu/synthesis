'''
Outer SAYNT driver: runs PomdpSynthesizer's AR-based search interleaved with Storm belief-exploration
analysis (via StormPOMDPControl), each side informing the other's next iteration. Absorbs the
iterative_storm_loop/strategy_storm control flow that used to live directly on SynthesizerPomdp.
'''

from paynt.pomdp.synthesizer import PomdpSynthesizer
import paynt.pomdp.saynt.synthesizer_ar_storm
import paynt.utils.timer

from threading import Thread
from queue import Queue
import time

import logging
logger = logging.getLogger(__name__)


class SayntSynthesizer(PomdpSynthesizer):

    def __init__(self, colored_mdp_factory, method, storm_control):
        super().__init__(colored_mdp_factory, method)
        self.storm_control = storm_control
        self.storm_control.colored_mdp = self.colored_mdp
        self.storm_control.pomdp = self.colored_mdp.pomdp
        self.storm_control.specification = self.task.specification
        self.storm_control.spec_formulas = self.task.specification.stormpy_formulae()
        self.synthesis_terminate = False
        self.synthesizer = paynt.pomdp.saynt.synthesizer_ar_storm.SynthesizerARStorm # SAYNT only works with abstraction refinement
        if self.storm_control.iteration_timeout is not None:
            self.saynt_timer = paynt.utils.timer.Timer()
            self.synthesizer.saynt_timer = self.saynt_timer
            self.storm_control.saynt_timer = self.saynt_timer

    def unfold_and_synthesize(self, mem_size, unfold_storm, unfold_imperfect_only=True):
        # unfold memory according to the best result
        if not unfold_storm:
            logger.info("Synthesizing optimal k={} controller ...".format(mem_size) )
            if unfold_imperfect_only:
                self.colored_mdp = self.colored_mdp_factory.set_imperfect_memory_size(mem_size)
            else:
                self.colored_mdp = self.colored_mdp_factory.set_global_memory_size(mem_size)
        else:
            if mem_size > 1:
                obs_memory_dict = {}
                if self.storm_control.is_storm_better:
                    # Storm's result is better and it needs memory
                    if self.storm_control.is_memory_needed():
                        obs_memory_dict = self.storm_control.memory_vector
                        logger.info(f'Added memory nodes to match Storm data')
                    else:
                        if self.storm_control.unfold_cutoff:
                            # consider the cut-off schedulers actions when updating memory
                            result_dict = self.storm_control.result_dict
                        else:
                            # only consider the induced DTMC without cut-off states
                            result_dict = self.storm_control.result_dict_no_cutoffs
                        for obs in range(self.colored_mdp.observations):
                            if obs in result_dict:
                                obs_memory_dict[obs] = self.colored_mdp.observation_memory_size[obs] + 1
                            else:
                                obs_memory_dict[obs] = self.colored_mdp.observation_memory_size[obs]
                        logger.info(f'Added memory nodes for observations based on Storm data')
                else:
                    for obs in range(self.colored_mdp.observations):
                        if self.colored_mdp.observation_states[obs]>1:
                            obs_memory_dict[obs] = self.colored_mdp.observation_memory_size[obs] + 1
                        else:
                            obs_memory_dict[obs] = 1
                    logger.info(f'Increased memory in all imperfect observation')
                self.colored_mdp = self.colored_mdp_factory.set_memory_from_dict(obs_memory_dict)

        parameter_space = self.colored_mdp.parameter_space

        # if Storm's result is better, use it to obtain a main parameter space that considers only the important actions
        if self.storm_control.is_storm_better:
            if self.storm_control.use_cutoffs:
                # consider the cut-off schedulers actions
                result_dict = self.storm_control.result_dict
            else:
                # only consider the induced DTMC actions without cut-off states
                result_dict =self.storm_control.result_dict_no_cutoffs
            main_parameter_space = self.storm_control.get_main_restricted_parameter_space(parameter_space,result_dict)
            parameter_subspace_restrictions = []
            if not self.storm_control.incomplete_exploration:
                parameter_subspace_restrictions = self.storm_control.get_parameter_subspaces_restrictions(parameter_space, result_dict)
            parameter_subspaces = self.storm_control.get_parameter_subspaces(parameter_subspace_restrictions, parameter_space)
        # if PAYNT is better continue normally
        else:
            main_parameter_space = parameter_space
            parameter_subspaces = []

        self.synthesizer.parameter_subspaces_buffer = parameter_subspaces
        self.synthesizer.main_parameter_space = main_parameter_space

        assignment = self.synthesize(parameter_space)
        return assignment

    # iterative strategy using Storm analysis to enhance the synthesis
    def strategy_iterative_storm(self, unfold_imperfect_only, unfold_storm=True):
        '''
        @param unfold_imperfect_only if True, only imperfect observations will be unfolded
        '''
        mem_size = self.colored_mdp_factory.task.memory_size
        self.synthesizer.storm_control = self.storm_control

        while True:
            assignment = self.unfold_and_synthesize(mem_size,unfold_storm)
            if assignment is not None:
                self.storm_control.latest_paynt_result = assignment
                self.storm_control.paynt_export = self.colored_mdp.extract_policy(assignment, self.task.specification)
                self.storm_control.paynt_bounds = self.task.specification.optimality.optimum
                self.storm_control.paynt_fsc_size = self.colored_mdp.policy_size(self.storm_control.latest_paynt_result)
                self.storm_control.latest_paynt_result_fsc = self.colored_mdp.assignment_to_fsc(self.storm_control.latest_paynt_result)
            self.storm_control.update_data()

            if self.synthesis_terminate:
                break

            mem_size += 1

    def print_synthesized_controllers(self):
        hline = "\n------------------------------------\n"
        print(hline)
        print("PAYNT results: ")
        print(self.storm_control.paynt_bounds)
        print("controller size: {}".format(self.storm_control.paynt_fsc_size))
        print()
        print("Storm results: ")
        print(self.storm_control.storm_bounds)
        print("controller size: {}".format(self.storm_control.belief_controller_size))
        print(hline)

    def iterative_storm_loop(self, timeout, paynt_timeout, storm_timeout, iteration_limit=0):
        ''' Main SAYNT loop. '''
        self.interactive_queue = Queue()
        self.synthesizer.s_queue = self.interactive_queue
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
            assert self.storm_control.latest_storm_result is not None
            self.storm_control.belief_controller_size = self.storm_control.get_belief_controller_size(self.storm_control.latest_storm_result, self.storm_control.paynt_fsc_size)

            self.print_synthesized_controllers()

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
        mem_size = self.colored_mdp_factory.task.memory_size
        self.synthesizer.storm_control = self.storm_control

        while True:
            if self.storm_control.is_storm_better == False:
                self.storm_control.parse_results(self.colored_mdp)
            assignment = self.unfold_and_synthesize(mem_size,unfold_storm)
            if assignment is not None:
                self.storm_control.latest_paynt_result = assignment
                self.storm_control.paynt_export = self.colored_mdp.extract_policy(assignment, self.task.specification)
                self.storm_control.paynt_bounds = self.task.specification.optimality.optimum

            self.storm_control.update_data()
            mem_size += 1

    def export_fsc(self, export_filename_base):
        fsc_json = None
        if self.storm_control.saynt_fsc is not None:
            fsc_json = self.storm_control.saynt_fsc.__str__()
        elif self.storm_control.latest_paynt_result_fsc is not None:
            fsc_json = self.storm_control.latest_paynt_result_fsc.__str__()
        else:
            # TODO add export option for pure PAYNT synthesis
            pass

        assert fsc_json is not None, "No FSC to export"

        with open(export_filename_base + ".fsc.json", "w") as f:
            f.write(fsc_json)

        logger.info(f"Exported FSC to {export_filename_base}.fsc.json")

    def run(self, optimum_threshold=None):
        logger.info("Storm POMDP option enabled")
        logger.info("Storm settings: iterative - {}, get_storm_result - {}, storm_options - {}, prune_storm - {}, unfold_strategy - {}, use_storm_cutoffs - {}".format(
                    (self.storm_control.iteration_timeout, self.storm_control.paynt_timeout, self.storm_control.storm_timeout), self.storm_control.get_result,
                    self.storm_control.storm_options, self.storm_control.incomplete_exploration, (self.storm_control.unfold_storm, self.storm_control.unfold_cutoff), self.storm_control.use_cutoffs
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
            self.strategy_storm(unfold_imperfect_only=True, unfold_storm=self.storm_control.unfold_storm)

        self.print_synthesized_controllers()

        if self.task.export_synthesis_filename_base is not None:
            self.export_fsc(self.task.export_synthesis_filename_base)
