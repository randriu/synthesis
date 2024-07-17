import payntbind
import stormpy

import paynt.quotient.quotient
import paynt.quotient.pomdp

import paynt.verification.property

import logging
logger = logging.getLogger(__name__)


class PosmgQuotient(paynt.quotient.quotient.Quotient):

    def __init__(self, posmg, specification):
        #super().__init__(quotient_mdp = quotient_mdp, specification = specification)

        # defualt POSMG model
        self.posmg = posmg

        # unfolded POSMG
        self.quotient_mdp = None
        self.design_space = None
        self.coloring = None

        # number of actions available at each observation
        self.actions_at_observation = None
        # action labels corresponding to ^
        self.action_labels_at_observation = None

        # mdp = smg.get_mdp()
        # pomdp = smg.get_pomdp()

        # result = payntbind.synthesis.smg_model_checking(smg, specification[0].raw_formula,
                                                        # only_initial_states=False, set_produce_schedulers=True,
                                                        # env=paynt.verification.property.Property.environment)

        #vals = result.values[smg.initial_states[0]]
        # vals2 = result.get_values()[smg.initial_states[0]]


        exit()
