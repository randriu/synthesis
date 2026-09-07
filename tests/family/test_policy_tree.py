import paynt.family


class TestPolicyTreeSynthesis:

    def test_synthesize_via_ar_finds_a_satisfying_policy_for_every_family_member(
        self, family_colored_mdp, family_colored_mdp_factory
    ):
        '''
        Synthesis is deterministic here, so beyond "every family member is satisfiable", this also checks
        the shape of the result (a fixed number of distinct policies covering the whole family) and,
        instead of trusting the synthesizer's own bookkeeping, independently re-verifies each returned
        policy via PolicyTreeSynthesizer.verify_policy -- the same model-checking call the CLI's own
        "found N satisfying policies for M/M family members" summary is built from.
        '''
        task = family_colored_mdp_factory.task
        synthesizer = paynt.family.PolicyTreeSynthesizer(family_colored_mdp, task)
        prop = task.get_property()
        evaluations = synthesizer.evaluate(prop=prop, print_stats=False)
        assert len(evaluations) == 3, "expected exactly 3 distinct policies to cover this family"
        assert all(evaluation.sat for evaluation in evaluations), "expected every family member to be satisfiable"
        for evaluation in evaluations:
            policy = evaluation.policy[0]
            assert synthesizer.verify_policy(evaluation.parameter_space, prop, policy)
