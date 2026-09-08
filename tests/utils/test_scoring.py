import pytest

import paynt.parser.sketch
import paynt.underlying_model.underlying_model
import paynt.utils.scoring
import paynt.synthesizer.search_node

from helpers.helper import get_sketch_paths


@pytest.fixture
def colored_mdp_parameter_space_prop_result():
    ''' A plain, non-specialized ColoredMdp -- see tests/underlying_model/test_model_index.py's fixture
    docstring for why this no longer goes through paynt.quotient.quotient.Quotient (deleted). '''
    sketch_path, props_path = get_sketch_paths("archive/jair24-synthesis/maze")
    colored_mdp_factory, task = paynt.parser.sketch.Sketch.load_sketch(sketch_path, props_path)
    colored_mdp = colored_mdp_factory.colored_mdp
    node = paynt.synthesizer.search_node.SearchNode(colored_mdp.parameter_space.copy())
    node.mdp, node.selected_choices = colored_mdp.build(node.parameter_space)
    prop = task.get_property()
    result = node.mdp.model_check_property(prop)
    return colored_mdp, node, prop, result


class TestSchedulerScoring:

    def test_estimate_scheduler_difference_returns_a_nonnegative_score_per_inconsistent_parameter(self, colored_mdp_parameter_space_prop_result):
        '''
        estimate_scheduler_difference is a thin wrapper around a native payntbind call, so (unlike
        choice_values) there's no independent formula worth re-deriving here in Python -- this checks the
        contract instead: one score per inconsistent parameter, each non-negative (it's a weighted value
        difference). Real numerical correctness is exercised end-to-end by every AR-based specialist's CLI
        regression check, which all route splitting decisions through this exact function.
        '''
        colored_mdp, node, prop, result = colored_mdp_parameter_space_prop_result
        selection = colored_mdp.scheduler_selection(node.mdp, result.result.scheduler)
        inconsistent_assignments = {parameter: options for parameter, options in enumerate(selection) if len(options) > 1}
        assert inconsistent_assignments, "expected at least one inconsistent parameter for this fixture"

        choice_values = paynt.underlying_model.underlying_model.ModelIndex.choice_values(node.mdp.model, prop, result.result.get_values())
        local_choices = result.result.scheduler.compute_action_support(node.mdp.model.nondeterministic_choice_indices)
        expected_visits = paynt.underlying_model.underlying_model.ModelIndex.compute_expected_visits(node.mdp.model, prop, local_choices)
        underlying_choice_map = list(range(node.mdp.model.nr_choices))

        scores = paynt.utils.scoring.estimate_scheduler_difference(
            colored_mdp, node.mdp.model, underlying_choice_map, inconsistent_assignments, choice_values, expected_visits)

        assert set(scores.keys()) == set(inconsistent_assignments.keys())
        assert all(score >= 0 for score in scores.values())

    def test_parameters_with_max_score(self):
        score = {0: 5, 1: 3, 2: 5}
        assert paynt.utils.scoring.parameters_with_max_score(score) == [0, 2]
