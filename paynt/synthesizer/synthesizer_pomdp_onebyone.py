import paynt.synthesizer.synthesizer
import paynt.quotient.pomdp
import paynt.synthesizer.synthesizer_ar

class SynthesizerPomdpOneByOne(paynt.synthesizer.synthesizer.Synthesizer):

    @property
    def method_name(self):
        return "pomdp 1-by-1"

    def synthesize_one(self, family):
        sat = 0
        unsat = 0

        for pomdp_combinations in family.all_combinations():
            combination = list(pomdp_combinations)
            pomdp_singleton_suboptions = [[option] for option in combination]
            pomdp_singleton_family = family.assume_options_copy(pomdp_singleton_suboptions)
            pomdp = self.quotient.build_pomdp(pomdp_singleton_family)

            pomdp_quotient = paynt.quotient.pomdp.PomdpQuotient(pomdp.model, self.quotient.specification)
            print(f"synthesizing for family {pomdp_singleton_family}")
            synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR(pomdp_quotient)
            res = synthesizer.synthesize(print_stats = False)

            if res:
                sat += 1
            else:
                unsat += 1

        print(f"sat: {sat}")
        print(f"unsat: {unsat}")


