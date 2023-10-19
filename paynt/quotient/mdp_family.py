import stormpy
import stormpy.synthesis

import paynt.quotient.holes
import paynt.quotient.models
import paynt.quotient.quotient
import paynt.verification.property_result

import logging
logger = logging.getLogger(__name__)


class MdpFamilyQuotientContainer(paynt.quotient.quotient.QuotientContainer):

    def __init__(self, quotient_mdp, coloring, specification):
        super().__init__(quotient_mdp = quotient_mdp, coloring = coloring, specification = specification)
        self.design_space = paynt.quotient.holes.DesignSpace(coloring.holes)
        self.quotient_mdp = stormpy.synthesis.add_choice_labels_from_jani(self.quotient_mdp)

        assert self.specification.has_double_optimality, "expecting double-optimality property"
        assert self.specification.optimality.dminimizing == self.specification.optimality.minimizing,\
            "alternating optimization is not supported"
    

    def build_chain(self, family):
        assert family.size == 1, "expecting family of size 1"
        _,_,selected_actions_bv = self.coloring.select_actions(family)
        mdp,state_map,choice_map = self.restrict_quotient(selected_actions_bv)
        return paynt.quotient.models.MDP(mdp,self,state_map,choice_map,family)

    def double_check_assignment(self, assignment):
        '''
        Double-check whether this assignment truly improves optimum.
        '''
        mdp = self.build_chain(assignment)
        res = mdp.check_specification(self.specification, double_check=False)
        if res.constraints_result.sat and self.specification.optimality.improves_optimum(res.optimality_result.primary.value):
            return assignment, res.optimality_result.primary.value
        else:
            return None, None