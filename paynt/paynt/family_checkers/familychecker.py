import logging
import operator
import json

from collections import OrderedDict
from enum import Enum
from functools import reduce

import stormpy

from ..jani.quotient_container import Engine

logger = logging.getLogger(__name__)


def prod(iterable):
    return reduce(operator.mul, iterable, 1)


class FamilyCheckMethod(Enum):
    """
    Enum to select the type of algorithm to use.
    """
    Lifting = 0,
    SchedulerIteration = 1,
    DtmcIteration = 2,
    AllInOne = 3,
    Hybrid = 5,
    CEGIS = 4

    @classmethod
    def from_string(cls, input_str):
        """
        Construct enum from string. 

        :param input_str: either of [cegar, cschedenum, onebyone, allinone, smt, cegis]
        :return: the corresponding enum, or None
        """
        if input_str == "cegar":
            # return cls.Lifting
            FamilyCheckMethod.regime = 2  # CEGARChecker
            return cls.Hybrid
        elif input_str == "cschedenum":
            return cls.SchedulerIteration
        elif input_str == "onebyone":
            # return cls.DtmcIteration
            FamilyCheckMethod.regime = 0  # EnumerationChecker
            return cls.Hybrid
        elif input_str == "allinone":
            return cls.AllInOne
        elif input_str == "cegis":
            # return cls.CEGIS
            FamilyCheckMethod.regime = 1  # CEGISChecker
            return cls.Hybrid
        elif input_str == "hybrid":
            FamilyCheckMethod.regime = 3
            return cls.Hybrid
        else:
            return None


class OptimalitySetting:
    def __init__(self, criterion, direction, epsilon):
        self._criterion = criterion
        assert direction in ["min", "max"]
        self._direction = direction
        self._eps = epsilon

    def __str__(self):
        return f"formula: {self._criterion.raw_formula}; direction: {self._direction}; eps: {self._eps}"

    @property
    def criterion(self):
        return self._criterion

    @property
    def direction(self):
        return self._direction

    def is_improvement(self, mc_result, best_so_far):
        if best_so_far is None:
            return True
        if self._direction == "min":
            return mc_result < best_so_far
        if self._direction == "max":
            return mc_result > best_so_far

    def get_violation_property(self, best_so_far, bound_translator):
        vp = stormpy.Property(
            "optimality_violation",
            self._criterion.raw_formula.clone(),
            comment="Optimality criterion with adapted bound"
        )
        if self._direction == "min":
            bound = best_so_far - best_so_far * self._eps
            ct = stormpy.logic.ComparisonType.LESS
        else:
            bound = best_so_far + best_so_far * self._eps
            ct = stormpy.logic.ComparisonType.GREATER
        bound = bound_translator(bound)
        vp.raw_formula.set_bound(ct, bound)
        return vp


def open_constants(model):
    return OrderedDict([(c.name, c) for c in model.constants if not c.defined])


class HoleOptions(OrderedDict):

    def __str__(self):
        return "HoleOptions {}".format(",".join([f"{k}: [{','.join([str(x) for x in v])}]" for k, v in self.items()]))

    def __repr__(self):
        return self.__str__()

    def size(self):
        return prod([len(v) for v in self.values()])

    def index_map(self, sub_options):
        result = OrderedDict()
        for k, values in sub_options.items():
            result[k] = []
            for v in values:
                for index, ref in enumerate(self.get(k)):
                    if ref == v:
                        result[k].append(index)
        return result

    def pick_one_in_family(self):
        result = dict()
        for k, v in self.items():
            result[k] = v[0]
        return result


class RoundStats:
    def __init__(self, round_var, queued, above, below, time):
        self.round = round_var
        self.queued = queued
        self.cumulative_above = above
        self.cumulative_below = below
        self.cumulative_time = time


class FamilyChecker:
    def __init__(self, sketch):
        self._check_prereq = False # FIXME: specify behaviour for <=0 and >=1 properties
        self.expression_manager = sketch.program.expression_manager
        
        self.sketch = sketch.jani

        self.holes = sketch.holes
        self.hole_options = sketch.hole_options
        self.symmetries = None
        self.differents = None

        self.properties = sketch.properties

        self._optimality_setting = None
        self._optimal_value = None
        if sketch.optimality_criterion is not None:
            optimality_direction = None
            opt_type = sketch.optimality_criterion.raw_formula.optimality_type
            if opt_type == stormpy.OptimizationDirection.Minimize:
                optimality_direction = "min"
                self._optimal_value = 999999999999999999
            else:
                optimality_direction = "max"
                self._optimal_value = 0.0
            self._optimality_setting = OptimalitySetting(sketch.optimality_criterion, optimality_direction, sketch.optimality_epsilon)
            self._optimal_assignment = None

        self.qualitative_properties = None
        self._engine = Engine.Sparse # FIXME: dd engine
        self.stats_keyword = "genericfamilychecker-stats" # ?

    def input_has_multiple_properties(self):
        if self._optimality_setting is not None:
            return len(self.properties) > 0
        return len(self.properties) > 1

    def input_has_optimality_property(self):
        return self._optimality_setting is not None

    def input_has_restrictions(self):
        return self._input_has_differents() or self._input_has_symmetries()

    def _input_has_symmetries(self):
        return self.symmetries is not None and len(self.symmetries) > 0

    def _input_has_differents(self):
        return self.differents is not None and len(self.differents) > 0

    def holes_as_string(self):
        return ",".join([name for name in self.holes])

    def initialise(self):
        pass

    def print_stats(self):
        pass

    def run_feasibility(self):
        raise RuntimeError("This method should be overridden")

    def run_partitioning(self):
        raise RuntimeError("This method should be overridden")

    def store_in_statistics(self):
        return []
