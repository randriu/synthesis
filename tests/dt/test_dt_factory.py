import paynt.dt
import paynt.synthesizer.search_node


class TestDtColoredMdpFactory:

    def test_load_sketch_produces_a_dt_colored_mdp(self, dt_colored_mdp):
        ''' An MDP-with-parameters sketch that doesn't have PRISM-declared parameters (no jani_unfolder) and
        isn't partially observable resolves through DtColoredMdpFactory. '''
        assert isinstance(dt_colored_mdp, paynt.dt.DtColoredMdp)
        assert dt_colored_mdp.feature_kind == "dt"

    def test_factory_builds_an_initial_depth_zero_tree(self, dt_colored_mdp, dt_colored_mdp_factory):
        ''' Regression test for the construction-order fix: DtColoredMdpFactory must produce a usable
        colored_mdp immediately (matching every other specialist factory), unlike the pre-refactor
        DtColoredMdpFactory which had no coloring/parameter_space until reset_tree was called externally. '''
        assert isinstance(dt_colored_mdp_factory, paynt.dt.DtColoredMdpFactory)
        assert dt_colored_mdp_factory.colored_mdp is dt_colored_mdp
        assert dt_colored_mdp.decision_tree.get_depth() == 0

    def test_reset_tree_produces_a_fresh_colored_mdp(self, dt_colored_mdp, dt_colored_mdp_factory):
        reset = dt_colored_mdp_factory.reset_tree(2)
        assert isinstance(reset, paynt.dt.DtColoredMdp)
        assert reset.decision_tree.get_depth() == 2
        # the identity data (computed once at construction) must carry over unchanged across reset_tree
        assert reset.action_labels is dt_colored_mdp.action_labels

    def test_build_produces_an_mdp(self, dt_colored_mdp):
        node = paynt.synthesizer.search_node.SearchNode(dt_colored_mdp.parameter_space.copy())
        node.mdp, node.selected_choices = dt_colored_mdp.build(node.parameter_space)
        assert node.mdp.states > 0

    def test_factory_without_a_task_matches_the_get_dt_with_api_pattern(self, dt_colored_mdp):
        ''' paynt.dt.api.synthesize's real callers (see get_dt_with_api.py) construct a
        DtColoredMdpFactory from just an mdp, with no task yet, and attach one later. '''
        factory = paynt.dt.DtColoredMdpFactory(dt_colored_mdp.underlying_mdp)
        assert factory.task is None
        assert factory.colored_mdp.decision_tree.get_depth() == 0
