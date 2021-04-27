import unittest
import subprocess
import logging

from test_utils import PayntTestUtils

"""
HybridTestSuite, which ensures that paynt works on the smoke level.
"""


class HybridTestSuite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # 1.setup phase
        logging.info("[SETUP] - Preparing HybridTestSuite")
        # self.shared_data = ...

    def test_hybrid_herman_5(self):

        # 2.exercise phase
        process = subprocess.Popen([
            'python3',
            PayntTestUtils.get_path_to_paynt_executable(),
            '--project',
            PayntTestUtils.get_path_to_workspace_examples() + '/herman/5/',
            'hybrid',
            '--short-summary',
            '--constants', 'CMAX=0',
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = process.communicate()
        # 3.verify phase
        self.assertIn("Hybrid: opt = 18.19306", str(stdout))
        self.assertEqual("b''", str(stderr))

    def run_kydie_for_oracle(self, method):

        process = subprocess.Popen([
            'python3',
            PayntTestUtils.get_path_to_paynt_executable(),
            '--project', PayntTestUtils.get_path_to_workspace_examples() + '/kydie/',
            f'{method}',
            '--short-summary',
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = process.communicate()
        # 3.verify phase
        method = "1-by-1" if method == "onebyone" else method
        self.assertIn(f"{method}: opt = 3.666667", str(stdout))
        self.assertEqual("b''", str(stderr))

    def test_kydie_hybrid(self):

        self.run_kydie_for_oracle('Hybrid')

    def test_kydie_cegar(self):

        self.run_kydie_for_oracle('CEGAR')

    def test_kydie_cegis(self):

        self.run_kydie_for_oracle('CEGIS')

    def test_kydie_one_by_one(self):

        self.run_kydie_for_oracle('onebyone')

    def run_grid_optimal_for_oracle(self, method):

        process = subprocess.Popen([
            'python3',
            PayntTestUtils.get_path_to_paynt_executable(),
            '--project', PayntTestUtils.get_path_to_workspace_examples() + '/grid/orig/',
            f'{method}',
            '--short-summary',
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = process.communicate()
        # 3.verify phase
        method = "1-by-1" if method == "onebyone" else method
        self.assertIn(f"{method}: opt = 0.064286", str(stdout))
        self.assertEqual("b''", str(stderr))

    def test_grid_optimal_hybrid(self):

        self.run_grid_optimal_for_oracle('Hybrid')

    def test_grid_optimal_cegar(self):

        self.run_grid_optimal_for_oracle('CEGAR')

    # def test_grid_optimal_cegis(self):
    #     self.run_grid_optimal_for_oracle('CEGIS')
    #
    # def test_grid_optimal_one_by_one(self):
    #     self.run_grid_optimal_for_oracle('onebyone')

    @classmethod
    def tearDownClass(cls):
        # 4.teardown phase
        logging.info("[TEARDOWN] - Cleaning HybridTestSuite")
        # self.shared_data = None


if __name__ == '__main__':
    unittest.main()
