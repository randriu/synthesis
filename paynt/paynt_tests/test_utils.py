"""
    Copyright Paynt authors
    License: TODO
"""
import os

"""
PayntUtils class, which provides auxiliary methods for the tests
"""


class PayntTestUtils:
    ROOT_DIR = "./../../"

    @staticmethod
    def get_path_to_paynt_executable():
        assert "paynt.py" in os.listdir(PayntTestUtils.ROOT_DIR + "/paynt/")
        return PayntTestUtils.ROOT_DIR + "/paynt/paynt.py"

    @staticmethod
    def get_path_to_workspace_examples():
        print(PayntTestUtils.ROOT_DIR)
        assert "workspace" in os.listdir(PayntTestUtils.ROOT_DIR)
        assert "examples" in os.listdir(PayntTestUtils.ROOT_DIR + "/workspace")
        return PayntTestUtils.ROOT_DIR + "/workspace/examples"
