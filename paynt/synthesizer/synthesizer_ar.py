import paynt.synthesizer.synthesizer

import logging
logger = logging.getLogger(__name__)

class SynthesizerAR(paynt.synthesizer.synthesizer.Synthesizer):

    @property
    def method_name(self):
        return "AR"

    
    def verify_family(self, family):
        self.quotient.build(family)
        self.stat.iteration_mdp(family.mdp.states)
        res = family.mdp.check_specification(
            self.quotient.specification, constraint_indices = family.constraint_indices, short_evaluation = True)
        if res.improving_assignment == "any":
            res.improving_assignment = family
        family.analysis_result = res

    
    def update_optimum(self, family):
        ia = family.analysis_result.improving_assignment
        if family.analysis_result.improving_value is not None:
            self.quotient.specification.optimality.update_optimum(family.analysis_result.improving_value)
            if isinstance(self.quotient, paynt.quotient.quotient_pomdp.POMDPQuotientContainer):
                self.stat.new_fsc_found(family.analysis_result.improving_value, ia, self.quotient.policy_size(ia))


    def synthesize_assignment(self, family):
        # return self.synthesize_assignment_experimental(family)
        self.quotient.discarded = 0

        satisfying_assignment = None
        families = [family]

        while families:

            family = families.pop(-1)

            self.verify_family(family)
            self.update_optimum(family)
            if family.analysis_result.improving_assignment is not None:
                satisfying_assignment = family.analysis_result.improving_assignment
            if family.analysis_result.can_improve == False:
                self.explore(family)
                continue

            # undecided
            subfamilies = self.quotient.split(family, paynt.synthesizer.synthesizer.Synthesizer.incomplete_search)
            families = families + subfamilies

        return satisfying_assignment

    
    def family_value(self, family):
        ur = family.analysis_result.undecided_result()
        value = ur.primary.value
        # we pick family with maximum value
        if ur.minimizing:
            value *= -1
        return value
    
    def synthesize_assignment_experimental(self, family):

        self.quotient.discarded = 0

        satisfying_assignment = None
        families = [family]
        while families:

            # analyze all families, keep optimal solution
            for family in families:
                if family.analysis_result is not None:
                    continue
                self.verify_family(family)
                self.update_optimum(family)
                if family.analysis_result.improving_assignment is not None:
                    satisfying_assignment = family.analysis_result.improving_assignment
            
            # analyze families once more and keep undecided ones
            undecided_families = []
            for family in families:
                family.analysis_result.evaluate()
                if family.analysis_result.can_improve == False:
                    self.explore(family)
                else:
                    undecided_families.append(family)
            if not undecided_families:
                break
            
            # sort families
            undecided_families = sorted(undecided_families, key=lambda f: self.family_value(f), reverse=True)
            # print([self.family_value(f) for f in undecided_families])

            # split family with the best value
            family = undecided_families[0]
            subfamilies = self.quotient.split(family, paynt.synthesizer.synthesizer.Synthesizer.incomplete_search)
            families = subfamilies + undecided_families[1:]
                

        return satisfying_assignment

    
    def synthesize_all(self, family=None):
        self.stat.start()
        if family is None:
            family = self.quotient.design_space
        logger.info("synthesis initiated, design space: {}".format(family.size))
        assert not self.quotient.specification.has_optimality, "expecting specification with constraints only"
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

        self.stat.finished(satisfying_families)
        return satisfying_families,unsatisfying_families


    def evaluate_family(self, family, prop, precision):
        self.quotient.build(family)
        self.stat.iteration_mdp(family.mdp.states)

        # compute minimum first
        result_primary = family.mdp.model_check_property(prop, alt=prop.maximizing)
        if prop.reward and math.isinf(result_primary.value):
            return None,None
        result_secondary = family.mdp.model_check_property(prop, alt=True)
        print(result_primary.value)
        exit()
    
    def evaluate_all(self, family=None, precision=0):
        raise NotImplementedError("AR does not support evaluation of all family members")

        self.stat.start()
        if family is None:
            family = self.quotient.design_space
        logger.info("synthesis initiated, design space: {}".format(family.size))
        assert self.quotient.specification.has_optimality, "expecting specification without contstraints"
        self.quotient.discarded = 0

        prop = self.quotient.get_property()
        family_to_value = []

        families = [family]
        while families:
            family = families.pop()
            res = self.evaluate_family(family,prop,precision)
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

        self.stat.finished(family_to_value)
        return family_to_value
