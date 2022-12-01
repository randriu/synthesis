from ast import Pass
from unittest import result
import stormpy
import stormpy.synthesis
import stormpy.pomdp

import time

from multiprocessing import Process, SimpleQueue


import logging
logger = logging.getLogger(__name__)

# TODO JUST A CONCEPT WE WILL TRY ITERATIVE METHOD FIRST
# class for managing PAYNT and Storm parallel processes
class ParallelControl:

    def __init__(self, synthesizer, storm_control):
        self.synthesizer = synthesizer              # PAYNT
        self.storm_control = storm_control          # STORM

    def run(self):
        storm_queue = SimpleQueue()
        paynt_queue = SimpleQueue()

        self.synthesizer.synthesizer.s_queue = paynt_queue
        self.storm_control.s_queue = storm_queue

        storm_process = Process(target=self.storm_control.get_storm_result)
        storm_process.start()

        paynt_process = Process(target=self.synthesizer.run, args=(True,))
        paynt_process.start()

        storm_process.join()

        storm_result = storm_queue.get()
        paynt_queue.put(storm_result)
        
        paynt_process.join()


        #s_queue.close()
