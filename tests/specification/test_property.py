import stormpy

import paynt.specification.property


def _reachability_properties():
    return stormpy.parse_properties_without_context('Pmax=? [F "goal"]')


class TestConstructSpecification:

    def test_builds_specification_from_raw_properties(self):
        spec = paynt.specification.property.construct_specification(_reachability_properties())
        assert spec.num_properties == 1
        assert spec.has_optimality


class TestSpecificationRewrap:

    def test_preserves_property_type_and_epsilon(self):
        '''
        JaniUnfolder needs this: after translating PRISM to JANI, property atoms may change, so the
        specification's properties must be rebuilt from new raw stormpy formulas while preserving each
        property's paynt-level type (Property vs OptimalityProperty) and epsilon.
        '''
        original = paynt.specification.property.construct_specification(_reachability_properties(), relative_error=0.1)
        assert original.has_optimality
        original_epsilon = original.optimality.epsilon

        # simulate what JaniUnfolder does: re-wrap around "new" (here: the same) raw stormpy formulas
        new_raw_properties = [p.property for p in original.all_properties()]
        rewrapped = original.rewrap(new_raw_properties)

        assert type(rewrapped.optimality) == type(original.optimality)
        assert rewrapped.optimality.epsilon == original_epsilon
        assert rewrapped.num_properties == original.num_properties
