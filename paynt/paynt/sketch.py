import logging

import re
import numpy

import stormpy

from collections import OrderedDict
from .annotated_property import AnnotatedProperty
from .family_checkers.familychecker import HoleOptions

logger = logging.getLogger(__name__)

class Sketch():

    @classmethod
    def parse_properties(cls, program, properites_path):
        # read lines
        lines = []
        with open(properites_path) as file:
            for line in file:
                line = line.replace(" ","")
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
    def identify_holes(cls, jani):
        holes = OrderedDict()
        for c in jani.constants:
            if not c.defined:
                holes[c.name] = c
        return holes
    
    @classmethod
    def annotate_properties(cls, program, jani, constant_str, properties, optimality_criterion):
        constants_map = cls.constants_map(program, jani, constant_str)
        properties = [
            AnnotatedProperty(
                stormpy.Property(f"property-{i}", p.raw_formula.clone().substitute(constants_map)),
                jani, add_prerequisites=False #FIXME: check prerequisites?
            ) for i, p in enumerate(properties)
            ]
        if optimality_criterion is not None:
            optimality_criterion = stormpy.Property(
                "optimality_property", optimality_criterion.raw_formula.clone().substitute(constants_map)
            )
        return properties, optimality_criterion

    @classmethod
    def load_template_definitions(cls, allowed_path, program, jani, holes):
        hole_options = HoleOptions()

        # parse allowed options
        definitions = OrderedDict()
        with open(allowed_path) as file:
            for line in file:
                line = line.rstrip()
                if not line or line == "":
                    continue
                if line.startswith("#"):
                    continue
                entries = line.strip().split(";")
                definitions[entries[0]] = entries[1:]

        constants_map = dict()
        ordered_holes = list(holes.keys())
        for k in ordered_holes:
            v = definitions[k]
            ep = stormpy.storage.ExpressionParser(program.expression_manager)
            ep.set_identifier_mapping(dict())
            if len(v) == 1:
                constants_map[holes[k].expression_variable] = ep.parse(v[0])
                del holes[k]
            else:
                hole_options[k] = [ep.parse(x) for x in v]

        # Eliminate holes with just a single option.
        jani = jani.define_constants(constants_map).substitute_constants()
        assert hole_options.keys() == holes.keys()

        logger.debug(f"Template variables: {hole_options}")
        design_space = numpy.prod([len(v) for v in hole_options.values()])
        logger.info(f"Design space (without constraints): {design_space}")

        return jani, hole_options

    def __init__(self, sketch_path, allowed_path, properties_path, constant_str):
        logger.info(f"Loading sketch from {sketch_path} with constants {constant_str}")
        self.program = stormpy.parse_prism_program(sketch_path)
        
        logger.info(f"Loading properties from {properties_path} with constants {constant_str}")
        self.properties, self.optimality_criterion, self.optimality_epsilon = self.parse_properties(self.program, properties_path)

        logger.debug("Constructing JANI program...")
        self.jani, self.properties, self.optimality_criterion = self.construct_jani(
            self.program, self.properties, self.optimality_criterion, constant_str)
        assert self.program.expression_manager == self.jani.expression_manager # sanity check

        logger.debug("Searching for holes in sketch ...")
        self.holes = self.identify_holes(self.jani)
        logger.debug(f"Holes found: {list(self.holes.keys())}")

        logger.debug("Annotating properties ...")
        self.properties, self.optimality_criterion = self.annotate_properties(
            self.program, self.jani, constant_str, self.properties, self.optimality_criterion)
        logger.info(f"Loading hole options from {allowed_path}")
        self.jani, self.hole_options = self.load_template_definitions(allowed_path, self.program, self.jani, self.holes)

