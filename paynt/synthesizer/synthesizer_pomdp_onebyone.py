# Contributions of
# BACHELORS'S THESIS
# STRATEGY SYNTHESIS FOR PARTIALLY OBSERVABLE STOCHASTIC GAMES
# by Antonin Masopust
#
# This whole file was created by me. It contains the code for solving families of POMDPs with the one-by-one method.
# It is used in the experiments to compare it to the game-abstraction method.

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

        paynt.quotient.pomdp.PomdpQuotient.initial_memory_size = 1

        for pomdp_combinations in family.all_combinations():
            # create family
            combination = list(pomdp_combinations)
            pomdp_singleton_suboptions = [[option] for option in combination]
            pomdp_singleton_family = family.assume_options_copy(pomdp_singleton_suboptions)
            self.quotient.build(pomdp_singleton_family)

            # create pomdp
            mdp = pomdp_singleton_family.mdp

            quotient_state_to_observation = self.quotient.unfolded_state_to_observation
            state_to_observation = []
            for quotient_state in mdp.quotient_state_map:
                observation = quotient_state_to_observation[quotient_state]
                state_to_observation.append(observation)

            pomdp = self.quotient.pomdp_from_mdp(mdp.model, state_to_observation)

            # solve singleton
            pomdp_quotient = paynt.quotient.pomdp.PomdpQuotient(pomdp, self.quotient.specification)
            print(f"synthesizing for family {pomdp_singleton_family}")
            synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR(pomdp_quotient)
            res = synthesizer.synthesize(print_stats = False)

            if res:
                sat += 1
            else:
                unsat += 1

        print(f"sat: {sat}")
        print(f"unsat: {unsat}")


