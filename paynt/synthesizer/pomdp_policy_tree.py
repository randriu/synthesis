
import paynt.quotient.pomdp
import paynt.synthesizer.policy_tree
import paynt.synthesizer.synthesizer_ar
import paynt.verification
import paynt.verification.property

class SynthesizerPomdpPolicyTree(paynt.synthesizer.policy_tree.SynthesizerPolicyTree):

    def solve_singleton(self, family, prop):
        mdp = family.mdp
        pomdp = None # remember in family / create from mdp + observations
        specification = paynt.verification.property.Specification([prop])
        quotient = paynt.quotient.pomdp.PomdpQuotient(pomdp, specification)
        synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR(quotient)
        assignment = synthesizer.synthesize(print_stats=False)

        if assignment is None:
            return False
        else:
            policy = None # create policy from assignment

            return policy

