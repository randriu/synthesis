import pytest
import stormpy

import paynt.dt
import paynt.dt.dtnest.task
import paynt.underlying_model.model_builder

from helpers.helper import get_sketch_paths


class TestDtSynthesis:

    def test_split_undecided_space_survives_a_multi_property_specification(self):
        '''
        Regression test: scheduler_choices is only ever populated by DtColoredMdp.scheduler_is_consistent
        when the specification is single-property (see split_undecided_space/verify_parameter_space's guards) -- for any
        specification with more than one property (a constraint alongside the optimality objective, as
        constructed here), it stays None on every parameter space. split_undecided_space used to copy it unconditionally
        (parent_info.scheduler_choices = parameter_space.scheduler_choices) and verify_parameter_space used to
        iterate it unconditionally too, so the very first split of a multi-property parameter space raised
        AttributeError -- silently never caught because every DT sketch actually used elsewhere in this
        suite happens to be single-property.
        '''
        sketch_path, _ = get_sketch_paths("tests/dt-orchard")
        prism = stormpy.parse_prism_program(sketch_path, prism_compat=True)
        # a trivially-true constraint alongside the real optimality objective: enough to make
        # is_single_property False without changing what the "right" answer is
        properties = stormpy.parse_properties_for_prism_program('P>=0 [F "goal"]; Pmax=? [F "goal"]', prism, None)
        assert len(properties) == 2

        explicit_model = paynt.underlying_model.model_builder.ModelBuilder.from_prism(prism, None, False)
        task = paynt.dt.dtnest.task.DtNestTask(properties, error_threshold=0.05, tree_depth=2, timeout=15)
        assert not task.specification.is_single_property

        factory = paynt.dt.DtColoredMdpFactory(explicit_model, task)
        synthesizer = paynt.dt.DtSynthesizer(factory)
        synthesizer.synthesize_tree(depth=2, timeout=15)
        assert synthesizer.best_tree is not None

    def test_synthesize_finds_the_known_optimum(self, dt_colored_mdp_factory):
        '''
        Regression test for DtSynthesizer.split_undecided_space/scheduler_scores (the search-policy methods moved
        off the factory during this migration). Kept at depth 0 deliberately: full AR-based tree synthesis
        is combinatorially expensive on this model at higher depths (which is exactly why get_dt_with_api.py
        uses dtnest's subtree-based search instead of plain synthesize_tree for real use) -- but dtnest's
        subtree calls go through this same split_undecided_space override internally, and that path is already
        verified end-to-end (byte-identical value 0.6313574509764854) via get_dt_with_api.py.

        Since synthesis is deterministic, the tree itself (not just its value) is checked too: at depth 0
        the only admissible tree is a single leaf, so its string form is a one-line action label.
        '''
        synthesizer = paynt.dt.DtSynthesizer(dt_colored_mdp_factory)
        synthesizer.synthesize_tree(depth=0)
        assert synthesizer.best_tree is not None
        assert synthesizer.best_tree_value == pytest.approx(0.48450450140758644, abs=1e-6)
        assert synthesizer.best_tree.to_string() == "roll\n"
