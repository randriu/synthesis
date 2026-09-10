import pytest

import paynt.parser.sketch

from helpers.helper import get_sketch_paths


@pytest.fixture
def pomdp_colored_mdp_factory():
    sketch_path, props_path = get_sketch_paths("tests/pomdp-maze")
    factory, task = paynt.parser.sketch.Sketch.load_sketch(sketch_path, props_path)
    return factory


@pytest.fixture
def pomdp_colored_mdp(pomdp_colored_mdp_factory):
    return pomdp_colored_mdp_factory.colored_mdp


@pytest.fixture
def decpomdp_colored_mdp_factory():
    """A genuine multi-agent Cassandra/.dpomdp sketch, which resolves through
    payntbind.synthesis.parse_decpomdp to a real decpomdp_manager (num_agents > 1) and so through
    DecPomdpColoredMdpFactory. This is NOT the same as models/archive/*/dec-pomdp/*, whose sketch.templ
    files are actually plain PRISM DTMC-with-parameters sketches (parse cleanly as PRISM, model_type DTMC) --
    similarly-named parameters, but they resolve to a plain paynt.colored_mdp.ColoredMdp (no specialist
    factory at all) and never touch this code at all."""
    sketch_path, props_path = get_sketch_paths("tests/decpomdp-dectiger", sketch_name="dectiger.dpomdp", props_name="dectiger.dpomdp")
    factory, task = paynt.parser.sketch.Sketch.load_sketch(sketch_path, props_path)
    return factory


@pytest.fixture
def decpomdp_colored_mdp(decpomdp_colored_mdp_factory):
    return decpomdp_colored_mdp_factory.colored_mdp
