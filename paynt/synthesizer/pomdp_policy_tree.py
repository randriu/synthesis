
import paynt.quotient.pomdp
import paynt.synthesizer.policy_tree
import paynt.synthesizer.synthesizer_ar
import paynt.verification
import paynt.verification.property

class SynthesizerPomdpPolicyTree(paynt.synthesizer.policy_tree.SynthesizerPolicyTree):

    def solve_singleton(self, family, prop):
        mdp = family.mdp

        quotient_state_to_observation = self.quotient.state_to_observation
        state_to_observation = []
        for quotient_state in mdp.quotient_state_map:
            observation = quotient_state_to_observation[quotient_state]
            state_to_observation.append(observation)

        pomdp = self.quotient.pomdp_from_mdp(mdp.model, state_to_observation)

        specification = paynt.verification.property.Specification([prop])
        quotient = paynt.quotient.pomdp.PomdpQuotient(pomdp, specification)
        synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR(quotient)
        assignment = synthesizer.synthesize(print_stats=False)

        if assignment is None:
            return False
        else:
            policy = self.quotient.assignment_to_policy(mdp, quotient, assignment)

            return policy

    def log_game_stats(self, states, game_solver):
        self.stat.iteration_game(states)
        self.stat.add_smg_iterations(game_solver.game_iterations)
