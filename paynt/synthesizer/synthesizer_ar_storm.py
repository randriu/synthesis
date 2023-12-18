from stormpy import pomdp
from .synthesizer import Synthesizer
from ..quotient.storm_pomdp_control import StormPOMDPControl
from os import makedirs

from time import sleep

import logging
logger = logging.getLogger(__name__)

# Abstraction Refinement + Storm splitting
class SynthesizerARStorm(Synthesizer):

    # family exploration order: True = DFS, False = BFS
    exploration_order_dfs = True

    # buffer containing subfamilies to be checked after the main restricted family
    subfamilies_buffer = None

    unresticted_family = None

    # if True, Storm over-approximation will be run to help with family pruning
    storm_pruning = False

    storm_control = None
    s_queue = None

    saynt_timer = None

    @property
    def method_name(self):
        return "AR"

    # performs splitting in family according to Storm result
    # main families contain only those actions that were considered by best found Storm FSC
    def storm_split(self, families):
        subfamilies = []
        main_families = []

        # split each family in the current buffer to main family and corresponding subfamilies
        for family in families:
            if self.storm_control.use_cutoffs:
                main_p = self.storm_control.get_main_restricted_family(family, self.storm_control.result_dict)
            else:
                main_p = self.storm_control.get_main_restricted_family(family, self.storm_control.result_dict_no_cutoffs)

            if main_p is None:
                subfamilies.append(family)
                continue

            main_families.append(main_p)

            if self.storm_control.use_cutoffs:
                subfamily_restrictions = self.storm_control.get_subfamilies_restrictions(family, self.storm_control.result_dict)
            else:
                subfamily_restrictions = self.storm_control.get_subfamilies_restrictions(family, self.storm_control.result_dict_no_cutoffs)

            subfamilies_p = self.storm_control.get_subfamilies(subfamily_restrictions, family)
            subfamilies.extend(subfamilies_p)

        logger.info(f"State after Storm splitting: Main families - {len(main_families)}, Subfamilies - {len(subfamilies)}")

        # if there are no main families we don't have to prioritize search
        if len(main_families) == 0:
            main_families = subfamilies
            subfamilies = []

        return main_families, subfamilies




    def verify_family(self, family):

        self.quotient.build(family)
        self.stat.iteration_mdp(family.mdp.states)
        res = family.mdp.check_specification(self.quotient.specification, constraint_indices = family.constraint_indices, short_evaluation = True)
        family.analysis_result = res

        if family.analysis_result.improving_value is not None:
            if self.saynt_timer is not None:
                print(f'-----------PAYNT----------- \
                    \nValue = {family.analysis_result.improving_value} | Time elapsed = {round(self.saynt_timer.read(),1)}s | FSC size = {self.quotient.policy_size(family.analysis_result.improving_assignment)}\n', flush=True)
                if self.storm_control.export_fsc_paynt is not None:
                    makedirs(self.storm_control.export_fsc_paynt, exist_ok=True)
                    with open(self.storm_control.export_fsc_paynt + "/paynt.fsc", "w") as text_file:
                        print(family.analysis_result.improving_assignment, file=text_file)
                        text_file.close()
            else:
                self.stat.new_fsc_found(family.analysis_result.improving_value, family.analysis_result.improving_assignment, self.quotient.policy_size(family.analysis_result.improving_assignment))
            self.quotient.specification.optimality.update_optimum(family.analysis_result.improving_value)

        # storm pruning runs Storm POMDP over-approximation analysis and on the sub-POMDP given by a family
        # this serves as a better abstraction for pruning, however is much more computationally intensive
        if self.quotient.specification.optimality.optimum and family.analysis_result.can_improve and self.storm_pruning:

            family_pomdp = self.quotient.get_family_pomdp(family.mdp)

            storm_res = StormPOMDPControl.storm_pomdp_analysis(family_pomdp, self.quotient.specification.stormpy_formulae())

            # compare computed bounds to the current optimum to see if the family can be pruned
            if self.quotient.specification.optimality.minimizing:
                if self.quotient.specification.optimality.optimum <= storm_res.lower_bound:
                    family.analysis_result.can_improve = False
                    logger.info(f"Used Storm result to prune a family with Storm value: {storm_res.lower_bound} compared to current optimum {self.quotient.specification.optimality.optimum}. Quotient MDP value: {res.optimality_result.primary.value}")
            else:
                if self.quotient.specification.optimality.optimum >= storm_res.upper_bound:
                    family.analysis_result.can_improve = False
                    logger.info(f"Used Storm result to prune a family with Storm value: {storm_res.upper_bound} compared to current optimum {self.quotient.specification.optimality.optimum}. Quotient MDP value: {res.optimality_result.primary.value}")



    def synthesize_one(self, family):

        self.quotient.discarded = 0

        satisfying_assignment = None
        families = [family]

        while families:

            # check whether PAYNT should be paused
            if self.s_queue is not None:
                # if the queue is non empty, pause for PAYNT was requested
                if not self.s_queue.empty():
                    if satisfying_assignment is not None:
                        self.storm_control.latest_paynt_result = satisfying_assignment
                        self.storm_control.paynt_export = self.quotient.extract_policy(satisfying_assignment)
                        self.storm_control.paynt_bounds = self.quotient.specification.optimality.optimum
                        self.storm_control.paynt_fsc_size = self.quotient.policy_size(self.storm_control.latest_paynt_result)
                        self.storm_control.update_data()
                    logger.info("Pausing synthesis")
                    self.s_queue.get()
                    self.stat.synthesis_time.stop()
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
                                return satisfying_assignment
                            else:
                                logger.info("Applying family split according to Storm results")
                                families, self.subfamilies_buffer = self.storm_split(families)
                        # if Storm's result is not better continue with the synthesis normally
                        else:
                            logger.info("PAYNT's value is better. Prioritizing synthesis results")
                        self.stat.synthesis_time.start()

                    elif status == "terminate":
                        logger.info("Terminating controller synthesis")
                        return satisfying_assignment

            if SynthesizerARStorm.exploration_order_dfs:
                family = families.pop(-1)
            else:
                family = families.pop(0)

            # simulate sequential
            family.parent_info = None

            self.verify_family(family)
            if family.analysis_result.improving_assignment is not None:
                satisfying_assignment = family.analysis_result.improving_assignment
            # family can be pruned
            if family.analysis_result.can_improve == False:
                self.explore(family)
                # if there are no more families in the main buffer coninue the exploration in the subfamilies
                if not families and self.subfamilies_buffer:
                    logger.info("Main family synthesis done")
                    logger.info(f"Subfamilies buffer contains: {len(self.subfamilies_buffer)} families")
                    families = self.subfamilies_buffer
                    self.subfamilies_buffer = []
                continue

            # undecided
            subfamilies = self.quotient.split(family, Synthesizer.incomplete_search)
            families = families + subfamilies

        return satisfying_assignment

