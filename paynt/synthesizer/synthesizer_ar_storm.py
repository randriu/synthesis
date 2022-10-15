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

    unresticted_family = None

    # list of explored restrictions
    explored_restrictions = []

    # if True, Storm over-approximation will be run to help with family pruning
    storm_pruning = False

    @property
    def method_name(self):
        return "AR"

    def create_subfamily(self, hole):

        subfamily = self.unresticted_family.copy()

        for exp_hole in self.explored_restrictions:

            if hole in exp_hole["holes"]:
                selected_actions = [action for action in subfamily[hole].options if action not in exp_hole["restriction"]]
            else:
                selected_actions = exp_hole["restriction"]

            if len(selected_actions) == 0:
                continue

            if hole in exp_hole["holes"]:
                subfamily[hole].assume_options(selected_actions)
            else:
                for h in exp_hole["holes"]:
                    subfamily[h].assume_options(selected_actions)

        return subfamily


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
            self.since_last_optimum_update = 0
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



    def synthesize(self, family):

        logger.info("Synthesis initiated. Storm AR.")

        self.stat.start()

        self.quotient.discarded = 0

        satisfying_assignment = None
        families = [family]

        while families:
            #print(len(families))

            if self.no_optimum_update_limit_reached():
                break

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

        logger.info("Main family synthesis done")
        logger.info(f"Subfamilies buffer contains: {len(self.subfamilies_buffer)} families")
        #self.stat.print()

        while self.subfamilies_buffer:

            logger.info(f"{len(self.subfamilies_buffer)} families remaining")

            subfamily_restriction = self.subfamilies_buffer.pop(0)

            self.explored_restrictions.append(subfamily_restriction)

            subfamily = self.create_subfamily(subfamily_restriction["holes"][0])

            families = [subfamily]

            #print(subfamily, len(families))

            while families:

                if self.no_optimum_update_limit_reached():
                    break

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

