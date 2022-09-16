import stormpy
import stormpy.synthesis
import stormpy.pomdp

from .models import MarkovChain,MDP,DTMC
from .holes import Hole,Holes,DesignSpace
from .quotient import QuotientContainer
from .quotient_pomdp import POMDPQuotientContainer
from .coloring import MdpColoring

import math
import re

import logging
logger = logging.getLogger(__name__)


class DecPomdpQuotientContainer(QuotientContainer):

    def __init__(self, decpomdp):
        
        self.decpomdp = decpomdp
        assert decpomdp is not None
        print(f"dec-POMDP has {decpomdp.num_agents} agents and {decpomdp.num_states} states")
        print("exiting...")
        exit()
        

        

