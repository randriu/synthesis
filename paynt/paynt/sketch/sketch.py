import stormpy

from .pomdp_parser import PomdpParser
from .property import Property, OptimalityProperty, Specification
from .holes import Hole, Holes, DesignSpace
from ..synthesizers.models import MarkovChain
from ..synthesizers.quotient import *
from ..synthesizers.quotient_pomdp import *
from ..profiler import Profiler

from collections import defaultdict

import os
import re
import uuid

import logging

class Sketch:

    # if True, unfolded JANI is exported and the program is aborted
    export_jani = False
    # if True, POMDP is exported to *.pomdp and the program is aborted
    export_pomdp = False
    # if True, the sketch is assumed to be a hole-free MDP
    hyperproperty_synthesis = False

    def __init__(self, sketch_path, properties_path, constant_str):

        Profiler.initialize()
        Profiler.start("sketch")
        
        self.explicit_model = None
        self.prism = None
        self.hole_expressions = None

        self.design_space = None
        self.specification = None
        self.quotient = None

        constant_map = None
        expression_parser = None

        logger.info(f"Loading sketch from {sketch_path}...")
        logger.info(f"Attempting to parse model as a POMDP in explicit format ...")
        self.explicit_model = PomdpParser.read_pomdp_model(sketch_path)

        if self.is_explicit:
            logger.info(f"Successfully parsed model in explicit format.")
            self.design_space = DesignSpace()
        else:
            logger.info(f"Assuming a sketch in a PRISM format ...")
            self.prism, hole_definitions = Sketch.load_sketch(sketch_path)

            expression_parser = stormpy.storage.ExpressionParser(self.prism.expression_manager)
            expression_parser.set_identifier_mapping(dict())

            if constant_str != '':
                logger.info(f"Assuming constant definitions: '{constant_str}' ...")
                constant_map = Sketch.map_constants(self.prism, expression_parser, constant_str)
                self.prism = self.prism.define_constants(constant_map)
                self.prism = self.prism.substitute_constants()

            if len(hole_definitions) == 0:
                logger.info("Sketch does not contain any hole definitions.")
                self.design_space = DesignSpace()
            else:
                logger.info("Processing hole definitions ...")
                self.prism, self.hole_expressions, self.design_space = Sketch.parse_holes(self.prism, expression_parser, hole_definitions)
                
                logger.info(f"Sketch has {self.design_space.num_holes} holes")
                # logger.info(f"Listing hole domains: {holes}"
                logger.info(f"Design space size: {self.design_space.size}")

        logger.info(f"Loading properties from {properties_path} ...")
        self.specification = Sketch.parse_specification(self.prism, constant_map, properties_path)
        logger.info(f"Found the following specification: {self.specification}")
        self.design_space.property_indices = self.specification.all_constraint_indices()
        MarkovChain.initialize(self.specification.stormpy_formulae())
        
        logger.info(f"Initializing the quotient ...")

        if self.is_dtmc:
            self.quotient = DTMCQuotientContainer(self)
        elif self.is_ma:
            self.quotient = MAQuotientContainer(self)
        elif self.is_mdp:
            if Sketch.hyperproperty_synthesis:
                self.quotient = HyperPropertyQuotientContainer(self)
            else:
                self.quotient = MDPQuotientContainer(self)
        elif self.is_pomdp:
            self.quotient = POMDPQuotientContainer(self)
            self.quotient.pomdp_manager.set_memory_size(POMDPQuotientContainer.pomdp_memory_size)
            self.quotient.unfold_memory()
            if Sketch.export_pomdp:
                PomdpParser.write_model_in_pomdp_solve_format(sketch_path, self.quotient)
                exit()
        else:
            raise TypeError("sketch type is not supported")

        logger.info(f"Sketch parsing complete.")
        Profiler.stop()


    @property
    def is_explicit(self):
        return self.explicit_model is not None

    @property
    def is_dtmc(self):
        return not self.is_explicit and self.prism.model_type == stormpy.storage.PrismModelType.DTMC
    
    @property
    def is_ctmc(self):
        return not self.is_explicit and self.prism.model_type == stormpy.storage.PrismModelType.CTMC

    @property
    def is_ma(self):
        return not self.is_explicit and self.prism.model_type == stormpy.storage.PrismModelType.MA

    @property
    def is_mdp(self):
        return not self.is_explicit and self.prism.model_type == stormpy.storage.PrismModelType.MDP

    @property
    def is_pomdp(self):
        if self.is_explicit:
            return self.explicit_model.is_nondeterministic_model and self.explicit_model.is_partially_observable
        else:
            return self.prism.model_type == stormpy.storage.PrismModelType.POMDP

    @classmethod
    def load_sketch(cls, sketch_path):
        # read lines
        with open(sketch_path) as f:
            sketch_lines = f.readlines()

        # replace hole definitions with constants
        hole_re = re.compile(r'^hole\s+(.*?)\s+(.*?)\s+in\s+\{(.*?)\};$')
        sketch_output = []
        hole_definitions = {}
        for line in sketch_lines:
            match = hole_re.search(line)
            if match is not None:
                hole_type = match.group(1)
                hole_name = match.group(2)
                hole_options = match.group(3).replace(" ", "")
                hole_definitions[hole_name] = hole_options
                line = f"const {hole_type} {hole_name};"
            sketch_output.append(line)

        # store modified sketch to a temporary file
        tmp_path = sketch_path + str(uuid.uuid4())
        with open(tmp_path, 'w') as f:
            for line in sketch_output:
                print(line, end="", file=f)

        # try to parse temporary sketch and then delete it
        try:
            prism = stormpy.parse_prism_program(tmp_path, prism_compat=True)
            os.remove(tmp_path)
        except:
            os.remove(tmp_path)

        return prism, hole_definitions

 
    @classmethod
    def map_constants(cls, prism, expression_parser, constant_str):
        constant_str = constant_str.replace(" ", "")
        if constant_str == "":
            return dict()
        
        constant_map = dict()
        constant_definitions = constant_str.split(",")
        prism_constants = {c.name:c for c in prism.constants}

        for constant_definition in constant_definitions:
            key_value = constant_definition.split("=")
            if len(key_value) != 2:
                raise ValueError(f"Expected key=value pair, got '{constant_definition}'.")

            expr = expression_parser.parse(key_value[1])
            name = key_value[0]
            constant = prism_constants[name].expression_variable
            constant_map[constant] = expr
        return constant_map


    @classmethod
    def parse_holes(cls, prism, expression_parser, hole_definitions):

        # parse hole definitions
        holes = Holes()
        hole_expressions = []
        for hole_name,definition in hole_definitions.items():
            options = definition.split(",")
            expressions = [expression_parser.parse(o) for o in options]
            hole_expressions.append(expressions)

            options = list(range(len(expressions)))
            option_labels = [str(e) for e in expressions]
            hole = Hole(hole_name, options, option_labels)
            holes.append(hole)

        # check that all undefined constants are indeed the holes
        undefined_constants = [c for c in prism.constants if not c.defined]
        assert len(undefined_constants) == len(holes), "some constants were unspecified"

        # convert single-valued holes to a defined constant
        trivial_holes_definitions = {}
        nontrivial_holes = Holes()
        nontrivial_hole_expressions = []
        for hole_index,hole in enumerate(holes):
            if hole.size == 1:
                trivial_holes_definitions[prism.get_constant(hole.name).expression_variable] = hole_expressions[hole_index][0]
            else:
                nontrivial_holes.append(hole)
                nontrivial_hole_expressions.append(hole_expressions[hole_index])
        holes = nontrivial_holes
        hole_expressions = nontrivial_hole_expressions

        # substitute trivial holes
        prism = prism.define_constants(trivial_holes_definitions)
        prism = prism.substitute_constants()
    
        design_space = DesignSpace(holes)

        return prism, hole_expressions, design_space

 
    @classmethod
    def parse_specification(cls, prism, constant_map, properites_path):
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

        if prism is not None:
            props = stormpy.parse_properties_for_prism_program(lines_properties, prism)
        else:
            props = stormpy.parse_properties_without_context(lines_properties)
        for prop in props:
            rf = prop.raw_formula
            assert rf.has_bound != rf.has_optimality_type, "optimizing formula contains a bound or a comparison formula does not"
            if rf.has_bound:
                # comparison formula
                properties.append(prop)
            else:
                # optimality formula
                assert optimality_property is None, "two optimality formulae specified"
                optimality_property = prop

        if constant_map is not None:
            # substitute constants in properties
            for p in properties:
                p.raw_formula.substitute(constant_map)
            if optimality_property is not None:
                optimality_property.raw_formula.substitute(constant_map)

        # wrap properties
        properties = [Property(p) for p in properties]
        if optimality_property is not None:
            optimality_property = OptimalityProperty(optimality_property, optimality_epsilon)

        specification = Specification(properties,optimality_property)
        return specification
    

    def restrict_prism(self, assignment):
        assert assignment.size == 1
        substitution = {}
        for hole_index,hole in enumerate(assignment):
            ev = self.prism.get_constant(hole.name).expression_variable
            expr = self.hole_expressions[hole_index][hole.options[0]]
            substitution[ev] = expr
        program = self.prism.define_constants(substitution)
        model = stormpy.build_sparse_model_with_options(program, MarkovChain.builder_options)
        return model

    
    