import stormpy

from .prism_parser import PrismParser
from .pomdp_parser import PomdpParser
from ..quotient.quotient import *
from ..quotient.quotient_pomdp import POMDPQuotientContainer
from ..quotient.quotient_decpomdp import DecPomdpQuotientContainer

import paynt

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
        decpomdp_manager = None

        logger.info(f"loading sketch from {sketch_path} ...")
        if filetype == "prism":
            explicit_quotient, specification, coloring, jani_unfolder = PrismParser.read_prism(sketch_path, constant_str, properties_path, relative_error)
        elif filetype == "drn":
            explicit_quotient = PomdpParser.read_pomdp_drn(sketch_path)
            specification = PrismParser.parse_specification(properties_path, relative_error)
        else: # filetype == "cassandra"
            decpomdp_manager = stormpy.synthesis.parse_decpomdp(sketch_path)
            logger.info("applying discount factor transformation...")
            decpomdp_manager.apply_discount_factor_transformation()
            explicit_quotient = decpomdp_manager.construct_pomdp()
            optimality = paynt.quotient.property.construct_reward_property(
                decpomdp_manager.reward_model_name,
                decpomdp_manager.reward_minimizing,
                decpomdp_manager.discount_sink_label)
            specification = paynt.quotient.property.Specification([],optimality)
             
        assert specification is not None
        MarkovChain.initialize(specification)
        
        logger.debug("constructed explicit quotient having {} states and {} actions".format(
            explicit_quotient.nr_states, explicit_quotient.nr_choices))

        specification.check()
        if specification.contains_until_properties() and filetype != "prism":
            logger.info("WARNING: using until formulae with non-PRISM inputs might lead to unexpected behaviour")
        specification.transform_until_to_eventually()

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

        quotient_container = None
        if jani_unfolder is not None:
            quotient_container = DTMCQuotientContainer(explicit_quotient, coloring, specification)
        else:
            assert explicit_quotient.is_nondeterministic_model
            if decpomdp_manager is not None and decpomdp_manager.num_agents > 1:
                quotient_container = DecPomdpQuotientContainer(decpomdp_manager, specification)
            else:
                quotient_container = POMDPQuotientContainer(explicit_quotient, specification)
        return quotient_container

