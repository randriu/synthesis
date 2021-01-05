import logging
import operator

from collections import OrderedDict
from enum import Enum
from functools import reduce

import stormpy

from ..annotated_property import AnnotatedProperty
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
    def from_string(cls, input_str, regime):
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
            FamilyCheckMethod.regime = regime
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
    def __init__(self, check_prerequisites=False, engine=Engine.Sparse):
        self._check_prereq = check_prerequisites
        self.expression_manager = None
        self.holes = None
        self.hole_options = None
        self.sketch = None
        self.symmetries = None
        self.differents = None
        self.properties = None
        self._optimality_setting = None
        self._optimal_value = None
        self._optimal_assignment = None

        self.qualitative_properties = None
        self._engine = engine
        # keyword that is written to stats files to help restore stats correctly.
        self.stats_keyword = "genericfamilychecker-stats"

    def _load_properties_from_file(self, program, path, constant_str=""):
        """
        Loads a list with properties from a file. 

        :param path: File path 
        :param constant_str: Constants to substitute
        :return: None. Properties are now loaded.
        """
        logger.debug("Load properties from file.")
        properties = []
        with open(path) as file:
            for line in file:
                line = line.rstrip()
                if not line or line == "":
                    continue
                if line.startswith("//"):
                    continue
                properties.append(line)
        self._load_properties(program, properties, constant_str)

    def _load_properties(self, program, properties, constant_str=""):
        """
        Load properties to be checked via model checking

        :param properties:
        :return:
        """
        self.properties = []
        self.qualitative_properties = []

        for p in properties:
            # prop = self._load_property_for_sketch(p, constant_str)[0]
            for prop in stormpy.parse_properties_for_prism_program(p, program):
                # prop = prp.property
                assert prop.raw_formula.has_bound
                # print(prop.raw_formula)

                if True:  # prop.raw_formula.is_probability_operator
                    # and prop.raw_formula.threshold > 0 and prop.raw_formula.threshold < 1:
                    self.properties.append(prop)
        _constants_map = self._constants_map(constant_str, program)

    @staticmethod
    def _parse_template_defs(location):
        definitions = OrderedDict()
        with open(location) as file:
            for line in file:
                line = line.rstrip()
                if not line or line == "":
                    continue
                if line.startswith("#"):
                    continue

                entries = line.strip().split(";")
                definitions[entries[0]] = entries[1:]
        return definitions

    def _register_unconstrained_design_space(self, size):
        logger.info(f"Design space (without constraints): {size}")

    def load_template_definitions(self, location):
        """
        Load template definitions containing the possible values for the holes

        :param location:
        :return:
        """
        self.hole_options = HoleOptions()
        definitions = self._parse_template_defs(location)

        constants_map = dict()
        ordered_holes = list(self.holes.keys())
        for k in ordered_holes:
            v = definitions[k]

            ep = stormpy.storage.ExpressionParser(self.expression_manager)
            ep.set_identifier_mapping(dict())
            if len(v) == 1:

                constants_map[self.holes[k].expression_variable] = ep.parse(v[0])

                del self.holes[k]
            else:
                self.hole_options[k] = [ep.parse(x) for x in v]

        # Eliminate holes with just a single option.
        self.sketch = self.sketch.define_constants(constants_map).substitute_constants()
        assert self.hole_options.keys() == self.holes.keys()

        logger.debug(f"Template variables: {self.hole_options}")
        self._register_unconstrained_design_space(prod([len(v) for v in self.hole_options.values()]))

    def _constants_map(self, constant_str, program):
        logger.debug(f"Load constants '{constant_str}'")
        if constant_str.rstrip() == "":
            return dict()
        constants_map = dict()
        kvs = constant_str.split(",")
        ep = stormpy.storage.ExpressionParser(self.expression_manager)
        ep.set_identifier_mapping(dict())

        holes = dict()
        for c in program.constants:
            holes[c.name] = c

        for kv in kvs:
            key_value = kv.split("=")
            if len(key_value) != 2:
                raise ValueError(f"Expected Key-Value pair, got '{kv}'.")

            expr = ep.parse(key_value[1])
            constants_map[holes[key_value[0]].expression_variable] = expr
        return constants_map

    def _find_holes(self):
        """
        Find holes in the sketch.

        :return:
        """
        logger.debug("Search for holes in sketch...")
        self.holes = OrderedDict()
        for c in self.sketch.constants:
            if not c.defined:
                self.holes[c.name] = c

        logger.debug(f"Holes found: {list(self.holes.keys())}")

    def _annotate_properties(self, constants_map):
        self.properties = [
            AnnotatedProperty(
                stormpy.Property(f"property-{i}", p.raw_formula.clone().substitute(constants_map)),
                self.sketch, add_prerequisites=self._check_prereq
            ) for i, p in enumerate(self.properties)
        ]

    def _set_constants(self, constant_str):
        constants_map = self._constants_map(constant_str, self.sketch)
        self.sketch = self.sketch.define_constants(constants_map)

    def load_sketch(self, path, property_path, optimality_path=None, constant_str=""):
        logger.info(f"Load sketch from {path} with constants {constant_str}")

        prism_program = stormpy.parse_prism_program(path)
        self.expression_manager = prism_program.expression_manager
        self._load_properties_from_file(prism_program, property_path, constant_str)
        if optimality_path is not None:
            self._load_optimality(optimality_path, prism_program)
            all_properties = self.properties + [self._optimality_setting.criterion]
        else:
            all_properties = self.properties
        self.sketch, all_properties = prism_program.to_jani(all_properties)
        if optimality_path is not None:
            self.properties = all_properties[:-1]
            self._optimality_setting._criterion = all_properties[-1]
        else:
            self.properties = all_properties
        self._set_constants(constant_str)
        self._find_holes()
        constants_map = self._constants_map(constant_str, self.sketch)
        if self._optimality_setting is not None:
            self._optimality_setting._criterion = stormpy.Property(
                "optimality_property", self._optimality_setting._criterion.raw_formula.clone().substitute(constants_map)
            )
        self._annotate_properties(constants_map)

        assert self.expression_manager == self.sketch.expression_manager

    def load_restrictions(self, location):
        logger.debug("Load restrictions")
        mode = "none"
        symmetries = list()
        differents = list()
        with open(location) as file:
            for line in file:
                line = line.rstrip()
                if not line or line == "":
                    continue
                if line.startswith("#"):
                    continue
                if line.startswith("!symmetries"):
                    mode = "symmetries"
                    continue
                if line.startswith("!different"):
                    mode = "different"
                    continue
                if mode == "symmetries":
                    entries = line.strip().split(";")
                    for e in entries:
                        symmetries.append(e.strip().split(","))
                if mode == "different":
                    entries = line.strip().split(";")
                    for e in entries:
                        if e == "":
                            continue
                        differents.append(e.strip().split(","))
                else:
                    raise RuntimeError("Restriction file does not set appropriate mode")
        for symmetry in symmetries:
            for hole_name in symmetry:
                if hole_name not in self.holes:
                    raise ValueError(f"Key {hole_name} not in template, but in list of symmetries")
        for different in differents:
            for hole_name in different:
                if hole_name not in self.holes:
                    raise ValueError(f"Key {hole_name} not in template, but in list of differents")
        self.symmetries = symmetries
        self.differents = differents

    def _load_optimality(self, path, program):
        logger.debug("Loading optimality info.")
        direction = None
        epsilon = None
        with open(path) as file:
            for line in file:
                if line.startswith("//"):
                    continue
                if line.rstrip() == "min":
                    direction = "min"
                elif line.rstrip() == "max":
                    direction = "max"
                elif line.startswith("relative"):
                    epsilon = float(line.split()[1])
                else:
                    logger.debug(f"Criterion {line}")
                    optimality_criterion = stormpy.parse_properties_for_prism_program(line, program)[0]
        logger.debug("Done parsing optimality file.")
        if direction is None:
            raise ValueError("direction not set")
        if epsilon is None:
            raise ValueError("epsilon not set")
        if not optimality_criterion:
            raise ValueError("optimality criterion not set")

        self._optimality_setting = OptimalitySetting(optimality_criterion, direction, epsilon)
        # TODO: Cannot send math.inf to stormpy.Rational()
        self._optimal_value = 0.0 if direction == "max" else 999999999999999999

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
