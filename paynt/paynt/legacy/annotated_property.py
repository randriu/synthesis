import stormpy
import stormpy.logic

class AnnotatedProperty:
    """
    (Very) simple property wrapper that caters for the need of prerequisite properties
    In particular, if we check expected rewards, we implicitly have to assume that the 
    probability to reach the target set is one. 
    This implicit assumption can be made explicit with a prerequisite property. 
    """

    def __init__(self, prop, sketch = None, add_prerequisites=True):
        self.property = prop
        self.prerequisite_property = None
        if add_prerequisites and prop.raw_formula.is_reward_operator:
            assert prop.raw_formula.has_bound
            assert sketch
            prereq_thresh = prop.raw_formula.threshold_expr.manager.create_rational(stormpy.Rational(1))
            operator = stormpy.ProbabilityOperator(prop.raw_formula.subformula.clone())
            operator.set_bound(stormpy.logic.ComparisonType.GEQ, prereq_thresh)
            new_prop = stormpy.parse_properties_for_jani_model(str(operator), sketch)
            self.prerequisite_property = stormpy.Property(prop.name + "_prereq", new_prop[0].raw_formula, comment="Prerequisite")

    @property
    def raw_formula(self):
        return self.property.raw_formula