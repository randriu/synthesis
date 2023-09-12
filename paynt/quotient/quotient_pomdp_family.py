import stormpy
import stormpy.synthesis

import paynt.quotient.quotient

from .holes import Hole,Holes,DesignSpace
# from .models import MarkovChain,MDP,DTMC
# from .quotient import QuotientContainer


import logging
logger = logging.getLogger(__name__)


class PomdpFamilyQuotientContainer(paynt.quotient.quotient.QuotientContainer):

    def __init__(self, quotient_mdp, coloring, specification, obs_evaluator):

        super().__init__(quotient_mdp = quotient_mdp, coloring = coloring, specification = specification)
        self.obs_evaluator = obs_evaluator
        self.design_space = DesignSpace(coloring.holes)
