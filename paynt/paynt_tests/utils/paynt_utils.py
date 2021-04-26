"""
    Copyright Paynt authors
    License: TODO
"""
import os
import subprocess

"""
PayntUtils class, which provides auxiliary methods for the tests
"""
class PayntUtils:

    ROOT_DIR = "./../../.."

    @staticmethod
    def getPathToPayntExecutable():
        assert "paynt.py" in os.listdir(PayntUtils.ROOT_DIR + "/paynt/")
        return PayntUtils.ROOT_DIR + "/paynt/paynt.py"

    @staticmethod
    def getPathToWorkspaceExamples():
        print(PayntUtils.ROOT_DIR)
        assert "workspace" in os.listdir(PayntUtils.ROOT_DIR)
        assert "examples" in os.listdir(PayntUtils.ROOT_DIR + "/workspace")
        return PayntUtils.ROOT_DIR + "/workspace/examples"
