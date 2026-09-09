import pytest
import stormpy

import paynt.dt
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
    '''
    DtNest has no mechanism to check a constraint directly -- it only ever approximates a single
    optimality-shaped numeric target within an epsilon-band (see synthesize_subtrees/
    classify_constraint_threshold). A specification with no optimality objective but exactly one constraint
    is reduced to one (reduce_constraint_to_optimality), and the constraint's own threshold becomes the
    acceptance target instead of chasing epsilon-close-to-the-true-optimum. This is a real, previously-
    broken code path: it used to import a function (get_optimality_specification) that never existed
    anywhere in the paynt package (only in two long-deleted throwaway scripts), so every one of these cases
    used to crash with ImportError.
    '''

    def test_constraint_between_random_and_optimal_is_treated_as_its_own_threshold(self):
        ''' P>=0.55 sits strictly between random (~0.4845) and optimal (~0.6314): DtNest should search for
        and find a tree clearing 0.55, not chase the unconstrained optimum. '''
        properties, explicit_model = _dtnest_factory('P>=0.55 [F "goal"]')
        task = paynt.dt.dtnest.DtNestTask(properties, error_threshold=0.05, timeout=30)
        factory = paynt.dt.DtColoredMdpFactory(explicit_model, task)
        result = paynt.dt.dtnest.synthesize(factory, task)
        assert result.success
        assert result.value >= 0.55

    def test_constraint_already_satisfied_by_random_returns_it_directly(self):
        ''' P>=0.3 is already cleared by the random/don't-care scheduler alone (~0.4845): DtNest should
        short-circuit to exactly the random scheduler's value without running any subtree search. '''
        properties, explicit_model = _dtnest_factory('P>=0.3 [F "goal"]')
        task = paynt.dt.dtnest.DtNestTask(properties, error_threshold=0.05, timeout=30)
        factory = paynt.dt.DtColoredMdpFactory(explicit_model, task)
        result = paynt.dt.dtnest.synthesize(factory, task)
        assert result.success
        assert result.value == pytest.approx(RANDOM, abs=1e-6)

    def test_constraint_above_optimal_is_unsatisfiable(self):
        ''' P>=0.9 is stricter than even the true optimum (~0.6314): no admissible tree exists. '''
        properties, explicit_model = _dtnest_factory('P>=0.9 [F "goal"]')
        task = paynt.dt.dtnest.DtNestTask(properties, error_threshold=0.05, timeout=30)
        factory = paynt.dt.DtColoredMdpFactory(explicit_model, task)
        result = paynt.dt.dtnest.synthesize(factory, task)
        assert not result.success

    def test_optimality_alongside_a_constraint_is_rejected(self):
        ''' DtNest has no mechanism to enforce a constraint at all -- silently dropping it would be worse
        than refusing outright. '''
        properties, explicit_model = _dtnest_factory('Pmax=? [F "goal"]; P>=0.5 [F "goal"]')
        task = paynt.dt.dtnest.DtNestTask(properties, error_threshold=0.05, timeout=30)
        factory = paynt.dt.DtColoredMdpFactory(explicit_model, task)
        with pytest.raises(ValueError):
            paynt.dt.dtnest.synthesize(factory, task)

    def test_multiple_constraints_without_optimality_is_rejected(self):
        ''' No sensible single-value reduction exists for more than one bare constraint. '''
        properties, explicit_model = _dtnest_factory('P>=0.5 [F "goal"]; P<=0.9 [F "goal"]')
        task = paynt.dt.dtnest.DtNestTask(properties, error_threshold=0.05, timeout=30)
        factory = paynt.dt.DtColoredMdpFactory(explicit_model, task)
        with pytest.raises(ValueError):
            paynt.dt.dtnest.synthesize(factory, task)
