"""
    Copyright Dynasty authors
    License: TODO
"""
import os
import subprocess

"""
DynastyUtils class, which provides auxiliary methods for the tests
"""
class DynastyUtils:

    ROOT_DIR = "./../../.."

    @staticmethod
    def getPathToDynastyExecutable():
        assert "dynasty.py" in os.listdir(DynastyUtils.ROOT_DIR + "/dynasty/")
        return DynastyUtils.ROOT_DIR + "/dynasty/dynasty.py"

    @staticmethod
    def getPathToWorkspaceExamples():
        print(DynastyUtils.ROOT_DIR)
        assert "workspace" in os.listdir(DynastyUtils.ROOT_DIR)
        assert "examples" in os.listdir(DynastyUtils.ROOT_DIR + "/workspace")
        return DynastyUtils.ROOT_DIR + "/workspace/examples"
