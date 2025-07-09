import z3

import logging
import os
logger = logging.getLogger(__name__)


class CostsConstraint():

    costs_threshold = 0
    model_folder : str

    COSTS_FILE = "sketch.costs"

    def __init__(self):
        pass

    def build_constraint(
        self,
        variables,
        quotient
    ):
        # We build the quotient here

        assertions = []
        
        lines = None
        costs_path = os.path.join(self.model_folder, self.COSTS_FILE)
        with open(costs_path, "r") as f:
            lines = f.readlines()

        cost_vars = []
        line_index = 0
        for hole in range(quotient.family.num_holes):
            for option in range(quotient.family.hole_num_options(hole)):
                hole_name = quotient.family.hole_name(hole)
                cost_var = z3.Int(f"cost_{hole_name}_{option}")
                cost_vars.append(cost_var)
                line = lines[line_index].strip()
                line_index += 1
                line_hole, line_option, cost_value = line.split()
                assert line_hole == hole_name, f"Expected hole {hole_name}, got {line_hole}"
                assert int(line_option) == option, f"Expected option {option}, got {line_option}"

                assertions.append(
                    z3.If(
                        variables[hole] == option,
                        cost_var == int(cost_value),
                        cost_var == 0
                    )
                )

        # Add constraint: sum of cost_vars <= costs_threshold
        assertions.append(z3.Sum(cost_vars) <= self.costs_threshold)
        return assertions
        