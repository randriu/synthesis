import paynt.pomdp
import paynt.synthesizer.search_node


class TestDecPomdpColoredMdpFactory:

    def test_load_sketch_produces_a_decpomdp_colored_mdp(self, decpomdp_colored_mdp):
        assert isinstance(decpomdp_colored_mdp, paynt.pomdp.decpomdp.DecPomdpColoredMdp)
        assert decpomdp_colored_mdp.feature_kind == "decpomdp"

    def test_factory_reports_agent_count(self, decpomdp_colored_mdp_factory):
        assert isinstance(decpomdp_colored_mdp_factory, paynt.pomdp.decpomdp.DecPomdpColoredMdpFactory)
        assert decpomdp_colored_mdp_factory.nr_agents == 2

    def test_build_produces_an_mdp(self, decpomdp_colored_mdp):
        node = paynt.synthesizer.search_node.SearchNode(decpomdp_colored_mdp.parameter_space.copy())
        node.mdp, node.selected_choices = decpomdp_colored_mdp.build(node.parameter_space)
        assert node.mdp.states > 0

    def test_set_imperfect_memory_size_produces_a_fresh_colored_mdp(self, decpomdp_colored_mdp_factory):
        reunfolded = decpomdp_colored_mdp_factory.set_imperfect_memory_size(2)
        assert isinstance(reunfolded, paynt.pomdp.decpomdp.DecPomdpColoredMdp)
        assert decpomdp_colored_mdp_factory.current_memory_size == 2

    def test_set_agent_imperfect_memory_size_produces_a_fresh_colored_mdp(self, decpomdp_colored_mdp_factory):
        """Per-agent memory sizing: distinct from set_imperfect_memory_size, which resizes every agent."""
        reunfolded = decpomdp_colored_mdp_factory.set_agent_imperfect_memory_size(0, 2)
        assert isinstance(reunfolded, paynt.pomdp.decpomdp.DecPomdpColoredMdp)
