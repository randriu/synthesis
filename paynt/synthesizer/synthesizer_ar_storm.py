from stormpy import pomdp
from .synthesizer import Synthesizer
from ..quotient.storm_pomdp_control import StormPOMDPControl

import logging
logger = logging.getLogger(__name__)


class SynthesizerARStorm(Synthesizer):

    # family exploration order: True = DFS, False = BFS
    exploration_order_dfs = True

    # buffer containing subfamilies to be checked after the main restricted family
    subfamilies_buffer = None

    subfamily_restrictions = None

    unresticted_family = None

    # list of explored restrictions
    explored_restrictions = []

    # if True, Storm over-approximation will be run to help with family pruning
    storm_pruning = False

    storm_control = None
    s_queue = None

    @property
    def method_name(self):
        return "AR"

    def create_subfamily(self, subfamily_restriction):

        subfamily = self.unresticted_family.copy()

        for hole_restriction in subfamily_restriction:

            selected_actions = hole_restriction["restriction"]

            if len(selected_actions) == 0:
                continue

            subfamily[hole_restriction["hole"]].assume_options(selected_actions)

        return subfamily

    def storm_split(self, families):
        #self.storm_control.parse_result(self.quotient)
        self.subfamily_restrictions = self.storm_control.get_subfamilies_restrictions(self.quotient)

        #print(self.subfamily_restrictions)
        
        subfamilies = []
        main_families = []

        # TODO MAIN FAMILIES
        for family in families:

            main_p = self.storm_control.get_main_restricted_family(family, self.quotient)
            main_families.append(main_p)

            subfamilies_p = self.storm_control.get_subfamilies(self.subfamily_restrictions, family)
            subfamilies.extend(subfamilies_p)

        logger.info(f"State after Storm splitting: Main families - {len(main_families)}, Subfamilies - {len(subfamilies)}")
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

        self.quotient.discarded = 0

        satisfying_assignment = None
        families = [family]

        while families:
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
            if can_improve == False:
                self.explore(family)
                continue

            #print("split", family)
            # undecided
            subfamilies = self.quotient.split(family, Synthesizer.incomplete_search)
            families = families + subfamilies

            if self.s_queue is not None:
                if not self.s_queue.empty():
                    self.storm_control.result_dict, self.storm_control.storm_bounds = self.s_queue.get()
                    logger.info("Applying family split according to Storm results")
                    families, self.subfamilies_buffer = self.storm_split(families)



        logger.info("Main family synthesis done")
        logger.info(f"Subfamilies buffer contains: {len(self.subfamilies_buffer)} families")
        #self.stat.print()

        while self.subfamilies_buffer:

            logger.info(f"{len(self.subfamilies_buffer)} families remaining")

            subfamily_restriction = self.subfamilies_buffer.pop(0)

            subfamily = self.create_subfamily(subfamily_restriction)

            #print(subfamily.size)

            families = [subfamily]

            #print(subfamily, len(families))

            while families:

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
                if can_improve == False:
                    self.explore(family)
                    continue

                #print("split", family)
                # undecided
                subfamilies = self.quotient.split(family, Synthesizer.incomplete_search)
                families = families + subfamilies

        self.stat.finished(satisfying_assignment)

        # if satisfying_assignment is not None:
        #     dtmc = self.sketch.quotient.build_chain(satisfying_assignment)
        #     spec = dtmc.check_specification(self.sketch.specification)
        #     logger.info("Double-checking specification satisfiability: {}".format(spec))
        return satisfying_assignment

