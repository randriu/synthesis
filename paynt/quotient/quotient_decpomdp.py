import stormpy
import stormpy.synthesis
import stormpy.pomdp

from .models import MarkovChain,MDP,DTMC
from .holes import Hole,Holes,DesignSpace
from .quotient import QuotientContainer

import paynt

import logging
logger = logging.getLogger(__name__)


class DecPomdpQuotientContainer(QuotientContainer):

    def __init__(self, decpomdp_manager, specification):
        super().__init__(specification = specification)

        assert decpomdp_manager.num_agents > 1
        self.decpomdp_manager = decpomdp_manager

        logger.info(f"dec-POMDP has {self.decpomdp_manager.num_agents} agents")

        self.quotient = self.decpomdp_manager.construct_mdp()
        print("MDP has {} states".format(self.quotient.nr_states))
        print("transitions from state 1: ", self.quotient.transition_matrix.get_row(1))

        logger.debug("nothing to do, aborting...")
        exit()
        

        

