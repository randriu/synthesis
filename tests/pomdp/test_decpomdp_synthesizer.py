import pytest

import paynt.pomdp


class TestDecPomdpSynthesis:

    def test_synthesize_finds_the_known_optimum(self, decpomdp_colored_mdp_factory):
        """Synthesis is deterministic here, so the synthesized assignment itself is checked, not just the
        reward value it achieves."""
        synthesizer = paynt.pomdp.decpomdp.DecPomdpSynthesizer(decpomdp_colored_mdp_factory)
        assignment = synthesizer.synthesize(synthesizer.colored_mdp.parameter_space, print_stats=False)
        optimum = synthesizer.task.specification.optimality.optimum
        assert optimum == pytest.approx(-2.0, abs=1e-4)
        assert str(assignment) == (
            "A(0,hear-left,0)=act_0, A(0,hear-right,0)=act_0, A(0,__no_obs__,0)=act_0, "
            "A(1,hear-left,0)=act_0, A(1,hear-right,0)=act_0, A(1,__no_obs__,0)=act_0"
        )
