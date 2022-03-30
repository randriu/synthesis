
from asyncio.log import logger
from copy import deepcopy

from ..utils.graphs import Graph
from .pomdp import SynthesizerPOMDP
from ..utils.restrictions import Conditions, set_memory
from ..profiler import Profiler
from .quotient import POMDPQuotientContainer

import cProfile
import pstats

import logging
logger = logging.getLogger(__name__)


class SynthesizerPOMDPIncremental(SynthesizerPOMDP):

    def __init__(self, sketch, method, min=0, max=0):
        super().__init__(sketch, method)
        self.design_space = deepcopy(sketch.design_space)

        print("min", min)
        print("max", max)

        self.mem_size = min
        self.max_size = max

    def run(self):

        top_optimum = 0

        while self.mem_size != self.max_size:
            logger.info("CURRENT TOP OPTIMUM: " + str(top_optimum))
            logger.info("MEM size: " + str(self.mem_size))
            self.sketch.quotient.pomdp_manager.set_memory_size(self.mem_size)
            self.sketch.quotient.unfold_memory()

            # if self.sketch.specification.optimality.optimum and top_optimum < self.sketch.specification.optimality.optimum:
            #     top_optimum = self.sketch.specification.optimality.optimum

            # self.sketch.specification.optimality.optimum = 0

            for item in Conditions().conditions:

                self.sketch.design_space = set_memory(
                    self.sketch.design_space,
                    self.mem_size,
                    item["condition"],
                    item["rewrite"],
                    item["restrict"],
                    item["name"],
                )

                if self.sketch.design_space.size > 4 and item["synthesize"]:
                    Graph().print(self.sketch.design_space,
                                  "workspace/log/out/" + str(self.mem_size) + "_" + item["name"].replace(" ", "_").lower(), True)

                    res = self.synthesize(self.sketch.design_space)
                    if not res:
                        logger.info("NO RESULT")
                    else:
                        Graph().print(self.sketch.design_space,
                                      "workspace/log/res/" + str(self.mem_size) + "_" + item["name"].replace(" ", "_").lower(), True)
                        logger.info(res)
            self.mem_size += 1

        logger.info("TOP optimal: " + str(top_optimum))
