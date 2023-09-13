import stormpy
import stormpy.synthesis

import paynt.quotient.quotient

from .holes import Hole,Holes,DesignSpace

import logging
logger = logging.getLogger(__name__)


class PomdpFamilyQuotientContainer(paynt.quotient.quotient.QuotientContainer):

    def __init__(self, quotient_mdp, coloring, specification, obs_evaluator):
        super().__init__(quotient_mdp = quotient_mdp, coloring = coloring, specification = specification)
        self.obs_evaluator = obs_evaluator
        self.design_space = DesignSpace(coloring.holes)

    
    def build_pomdp(self, family):
        ''' Construct the sub-POMDP from the given hole assignment. '''
        assert family.size == 1, "expecting family of size 1"
        
        _,_,selected_actions_bv = self.coloring.select_actions(family)
        mdp,state_map,choice_map = self.restrict_quotient(selected_actions_bv)
        pomdp = self.obs_evaluator.build_sub_pomdp(mdp,state_map)
        return pomdp

