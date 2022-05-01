from copy import deepcopy

from ..utils.graphs import Graph
from .pomdp import SynthesizerPOMDP
from ..utils.restrictions import Conditions, set_memory

import logging
logger = logging.getLogger(__name__)

class SynthesizerPOMDPIncremental(SynthesizerPOMDP):

    def __init__(self, sketch, method, min=0, max=0):
        super().__init__(sketch, method, strategy=None)

        self.mem_size = min
        self.max_size = max

    def run(self):

        while self.mem_size != self.max_size:
            self.sketch.quotient.pomdp_manager.set_memory_size(self.mem_size)
            self.sketch.quotient.unfold_memory()

            for item in Conditions().conditions:

                self.sketch.design_space = set_memory(
                    self.sketch.design_space,
                    self.mem_size,
                    item["condition"],
                    item["rewrite"],
                    item["restrict"],
                    item["name"],
                )

                if self.sketch.design_space.size and item["synthesize"]:
                    f = open("workspace/log/output.csv", "a")
                    f.write(
                        f"\n{self.sketch.sketch_path},Full incremental,{item['name']},{self.mem_size},")
                    f.close()
                    res = self.synthesize(self.sketch.design_space)
                    print("RESULT", res)
                    Graph().print(res, "workspace/log/" +
                                  self.sketch.sketch_path[25:-13].replace("/", "_") + "/incremental_" + str(self.mem_size), True)

            self.mem_size += 1
