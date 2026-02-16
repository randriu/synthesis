import paynt

def test_api_import():
    # Test that API functions are available at package level
    assert hasattr(paynt, "get_version"), "get_version not found in paynt package"
    assert callable(paynt.get_version), "get_version is not callable"
    print("paynt API import test passed.")

if __name__ == "__main__":
    test_api_import()
