import paynt.pomdp


class TestPomdpColoredMdpFactory:

    def test_load_sketch_produces_a_pomdp_colored_mdp(self, pomdp_colored_mdp):
        assert isinstance(pomdp_colored_mdp, paynt.pomdp.PomdpColoredMdp)
        assert pomdp_colored_mdp.feature_kind == "pomdp"

    def test_build_produces_an_mdp(self, pomdp_colored_mdp):
        parameter_space = pomdp_colored_mdp.parameter_space.copy()
        pomdp_colored_mdp.build(parameter_space)
        assert parameter_space.mdp.states > 0

    def test_set_imperfect_memory_size_produces_a_fresh_colored_mdp(self, pomdp_colored_mdp_factory):
        reunfolded = pomdp_colored_mdp_factory.set_imperfect_memory_size(2)
        assert isinstance(reunfolded, paynt.pomdp.PomdpColoredMdp)
        assert pomdp_colored_mdp_factory.current_memory_size == 2
