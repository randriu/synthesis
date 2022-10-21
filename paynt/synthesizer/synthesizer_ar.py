from .synthesizer import Synthesizer

import logging
logger = logging.getLogger(__name__)


class SynthesizerAR(Synthesizer):

    # family exploration order: True = DFS, False = BFS
    exploration_order_dfs = True

    @property
    def method_name(self):
        return "AR"

    def analyze_family_ar(self, family):
        """
        :return (1) family feasibility (True/False/None)
        :return (2) new satisfying assignment (or None)
        """
        # logger.debug("analyzing family {}".format(family))
        
        self.quotient.build(family)
        self.stat.iteration_mdp(family.mdp.states)

        res = family.mdp.check_specification(self.quotient.specification, property_indices = family.property_indices, short_evaluation = True)
        family.analysis_result = res
        # print(res)

        improving_assignment,improving_value,can_improve = res.improving(family)
        # print(improving_value, can_improve)
        if improving_value is not None:
            self.quotient.specification.optimality.update_optimum(improving_value)
        # print(res, can_improve)
        # print(res.optimality_result.primary.result.get_values())

        return can_improve, improving_assignment


    
    def synthesize_assignment(self, family):

        self.quotient.discarded = 0

        satisfying_assignment = None
        families = [family]

        while families:

            if SynthesizerAR.exploration_order_dfs:
                family = families.pop(-1)
            else:
                family = families.pop(0)

            # simulate sequential
            family.parent_info = None

            can_improve,improving_assignment = self.analyze_family_ar(family)
            if improving_assignment is not None:
                satisfying_assignment = improving_assignment
            if can_improve == False:
                self.explore(family)
                continue

            # undecided
            subfamilies = self.quotient.split(family, Synthesizer.incomplete_search)
            families = families + subfamilies

        return satisfying_assignment

