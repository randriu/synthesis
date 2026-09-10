import pytest

import paynt.parser.sketch

from helpers.helper import get_sketch_paths


@pytest.fixture
def colored_mdp():
    sketch_path, props_path = get_sketch_paths("archive/jair24-synthesis/maze")
    colored_mdp_factory, task = paynt.parser.sketch.Sketch.load_sketch(sketch_path, props_path)
    return colored_mdp_factory.colored_mdp


class TestColoredMdp:

    def test_representation_only_surface(self, colored_mdp):
        """
        ColoredMdp is a realization of colored MDP = (M, V, kappa) (Definition 2, arXiv:2511.08078): it must
        not carry algorithm/scoring helpers that don't touch the coloring or the parameter space. Those live
        in paynt.underlying_model.underlying_model.ModelIndex (generic scheduler/choice-index plumbing and
        model-checking-result facts) or paynt.utils.scoring (the one coloring-aware splitting heuristic) instead.
        """
        removed = [
            "empty_scheduler",
            "discard_unreachable_choices",
            "scheduler_to_state_to_choice",
            "state_to_choice_to_choices",
            "choice_values",
            "compute_expected_visits",
            "make_vector_defined",
            "holes_with_max_score",
            "parameters_with_max_score",
            "estimate_scheduler_difference",
            "identify_target_states",
            "restrict",
        ]
        leaked = [name for name in removed if hasattr(colored_mdp, name)]
        assert not leaked, f"ColoredMdp should not expose: {leaked}"
