import paynt.utils.timer
import stormpy

import paynt.quotient.posmg
import paynt.synthesizer.synthesizer_ar

import logging
logger = logging.getLogger(__name__)

# TODO synthesis - gradually increase memory (replacing SynthesizerAR with SynthesizerPOSMG should be enough)
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
        logger.info('synthesis initiated')
        synthesis_timer = paynt.utils.timer.Timer()
        synthesis_timer.start()

        posmg = self.quotient.game_abstraction
        posmgSpecification = self.create_posmg_specification(self.quotient.specification.all_properties()[0])
        posmgQuotient = paynt.quotient.posmg.PosmgQuotient(posmg, posmgSpecification)
        posmgSynthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR(posmgQuotient)
        assignment = posmgSynthesizer.synthesize(print_stats=False)
        value = self.get_value(posmgQuotient, assignment)

        synthesis_timer.stop()
        time = synthesis_timer.time
        logger.info(f'synthesis completed, value: {round(value, 6)}, time: {round(time, 2)} s')
        # better summary?? use Statistic class? (specification, game iterations, ...)

        return value

    def run(self, optimum_threshold=None):
        return self.synthesize()