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
        if self.quotient_game_required:
            self.build_quotient_game(self.quotient_mdp, self.specification)

    @property
    def quotient_game_required(self):
        return self.specification.optimality.dminimizing != self.specification.optimality.minimizing

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

    
    @classmethod
    def extract_choice_labels(cls, mdp):
        '''
        Make sure that for each state of the MDP, either all its rows have no labels or all its rows have exactly one
        (non necessarily unique) label.
        Map each row to the index of its label, or -1 if no label.
        :return a list of choice labels
        :return for each row, the index of its label, or -1 if the row is not labeled
        :return for each state, a list of label indices associated with the rows of this state
        '''
        assert mdp.has_choice_labeling, "MDP does not have a choice labeling"
        cl = mdp.choice_labeling
        tm = mdp.transition_matrix
        
        choice_labels = list(cl.get_labels())
        choice_label_index = [None] * mdp.nr_choices
        state_to_choice_label_indices = []

        label_to_index = {label:index for index,label in enumerate(choice_labels)}
        for state in range(mdp.nr_states):
            state_rows_have_no_labels = None
            state_choice_label_indices = set()
            for row in range(tm.get_row_group_start(state),tm.get_row_group_end(state)):
                row_labels = cl.get_labels_of_choice(row)
                if state_rows_have_no_labels is None:
                    state_rows_have_no_labels = len(row_labels)==0
                if state_rows_have_no_labels:
                    assert len(row_labels) == 0, "expected unlabeled row"
                    row_label_index = -1
                else:
                    assert len(row_labels) == 1, "expected row with exactly one label"
                    row_label_index = label_to_index[list(row_labels)[0]]
                choice_label_index[row] = row_label_index
                state_choice_label_indices.add(row_label_index)
            state_to_choice_label_indices.append(list(state_choice_label_indices))

        return choice_labels,choice_label_index,state_to_choice_label_indices


    def build_quotient_game(self, mdp, specification):
        # assuming a single probability objective
        assert specification.num_properties == 1 and not specification.optimality.reward,\
            "expecting a single reachability probability optimization"
        mdp = self.quotient_mdp

        # identify target states
        state_is_target = [False] * mdp.nr_states
        target_label = str(specification.optimality.formula.subformula.subformula)
        for state in range(mdp.nr_states):
            if target_label in mdp.labeling.get_labels_of_state(state):
                state_is_target[state] = True

        self.choice_labels,self.choice_label_index,self.state_to_choice_label_indices = \
            MdpFamilyQuotientContainer.extract_choice_labels(self.quotient_mdp)

        # build the quotient game
        # player1 chooses the action, player2 chooses the action color
        # player1 states are states of the original MDP
        # player2 states are pairs (state,action)
        tm = self.quotient_mdp.transition_matrix
        player2_matrix_builder = stormpy.storage.SparseMatrixBuilder(0,0,0,False,True)
        player2_num_rows = 0
        player2_state_pairs = []
        player2_row_rewards = []
        for state in range(mdp.nr_states):
            for label_index in self.state_to_choice_label_indices[state]:
                # add this action selection for player 1
                player2_state = len(player2_state_pairs)
                player2_state_pairs.append((state,label_index))
                
                # add all variants of this action to player 2
                player2_matrix_builder.new_row_group(player2_num_rows)
                if state_is_target[state]:
                    # target state, add empty row with unit reward
                    player2_row_rewards.append(1)
                    player2_num_rows += 1
                    continue
                for row in range(tm.get_row_group_start(state),tm.get_row_group_end(state)):
                    if self.choice_label_index[row] != label_index:
                        continue
                    for entry in tm.get_row(row):
                        player2_matrix_builder.add_next_value(player2_num_rows,entry.column,entry.value())
                    player2_row_rewards.append(0)
                    player2_num_rows += 1
        player2_matrix = player2_matrix_builder.build()
        
        solver = stormpy.synthesis.StochasticGameSolver()
        solver.solve(self.state_to_choice_label_indices, player2_matrix, player2_row_rewards, specification.optimality.minimizing, specification.optimality.dminimizing)

        print(solver.player1_state_values)
        print(solver.player1_choices)
        print(solver.player2_choices)

        exit()