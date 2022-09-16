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
        print("dec-POMDP has ? agents and ? states")
        exit()
        

        

