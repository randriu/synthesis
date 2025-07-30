import paynt.synthesizer.statistic_ipomdp
import stormpy

import paynt.quotient.posmg
import paynt.synthesizer.synthesizer_ar

import logging
logger = logging.getLogger(__name__)

# TODO synthesis - gradually increase memory (replacing SynthesizerAR with SynthesizerPOSMG should be enough)
class SynthesizerIpomdp:
    @property
    def method_name(self):
        return "game abstraction"

    def __init__(self, quotient):
        self.quotient = quotient

    # currently, target states can be specified only using labels (this is ok, bc input format is only drn)
    # if there was a need to also support expresion target states, take inspiration from GameAbstractionSolver
    def create_posmg_specification(self, prop):
        formula_str = prop.formula.__str__()
        optimizing_player = 0 # hard coded. Has to correspond with state_player_indications
        game_formula_str = f"<<{optimizing_player}>> " + formula_str

        storm_property = stormpy.parse_properties(game_formula_str)[0]
        property = paynt.verification.property.construct_property(storm_property, 0)
        specification = paynt.verification.property.Specification([property])

        return specification

    def get_value(self, quotient, assignment):
        dtmc = quotient.build_assignment(assignment)
        result = dtmc.check_specification(quotient.specification)
        return result.optimality_result.value

    def synthesize(self, optimum_threshold=None):
        self.stat = paynt.synthesizer.statistic_ipomdp.StatisticIpompdp(self)
        self.stat.start()

        posmg = self.quotient.game_abstraction
        posmgSpecification = self.create_posmg_specification(self.quotient.specification.all_properties()[0])
        posmgQuotient = paynt.quotient.posmg.PosmgQuotient(posmg, posmgSpecification)
        posmgSynthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR(posmgQuotient)
        posmgSynthesizer.synthesize(print_stats=False, optimum_threshold=optimum_threshold, keep_optimum=True)
        value = posmgSynthesizer.best_assignment_value

        self.stat.finished_synthesis(value)
        self.stat.acc_size_game = posmgSynthesizer.stat.acc_size_game
        self.stat.iterations_game = posmgSynthesizer.stat.iterations_game
        self.stat.print()

        return value

    def run(self, optimum_threshold=None):
        return self.synthesize(optimum_threshold=optimum_threshold)