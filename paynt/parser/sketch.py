import stormpy

from .prism_parser import PrismParser
from .pomdp_parser import PomdpParser
from ..quotient.quotient import *
from ..quotient.quotient_pomdp import POMDPQuotientContainer

import logging
logger = logging.getLogger(__name__)


class Sketch:


    @classmethod
    def substitute_suffix(cls, string, delimiter, replacer):
        '''Subsitute the suffix behind the last delimiter.'''
        output_string = string.split(delimiter)
        output_string[-1] = str(replacer)
        output_string = delimiter.join(output_string)
        return output_string

    @classmethod
    def load_sketch(self, sketch_path, filetype, export,
        properties_path, constant_str, relative_error):

        explicit_quotient = None
        specification = None
        coloring = None
        jani_unfolder = None

        logger.info(f"loading sketch from {sketch_path} ...")
        if filetype == "prism":
            explicit_quotient, specification, coloring, jani_unfolder = PrismParser.read_prism(sketch_path, constant_str, properties_path, relative_error)
        else:
            if filetype == "drn":
                explicit_quotient = PomdpParser.read_pomdp_drn(sketch_path)
            else: #filetype == "pomdp"
                explicit_quotient = PomdpParser.read_pomdp_solve(sketch_path)
            specification = PrismParser.parse_specification(properties_path, relative_error)
        logger.debug("constructed explicit quotient having {} states and {} actions".format(
            explicit_quotient.nr_states, explicit_quotient.nr_choices))

        if export is not None:
            if export == "jani":
                assert jani_unfolder is not None, "jani unfolder was not used"
                jani_unfolder.write_jani(sketch_path)
            if export == "drn":
                output_path = Sketch.substitute_suffix(sketch_path, '.', 'drn')
                stormpy.export_to_drn(explicit_quotient, output_path)
            if export == "pomdp":
                assert explicit_quotient.is_nondeterministic_model and explicit_quotient.is_partially_observable, \
                    "cannot '--export pomdp' with non-POMDP sketches"
                output_path = Sketch.substitute_suffix(sketch_path, '.', 'pomdp')
                property_path = Sketch.substitute_suffix(sketch_path, '/', 'props.pomdp')
                PomdpParser.write_model_in_pomdp_solve_format(explicit_quotient, output_path, property_path)
            exit(0)

        logger.info(f"initializing quotient container...")
        quotient_container = None
        if jani_unfolder is not None:
            quotient_container = DTMCQuotientContainer(explicit_quotient, coloring, specification)
        else:
            assert explicit_quotient.is_nondeterministic_model
            if explicit_quotient.is_partially_observable:
                quotient_container = POMDPQuotientContainer(explicit_quotient, specification)
            else:
                # left intentionally blank
                pass
        return quotient_container

