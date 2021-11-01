import logging

import os
import re
import numpy
import uuid

import stormpy

from collections import OrderedDict
from .annotated_property import AnnotatedProperty
from .family_checkers.familychecker import HoleOptions

logger = logging.getLogger(__name__)


class Sketch:

    @classmethod
    def load_sketch(cls, sketch_path):
        # read lines
        with open(sketch_path) as f:
            sketch_lines = f.readlines()

        # strip hole definitions
        hole_re = re.compile(r'^hole\s+(.*?)\s+(.*?)\s+in\s+\{(.*?)\};$')
        sketch_output = []
        hole_definitions = OrderedDict()
        for line in sketch_lines:
            match = hole_re.search(line)
            if match is not None:
                hole_name = match.group(2)
                hole_definitions[hole_name] = match.group(3).replace(" ", "")
                line = f"const {match.group(1)} {hole_name};"
            sketch_output.append(line)

        # store stripped sketch to a temporary file
        tmp_path = sketch_path + str(uuid.uuid4())
        with open(tmp_path, 'w') as f:
            for line in sketch_output:
                print(line, end="", file=f)

        # parse temporary sketch
        program = stormpy.parse_prism_program(tmp_path)

        # delete temporary sketch
        os.remove(tmp_path)

        return program, hole_definitions

    @classmethod
    def parse_properties(cls, program, properites_path):
        # read lines
        lines = []
        with open(properites_path) as file:
            for line in file:
                line = line.replace(" ", "")
                if not line or line == "" or line.startswith("//"):
                    continue
                lines.append(line)

        # strip relative error
        lines_correct = []
        relative_error_re = re.compile(r'^(.*)\{(.*?)\}(=\?.*?$)')
        relative_error_str = None
        for line in lines:
            match = relative_error_re.search(line)
            if match is not None:
                relative_error_str = match.group(2)
                line = match.group(1) + match.group(3)
            lines_correct.append(line)
        optimality_epsilon = float(relative_error_str) if relative_error_str is not None else 0

        # parse all properties
        properties = []
        optimality_criterion = None
        for line in lines_correct:
            for prop in stormpy.parse_properties_for_prism_program(line, program):
                rf = prop.raw_formula
                assert rf.has_bound != rf.has_optimality_type, "optimizing formula contains a bounds or a comparison formula does not"
                if rf.has_bound:
                    # comparison formula
                    properties.append(prop)
                else:
                    # optimality formula
                    assert optimality_criterion is None, "two optimality formulae specified"
                    optimality_criterion = prop

        return properties, optimality_criterion, optimality_epsilon

    @classmethod
    def constants_map(cls, program, jani, constant_str):
        if constant_str.rstrip() == "":
            return dict()
        constants_map = dict()
        kvs = constant_str.split(",")
        ep = stormpy.storage.ExpressionParser(program.expression_manager)
        ep.set_identifier_mapping(dict())

        holes = dict()
        for c in jani.constants:
            holes[c.name] = c

        for kv in kvs:
            key_value = kv.split("=")
            if len(key_value) != 2:
                raise ValueError(f"Expected Key-Value pair, got '{kv}'.")

            expr = ep.parse(key_value[1])
            constants_map[holes[key_value[0]].expression_variable] = expr
        return constants_map

    @classmethod
    def construct_jani(cls, program, properties, optimality_criterion, constant_str):
        all_properties = properties
        if optimality_criterion is not None:
            all_properties = properties + [optimality_criterion]
        jani, all_properties = program.to_jani(all_properties)
        properties = all_properties
        if optimality_criterion is not None:
            properties = all_properties[:-1]
            optimality_criterion = all_properties[-1]
        constants_map = cls.constants_map(program, jani, constant_str)
        jani = jani.define_constants(constants_map)
        return jani, properties, optimality_criterion

    @classmethod
    def annotate_properties(cls, program, jani, constant_str, properties, optimality_criterion):
        constants_map = cls.constants_map(program, jani, constant_str)
        properties = [
            AnnotatedProperty(
                stormpy.Property(f"property-{i}", p.raw_formula.clone().substitute(constants_map)),
                jani, add_prerequisites=False  # FIXME: check prerequisites?
            ) for i, p in enumerate(properties)
        ]
        if optimality_criterion is not None:
            optimality_criterion = stormpy.Property(
                "optimality_property", optimality_criterion.raw_formula.clone().substitute(constants_map)
            )
        return properties, optimality_criterion

    @classmethod
    def parse_hole_definitions(cls, program, hole_definitions, jani):

        # identify undefined constants
        constants = OrderedDict()
        for c in jani.constants:
            if not c.defined:
                constants[c.name] = c

        # ensure that all undefined constants are indeed holes
        assert len(constants) == len(hole_definitions.keys()), "most likely some constants were unspecified"

        # parse allowed options
        definitions = OrderedDict()
        for hole, definition in hole_definitions.items():
            definitions[hole] = definition.split(",")

        hole_options = HoleOptions()
        constants_map = dict()
        ordered_holes = list(constants.keys())
        for k in ordered_holes:
            v = definitions[k]
            ep = stormpy.storage.ExpressionParser(program.expression_manager)
            ep.set_identifier_mapping(dict())
            if len(v) == 1:
                constants_map[constants[k].expression_variable] = ep.parse(v[0])
                del constants[k]
            else:
                hole_options[k] = [ep.parse(x) for x in v]

        # Eliminate holes with just a single option.
        jani = jani.define_constants(constants_map).substitute_constants()
        assert hole_options.keys() == constants.keys()

        return jani, constants, hole_options

    def __init__(self, sketch_path, properties_path, constant_str):
        logger.info(f"Loading sketch from {sketch_path} with constants {constant_str}")
        self.program, hole_definitions = self.load_sketch(sketch_path)

        logger.info(f"Loading properties from {properties_path} with constants {constant_str}")
        properties, optimality_criterion, self.optimality_epsilon = self.parse_properties(
            self.program, properties_path)

        logger.debug("Constructing JANI program...")
        jani, properties, optimality_criterion = self.construct_jani(
            self.program, properties, optimality_criterion, constant_str)
        assert self.program.expression_manager == jani.expression_manager  # sanity check

        logger.debug("Annotating properties ...")
        self.properties, self.optimality_criterion = self.annotate_properties(
            self.program, jani, constant_str, properties, optimality_criterion)

        logger.debug("Parsing hole definitions ...")
        self.jani, self.holes, self.hole_options = self.parse_hole_definitions(self.program, hole_definitions, jani)
        logger.debug(f"Sketch has {len(self.hole_options.keys())} holes: {list(self.hole_options.keys())}")

        logger.debug(f"Template variables: {self.hole_options}")
        design_space = numpy.prod([len(v) for v in self.hole_options.values()])
        logger.info(f"Design space (without constraints): {design_space}")
