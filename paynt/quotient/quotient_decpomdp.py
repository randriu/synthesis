import stormpy
import stormpy.synthesis
import stormpy.pomdp

from .models import MarkovChain,MDP,DTMC
from .holes import Hole,Holes,DesignSpace
from .quotient import QuotientContainer
from .quotient_pomdp import POMDPQuotientContainer

import logging
logger = logging.getLogger(__name__)


class DecPomdpQuotientContainer(QuotientContainer):

    def __init__(self, decpomdp):
        
        assert decpomdp is not None

        self.decpomdp = decpomdp
        print(f"dec-POMDP has {decpomdp.num_agents} agents and {decpomdp.num_states} states")
        print()

        print("transition matrix:")
        print(decpomdp.transition_matrix[2])
        print()

        print("reward vectors:")
        print(decpomdp.row_reward)
        print()

        if decpomdp.reward_minimizing:
            formula_str = 'R{"rew0"}min=? [F "target"]'
        else:
            formula_str = 'R{"rew0"}max=? [F "target"]'
        print("specification: ", formula_str)
        print()

        print("exiting...")

        exit()
        

        

