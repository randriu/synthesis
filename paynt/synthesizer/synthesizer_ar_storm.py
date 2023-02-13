from stormpy import pomdp
from .synthesizer import Synthesizer
from ..quotient.storm_pomdp_control import StormPOMDPControl

from time import sleep

import logging
logger = logging.getLogger(__name__)


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

    @property
    def method_name(self):
        return "AR"

    def storm_split(self, families):
        subfamilies = []
        main_families = []

        for family in families:
            if self.storm_control.use_cutoffs:
                main_p = self.storm_control.get_main_restricted_family_new(family, self.storm_control.result_dict)
            else:
                main_p = self.storm_control.get_main_restricted_family_new(family, self.storm_control.result_dict_no_cutoffs)

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
        if len(main_families) == 0:
            main_families = subfamilies
            subfamilies = []
        return main_families, subfamilies




    def analyze_family_ar(self, family):
        """
        :return (1) family feasibility (True/False/None)
        :return (2) new satisfying assignment (or None)
        """
        # logger.debug("analyzing family {}".format(family))

        self.quotient.build(family)
        self.stat.iteration_mdp(family.mdp.states)

        res = family.mdp.check_specification(self.quotient.specification, property_indices = family.property_indices, short_evaluation = True)
        #print(res.optimality_result.primary)
        family.analysis_result = res

        #print(res)
        improving_assignment,improving_value,can_improve = res.improving(family)
        #print(improving_assignment)
        #print(improving_value, can_improve)
        if improving_value is not None:
            self.quotient.specification.optimality.update_optimum(improving_value)
        # print(res, can_improve)
        # print(res.optimality_result.primary.result.get_values())

        #print(res.optimality_result.primary)
        #print(res.optimality_result.secondary)

        #if res.optimality_result.primary.value > 20:
        #    can_improve = False

        if self.quotient.specification.optimality.optimum and can_improve and self.storm_pruning:

            family_pomdp = self.quotient.get_family_pomdp(family.mdp)

            #print(family_pomdp)
            storm_res = StormPOMDPControl.storm_pomdp_analysis(family_pomdp, self.quotient.specification.stormpy_formulae())

            #print(storm_res.lower_bound)
            #print(storm_res.upper_bound)
            #print(storm_res.induced_mc_from_scheduler)
            #print(storm_res.cutoff_schedulers[0])

            if self.quotient.specification.optimality.minimizing:
                if self.quotient.specification.optimality.optimum <= storm_res.lower_bound:
                    can_improve = False
                    #print(self.quotient.specification.optimality.threshold)
                    logger.info(f"Used Storm result to prune a family with Storm value: {storm_res.lower_bound} compared to current optimum {self.quotient.specification.optimality.optimum}. Quotient MDP value: {res.optimality_result.primary.value}")
                #else:
                #    logger.info(f"Storm result: {storm_res.lower_bound}. Lower bounds: {storm_res.upper_bound}. Quotient MDP value: {res.optimality_result.primary.value}")
            else:
                if self.quotient.specification.optimality.optimum >= storm_res.upper_bound:
                    can_improve = False
                    #print(self.quotient.specification.optimality.threshold)
                    logger.info(f"Used Storm result to prune a family with Storm value: {storm_res.upper_bound} compared to current optimum {self.quotient.specification.optimality.optimum}. Quotient MDP value: {res.optimality_result.primary.value}")
                #else:
                #    logger.info(f"Storm result: {storm_res.upper_bound}. Lower bounds: {storm_res.lower_bound}. Quotient MDP value: {res.optimality_result.primary.value}")

        return can_improve, improving_assignment



    def synthesize_assignment(self, family):

        #try:
        self.quotient.discarded = 0

        satisfying_assignment = None
        families = [family]

        while families:

            if self.s_queue is not None:
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
                    while self.s_queue.empty():
                        sleep(1)
                    status = self.s_queue.get()
                    if status == "resume":
                        logger.info("Resuming synthesis")
                        if self.storm_control.is_storm_better:
                            if self.storm_control.is_memory_needed():
                                logger.info("Additional memory needed")
                                return satisfying_assignment
                            else:
                                logger.info("Applying family split according to Storm results")
                                families, self.subfamilies_buffer = self.storm_split(families)
                        else:
                            logger.info("PAYNT's value is better. Prioritizing synthesis results")
                        self.stat.synthesis_time.start()

                    elif status == "terminate":
                        logger.info("Terminating controller synthesis")
                        return satisfying_assignment

            #print(len(families))

            if SynthesizerARStorm.exploration_order_dfs:
                family = families.pop(-1)
            else:
                family = families.pop(0)

            #print(family)

            # simulate sequential
            family.parent_info = None

            can_improve,improving_assignment = self.analyze_family_ar(family)
            if improving_assignment is not None:
                satisfying_assignment = improving_assignment
                #print(satisfying_assignment)
            if can_improve == False:
                self.explore(family)
                if not families and self.subfamilies_buffer:
                    logger.info("Main family synthesis done")
                    logger.info(f"Subfamilies buffer contains: {len(self.subfamilies_buffer)} families")
                    families = self.subfamilies_buffer
                    self.subfamilies_buffer = []
                continue

            #print("split", family)
            # undecided
            subfamilies = self.quotient.split(family, Synthesizer.incomplete_search)
            families = families + subfamilies
        #except:
        #    if satisfying_assignment:
        #        extracted_result = self.quotient.extract_policy(satisfying_assignment)
        #        print(satisfying_assignment)
        #        print(extracted_result)
        #    exit()

        return satisfying_assignment

