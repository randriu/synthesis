import paynt.specification.property_result


class _FakeConstraintResult:
    def __init__(self, sat):
        self.sat = sat


class _FakeOptimalityResult:
    def __init__(self, improves_optimum, value=None):
        self.improves_optimum = improves_optimum
        self.value = value


def _spec_result(constraint_sats, optimality_result=None):
    spec_result = paynt.specification.property_result.SpecificationResult()
    spec_result.constraints_result = paynt.specification.property_result.ConstraintsResult(
        [_FakeConstraintResult(sat) for sat in constraint_sats])
    spec_result.optimality_result = optimality_result
    return spec_result


class TestAcceptingDtmc:
    '''
    Regression coverage for SpecificationResult.accepting_dtmc's contract: it always returns a
    (accepting: bool, improving_value) tuple, never a bare bool. A caller that writes
    `if result.accepting_dtmc(spec):` instead of unpacking gets a tuple -- which is truthy in Python
    regardless of its contents, including (False, None) -- so the check always passes. This was a real bug
    in SynthesizerAR.check_specification (paynt/synthesizer/synthesizer_ar.py), silently marking a
    constraint's result "sat" and recording an "admissible_assignment" for any consistent scheduler
    regardless of whether the resulting DTMC actually satisfied the specification. It went undetected
    because it only executes when a specification has at least one explicit constraint (empty and skipped
    entirely for the optimality-only sketches this refactor's CLI regression battery has used), fixed by
    unpacking first: `accepting,_ = result.accepting_dtmc(spec); if accepting:`.
    '''

    def test_unsat_constraints_return_false_and_must_not_be_used_as_a_bare_condition(self):
        result = _spec_result(constraint_sats=[False])
        assert result.accepting_dtmc(specification=None) == (False, None)
        # the actual regression: a non-empty tuple is always truthy, so `if result.accepting_dtmc(...):`
        # would incorrectly treat this unsatisfying result as accepting -- only the unpacked first
        # element may be used as the condition
        accepting,_ = result.accepting_dtmc(specification=None)
        assert accepting is False

    def test_sat_constraints_no_optimality_returns_true_and_none(self):
        result = _spec_result(constraint_sats=[True])
        assert result.accepting_dtmc(specification=None) == (True, None)

    def test_sat_constraints_optimality_not_improving_returns_false(self):
        ''' The scenario that actually triggers the bug in a real multi-constraint-with-optimality search:
        a different, already-found assignment locked in a better optimum, so a later, still-constraint-
        satisfying assignment no longer "improves" -- accepting_dtmc correctly reports this as not
        accepting, which the old unfixed caller would have silently overridden. '''
        result = _spec_result(constraint_sats=[True], optimality_result=_FakeOptimalityResult(improves_optimum=False))
        accepting,improving_value = result.accepting_dtmc(specification=None)
        assert accepting is False
        assert improving_value is None

    def test_sat_constraints_optimality_improving_returns_true_and_value(self):
        result = _spec_result(constraint_sats=[True], optimality_result=_FakeOptimalityResult(improves_optimum=True, value=0.75))
        assert result.accepting_dtmc(specification=None) == (True, 0.75)
