import paynt.family
import paynt.family.colored_mdp
import paynt.synthesizer.search_node


class TestFamilyColoredMdpFactory:

    def test_load_sketch_produces_a_family_colored_mdp(self, family_colored_mdp):
        assert isinstance(family_colored_mdp, paynt.family.colored_mdp.FamilyColoredMdp)
        assert family_colored_mdp.feature_kind == "family"

    def test_build_produces_an_mdp_not_necessarily_deterministic(self, family_colored_mdp):
        node = paynt.synthesizer.search_node.SearchNode(family_colored_mdp.parameter_space.copy())
        node.mdp, node.selected_choices = family_colored_mdp.build(node.parameter_space)
        assert node.mdp.states > 0

    def test_build_assignment_does_not_force_a_dtmc(self, family_colored_mdp):
        '''
        Regression test: FamilyColoredMdp.build_assignment overrides the base ColoredMdp implementation
        specifically because fixing every parameter (picking one family member) does not fix the agent's
        policy -- the resulting model can still be nondeterministic, so it must not be converted to a DTMC
        the way the base ColoredMdp.build_assignment does for every other colored-MDP variant.
        '''
        assignment = family_colored_mdp.parameter_space.pick_any()
        mdp = family_colored_mdp.build_assignment(assignment)
        assert mdp.states > 0

    def test_empty_policy_has_one_entry_per_state(self, family_colored_mdp):
        policy = family_colored_mdp.empty_policy()
        assert len(policy) == family_colored_mdp.underlying_mdp.nr_states
        assert all(action is None for action in policy)

    def test_action_structure_is_populated(self, family_colored_mdp):
        assert family_colored_mdp.num_actions > 0
        assert len(family_colored_mdp.action_labels) == family_colored_mdp.num_actions
        assert len(family_colored_mdp.state_to_actions) == family_colored_mdp.underlying_mdp.nr_states
