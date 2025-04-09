import stormpy

import paynt.quotient.posmg
import paynt.synthesizer.synthesizer_ar

class SynthesizerIpomdp:
    def __init__(self, quotient):
        self.quotient = quotient

    # currently, target states can be specified only using labels (this is ok, bc input format is only drn)
    # if there was a need to also support expresion target states, take inspiration from GameAbstractionSolver
    def create_posmg_specification(self, prop):
        formula_str = prop.formula.__str__()
        optimizing_player = 0 # hard coded. Has to correspond with state_player_indications
        game_fromula_str = f"<<{optimizing_player}>> " + formula_str

        storm_property = stormpy.parse_properties(game_fromula_str)[0]
        property = paynt.verification.property.construct_property(storm_property, 0)
        specification = paynt.verification.property.Specification([property])

        return specification

    def get_value(self, quotient, assignment):
        dtmc = quotient.build_assignment(assignment)
        result = dtmc.check_specification(quotient.specification)
        return result.optimality_result.value

    def synthesize(self):
        posmg = self.quotient.game_abstraction
        posmgSpecification = self.create_posmg_specification(self.quotient.specification.all_properties()[0])
        posmgQuotient = paynt.quotient.posmg.PosmgQuotient(posmg, posmgSpecification)
        posmgSynthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR(posmgQuotient)
        assignment = posmgSynthesizer.synthesize(print_stats=False)

        return self.get_value(posmgQuotient, assignment)

    def run(self, optimum_threshold=None):
        return self.synthesize()