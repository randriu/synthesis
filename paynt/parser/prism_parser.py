import stormpy
import payntbind

import paynt.family.family
import paynt.verification.property
import paynt.parser.jani
import paynt.quotient.models

import os
import re
import uuid

import logging
logger = logging.getLogger(__name__)


class PrismParser:

    @classmethod
    def read_prism(cls, sketch_path, properties_path, relative_error):

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
        family = None
        if len(hole_definitions) > 0:
            logger.info("processing hole definitions...")
            prism, hole_expressions, family = PrismParser.parse_holes(prism, expression_parser, hole_definitions)

        specification = PrismParser.parse_specification(properties_path, relative_error, prism)

        # construct the quotient
        coloring = None
        jani_unfolder = None
        obs_evaluator = None
        if family is not None:
            assert prism_model_type in ["DTMC","MDP","POMDP"], "hole detected, but the program is neither DTMC nor (PO)MDP"
            # unfold hole options via Jani
            jani_unfolder = paynt.parser.jani.JaniUnfolder(prism, hole_expressions, specification, family)
            specification = jani_unfolder.specification
            quotient_mdp = jani_unfolder.quotient_mdp
            coloring = payntbind.synthesis.Coloring(family.family, quotient_mdp.nondeterministic_choice_indices, jani_unfolder.choice_to_hole_options)
            paynt.quotient.models.Mdp.initialize(specification)
            if prism.model_type == stormpy.storage.PrismModelType.POMDP:
                obs_evaluator = payntbind.synthesis.ObservationEvaluator(prism, quotient_mdp)
            quotient_mdp = payntbind.synthesis.addChoiceLabelsFromJani(quotient_mdp)
        else:
            paynt.quotient.models.Mdp.initialize(specification)
            quotient_mdp = paynt.quotient.models.Mdp.from_prism(prism)

        return prism, quotient_mdp, specification, family, coloring, jani_unfolder, obs_evaluator

    
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
        family = paynt.family.family.Family()
        hole_expressions = []
        hole_min = []
        hole_max = []
        for hole_name,hole_type,hole_options in hole_definitions:
            if ".." in hole_options:
                assert hole_type == "int" or hole_type == "double", "cannot use range-based definitions for non-integer of non-double hole types"
                if hole_type == "double":
                    assert ":" in hole_options, "using range-based definition for double requires specifying the increment step range_start..range_end:step"
                    range_start = float(hole_options[0:hole_options.find('..')])
                    range_end = float(hole_options[hole_options.find('..')+2:hole_options.find(':')].strip())
                    increment_string = hole_options.split(':')[-1].strip()
                    increment = float(increment_string)
                    increment_decimal_precision = len(increment_string.split('.')[-1])
                    hole_min.append(range_start)
                    hole_max.append(range_end)
                    steps = (range_end - range_start) / increment
                    options = ["{:.{n}f}".format(range_start + x * increment, n=increment_decimal_precision) for x in range(int(round(steps)+1))]
                    if float(options[-1]) > range_end:
                        options = options[:-1]
                else:
                    if ":" in hole_options:
                        range_start = int(hole_options[0:hole_options.find('..')])
                        range_end = int(hole_options[hole_options.find('..')+2:hole_options.find(':')].strip())
                        increment = int(hole_options.split(':')[-1].strip())
                    else:
                        options = hole_options.split("..")
                        range_start = int(options[0])
                        range_end = int(options[1])
                        increment = 1
                    hole_min.append(range_start)
                    hole_max.append(range_end)
                    options = [str(o) for o in range(range_start,range_end+1, increment)]
            else:
                options = hole_options.split(",")
                if hole_type == "int":
                    options_numerical = [int(o) for o in options]
                else:
                    options_numerical = [float(o) for o in options]
                hole_min.append(min(options_numerical))
                hole_max.append(max(options_numerical))
            expressions = [expression_parser.parse(o) for o in options]
            hole_expressions.append(expressions)

            option_labels = [str(e) for e in expressions]
            family.add_hole(hole_name, option_labels)

        # substitute constants used as min/max values of holes
        hole_range_definitions = {}
        for hole in range(family.num_holes):
            hole_name = family.hole_name(hole)
            var_min = prism.get_constant(f"{hole_name}_MIN").expression_variable
            hole_range_definitions[var_min] = expression_parser.parse(str(hole_min[hole]))
            var_max = prism.get_constant(f"{hole_name}_MAX").expression_variable
            hole_range_definitions[var_max] = expression_parser.parse(str(hole_max[hole]))
        prism = prism.define_constants(hole_range_definitions)

        # check that all undefined constants are indeed the holes
        hole_names = [family.hole_name(hole) for hole in range(family.num_holes)]
        for c in prism.constants:
            if not c.defined:
                assert c.name in hole_names, f"constant {c.name} was not specified"

        return prism, hole_expressions, family

 
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
    def parse_specification(cls, properties_path, relative_error=0, prism=None):
        '''
        Expecting one property per line. The line may be terminated with a semicolon.
        Empty lines or comments are allowed.
        '''
        if not os.path.isfile(properties_path):
            raise ValueError(f"the properties file {properties_path} does not exist")
        logger.info(f"loading properties from {properties_path} ...")

        lines = ""
        with open(properties_path) as file:
            lines = [line for line in file]
        
        properties = []

        for line in lines:
            formula = PrismParser.parse_property(line,prism)
            if formula is None:
                continue
            prop = paynt.verification.property.construct_property(formula, relative_error)
            properties.append(prop)

        specification = paynt.verification.property.Specification(properties)
        logger.info(f"found the following specification: {specification}")
        return specification
