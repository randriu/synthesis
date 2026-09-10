import pytest
import stormpy

import paynt.task
import paynt.dt.task
import paynt.dt.dtnest.task


def _reachability_properties():
    return stormpy.parse_properties_without_context('Pmax=? [F "goal"]')


def _reward_properties():
    return stormpy.parse_properties_without_context('R{"steps"}min=? [F "goal"]')


class TestDtTask:

    def test_is_a_task(self):
        task = paynt.dt.task.DtTask(_reachability_properties(), tree_depth=3, timeout=120)
        assert isinstance(task, paynt.task.Task)
        assert task.specification.num_properties == 1
        assert task.timeout == 120
        assert task.tree_depth == 3

    def test_scheduler_to_map_starts_unset(self):
        task = paynt.dt.task.DtTask(_reachability_properties(), tree_depth=3)
        assert not task.has_scheduler_to_map
        task.set_scheduler_to_map("some-scheduler")
        assert task.has_scheduler_to_map

    def test_use_exact_is_no_longer_hardcoded_to_false(self):
        """
        Regression test: DtTask used to hardcode Property.initialize(False) regardless of the caller's
        use_exact, silently ignoring it. use_exact now flows through to construct_property (via the
        inherited Task.__init__) like every other Task, which rejects reward properties when use_exact=True.
        """
        with pytest.raises(ValueError):
            paynt.dt.task.DtTask(_reward_properties(), tree_depth=3, use_exact=True)
        # sanity: the same construction succeeds without use_exact
        paynt.dt.task.DtTask(_reward_properties(), tree_depth=3, use_exact=False)


class TestDtNestTask:

    def test_is_a_dt_task(self):
        task = paynt.dt.dtnest.task.DtNestTask(_reachability_properties(), error_threshold=0.05, tree_depth=5)
        assert isinstance(task, paynt.dt.task.DtTask)
        assert task.error_threshold == 0.05
        assert task.tree_depth == 5
        assert task.specification.num_properties == 1

    def test_initial_tree_defaults_to_none(self):
        task = paynt.dt.dtnest.task.DtNestTask(_reachability_properties(), error_threshold=0.05)
        assert task.initial_tree is None
