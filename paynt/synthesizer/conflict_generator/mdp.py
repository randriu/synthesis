import payntbind

import paynt.synthesizer.conflict_generator.dtmc
import paynt.specification.property

import logging
logger = logging.getLogger(__name__)


class ConflictGeneratorMdp(paynt.synthesizer.conflict_generator.dtmc.ConflictGeneratorDtmc):

    def initialize(self):
        state_to_parameters_bv = self.colored_mdp.coloring.getStateToHoles().copy()
        state_to_parameters = []
        for state,parameters_bv in enumerate(state_to_parameters_bv):
            parameters = set([parameter for parameter in parameters_bv])
            state_to_parameters.append(parameters)
        formulae = self.task.specification.stormpy_formulae()
        self.counterexample_generator = payntbind.synthesis.CounterexampleGeneratorMdp(
            self.colored_mdp.underlying_mdp, self.colored_mdp.parameter_space.num_parameters,
            state_to_parameters, formulae
        )

    def prepare_model(self, model):
        self.counterexample_generator.prepare_mdp(model.model, model.underlying_mdp_state_map)
