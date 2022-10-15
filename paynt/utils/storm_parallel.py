from ast import Pass
from unittest import result
import stormpy
import stormpy.synthesis
import stormpy.pomdp

import time

from multiprocessing import Process


import logging
logger = logging.getLogger(__name__)


# class for managing PAYNT and Storm parallel processes
class ParallelMain:

    def __init__(self, synthesizer, storm_control):
        self.synthesizer = synthesizer              # PAYNT
        self.storm_control = storm_control          # STORM

    def run(self):
        storm_process = Process(target=self.storm_control.run_storm_analysis)
        storm_process.start()

        paynt_process = Process(target=self.synthesizer.run, args=(True,))
        paynt_process.start()

        
        paynt_process.join()
