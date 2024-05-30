import paynt.synthesizer.synthesizer
import paynt.quotient.pomdp
import paynt.verification.property_result

import logging
logger = logging.getLogger(__name__)

class SynthesizerAR(paynt.synthesizer.synthesizer.Synthesizer):

    #------------xshevc01----------------  
    iterations = 0
    #------------------------------------

    @property
    def method_name(self):
        return "AR"
    
    def verify_family(self, family):
        self.quotient.build(family)
        self.stat.iteration_mdp(family.mdp.states, self.quotient.use_smart_inheritance)
        res = self.quotient.check_specification_for_mdp(family.mdp, family.constraint_indices)
        if res.improving_assignment == "any":
            res.improving_assignment = family
        family.analysis_result = res
    
    def update_optimum(self, family):
        ia = family.analysis_result.improving_assignment
        if family.analysis_result.improving_value is not None:
            self.quotient.specification.optimality.update_optimum(family.analysis_result.improving_value)
            # print values for constraints, TODO discuss some nice way of doing this naturally
            if False:
                print(ia)
                dtmc = self.quotient.build_assignment(ia)
                mc_result = self.quotient.check_specification_for_dtmc(dtmc)
                print(mc_result)
            if isinstance(self.quotient, paynt.quotient.pomdp.PomdpQuotient):
                self.stat.new_fsc_found(family.analysis_result.improving_value, ia, self.quotient.policy_size(ia))


    def synthesize_one(self, family):
        # return self.synthesize_one_experimental(family)

        satisfying_assignment = None
        families = [family]

        iteration_count = 0

        while families:
            #------------xshevc01----------------
            iteration_count += 1
            if self.iterations != 0 and iteration_count > self.iterations:
                 break
            
            if self.quotient.use_smart_inheritance and (self.iterations != 0 and iteration_count > self.iterations / 5.0 or iteration_count > 100 or self.stat.stop):
                    self.quotient.use_smart_inheritance = False
                    affected_states_average = self.quotient.perc_affected_sum/self.quotient.perc_affected_entries
                    choices_per_affected_state = self.quotient.choices_per_affected_sum/self.quotient.perc_affected_entries
                    if affected_states_average > 85 or choices_per_affected_state < 5.5:
                        print("SWITCHING TO AR DUE TO AFFECTED STATES")
                    else:
                        self.quotient.use_inheritance_extended = True
                        print("SWITCHING TO EIDAR")
            #------------------------------------

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
    
    def synthesize_one_experimental(self, family):

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
