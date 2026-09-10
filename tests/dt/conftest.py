import pytest

import paynt.parser.sketch

from helpers.helper import get_sketch_paths


@pytest.fixture
def dt_colored_mdp_factory():
    """The same sketch get_dt_with_api.py (a real script exercising paynt.dt's library API) uses --
    confirmed to resolve through DtColoredMdpFactory via the normal Sketch.load_sketch path too. Plenty of
    sketches that superficially look DT-shaped actually resolve elsewhere: e.g. archive/jair24-synthesis/maze
    is a plain PRISM DTMC-with-parameters and never touches this code at all (same trap as DecPomdp's
    dec-tiger-2fsc earlier in this refactor)."""
    sketch_path, props_path = get_sketch_paths("tests/dt-orchard")
    factory, task = paynt.parser.sketch.Sketch.load_sketch(sketch_path, props_path)
    return factory


@pytest.fixture
def dt_colored_mdp(dt_colored_mdp_factory):
    return dt_colored_mdp_factory.colored_mdp
