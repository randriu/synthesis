import paynt.parser.sketch as sketch
import paynt.quotient.mdp
import paynt.quotient.quotient

from helpers.helper import get_stormpy_example_path, get_sketch_paths

class TestSketch:

    def test_load_sketch_mdp_prism(self):
        # setup
        sketch_path, props_path = get_sketch_paths("mdp/maze")

        # test
        quotient = sketch.Sketch.load_sketch(sketch_path, props_path)

        # assert
        assert isinstance(quotient, paynt.quotient.mdp.MdpQuotient)
        assert quotient.quotient_mdp.nr_states == 15
        # TODO add more asserts

    # add more tests