import stormpy
import stormpy.synthesis

from .jani import JaniUnfolder
from ..quotient.holes import Hole, Holes, DesignSpace
from ..quotient.models import MarkovChain
from ..quotient.coloring import Coloring

import paynt.verification.property

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
        prism_model_type = {
            stormpy.storage.PrismModelType.DTMC:"DTMC",
            stormpy.storage.PrismModelType.MDP:"MDP",
            stormpy.storage.PrismModelType.POMDP:"POMDP"
        }[prism.model_type]
        logger.debug("PRISM model type: " + prism_model_type)

        # parse constants
        constant_map = None

        # parse hole definitions
        hole_expressions = None
        holes = None
        if len(hole_definitions) > 0:
            logger.info("processing hole definitions...")
            prism, hole_expressions, holes = PrismParser.parse_holes(prism, expression_parser, hole_definitions)

        specification = PrismParser.parse_specification(properties_path, relative_error, discount_factor, prism, holes)

        # construct the quotient
        coloring = None
        jani_unfolder = None
        obs_evaluator = None
        if holes is not None:
            assert prism_model_type in ["DTMC","MDP","POMDP"], "hole detected, but the program is neither DTMC nor (PO)MDP"
            # unfold hole options via Jani
            jani_unfolder = JaniUnfolder(prism, hole_expressions, specification, holes)
            specification = jani_unfolder.specification
            quotient_mdp = jani_unfolder.quotient_mdp
            coloring = Coloring(quotient_mdp, holes, jani_unfolder.action_to_hole_options)
            MarkovChain.initialize(specification)
            if prism.model_type == stormpy.storage.PrismModelType.POMDP:
                obs_evaluator = stormpy.synthesis.ObservationEvaluator(prism, quotient_mdp)
            quotient_mdp = stormpy.synthesis.add_choice_labels_from_jani(quotient_mdp)
        else:
            MarkovChain.initialize(specification)
            quotient_mdp = MarkovChain.from_prism(prism)

        return prism, quotient_mdp, specification, coloring, jani_unfolder, obs_evaluator

    
    @classmethod
    def load_sketch_prism(cls, sketch_path):
        # read lines
        with open(sketch_path) as f:
            sketch_lines = f.readlines()

        # replace hole definitions with constants
        hole_re_brace = re.compile(r'^\s*hole\s+(.*?)\s+(.*?)\s+in\s+\{(.*?)\}\s*;\s*$')
        # hole_re_bracket = re.compile(r'^\s*hole\s+(.*?)\s+(.*?)\s+in\s+[(.*?)]\s+;\s+$')
        sketch_output = []
        hole_definitions = []
        for line in sketch_lines:
            match = hole_re_brace.search(line)
            if match is None:
                sketch_output.append(line)
                continue
            hole_type = match.group(1)
            hole_name = match.group(2)
            hole_options = match.group(3).replace(" ", "")
            hole_definitions.append( (hole_name,hole_type,hole_options) )
            sketch_output.append(f"const {hole_type} {hole_name};\n")
            sketch_output.append(f"const {hole_type} {hole_name}_MIN;\n")
            sketch_output.append(f"const {hole_type} {hole_name}_MAX;\n")


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
        hole_min = []
        hole_max = []
        for hole_name,hole_type,hole_options in hole_definitions:
            if ".." in hole_options:
                assert hole_type == "int", "cannot use range-based definitions for non-integer hole types"
                options = hole_options.split("..")
                range_start = int(options[0])
                range_end = int(options[1])
                hole_min.append(range_start)
                hole_max.append(range_end)
                options = [str(o) for o in range(range_start,range_end+1)]
            else:
                options = hole_options.split(",")
            expressions = [expression_parser.parse(o) for o in options]
            hole_expressions.append(expressions)

            options = list(range(len(expressions)))
            option_labels = [str(e) for e in expressions]
            hole = Hole(hole_name, options, option_labels)
            holes.append(hole)

        # substitute constants used as min/max values of holes
        hole_range_definitions = {}
        for hole_index,hole in enumerate(holes): 
            var_min = prism.get_constant(f"{hole.name}_MIN").expression_variable
            hole_range_definitions[var_min] = expression_parser.parse(str(hole_min[hole_index]))
            var_max = prism.get_constant(f"{hole.name}_MAX").expression_variable
            hole_range_definitions[var_max] = expression_parser.parse(str(hole_max[hole_index]))
        prism = prism.define_constants(hole_range_definitions)

        # check that all undefined constants are indeed the holes
        hole_names = [hole.name for hole in holes]
        for c in prism.constants:
            if not c.defined:
                assert c.name in hole_names, f"constant {c.name} was not specified"

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
    def parse_property(cls, line, prism=None):
        '''
        Parse a line containing a single PCTL property.
        @return the property or None if no property was detected
        '''
        if prism is not None:
            props = stormpy.parse_properties_for_prism_program(line, prism)
        else:
            props = stormpy.parse_properties_without_context(line)
        if len(props) == 0:
            return None
        if len(props)>1:
            logger.warning("multiple properties detected on one line, dropping all but the first one")
        return props[0]

    @classmethod
    def parse_specification(cls, properties_path, relative_error, discount_factor, prism=None, holes=None):
        '''
        Expecting one property per line. The line may be terminated with a semicolon.
        Empty lines or comments are allowed.
        '''
        
        if not os.path.isfile(properties_path):
            raise ValueError(f"the properties file {properties_path} does not exist")
        logger.info(f"loading properties from {properties_path} ...")

        mdp_spec = re.compile(r'^\s*(min|max)\s+(.*)$')

        lines = ""
        with open(properties_path) as file:
            lines = [line for line in file]
        
        properties = []

        for line in lines:
            minmax = None
            match = mdp_spec.search(line)
            if match is not None:
                minmax = match.group(1)
                line = match.group(2)
            prop = PrismParser.parse_property(line,prism)
            if prop is None:
                continue

            rf = prop.raw_formula
            assert rf.has_bound != rf.has_optimality_type, \
                "optimizing formula contains a bound or a comparison formula does not"
            if minmax is None:
                if rf.has_bound:
                    prop = paynt.verification.property.Property(prop,discount_factor)
                else:
                    prop = paynt.verification.property.OptimalityProperty(prop, discount_factor, relative_error)
            else:
                assert not rf.has_bound, "double-optimality objective cannot contain a bound"
                dminimizing = (minmax=="min")
                prop = paynt.verification.property.DoubleOptimalityProperty(prop, dminimizing, discount_factor, relative_error)
            properties.append(prop)

        specification = paynt.verification.property.Specification(properties)
        logger.info(f"found the following specification: {specification}")
        assert not specification.has_double_optimality, "did not expect double-optimality property"
        return specification
