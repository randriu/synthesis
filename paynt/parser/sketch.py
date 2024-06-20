import stormpy
import payntbind

from paynt.parser.prism_parser import PrismParser
from paynt.parser.pomdp_parser import PomdpParser

import paynt.quotient.models

import paynt.quotient.quotient
import paynt.quotient.pomdp
import paynt.quotient.decpomdp
import paynt.quotient.posg
import paynt.quotient.mdp_family
import paynt.quotient.pomdp_family
import paynt.verification.property

import uuid

import logging
logger = logging.getLogger(__name__)

import os


def substitute_suffix(string, delimiter, replacer):
    '''Subsitute the suffix behind the last delimiter.'''
    output_string = string.split(delimiter)
    output_string[-1] = str(replacer)
    output_string = delimiter.join(output_string)
    return output_string

def make_rewards_action_based(model):
    tm = model.transition_matrix
    for name,reward_model in model.reward_models.items():
        assert not reward_model.has_transition_rewards, "Paynt does not support transition rewards"
        if not reward_model.has_state_rewards:
            continue
        logger.info("converting state rewards '{}' to state-action rewards".format(name))
        if reward_model.has_state_action_rewards:
            logger.info("state rewards will be added to existing state-action rewards".format(name))
            action_reward = reward_model.state_action_rewards.copy()
        else:
            action_reward = [0] * model.nr_choices

        for state in range(model.nr_states):
            state_reward = reward_model.get_state_reward(state)
            for action in range(tm.get_row_group_start(state),tm.get_row_group_end(state)):
                action_reward[action] += state_reward

        payntbind.synthesis.remove_reward_model(model,name)
        new_reward_model = stormpy.storage.SparseRewardModel(optional_state_action_reward_vector=action_reward)
        model.add_reward_model(name, new_reward_model)



class Sketch:


    @classmethod
    def load_sketch(cls, sketch_path, properties_path,
        export=None, relative_error=0, precision=1e-4, constraint_bound=None):

        prism = None
        explicit_quotient = None
        specification = None
        family = None
        coloring = None
        jani_unfolder = None
        decpomdp_manager = None
        obs_evaluator = None

        paynt.verification.property.Property.model_checking_precision = precision

        # check path
        if not os.path.isfile(sketch_path):
            raise ValueError(f"the sketch file {sketch_path} does not exist")
        logger.info(f"loading sketch from {sketch_path} ...")

        filetype = None
        try:
            logger.info(f"assuming sketch in PRISM format...")
            prism, explicit_quotient, specification, family, coloring, jani_unfolder, obs_evaluator = PrismParser.read_prism(
                        sketch_path, properties_path, relative_error)
            filetype = "prism"
        except SyntaxError:
            pass
        if filetype is None:
            try:
                logger.info(f"assuming sketch in DRN format...")
                explicit_quotient = PomdpParser.read_pomdp_drn(sketch_path)
                specification = PrismParser.parse_specification(properties_path, relative_error)
                filetype = "drn"
            except:
                pass
        if filetype is None:
            try:
                logger.info(f"assuming sketch in Cassandra format...")
                decpomdp_manager = payntbind.synthesis.parse_decpomdp(sketch_path)
                if constraint_bound is not None:
                    decpomdp_manager.set_constraint(constraint_bound)
                if decpomdp_manager is None:
                    raise SyntaxError
                logger.info("applying discount factor transformation...")
                decpomdp_manager.apply_discount_factor_transformation()
                explicit_quotient = decpomdp_manager.construct_pomdp()
                if constraint_bound is not None:
                    specification = PrismParser.parse_specification(properties_path, relative_error)
                else:
                    optimality = paynt.verification.property.construct_reward_property(
                        decpomdp_manager.reward_model_name,
                        decpomdp_manager.reward_minimizing,
                        decpomdp_manager.discount_sink_label)
                    specification = paynt.verification.property.Specification([optimality])
                filetype = "cassandra"
            except SyntaxError:
                pass

        assert filetype is not None, "unknow format of input file"
        logger.info("sketch parsing OK")
             
        paynt.quotient.models.Mdp.initialize(specification)
        paynt.verification.property.Property.initialize()
        
        make_rewards_action_based(explicit_quotient)
        logger.debug("constructed explicit quotient having {} states and {} actions".format(
            explicit_quotient.nr_states, explicit_quotient.nr_choices))

        specification.check()
        if specification.contains_until_properties() and filetype != "prism":
            logger.info("WARNING: using until formulae with non-PRISM inputs might lead to unexpected behaviour")
        specification.transform_until_to_eventually()
        logger.info(f"found the following specification {specification}")

        if export is not None:
            Sketch.export(export, sketch_path, jani_unfolder, explicit_quotient)
            logger.info("export OK, aborting...")
            exit(0)

        return Sketch.build_quotient_container(prism, jani_unfolder, explicit_quotient, family, coloring, specification, obs_evaluator, decpomdp_manager)
    

    @classmethod
    def load_sketch_as_all_in_one(cls, sketch_path, properties_path):
        if not os.path.isfile(sketch_path):
            raise ValueError(f"the sketch file {sketch_path} does not exist")
        logger.info(f"loading sketch from {sketch_path} ...")
        logger.info(f"all in one approach so assuming input in PRISM format...")
        try:
            prism, hole_definitions = PrismParser.load_sketch_prism(sketch_path)
            expression_parser = stormpy.storage.ExpressionParser(prism.expression_manager)
            expression_parser.set_identifier_mapping(dict())
            prism_model_type = {
                stormpy.storage.PrismModelType.DTMC:"DTMC",
                stormpy.storage.PrismModelType.MDP:"MDP",
                stormpy.storage.PrismModelType.POMDP:"POMDP"
            }[prism.model_type]
            logger.debug("PRISM model type: " + prism_model_type)

            hole_expressions = None
            family = None
            if len(hole_definitions) > 0:
                logger.info("processing hole definitions...")
                prism, hole_expressions, family = PrismParser.parse_holes(prism, expression_parser, hole_definitions)

            specification = PrismParser.parse_specification(properties_path, prism=prism)

            prism = prism.replace_variable_initialization_by_init_expression()
            expression_manager = prism.expression_manager
            for index, hole in enumerate(hole_definitions):
                # TODO add support for double holes
                assert hole[1] == 'int', "all in one approach only works with integer holes"
                var = prism.get_constant(hole[0])
                var_values = [x.evaluate_as_int() for x in hole_expressions[index]]
                prism = prism.replace_constant_by_variable(var, expression_manager.create_integer(min(var_values)), expression_manager.create_integer(max(var_values)))
                var_options = [stormpy.Expression.Eq(var.expression_variable.get_expression(), expression_manager.create_integer(val)) for val in var_values]
                prism.update_initial_states_expression(stormpy.Expression.And(prism.initial_states_expression, stormpy.Expression.Disjunction(var_options)))

            # TODO investigate why we have to print and load the prism program again for all in one construction to work
            tmp_path = sketch_path + str(uuid.uuid4())
            with open(tmp_path, 'w') as f:
                print(prism, end="", file=f)
            try:
                prism = stormpy.parse_prism_program(tmp_path, prism_compat=True)
                os.remove(tmp_path)
            except:
                os.remove(tmp_path)
                raise SyntaxError

        except SyntaxError as e:
            logger.error(f"all in one approach supports only input in PRISM format!")
            raise e
        
        return prism, specification, family
    
    @classmethod
    def export(cls, export, sketch_path, jani_unfolder, explicit_quotient):
        if export == "jani":
            assert jani_unfolder is not None, "jani unfolder was not used"
            output_path = substitute_suffix(sketch_path, '.', 'jani')
            jani_unfolder.write_jani(output_path)
        if export == "drn":
            output_path = substitute_suffix(sketch_path, '.', 'drn')
            stormpy.export_to_drn(explicit_quotient, output_path)
        if export == "pomdp":
            assert explicit_quotient.is_nondeterministic_model and explicit_quotient.is_partially_observable, \
                "cannot '--export pomdp' with non-POMDP sketches"
            output_path = substitute_suffix(sketch_path, '.', 'pomdp')
            property_path = substitute_suffix(sketch_path, '/', 'props.pomdp')
            PomdpParser.write_model_in_pomdp_solve_format(explicit_quotient, output_path, property_path)


    @classmethod
    def build_quotient_container(cls, prism, jani_unfolder, explicit_quotient, family, coloring, specification, obs_evaluator, decpomdp_manager):
        if jani_unfolder is not None:
            if prism.model_type == stormpy.storage.PrismModelType.DTMC:
                quotient_container = paynt.quotient.quotient.DtmcFamilyQuotient(explicit_quotient, family, coloring, specification)
            elif prism.model_type == stormpy.storage.PrismModelType.MDP:
                quotient_container = paynt.quotient.mdp_family.MdpFamilyQuotient(explicit_quotient, family, coloring, specification)
            elif prism.model_type == stormpy.storage.PrismModelType.POMDP:
                quotient_container = paynt.quotient.pomdp_family.PomdpFamilyQuotient(explicit_quotient, family, coloring, specification, obs_evaluator)
        else:
            assert explicit_quotient.is_nondeterministic_model
            if decpomdp_manager is not None and decpomdp_manager.num_agents > 1:
                quotient_container = paynt.quotient.decpomdp.DecPomdpQuotient(decpomdp_manager, specification)
            elif explicit_quotient.labeling.contains_label(paynt.quotient.posg.PosgQuotient.PLAYER_1_STATE_LABEL):
                quotient_container = paynt.quotient.posg.PosgQuotient(explicit_quotient, specification)
            else:
                quotient_container = paynt.quotient.pomdp.PomdpQuotient(explicit_quotient, specification, decpomdp_manager)
        return quotient_container


