import paynt.synthesizer.synthesizer_ar
import paynt.synthesizer.statistic
import paynt.utils.timer
import paynt.utils.scoring
import paynt.underlying_model.underlying_model
import paynt.specification.property_result

import paynt.dt.result

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


class SynthesizerARDt(paynt.synthesizer.synthesizer_ar.SynthesizerAR):
    '''
    AR specialized for decision-tree synthesis: splits by parameter kind (action/decision/variable) rather
    than by scored inconsistency variance, and adds harmonization (retrying an inconsistent scheduler
    selection against both directions of one parameter before giving up) plus a "scheduler preserved across
    split" shortcut specific to how DtColoredMdp.scheduler_is_consistent reports single-property results.
    This is the inner search engine; the outer DtSynthesizer constructs a fresh instance of this class for
    every tree depth it tries, mirroring the SynthesizerARStorm/SayntSynthesizer split.
    '''

    def __init__(self, colored_mdp, task):
        super().__init__(colored_mdp, task)
        self.counters_reset()

    @property
    def method_name(self):
        return "AR (decision tree)"

    def verify_parameter_selection(self, parameter_space, parameter_selection):
        spec = self.task.specification
        assignment = parameter_space.assume_options_copy(parameter_selection)
        dtmc = self.colored_mdp.build_assignment(assignment)
        res = dtmc.check_specification(spec)
        if not res.constraints_result.sat:
            return
        if not spec.has_optimality:
            parameter_space.analysis_result.improving_assignment = assignment
            parameter_space.analysis_result.can_improve = False
            return
        assignment_value = res.optimality_result.value
        if spec.optimality.improves_optimum(assignment_value):
            # logger.info(f"harmonization achieved value {res.optimality_result.value}")
            self.num_harmonization_succeeded += 1
            parameter_space.analysis_result.improving_assignment = assignment
            parameter_space.analysis_result.improving_value = assignment_value
            parameter_space.analysis_result.can_improve = True
            self.update_optimum(parameter_space)


    def harmonize_inconsistent_scheduler(self, parameter_space):
        self.num_harmonizations += 1
        mdp = parameter_space.mdp
        result = parameter_space.analysis_result.undecided_result()
        parameter_selection = result.primary_selection
        harmonizing_parameter = [parameter for parameter,options in enumerate(parameter_selection) if len(options)>1][0]
        selection_1 = parameter_selection.copy(); selection_1[harmonizing_parameter] = [selection_1[harmonizing_parameter][0]]
        selection_2 = parameter_selection.copy(); selection_2[harmonizing_parameter] = [selection_2[harmonizing_parameter][1]]
        for selection in [selection_1,selection_2]:
            self.verify_parameter_selection(parameter_space,selection)


    def verify_parameter_space(self, parameter_space):
        self.num_parameter_spaces_considered += 1
        self.colored_mdp.build(parameter_space)

        self.stat.iteration(parameter_space.mdp)
        # scheduler_choices is only ever populated by DtColoredMdp.scheduler_is_consistent when the
        # specification is single-property (see split_undecided_space below) -- for a multi-property specification
        # it stays None on every parameter space, so the "scheduler preserved" shortcut must be skipped rather than
        # assumed available, falling through to a real (slower, but correct) model-check instead.
        if parameter_space.parent_info is not None and parameter_space.parent_info.scheduler_choices is not None:
            for choice in parameter_space.parent_info.scheduler_choices:
                if not parameter_space.selected_choices[choice]:
                    break
            else:
                # scheduler preserved in the sub-parameter-space
                self.num_schedulers_preserved += 1
                parameter_space.analysis_result = parameter_space.parent_info.analysis_result
                parameter_space.scheduler_choices = parameter_space.parent_info.scheduler_choices
                consistent,parameter_selection = self.colored_mdp.are_choices_consistent(parameter_space.scheduler_choices, parameter_space)
                assert not consistent
                if parameter_space.analysis_result.optimality_result is None:
                    for constraint_res in parameter_space.analysis_result.constraints_result.results:
                        constraint_res.primary_selection = parameter_selection
                else:
                    parameter_space.analysis_result.optimality_result.primary_selection = parameter_selection
                return

        self.num_parameter_spaces_model_checked += 1
        self.check_specification(parameter_space)
        if not parameter_space.analysis_result.can_improve:
            return
        self.harmonize_inconsistent_scheduler(parameter_space)

    def build_unsat_result(self):
        spec_result = paynt.specification.property_result.MdpSpecificationResult()
        spec_result.constraints_result = paynt.specification.property_result.ConstraintsResult([])
        spec_result.optimality_result = paynt.specification.property_result.MdpOptimalityResult(None)
        spec_result.evaluate(None)
        spec_result.can_improve = False
        return spec_result

    def scheduler_scores(self, selection):
        ''' Decision-tree splitting heuristic: classify inconsistent parameters by kind (action/decision/
        variable) and pick one deterministically, rather than scoring by choice-value variance -- a
        genuinely different algorithm from the shared AR default, not a performance variant of it. '''
        inconsistent_assignments = {parameter:options for parameter,options in enumerate(selection) if len(options) > 1 }
        assert len(inconsistent_assignments) > 0, f"obtained selection with no inconsistencies: {selection}"
        inconsistent_action_parameters = [(parameter,options) for parameter,options in inconsistent_assignments.items() if self.colored_mdp.is_action_parameter[parameter]]
        inconsistent_decision_parameters = [(parameter,options) for parameter,options in inconsistent_assignments.items() if self.colored_mdp.is_decision_parameter[parameter]]
        inconsistent_variable_parameters = [(parameter,options) for parameter,options in inconsistent_assignments.items() if self.colored_mdp.is_variable_parameter[parameter]]

        # choose one splitter
        splitter = None
        # try action or decision parameters first
        if len(inconsistent_action_parameters) > 0:
            splitter = inconsistent_action_parameters[0][0]
        elif len(inconsistent_decision_parameters) > 0:
            splitter = inconsistent_decision_parameters[0][0]
        else:
            splitter = inconsistent_variable_parameters[0][0]
        assert splitter is not None, "splitter not set"
        # force the score of the selected splitter
        return {splitter:10}

    def split_undecided_space(self, parameter_space):
        mdp = parameter_space.mdp
        assert not mdp.is_deterministic

        # split wrt last undecided result
        result = parameter_space.analysis_result.undecided_result()
        parameter_assignments = result.primary_selection
        scores = self.scheduler_scores(result.primary_selection)

        splitters = paynt.utils.scoring.parameters_with_max_score(scores)
        splitter = splitters[0]
        if self.colored_mdp.is_action_parameter[splitter] or self.colored_mdp.is_decision_parameter[splitter]:
            assert len(parameter_assignments[splitter]) > 1
            core_suboptions,other_suboptions = mdp.parameter_space.suboptions_enumerate(splitter, parameter_assignments[splitter])
        else:
            # split by inconsistent options
            splitter_options = parameter_space.parameter_options(splitter)
            option_2 = parameter_assignments[splitter][1]
            index_split = splitter_options.index(option_2)

            core_suboptions = [splitter_options[:index_split], splitter_options[index_split:]]
            for options in core_suboptions: assert len(options) > 0
            other_suboptions = []

        if len(other_suboptions) == 0:
            suboptions = core_suboptions
        else:
            suboptions = [other_suboptions] + core_suboptions  # DFS solves core first

        # construct corresponding parameter_subspaces
        parent_info = parameter_space.collect_parent_info(self.task.specification)
        parent_info.analysis_result = parameter_space.analysis_result
        # None (not just absent) for a multi-property specification -- see the guard in verify_parameter_space
        parent_info.scheduler_choices = getattr(parameter_space, 'scheduler_choices', None)
        # parent_info.unsat_core_hint = self.colored_mdp.coloring.unsat_core.copy()
        parameter_subspaces = parameter_space.split(splitter,suboptions)
        assert parameter_space.size == sum([parameter_subspace.size for parameter_subspace in parameter_subspaces])
        for parameter_subspace in parameter_subspaces:
            parameter_subspace.add_parent_info(parent_info)
        return parameter_subspaces

    def counters_reset(self):
        self.num_parameter_spaces_considered = 0
        self.num_parameter_spaces_skipped = 0
        self.num_parameter_spaces_model_checked = 0
        self.num_schedulers_preserved = 0
        self.num_harmonizations = 0
        self.num_harmonization_succeeded = 0

    # TODO remove, debugging only
    def counters_print(self):
        logger.info(f"families considered: {self.num_parameter_spaces_considered}")
        logger.info(f"families skipped by construction: {self.num_parameter_spaces_skipped}")
        logger.info(f"families with schedulers preserved: {self.num_schedulers_preserved}")
        logger.info(f"families model checked: {self.num_parameter_spaces_model_checked}")
        logger.info(f"harmonizations attempted: {self.num_harmonizations}")
        logger.info(f"harmonizations succeeded: {self.num_harmonization_succeeded}")


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
            synthesizer.explored = 0
            synthesizer.stat = paynt.synthesizer.statistic.Statistic(synthesizer)
            synthesizer.stat.start(parameter_space)
            timeout = depth_timeout if depth < max_depth-1 else overall_timeout / 2 # second half of the time for the last depth
            synthesizer.synthesis_timer = paynt.utils.timer.Timer(timeout)
            synthesizer.synthesis_timer.start()
            parameter_spaces = [parameter_space]

            if self.best_tree is not None:
                parameter_subspace = parameter_space.copy()
                self.colored_mdp.decision_tree.root.apply_hint(parameter_subspace,self.best_tree.root)
                parameter_spaces = [parameter_subspace,parameter_space]

            for ps in parameter_spaces:
                synthesizer.synthesize_one(ps)
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
            parameter_space = self.colored_mdp.parameter_space.copy()
            parameter_space.analysis_result = synthesizer.build_unsat_result()
            self.colored_mdp.build(parameter_space)
            consistent,parameter_selection = self.colored_mdp.are_choices_consistent(scheduler_choices, parameter_space)
            if consistent:
                synthesizer.verify_parameter_selection(parameter_space,parameter_selection)
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

        return self.best_tree
