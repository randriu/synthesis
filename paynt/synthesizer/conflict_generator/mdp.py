import payntbind

import paynt.synthesizer.conflict_generator.dtmc
import paynt.verification.property

import logging
logger = logging.getLogger(__name__)


class ConflictGeneratorMdp(paynt.synthesizer.conflict_generator.dtmc.ConflictGeneratorDtmc):

    def initialize(self):
        state_to_holes_bv = self.quotient.coloring.getStateToHoles().copy()
        state_to_holes = []
        for state,holes_bv in enumerate(state_to_holes_bv):
            holes = set([hole for hole in holes_bv])
            state_to_holes.append(holes)
        formulae = self.quotient.specification.stormpy_formulae()
        self.counterexample_generator = payntbind.synthesis.CounterexampleGeneratorMdp(
            self.quotient.quotient_mdp, self.quotient.family.num_holes,
            state_to_holes, formulae
        )

    def prepare_model(self, model):
        self.counterexample_generator.prepare_mdp(model.model, model.quotient_state_map)
