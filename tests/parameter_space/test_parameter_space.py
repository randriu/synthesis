import paynt.parameter_space.parameter_space


class TestParameterSpaceRepresentationOnlySurface:

    def test_fresh_parameter_space_carries_no_search_state(self):
        """
        ParameterSpace is the pure value V of the colored MDP C = (M, V, kappa) (Definition 2,
        arXiv:2511.08078): it must not carry AR/CEGIS/policy-tree search bookkeeping (a built MDP, analysis
        results, parent/refinement/constraint tracking, an SMT encoding) or any feature-specific search field
        (policy-tree's candidate_policy, DT's scheduler_choices). That all lives on
        paynt.synthesizer.search_node.SearchNode (and its DtSearchNode/PolicyTreeNode subclasses) instead,
        which wraps a ParameterSpace rather than the other way around. This guards against any of these
        fields reappearing directly on the value type, whether declared or dynamically bolted on.
        """
        parameter_space = paynt.parameter_space.parameter_space.ParameterSpace()
        removed_or_never_present = [
            "mdp",
            "selected_choices",
            "analysis_result",
            "encoding",
            "parent_info",
            "refinement_depth",
            "constraint_indices",
            "candidate_policy",
            "scheduler_choices",
            "add_parent_info",
            "collect_parent_info",
            "encode",
        ]
        leaked = [name for name in removed_or_never_present if hasattr(parameter_space, name)]
        assert not leaked, f"ParameterSpace should not expose: {leaked}"

    def test_copy_also_carries_no_search_state(self):
        """.copy() must not resurrect any search field either -- it only ever copies native/
        parameter_to_name/parameter_to_option_labels."""
        parameter_space = paynt.parameter_space.parameter_space.ParameterSpace()
        parameter_space.add_parameter("x", ["a", "b"])
        copy = parameter_space.copy()
        assert not hasattr(copy, "mdp")
        assert not hasattr(copy, "analysis_result")
