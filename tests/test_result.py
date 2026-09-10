import paynt.result


class TestResult:

    def test_stores_success_and_value(self):
        result = paynt.result.Result(True, 3.14)
        assert result.success is True
        assert result.value == 3.14

    def test_value_defaults_to_none(self):
        result = paynt.result.Result(False)
        assert result.value is None
