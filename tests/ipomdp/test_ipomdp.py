import pytest

import paynt.quotient.ipomdp
import payntbind

import stormpy

# entries is a list of tuples in format (row, column, value)
def matrices_are_same(tm, entries):
    entry_idx = 0
    for row_idx in range(tm.nr_rows):
        row = tm.get_row(row_idx)
        for entry in row:
            column = entry.column
            value = entry.value()
            e = entries[entry_idx]
            if not (row_idx == e[0] and column == e[1] and value == e[2]):
                print(f'row {row_idx} col {column} val {value}')
                return False
            entry_idx += 1

    return True


class TestIpomdp:

    def test_create_abstraction_simple1(self):
        # setup
        ipomdp = stormpy.build_interval_model_from_drn('models/ipomdp/simple1/sketch.templ')

        # test
        quotient = paynt.quotient.ipomdp.IpomdpQuotient(ipomdp, None)
        ga = quotient.game_abstraction

        # assert
        assert type(ga) == payntbind.synthesis.Posmg
        assert ga.nr_states == 4, f"Expected 4 states, but got {ga.nr_states}"
        assert ga.nr_choices == 6, f"Expected 6 choices, but got {ga.nr_choices}"
        assert ga.nr_transitions == 9, f"Expected 9 transitions, but got {ga.nr_transitions}"
        mat = [
            (0, 3, 1),
            (1, 1, 0.4), (1, 2, 0.6),
            (2, 1, 1),
            (3, 2, 1),
            (4, 1, 0.7), (4, 2, 0.3),
            (5, 1, 0.2), (5, 2, 0.8)
        ]
        assert matrices_are_same(ga.transition_matrix, mat)
        assert ga.labeling.get_labels_of_state(0) == {'init'}
        assert ga.labeling.get_labels_of_state(1) == {'target'}
        assert not ga.reward_models
        assert not ga.has_choice_labeling()
        assert ga.get_state_player_indications() == [0, 0, 0, 1]
        assert ga.get_observations() == [0, 1, 2, 3]


    def test_create_abstraction_simple2(self):
        # setup
        ipomdp = stormpy.build_interval_model_from_drn('models/ipomdp/simple2/sketch.templ')

        # test
        quotient = paynt.quotient.ipomdp.IpomdpQuotient(ipomdp, None)
        ga = quotient.game_abstraction

        # assert
        assert type(ga) == payntbind.synthesis.Posmg
        assert ga.nr_states == 13, f"Expected 13 states, but got {ga.nr_states}"
        assert ga.nr_choices == 21, f"Expected 21 choices, but got {ga.nr_choices}"
        assert ga.nr_transitions == 43, f"Expected 43 transitions, but got {ga.nr_transitions}"
        mat = [
            (0, 9, 1),
            (1, 10, 1),
            (2, 2, 1),
            (3, 11, 1),
            (4, 12, 1),
            (5, 4, 1),
            (6, 5, 1),
            (7, 6, 1),
            (8, 7, 1),
            (9, 8, 1),
            (10, 1, 0.4), (10, 2, 0.2), (10, 3, 0.3), (10, 4, 0.1),
            (11, 1, 0.1), (11, 2, 0.5), (11, 3, 0.3), (11, 4, 0.1),
            (12, 1, 0.1), (12, 2, 0.2), (12, 3, 0.6), (12, 4, 0.1),
            (13, 1, 0.1), (13, 2, 0.2), (13, 3, 0.3), (13, 4, 0.4),
            (14, 5, 0.6), (14, 6, 0.2), (14, 7, 0.2),
            (15, 5, 0.2), (15, 6, 0.6), (15, 7, 0.2),
            (16, 5, 0.2), (16, 6, 0.2), (16, 7, 0.6),
            (17, 3, 0.6), (17, 8, 0.4),
            (18, 3, 0.3), (18, 8, 0.7),
            (19, 3, 0.5), (19, 8, 0.5),
            (20, 3, 0.2), (20, 8, 0.8),
        ]
        assert matrices_are_same(ga.transition_matrix, mat)
        assert ga.labeling.get_labels_of_state(0) == {'init'}
        assert ga.labeling.get_labels_of_state(4) == {'goal'}
        assert ga.labeling.get_labels_of_state(7) == {'goal'}
        assert not ga.reward_models
        assert not ga.has_choice_labeling()
        assert ga.get_state_player_indications() == [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1]
        assert ga.get_observations() == [0, 0, 1, 2, 1, 1, 1, 1, 1, 3, 3, 3, 3]

    def test_create_abstraction_rewards(self):
        pass
        # todo

    def test_wrong_interval_definition(self):
        ipomdp = stormpy.build_interval_model_from_drn('models/ipomdp/wrong_intervals/sketch.templ')

        with pytest.raises(AssertionError):
            quotient = paynt.quotient.ipomdp.IpomdpQuotient(ipomdp, None)