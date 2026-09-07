import stormpy
import payntbind

import paynt.underlying_model.model_builder
import paynt.colored_mdp
import paynt.family
import paynt.family.task
import paynt.posmg
import paynt.posmg.task
import paynt.pomdp
import paynt.pomdp.task
import paynt.specification.property
import paynt.task

from paynt.dt import DtColoredMdpFactory
import paynt.dt.dtnest.task

from paynt.parser.prism_parser import PrismParser
from paynt.parser.drn_parser import DrnParser

from ._utils import substitute_suffix, make_rewards_action_based

import os
import json

import logging
logger = logging.getLogger(__name__)

class Sketch:

    @classmethod
    def load_sketch(cls, sketch_path, properties_path,
        export=None, relative_error=0, precision=1e-4, constraint_bound=None, use_exact=False, task_kwargs=None):

        prism = None
        explicit_model = None
        specification = None
        parameter_space = None
        coloring = None
        jani_unfolder = None
        decpomdp_manager = None
        obs_evaluator = None

        paynt.specification.property.Property.model_checking_precision = precision

        # check path
        if not os.path.isfile(sketch_path):
            raise ValueError(f"the sketch file {sketch_path} does not exist")
        logger.info(f"loading sketch from {sketch_path} ...")

        filetype = None
        try:
            logger.info(f"assuming sketch in PRISM format...")
            prism, explicit_model, specification, parameter_space, coloring, jani_unfolder, obs_evaluator = PrismParser.read_prism(
                        sketch_path, properties_path, relative_error, use_exact)
            filetype = "prism"
        except SyntaxError:
            pass
        if filetype is None:
            try:
                logger.info(f"assuming sketch in DRN format...")
                explicit_model = paynt.underlying_model.model_builder.ModelBuilder.from_drn(sketch_path, use_exact)
                specification = PrismParser.parse_specification(properties_path, relative_error, use_exact=use_exact)
                filetype = "drn"
                project_path = os.path.dirname(sketch_path)
                valuations_filename = "state-valuations.json"
                valuations_path = project_path + "/" + valuations_filename
                state_valuations = None
                if os.path.exists(valuations_path) and os.path.isfile(valuations_path):
                    with open(valuations_path) as file:
                        state_valuations = json.load(file)
                if state_valuations is not None:
                    if use_exact:
                        raise Exception("exact synthesis is not supported with state valuations")
                    logger.info(f"found state valuations in {valuations_path}, adding to the model...")
                    explicit_model = payntbind.synthesis.addStateValuations(explicit_model,state_valuations)
            except Exception as e:
                print(e)
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
                explicit_model = decpomdp_manager.construct_pomdp()
                if constraint_bound is not None:
                    specification = PrismParser.parse_specification(properties_path, relative_error)
                else:
                    optimality = paynt.specification.property.construct_reward_property(
                        decpomdp_manager.reward_model_name,
                        decpomdp_manager.reward_minimizing,
                        decpomdp_manager.discount_sink_label)
                    specification = paynt.specification.property.Specification([optimality])
                filetype = "cassandra"
            except SyntaxError:
                pass

        assert filetype is not None, "unknown format of input file"
        logger.info("sketch parsing OK")

        paynt.specification.property.Property.initialize(use_exact)
        if explicit_model.is_exact:
            updated = payntbind.synthesis.addMissingChoiceLabelsExact(explicit_model)
        else:
            updated = payntbind.synthesis.addMissingChoiceLabels(explicit_model)
        if updated is not None: explicit_model = updated
        if not payntbind.synthesis.assertChoiceLabelingIsCanonic(explicit_model.nondeterministic_choice_indices,explicit_model.choice_labeling,False):
            logger.warning("WARNING: choice labeling for the model is not canonic")


        make_rewards_action_based(explicit_model)
        logger.debug("constructed explicit model having {} states and {} choices".format(
            explicit_model.nr_states, explicit_model.nr_choices))

        if specification.contains_until_properties() and filetype != "prism":
            logger.info("WARNING: using until formulae with non-PRISM inputs might lead to unexpected behaviour")
        specification.transform_until_to_eventually()
        logger.info(f"found the following specification {specification}")

        if export is not None:
            Sketch.export(export, sketch_path, jani_unfolder, explicit_model)
            logger.info("export OK, aborting...")
            exit(0)

        task_kwargs = task_kwargs or {}

        if jani_unfolder is not None:
            if prism.model_type == stormpy.storage.PrismModelType.DTMC:
                task = paynt.task.Task.from_specification(specification, use_exact=use_exact, **task_kwargs)
                colored_mdp = paynt.colored_mdp.ColoredMdp(explicit_model, parameter_space, coloring, use_exact=use_exact)
                colored_mdp_factory = paynt.colored_mdp.IdentityColoredMdpFactory(colored_mdp, task)
            elif prism.model_type == stormpy.storage.PrismModelType.MDP:
                task = paynt.family.task.FamilyTask.from_specification(specification, use_exact=use_exact, **task_kwargs)
                colored_mdp_factory = paynt.family.FamilyColoredMdpFactory(explicit_model, parameter_space, coloring, task, use_exact=use_exact)
            elif prism.model_type == stormpy.storage.PrismModelType.POMDP:
                task = paynt.family.task.FamilyTask.from_specification(specification, use_exact=use_exact, **task_kwargs)
                colored_mdp_factory = paynt.family.PomdpFamilyColoredMdpFactory(explicit_model, parameter_space, coloring, task, obs_evaluator, use_exact=use_exact)
        else:
            # assert explicit_model.is_nondeterministic_model, "expected nondeterministic model"
            if decpomdp_manager is not None and decpomdp_manager.num_agents > 1:
                task = paynt.pomdp.task.PomdpTask.from_specification(specification, use_exact=use_exact, **task_kwargs)
                colored_mdp_factory = paynt.pomdp.decpomdp.DecPomdpColoredMdpFactory(decpomdp_manager, task, use_exact=use_exact)
            elif isinstance(explicit_model, payntbind.synthesis.Posmg):
                task = paynt.posmg.task.PosmgTask.from_specification(specification, use_exact=use_exact, **task_kwargs)
                colored_mdp_factory = paynt.posmg.PosmgColoredMdpFactory(explicit_model, task, use_exact=use_exact)
            elif not explicit_model.is_partially_observable:
                # always use the more capable DtNestTask (a strict superset of DtTask) since at this point
                # we don't yet know whether the caller intends to run dtnest or plain AR on this sketch
                task = paynt.dt.dtnest.task.DtNestTask.from_specification(specification, use_exact=use_exact, **task_kwargs)
                colored_mdp_factory = DtColoredMdpFactory(explicit_model, task, use_exact=use_exact)
            else:
                task = paynt.pomdp.task.PomdpTask.from_specification(specification, use_exact=use_exact, **task_kwargs)
                colored_mdp_factory = paynt.pomdp.PomdpColoredMdpFactory(explicit_model, task, decpomdp_manager, use_exact=use_exact)
        return colored_mdp_factory, task


    @classmethod
    def export(cls, export, sketch_path, jani_unfolder, explicit_model):
        if export == "jani":
            assert jani_unfolder is not None, "jani unfolder was not used"
            output_path = substitute_suffix(sketch_path, '.', 'jani')
            jani_unfolder.write_jani(output_path)
        if export == "drn":
            output_path = substitute_suffix(sketch_path, '.', 'drn')
            stormpy.export_to_drn(explicit_model, output_path)
        if export == "pomdp":
            assert explicit_model.is_nondeterministic_model and explicit_model.is_partially_observable, \
                "cannot '--export pomdp' with non-POMDP sketches"
            output_path = substitute_suffix(sketch_path, '.', 'pomdp')
            property_path = substitute_suffix(sketch_path, '/', 'props.pomdp')
            paynt.parser.pomdp_parser.PomdpParser.write_model_in_pomdp_solve_format(explicit_model, output_path, property_path)
