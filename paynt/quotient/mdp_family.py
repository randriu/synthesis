import stormpy
import stormpy.synthesis

import paynt.quotient.holes
import paynt.quotient.quotient

import logging
logger = logging.getLogger(__name__)


class MdpFamilyQuotientContainer(paynt.quotient.quotient.QuotientContainer):

    def __init__(self, quotient_mdp, coloring, specification):
        super().__init__(quotient_mdp = quotient_mdp, coloring = coloring, specification = specification)
        self.design_space = paynt.quotient.holes.DesignSpace(coloring.holes)
        self.quotient_mdp = stormpy.synthesis.add_choice_labels_from_jani(self.quotient_mdp)
    
    def build_pomdp(self, family):
        raise NotImplementedError
        ''' Construct the sub-POMDP from the given hole assignment. '''
        assert family.size == 1, "expecting family of size 1"
        
        _,_,selected_actions_bv = self.coloring.select_actions(family)
        mdp,state_map,choice_map = self.restrict_quotient(selected_actions_bv)
        pomdp = self.obs_evaluator.build_sub_pomdp(mdp,state_map)
        return pomdp
