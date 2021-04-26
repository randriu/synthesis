import pytest
import unittest
import subprocess
import logging

from ..utils.paynt_utils import PayntUtils

"""
HybridTestSuite, which ensures that paynt works on the smoke level.
"""
class HybridTestSuite(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # 1.setup phase
        logging.info("[SETUP] - Preparing HybridTestSuite")
        # self.shared_data = ...

    def test_hybrid_herman_5(self):
        # 2.exercise phase
        process = subprocess.Popen(['python3',
            PayntUtils.getPathToPayntExecutable(),
            '--project',
            PayntUtils.getPathToWorkspaceExamples() + '/herman/5/',
            'hybrid',
            '--short-summary',
            '--constants',
            'CMAX=0,THRESHOLD=1.0',
            '--optimality', 'sketch.optimal',
            '--properties', 'optimal.properties'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = process.communicate()
        # 3.verify phase
        self.assertIn("T = [18.1930600768] - Hybrid: opt = 18.19306", str(stdout))
        self.assertEqual("b''", str(stderr))

    @classmethod
    def tearDownClass(self):
        # 4.teardown phase
        logging.info("[TEARDOWN] - Cleaning HybridTestSuite")
        # self.shared_data = None

if __name__ == '__main__':
    unittest.main()