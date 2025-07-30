import pytest
from helpers.helper import get_sketch_paths

import paynt.parser.sketch
import paynt.synthesizer.synthesizer_ar
import paynt.utils.timer

class TestPosmg:
    def test_simple_posmg(self):
        paynt.utils.timer.GlobalTimer.start()
        sketch_path, prop_path = get_sketch_paths('posmg/test-game')
        quotient = paynt.parser.sketch.Sketch.load_sketch(sketch_path, prop_path)
        synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR(quotient)
        synthesizer.synthesize(keep_optimum=True)

        assert synthesizer.best_assignment_value == pytest.approx(0.375)


    def test_constraints_feasible(self):
        paynt.utils.timer.GlobalTimer.start()
        sketch_path, prop_path = get_sketch_paths('posmg/test-game', props_name='constraint-feasible.props')
        quotient = paynt.parser.sketch.Sketch.load_sketch(sketch_path, prop_path)
        synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR(quotient)
        synthesizer.synthesize(keep_optimum=True)

        assert synthesizer.best_assignment is not None

    def test_constraints_nonfeasible(self):
        paynt.utils.timer.GlobalTimer.start()
        sketch_path, prop_path = get_sketch_paths('posmg/test-game', props_name='constraint-nonfeasible.props')
        quotient = paynt.parser.sketch.Sketch.load_sketch(sketch_path, prop_path)
        synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR(quotient)
        synthesizer.synthesize(keep_optimum=True)

        assert synthesizer.best_assignment is None

    def test_rewards(self):
        paynt.utils.timer.GlobalTimer.start()
        sketch_path, prop_path = get_sketch_paths('posmg/testing-rewards')
        quotient = paynt.parser.sketch.Sketch.load_sketch(sketch_path, prop_path)
        synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR(quotient)
        synthesizer.synthesize(keep_optimum=True)

        assert synthesizer.best_assignment_value == pytest.approx(75)