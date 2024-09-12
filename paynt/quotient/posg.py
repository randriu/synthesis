import payntbind
import stormpy

import paynt.quotient.quotient
import paynt.quotient.pomdp

import paynt.verification.property

import logging
logger = logging.getLogger(__name__)


class PosgQuotient(paynt.quotient.quotient.Quotient):

    # label associated with states of Player 1
    PLAYER_1_STATE_LABEL = "__player_1_state__"

    
    def __init__(self, quotient_mdp, specification):
        super().__init__(quotient_mdp = quotient_mdp, specification = specification)

        # TODO Antonin
        self.coloring = None
        self.family = None

        pomdp = self.quotient_mdp
        print(type(pomdp), dir(pomdp))
        print(dir(pomdp.labeling))
        # print(pomdp.labeling.get_states("__player_1_state__"))

        exit()
