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

        self.action_labels,self.choice_to_action,self.state_to_actions = \
            MdpFamilyQuotientContainer.extract_choice_labels(self.quotient_mdp)

    
    @classmethod
    def extract_choice_labels(cls, mdp):
        '''
        :param mdp having a canonic choice labeling (exactly 1 label for each choice)
        :return a list of action labels
        :return for each row, its action
        :return for each state, a list of actions associated with the rows of this state
        '''
        assert mdp.has_choice_labeling, "MDP does not have a choice labeling"
        
        action_labels = list(mdp.choice_labeling.get_labels())
        label_to_action = {label:index for index,label in enumerate(action_labels)}
        
        choice_to_action = [None] * mdp.nr_choices
        state_to_actions = []
        tm = mdp.transition_matrix
        for state in range(mdp.nr_states):
            state_choice_label_indices = set()
            for choice in range(tm.get_row_group_start(state),tm.get_row_group_end(state)):
                label = list(mdp.choice_labeling.get_labels_of_choice(choice))[0]
                action = label_to_action[label]
                choice_to_action[choice] = action
                state_choice_label_indices.add(action)
            state_to_actions.append(list(state_choice_label_indices))

        return action_labels,choice_to_action,state_to_actions


    def build_chain(self, family):
        assert not self.quotient_game_required
        assert family.size == 1, "expecting family of size 1"
        _,_,selected_actions_bv = self.coloring.select_actions(family)
        mdp,state_map,choice_map = self.restrict_quotient(selected_actions_bv)
        return paynt.quotient.models.MDP(mdp,self,state_map,choice_map,family)

    
    def double_check_assignment(self, assignment):
        '''
        Double-check whether this assignment truly improves optimum.
        '''
        assert not self.quotient_game_required
        mdp = self.build_chain(assignment)
        res = mdp.check_specification(self.specification, double_check=False)
        if res.constraints_result.sat and self.specification.optimality.improves_optimum(res.optimality_result.primary.value):
            return assignment, res.optimality_result.primary.value
        else:
            return None, None

    def build_game_abstraction_solver(self, prop):
        target_label = str(prop.formula.subformula.subformula)
        solver = stormpy.synthesis.GameAbstractionSolver(
            self.quotient_mdp, len(self.action_labels), self.choice_to_action,
            self.state_to_actions, target_label
        )
        return solver
