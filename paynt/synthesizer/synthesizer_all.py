import paynt.synthesizer.synthesizer
import paynt.synthesizer.synthesizer_ar

import logging
logger = logging.getLogger(__name__)

class SynthesizerAll(paynt.synthesizer.synthesizer_ar.SynthesizerAR):

    @property
    def method_name(self):
        return "AR (all)"

    def synthesize(self, family=None, find_all=False):
        self.stat.start()
        if family is None:
            family = self.quotient.design_space
        logger.info("synthesis initiated, design space: {}".format(family.size))
        satisfying_families,unsatisfying_families = self.synthesize_all(family)
        self.stat.finished(satisfying_families)
        return satisfying_families

    def synthesize_all(self, family=None):
        # assuming no optimality
        assert not self.quotient.specification.has_optimality
        self.quotient.discarded = 0
        satisfying_families = []
        unsatisfying_families = []
        families = [family]
        while families:
            family = families.pop()
            self.quotient.build(family)
            self.stat.iteration_mdp(family.mdp.states)
            res = family.mdp.check_specification(self.quotient.specification, constraint_indices = family.constraint_indices, short_evaluation = True)
            family.analysis_result = res
            if res.improving_assignment == "any":
                self.explore(family)
                satisfying_families.append(family)
                continue

            if res.can_improve == False:
                self.explore(family)
                unsatisfying_families.append(family)
                continue

            # undecided
            subfamilies = self.quotient.split(family, paynt.synthesizer.synthesizer.Synthesizer.incomplete_search)
            families = families + subfamilies

        return satisfying_families,unsatisfying_families


    def evaluate_all(self, family):
        pass
