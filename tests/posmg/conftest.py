import pytest

import paynt.parser.sketch

from helpers.helper import get_sketch_paths


@pytest.fixture
def posmg_colored_mdp_factory():
    ''' A POSMG sketch resolves to a PosmgColoredMdp via PosmgColoredMdpFactory. mec-test has only
    single-state (perfect-information) observations for the optimizing player, so it is fast but never
    actually exercises memory unfolding -- see posmg_test_game_colored_mdp_factory/test_posmg_synthesizer.py
    for that. '''
    sketch_path, props_path = get_sketch_paths("tests/posmg-mec-test")
    factory, task = paynt.parser.sketch.Sketch.load_sketch(sketch_path, props_path)
    return factory


@pytest.fixture
def posmg_colored_mdp(posmg_colored_mdp_factory):
    return posmg_colored_mdp_factory.colored_mdp


@pytest.fixture
def posmg_test_game_colored_mdp_factory():
    ''' Unlike mec-test, test-game's optimizing player has multi-state observations, so this is the fixture
    that actually exercises memory unfolding (see test_synthesize_improves_with_memory_unfolding). '''
    sketch_path, props_path = get_sketch_paths("tests/posmg-test-game")
    factory, task = paynt.parser.sketch.Sketch.load_sketch(sketch_path, props_path)
    return factory
