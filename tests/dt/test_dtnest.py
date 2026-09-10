import pytest
import stormpy

import paynt.dt
import paynt.dt.decision_tree
import paynt.dt.dtnest
import paynt.underlying_model.model_builder

from helpers.helper import get_sketch_paths

# established baseline for this model+property (see get_dt_with_api.py and test_dt_synthesizer.py):
# optimal ~0.6313574509764854, random/don't-care scheduler ~0.48451914218945663
OPTIMAL = 0.6313574509764854
RANDOM = 0.48451914218945663


def _dtnest_factory(properties_string):
    sketch_path, _ = get_sketch_paths("tests/dt-orchard")
    prism = stormpy.parse_prism_program(sketch_path, prism_compat=True)
    properties = stormpy.parse_properties_for_prism_program(properties_string, prism, None)
    explicit_model = paynt.underlying_model.model_builder.ModelBuilder.from_prism(prism, None, False)
    return properties, explicit_model


class TestDtNestConstraintHandling:
    """
    DtNest has no mechanism to check a constraint directly -- it only ever approximates a single
    optimality-shaped numeric target within an epsilon-band (see synthesize_subtrees/
    classify_constraint_threshold). A specification with no optimality objective but exactly one constraint
    is reduced to one (reduce_constraint_to_optimality), and the constraint's own threshold becomes the
    acceptance target instead of chasing epsilon-close-to-the-true-optimum. This is a real, previously-
    broken code path: it used to import a function (get_optimality_specification) that never existed
    anywhere in the paynt package (only in two long-deleted throwaway scripts), so every one of these cases
    used to crash with ImportError.
    """

    def test_constraint_between_random_and_optimal_is_treated_as_its_own_threshold(self):
        """P>=0.55 sits strictly between random (~0.4845) and optimal (~0.6314): DtNest should search for
        and find a tree clearing 0.55, not chase the unconstrained optimum."""
        properties, explicit_model = _dtnest_factory('P>=0.55 [F "goal"]')
        task = paynt.dt.dtnest.DtNestTask(properties, error_threshold=0.05, timeout=30)
        factory = paynt.dt.DtColoredMdpFactory(explicit_model, task)
        result = paynt.dt.dtnest.synthesize(factory, task)
        assert result.success
        assert result.value >= 0.55

    def test_constraint_already_satisfied_by_random_returns_it_directly(self):
        """P>=0.3 is already cleared by the random/don't-care scheduler alone (~0.4845): DtNest should
        short-circuit to exactly the random scheduler's value without running any subtree search."""
        properties, explicit_model = _dtnest_factory('P>=0.3 [F "goal"]')
        task = paynt.dt.dtnest.DtNestTask(properties, error_threshold=0.05, timeout=30)
        factory = paynt.dt.DtColoredMdpFactory(explicit_model, task)
        result = paynt.dt.dtnest.synthesize(factory, task)
        assert result.success
        assert result.value == pytest.approx(RANDOM, abs=1e-6)

    def test_constraint_above_optimal_is_unsatisfiable(self):
        """P>=0.9 is stricter than even the true optimum (~0.6314): no admissible tree exists."""
        properties, explicit_model = _dtnest_factory('P>=0.9 [F "goal"]')
        task = paynt.dt.dtnest.DtNestTask(properties, error_threshold=0.05, timeout=30)
        factory = paynt.dt.DtColoredMdpFactory(explicit_model, task)
        result = paynt.dt.dtnest.synthesize(factory, task)
        assert not result.success

    def test_optimality_alongside_a_constraint_is_rejected(self):
        """DtNest has no mechanism to enforce a constraint at all -- silently dropping it would be worse
        than refusing outright."""
        properties, explicit_model = _dtnest_factory('Pmax=? [F "goal"]; P>=0.5 [F "goal"]')
        task = paynt.dt.dtnest.DtNestTask(properties, error_threshold=0.05, timeout=30)
        factory = paynt.dt.DtColoredMdpFactory(explicit_model, task)
        with pytest.raises(ValueError):
            paynt.dt.dtnest.synthesize(factory, task)

    def test_multiple_constraints_without_optimality_is_rejected(self):
        """No sensible single-value reduction exists for more than one bare constraint."""
        properties, explicit_model = _dtnest_factory('P>=0.5 [F "goal"]; P<=0.9 [F "goal"]')
        task = paynt.dt.dtnest.DtNestTask(properties, error_threshold=0.05, timeout=30)
        factory = paynt.dt.DtColoredMdpFactory(explicit_model, task)
        with pytest.raises(ValueError):
            paynt.dt.dtnest.synthesize(factory, task)


def _node(identifier, old_identifier):
    node = paynt.dt.decision_tree.DecisionTreeNode(None)
    node.identifier = identifier
    node.old_identifier = old_identifier
    return node


class TestRemapNodeQueueAfterReplacement:
    """
    DtNest.synthesize_subtrees keeps a long-lived node_queue worklist that survives across many subtree
    replacements: after each replacement, every surviving entry's "id" (an identifier in the OLD tree) is
    translated to its counterpart in the new tree via old_identifier (set by
    DecisionTreeNode.assign_identifiers(keep_old=True) right after the replacement). This used to assert
    exactly one match and crash (AssertionError: only one node should have the old_identifier equal to X)
    whenever a queued node had no counterpart at all -- which happens for real: a still-queued node can end
    up structurally nested inside a later replacement's target before its own turn comes up (e.g. it was
    enqueued while the target's subtree was still small, and the target grew to enclose it via an
    intervening nested replacement), in which case its subtree no longer exists in the new tree. See the
    PAYNT refactor plan file for the full root-cause writeup (confirmed via instrumented reproduction on
    models/tests/dt-orchard with --dtnest --dtnest-subtree-depth 3).
    """

    def test_matching_entry_is_remapped_to_the_new_identifier(self):
        tree = paynt.dt.decision_tree.DecisionTree([], [])
        tree.root = _node(identifier=10, old_identifier=3)
        node_queue = [{"id": 3, "extra": "kept"}]
        result = paynt.dt.dtnest.DtNest.remap_node_queue_after_replacement(node_queue, tree)
        assert len(result) == 1
        assert result[0]["id"] == 10
        assert result[0]["extra"] == "kept"

    def test_entry_with_no_surviving_counterpart_is_dropped_not_raised(self):
        """Reproduces the exact shape of the real (pre-fix) crash directly: a queued node made obsolete by
        a later replacement has no node anywhere in the new tree with old_identifier equal to its id."""
        tree = paynt.dt.decision_tree.DecisionTree([], [])
        tree.root = _node(identifier=0, old_identifier=0)
        node_queue = [{"id": 0}, {"id": 999}]
        result = paynt.dt.dtnest.DtNest.remap_node_queue_after_replacement(node_queue, tree)
        assert len(result) == 1
        assert result[0]["id"] == 0

    def test_multiple_counterparts_raises(self):
        """Should never happen in practice (assign_identifiers(keep_old=True) always yields unique
        old_identifier values within one tree), but the defensive assert must still fire if it ever does."""
        root = _node(identifier=0, old_identifier=5)
        root.child_true = _node(identifier=1, old_identifier=5)
        root.child_false = _node(identifier=2, old_identifier=2)
        tree = paynt.dt.decision_tree.DecisionTree([], [])
        tree.root = root
        node_queue = [{"id": 5}]
        with pytest.raises(AssertionError):
            paynt.dt.dtnest.DtNest.remap_node_queue_after_replacement(node_queue, tree)
