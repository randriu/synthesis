import paynt.synthesizer.statistic
import paynt.utils.timer
import paynt.underlying_model.underlying_model

import paynt.dt.result
from paynt.dt.synthesizer_ar_dt import SynthesizerARDt

from ._utils import simplify_tree

import stormpy
import payntbind

import os
import json

import logging
logger = logging.getLogger(__name__)


def _choose_solver_for_dt_task(paynt_task_dt):
    if paynt_task_dt.has_scheduler_to_map:
        return "dtmap"
    return "dtpaynt"


def _run_dt_map_scheduler(cmdp_factory_dt, scheduler, tree_depth):
    """Helper function to map a scheduler to a decision tree using the DTMap algorithm. Returns a tuple (success, decision_tree)."""

    state_to_choice = payntbind.synthesis.schedulerToStateToGlobalChoice(scheduler, cmdp_factory_dt.underlying_mdp, [x for x in range(cmdp_factory_dt.underlying_mdp.nr_choices)])
    state_to_choice = paynt.underlying_model.underlying_model.ModelIndex.discard_unreachable_choices(
        cmdp_factory_dt.underlying_mdp, cmdp_factory_dt.choice_destinations, state_to_choice)
    choices = paynt.underlying_model.underlying_model.ModelIndex.state_to_choice_to_choices(cmdp_factory_dt.underlying_mdp, state_to_choice)

    dt_synthesizer = DtSynthesizer(cmdp_factory_dt)
    dt_synthesizer.map_scheduler(choices, tree_depth=tree_depth)

    simplify_tree(dt_synthesizer.best_tree, dt_synthesizer.colored_mdp)

    return paynt.dt.result.DtResult(
        success = dt_synthesizer.best_tree is not None,
        value = dt_synthesizer.best_tree_value,
        tree = dt_synthesizer.best_tree
    )


def _run_dtpaynt(cmdp_factory_dt, tree_depth, timeout=None):
    dt_synthesizer = DtSynthesizer(cmdp_factory_dt)
    dt_synthesizer.synthesize_tree(tree_depth, timeout=timeout)

    simplify_tree(dt_synthesizer.best_tree, dt_synthesizer.colored_mdp)

    return paynt.dt.result.DtResult(
        success = dt_synthesizer.best_tree is not None,
        value = dt_synthesizer.best_tree_value,
        tree = dt_synthesizer.best_tree
    )


class DtSynthesizer:
    '''
    Outer driver: repeatedly re-unfolds the decision tree at different depths (DtColoredMdpFactory.reset_tree
    tries a fresh depth/coloring each time, unlike the FSC-unfolding factories' memory-size growth) and runs
    SynthesizerARDt -- a fresh inner AR engine constructed for each depth -- against each unfolding, keeping
    the best tree found so far across depths. Mirrors the PomdpSynthesizer/SayntSynthesizer split from their
    own inner AR engine.
    '''

    def __init__(self, colored_mdp_factory):
        self.colored_mdp_factory = colored_mdp_factory
        self.colored_mdp = colored_mdp_factory.colored_mdp
        self.task = colored_mdp_factory.task
        self.best_tree = None
        self.best_tree_value = None

    @property
    def method_name(self):
        return "AR (decision tree)"

    def compute_normalized_value(self, value, opt, random):
        return (value-random)/(opt-random) if opt-random != 0 else 1.0

    def export_decision_tree(self, decision_tree, export_filename_base):
        tree = decision_tree.to_graphviz()
        tree_filename = export_filename_base + ".dot"
        directory = os.path.dirname(tree_filename)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(tree_filename, 'w') as file:
            file.write(tree.source)
        logger.info(f"exported decision tree to {tree_filename}")

        tree_visualization_filename = export_filename_base + ".png"
        tree.render(export_filename_base, format="png", cleanup=True) # using export_filename_base since graphviz appends .png by default
        logger.info(f"exported decision tree visualization to {tree_visualization_filename}")

        tree_string_filename = export_filename_base + ".txt"
        with open(tree_string_filename, 'w') as file:
            file.write(decision_tree.to_string())
        logger.info(f"exported decision tree string to {tree_string_filename}")


    def synthesize_tree(self, depth : int, timeout : int = None):
        self.colored_mdp = self.colored_mdp_factory.reset_tree(depth)
        synthesizer = SynthesizerARDt(self.colored_mdp, self.task)
        synthesizer.synthesize(keep_optimum=True, timeout=timeout)
        if synthesizer.best_assignment is not None:
            self.colored_mdp.decision_tree.root.associate_assignment(synthesizer.best_assignment)
            self.best_tree = self.colored_mdp.decision_tree
            self.best_tree_value = synthesizer.best_assignment_value

    def synthesize_tree_sequence(self, opt_result_value, overall_timeout=None, max_depth=None, break_if_found=False):
        self.best_tree = self.best_tree_value = None

        if max_depth is None:
            max_depth = self.task.tree_depth+1
        if overall_timeout is None:
            global_timeout = paynt.utils.timer.GlobalTimer.global_timer.time_limit_seconds
            if global_timeout is None: global_timeout = 900 # TODO this should probably not be the deafult behaviour, we want to run the synthesis indefinitely if the user does not give us timeout
            overall_timeout = global_timeout
            tree_sequence_timer = None
        else:
            tree_sequence_timer = paynt.utils.timer.Timer(overall_timeout)
            tree_sequence_timer.start()
        depth_timeout = overall_timeout / 2 / (max_depth-1) if max_depth > 1 else overall_timeout
        best_assignment = None
        for depth in range(max_depth):
            self.colored_mdp = self.colored_mdp_factory.reset_tree(depth)
            synthesizer = SynthesizerARDt(self.colored_mdp, self.task)
            best_assignment_old = best_assignment

            parameter_space = self.colored_mdp.parameter_space
            node = synthesizer.search_node_type(parameter_space)
            synthesizer.explored = 0
            synthesizer.stat = paynt.synthesizer.statistic.Statistic(synthesizer)
            synthesizer.stat.start(parameter_space)
            timeout = depth_timeout if depth < max_depth-1 else overall_timeout / 2 # second half of the time for the last depth
            synthesizer.synthesis_timer = paynt.utils.timer.Timer(timeout)
            synthesizer.synthesis_timer.start()
            nodes = [node]

            if self.best_tree is not None:
                parameter_subspace = parameter_space.copy()
                self.colored_mdp.decision_tree.root.apply_hint(parameter_subspace,self.best_tree.root)
                nodes = [synthesizer.search_node_type(parameter_subspace),node]

            for n in nodes:
                synthesizer.synthesize_one(n)
            synthesizer.stat.finished_synthesis()
            synthesizer.stat.print()
            synthesizer.synthesis_timer = None

            best_assignment = synthesizer.best_assignment
            new_assignment_synthesized = best_assignment != best_assignment_old
            if new_assignment_synthesized:
                logger.info("printing synthesized assignment below:")
                logger.info(best_assignment)

                if best_assignment is not None and best_assignment.size == 1:
                    dtmc = self.colored_mdp.build_assignment(best_assignment)
                    result = dtmc.check_specification(self.task.specification)
                    logger.info(f"double-checking specification satisfiability: {result}")

                self.best_tree = self.colored_mdp.decision_tree
                self.best_tree.root.associate_assignment(best_assignment)
                self.best_tree_value = synthesizer.best_assignment_value

                if break_if_found or (opt_result_value != 0 and abs( (synthesizer.best_assignment_value-opt_result_value)/opt_result_value ) < 1e-3) or (opt_result_value == 0 and synthesizer.best_assignment_value < 1e-3):
                    break

            if synthesizer.resource_limit_reached() or tree_sequence_timer is not None and tree_sequence_timer.time_limit_reached():
                break

    def map_scheduler(self, scheduler_choices, tree_depth=None):
        if tree_depth is None:
            tree_depth = self.task.tree_depth
        for depth in range(tree_depth+1):
            self.colored_mdp = self.colored_mdp_factory.reset_tree(depth,enable_harmonization=False)
            synthesizer = SynthesizerARDt(self.colored_mdp, self.task)
            node = synthesizer.search_node_type(self.colored_mdp.parameter_space.copy())
            node.analysis_result = synthesizer.build_unsat_result()
            node.mdp, node.selected_choices = self.colored_mdp.build(node.parameter_space)
            consistent,parameter_selection = self.colored_mdp.are_choices_consistent(scheduler_choices, node.parameter_space)
            if consistent:
                synthesizer.verify_parameter_selection(node,parameter_selection)
                if synthesizer.best_assignment is not None:
                    self.best_tree = self.colored_mdp.decision_tree
                    self.best_tree.root.associate_assignment(synthesizer.best_assignment)
                    self.best_tree_value = synthesizer.best_assignment_value
                    break

            if synthesizer.resource_limit_reached():
                break

    def run(self, optimum_threshold=None):
        scheduler_choices = None
        if self.task.scheduler_path is None:
            paynt_mdp = paynt.underlying_model.underlying_model.Mdp(self.colored_mdp.underlying_mdp)
            mc_result = paynt_mdp.model_check_property(self.task.get_property())
        else:
            opt_result_value = None
            with open(self.task.scheduler_path, 'r') as f:
                scheduler_json = json.load(f)
            scheduler_choices,scheduler_json_relevant = self.colored_mdp.scheduler_json_to_choices(scheduler_json, discard_unreachable_states=True)

            submdp = self.colored_mdp.build_from_choice_mask(scheduler_choices)
            mc_result = submdp.model_check_property(self.task.get_property())
        opt_result_value = mc_result.value
        logger.info(f"the optimal scheduler has value: {opt_result_value}")

        if self.colored_mdp.DONT_CARE_ACTION_LABEL in self.colored_mdp.action_labels:
            random_choices = self.colored_mdp.get_random_choices()
            submdp_random = self.colored_mdp.build_from_choice_mask(random_choices)
            mc_result_random = submdp_random.model_check_property(self.task.get_property())
            random_result_value = mc_result_random.value
            logger.info(f"the random scheduler has value: {random_result_value}")

        self.best_tree = self.best_tree_value = None
        if scheduler_choices is not None:
            self.map_scheduler(scheduler_choices)
        else:
            if self.task.specification.has_optimality:
                epsilon = 1e-1
                mc_result_positive = opt_result_value > 0
                if self.task.specification.optimality.maximizing == mc_result_positive:
                    epsilon *= -1
            # equivalent to Synthesizer.set_optimality_threshold, inlined since this outer driver isn't a
            # Synthesizer subclass itself (only the inner SynthesizerARDt engines it constructs are)
            if self.task.specification.has_optimality and optimum_threshold is not None:
                self.task.specification.optimality.update_optimum(optimum_threshold)

            if not self.task.tree_enumeration:
                self.synthesize_tree(self.task.tree_depth)
            else:
                self.synthesize_tree_sequence(opt_result_value)

        logger.info(f"the optimal scheduler has value: {opt_result_value}")
        if self.colored_mdp.DONT_CARE_ACTION_LABEL in self.colored_mdp.action_labels:
            logger.info(f"the random scheduler has value: {random_result_value}")
        if self.best_tree is None:
            logger.info("no admissible tree found")
        else:
            relevant_state_valuations = [self.colored_mdp.relevant_state_valuations[state] for state in self.colored_mdp.state_is_relevant_bv]
            self.best_tree.simplify(relevant_state_valuations)
            depth = self.best_tree.get_depth()
            num_nodes = len(self.best_tree.collect_nonterminals())
            logger.info(f"synthesized tree of depth {depth} with {num_nodes} decision nodes")
            if self.task.specification.has_optimality:
                logger.info(f"the synthesized tree has value {self.best_tree_value}")
                if self.colored_mdp.DONT_CARE_ACTION_LABEL in self.colored_mdp.action_labels:
                    logger.info(f"the synthesized tree has relative value: {self.compute_normalized_value(self.best_tree_value, opt_result_value, random_result_value)}")
            logger.info(f"printing the synthesized tree below:")
            logger.info(f"\n{self.best_tree.to_string()}")

            if self.task.export_synthesis_filename_base is not None:
                self.export_decision_tree(self.best_tree, self.task.export_synthesis_filename_base)

        time_total = round(paynt.utils.timer.GlobalTimer.read(),2)
        logger.info(f"synthesis finished after {time_total} seconds")

        return paynt.dt.result.DtResult(success=self.best_tree is not None, value=self.best_tree_value, tree=self.best_tree)
