import paynt


def test_api_import():
    # Test that API functions are available at package level
    assert hasattr(paynt, "get_version"), "get_version not found in paynt package"
    assert callable(paynt.get_version), "get_version is not callable"
    # regression test: get_version() used to crash with AttributeError ('function' object has no
    # attribute '__version__'), since it read version.__version__ instead of calling version() --
    # hasattr/callable alone can't catch this, since the function exists and is callable either way
    assert isinstance(paynt.get_version(), str) and paynt.get_version() != ""
    print("paynt API import test passed.")


if __name__ == "__main__":
    test_api_import()
