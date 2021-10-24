import stormpy
from .property import Property
from .holes import HoleOptions, DesignSpace

import os
import re
import uuid
import itertools
from collections import OrderedDict

import logging
logger = logging.getLogger(__name__)


class Sketch:
    
    def __init__(self, sketch_path, properties_path, constant_str):
        self.constant_str = constant_str
        self.properties = None
        self.optimality_property = None
        self.design_space = None
        self.pomdp_memory_size = 2 # FIXME as a CLI argument

        self.prism = None
        self.jani = None

        logger.info(f"Loading sketch from {sketch_path} with constants {constant_str} ...")
        self.prism, hole_options = Sketch.load_sketch(sketch_path, constant_str)

        logger.info(f"Loading properties from {properties_path} with constants {constant_str} ...")
        self.properties, self.optimality_property = Sketch.parse_properties(self.prism, properties_path, constant_str)
        
        self.design_space = DesignSpace(hole_options, self.properties)

        logger.debug(f"Sketch has {self.design_space.hole_count} holes: {self.design_space.holes}")
        logger.debug(f"Hole options: {self.design_space}")
        logger.info(f"Design space: {self.design_space.size}")


    @classmethod
    def constants_map(cls, prism, constant_str):
        constant_str = constant_str.replace(" ", "")
        if constant_str == "":
            return dict()
        constants_map = dict()
        kvs = constant_str.split(",")
        ep = stormpy.storage.ExpressionParser(prism.expression_manager)
        ep.set_identifier_mapping(dict())

        holes = {c.name:c for c in prism.constants}

        for kv in kvs:
            key_value = kv.split("=")
            if len(key_value) != 2:
                raise ValueError(f"Expected key=value pair, got '{kv}'.")

            expr = ep.parse(key_value[1])
            constants_map[holes[key_value[0]].expression_variable] = expr
        return constants_map
    

    @classmethod
    def load_sketch(cls, sketch_path, constant_str):
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
            prism = stormpy.parse_prism_program(tmp_path)
        except:
            parse_error = True
        os.remove(tmp_path)
        if parse_error:
            exit()

        # substitute constants
        prism = prism.define_constants(cls.constants_map(prism,constant_str))

        # parse hole definitions
        hole_options = HoleOptions()
        ep = stormpy.storage.ExpressionParser(prism.expression_manager)
        ep.set_identifier_mapping(dict())    
        for hole, definition in hole_definitions.items():
            options = definition.split(",")
            hole_options[hole] = [ep.parse(o) for o in options]

        # collect undefined constants (must be the holes)
        program_constants = OrderedDict([(c.name, c) for c in prism.constants if not c.defined])
        assert len(program_constants.keys()) == hole_options.hole_count, "some constants were unspecified"

        # convert single-valued holes to a defined constant
        constant_definitions = dict()
        holes_to_remove = []
        for hole,options in hole_options.items():
            if len(options) == 1:
                constant_definitions[program_constants[hole].expression_variable] = options[0]
                holes_to_remove.append(hole)
        
        for hole in holes_to_remove:
            del hole_options[hole]

        # define constants in the program
        prism = prism.define_constants(constant_definitions)
        prism = prism.substitute_constants()

        # success
        return prism, hole_options

 
    @classmethod
    def parse_properties(cls, prism, properites_path, constant_str):
        # read lines
        lines = []
        with open(properites_path) as file:
            for line in file:
                line = line.replace(" ", "")
                line = line.replace("\n", "")
                if not line or line == "" or line.startswith("//"):
                    continue
                lines.append(line)

        # strip relative error
        lines_properties = ""
        relative_error_re = re.compile(r'^(.*)\{(.*?)\}(=\?.*?$)')
        relative_error_str = None
        for line in lines:
            match = relative_error_re.search(line)
            if match is not None:
                relative_error_str = match.group(2)
                line = match.group(1) + match.group(3)
            lines_properties += line + ";"
        optimality_epsilon = float(relative_error_str) if relative_error_str is not None else 0

        # parse all properties
        properties = []
        optimality_property = None
        for prop in stormpy.parse_properties_for_prism_program(lines_properties, prism):
            rf = prop.raw_formula
            assert rf.has_bound != rf.has_optimality_type, "optimizing formula contains a bound or a comparison formula does not"
            if rf.has_bound:
                # comparison formula
                properties.append(prop)
            else:
                # optimality formula
                assert optimality_property is None, "two optimality formulae specified"
                optimality_property = prop

        # substitute constants in properties
        constants_map = cls.constants_map(prism, constant_str)
        for p in properties:
            p.raw_formula.substitute(constants_map)
        if optimality_property is not None:
            optimality_property.raw_formula.substitute(constants_map)

        # wrap properties
        properties = [Property(p) for p in properties]
        if optimality_property is not None:
            optimality_property = Property(optimality_property, optimality_epsilon)

        return properties, optimality_property

    def restrict(self, assignment):
        program_constants = OrderedDict([(c.name, c.expression_variable) for c in self.prism.constants if not c.defined])
        substitution = {program_constants[hole]:assignment[hole][0] for hole in assignment.keys()}
        program = self.prism.define_constants(substitution)
        return program

    @property
    def is_pomdp(self):
        return self.prism.model_type == stormpy.storage.PrismModelType.POMDP


    