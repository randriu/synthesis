
import stormpy
from .annotated_property import AnnotatedProperty
from .synthesizers.synthesizer import Formula

import os
import re
import numpy
import uuid
import itertools
from collections import OrderedDict

import logging
logger = logging.getLogger(__name__)

class DesignSpace(OrderedDict):
    """ Mapping of hole names to hole options. """
    
    @property
    def holes(self):
        return self.keys()

    @property
    def hole_count(self):
        return len(self.holes)

    @property
    def size(self):
        return numpy.prod([len(v) for v in self.values()])

    def all_assignments(self):
        return itertools.product(*self.values())

    def __str__(self):
        return ",".join([f"{k}: [{','.join([str(x) for x in v])}]" for k, v in self.items()])

    def __repr__(self):
        return self.__str__()

    def readable_assignment(self,assignment):
        return ",".join([f"{hole}={assignment[index]}" for index,hole in enumerate(self.holes)])

    

class Sketch:
    
    def __init__(self, sketch_path, properties_path, constant_str):
        self.program = None
        self.jani = None
        self.design_space = None
        self.properties = None
        self.optimality_formula = None

        logger.info(f"Loading sketch from {sketch_path} with constants {constant_str}")
        self.program, design_space = self.load_sketch(sketch_path)

        logger.info(f"Loading properties from {properties_path} with constants {constant_str}")
        properties, optimality_property, optimality_epsilon = self.parse_properties(
            self.program, properties_path)

        logger.debug("Constructing JANI program...")
        jani, properties, optimality_property = self.construct_jani(
            self.program, properties, optimality_property, constant_str)
        assert self.program.expression_manager == jani.expression_manager  # sanity check

        logger.debug("Annotating properties ...")
        self.formulae, self.optimality_formula = self.annotate_properties(
            self.program, jani, constant_str, properties, optimality_property, optimality_epsilon)

        logger.debug("Parsing hole definitions ...")
        self.jani, self.design_space = self.parse_hole_definitions(self.program, jani, design_space)

        logger.debug(f"Sketch has {len(self.design_space.keys())} holes: {list(self.design_space.keys())}")
        logger.debug(f"Hole options: {self.design_space}")
        logger.info(f"Design space: {self.design_space.size}")

        

    
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

        # try to parse temporary sketch and then delete it
        parse_error = False
        try:
            program = stormpy.parse_prism_program(tmp_path)
        except:
            parse_error = True
        os.remove(tmp_path)
        if parse_error:
            exit()

        # parse hole definitions
        design_space = DesignSpace()
        for hole, definition in hole_definitions.items():
            options = definition.split(",")
            ep = stormpy.storage.ExpressionParser(program.expression_manager)
            ep.set_identifier_mapping(dict())
            design_space[hole] = [ep.parse(o) for o in options]

        # success
        return program, design_space

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
        optimality_property = None
        for line in lines_correct:
            for prop in stormpy.parse_properties_for_prism_program(line, program):
                rf = prop.raw_formula
                assert rf.has_bound != rf.has_optimality_type, "optimizing formula contains a bounds or a comparison formula does not"
                if rf.has_bound:
                    # comparison formula
                    properties.append(prop)
                else:
                    # optimality formula
                    assert optimality_property is None, "two optimality formulae specified"
                    optimality_property = prop

        return properties, optimality_property, optimality_epsilon

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
    def construct_jani(cls, program, properties, optimality_property, constant_str):
        all_properties = properties
        if optimality_property is not None:
            all_properties = properties + [optimality_property]
        jani, all_properties = program.to_jani(all_properties)
        properties = all_properties
        if optimality_property is not None:
            properties = all_properties[:-1]
            optimality_property = all_properties[-1]
        constants_map = cls.constants_map(program, jani, constant_str)
        jani = jani.define_constants(constants_map)
        return jani, properties, optimality_property

    @classmethod
    def annotate_properties(cls, program, jani, constant_str, properties, optimality_property, optimality_epsilon):
        constants_map = cls.constants_map(program, jani, constant_str)
        properties = [
            AnnotatedProperty(
                stormpy.Property(f"property-{i}", p.raw_formula.clone().substitute(constants_map)),
                jani, add_prerequisites=False  # FIXME: check prerequisites?
            ) for i, p in enumerate(properties)
        ]
        if optimality_property is not None:
            optimality_property = stormpy.Property(
                "optimality_property", optimality_property.raw_formula.clone().substitute(constants_map)
            )

        formulae = [Formula(p) for p in properties]
        optimality_formula = Formula(optimality_property,optimality_epsilon) if optimality_property is not None else None
        return formulae, optimality_formula

    @classmethod
    def parse_hole_definitions(cls, program, jani, design_space):

        # collect undefined constants
        constants = OrderedDict([(c.name, c) for c in jani.constants if not c.defined])
        # ensure that all undefined constants are indeed holes
        assert len(constants) == len(design_space.keys()), "some constants were unspecified"

        # convert single-valued holes to a defined constant
        constant_definitions = dict()
        for hole,options in design_space.items():
            if len(options) == 1:
                constant_definitions[constants[hole].expression_variable] = options[0]
                del design_space[hole]

        jani = jani.define_constants(constant_definitions).substitute_constants()

        return jani, design_space
