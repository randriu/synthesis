import stormpy
import stormpy.synthesis

from .jani import JaniUnfolder
from ..quotient.holes import Hole, Holes, DesignSpace
from ..quotient.models import MarkovChain
from ..quotient.coloring import MdpColoring

from paynt.verification.property import *

import os
import re
import uuid

import logging
logger = logging.getLogger(__name__)


class PrismParser:

    @classmethod
    def read_prism(cls, sketch_path, properties_path, relative_error, discount_factor):

        # parse the program
        prism, hole_definitions = PrismParser.load_sketch_prism(sketch_path)
        expression_parser = stormpy.storage.ExpressionParser(prism.expression_manager)
        expression_parser.set_identifier_mapping(dict())
        logger.debug("PRISM model type: " + str(prism.model_type))

        # parse constants
        constant_map = None

        # parse hole definitions
        hole_expressions = None
        holes = None
        if len(hole_definitions) > 0:
            logger.info("processing hole definitions...")
            prism, hole_expressions, holes = PrismParser.parse_holes(
                prism, expression_parser, hole_definitions)

        specification = PrismParser.parse_specification(properties_path, relative_error, discount_factor, prism)

        # construct the quotient
        coloring = None
        jani_unfolder = None
        obs_evaluator = None
        if holes is not None:
            assert prism.model_type in {stormpy.storage.PrismModelType.DTMC,stormpy.storage.PrismModelType.POMDP},\
                "hole detected, but the program is neither DTMC nor POMDP"
            # unfold hole options via Jani
            jani_unfolder = JaniUnfolder(prism, hole_expressions, specification, holes)
            specification = jani_unfolder.specification
            quotient_mdp = jani_unfolder.quotient_mdp
            coloring = MdpColoring(quotient_mdp, holes, jani_unfolder.action_to_hole_options)
            MarkovChain.initialize(specification)
            if prism.model_type == stormpy.storage.PrismModelType.POMDP:
                obs_evaluator = stormpy.synthesis.ObservationEvaluator(prism, quotient_mdp)
        else:
            MarkovChain.initialize(specification)
            quotient_mdp = MarkovChain.from_prism(prism)

        return quotient_mdp, specification, coloring, jani_unfolder, obs_evaluator

    
    @classmethod
    def load_sketch_prism(cls, sketch_path):
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
                line = f"const {hole_type} {hole_name};\n"
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
            raise SyntaxError

        return prism, hole_definitions


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

        return prism, hole_expressions, holes

 
    @classmethod
    def parse_specification(cls, properties_path, relative_error, discount_factor, prism = None):

        if not os.path.isfile(properties_path):
            raise ValueError(f"the properties file {properties_path} does not exist")
        logger.info(f"loading properties from {properties_path} ...")
        lines = ""
        with open(properties_path) as file:
            for line in file:
                lines += line + ";"
        if prism is not None:
            props = stormpy.parse_properties_for_prism_program(lines, prism)
        else:
            props = stormpy.parse_properties_without_context(lines)

        # check properties
        constraints = []
        optimality = None
        for prop in props:
            rf = prop.raw_formula
            assert rf.has_bound != rf.has_optimality_type, \
                "optimizing formula contains a bound or a comparison formula does not"
            if rf.has_bound:
                constraints.append(prop)
            else:
                assert optimality is None, "more than one optimality formula specified"
                optimality = prop

        # wrap properties
        constraints = [Property(p,discount_factor) for p in constraints]
        if optimality is not None:
            optimality = OptimalityProperty(optimality, discount_factor, relative_error)
        specification = Specification(constraints,optimality)

        logger.info(f"found the following specification: {specification}")
        return specification
