import paynt.synthesizer.synthesizer
import paynt.specification.property_result
import paynt.underlying_model.underlying_model
import paynt.utils.scoring

import logging
logger = logging.getLogger(__name__)


def scheduler_scores(colored_mdp, task, mdp, prop, result, selection):
    inconsistent_assignments = {parameter:options for parameter,options in enumerate(selection) if len(options) > 1}
    choice_values = paynt.underlying_model.underlying_model.ModelIndex.choice_values(mdp.model, prop, result.get_values())
    choices = result.scheduler.compute_action_support(mdp.model.nondeterministic_choice_indices)
    expected_visits = paynt.underlying_model.underlying_model.ModelIndex.compute_expected_visits(
        mdp.model, prop, choices, disable_expected_visits=task.disable_expected_visits)
    # POMDP has a specialized, hand-optimized scorer for the common posterior-unaware case; every other
    # colored-MDP variant (and posterior-aware POMDPs) uses the generic implementation. Dispatched by
    # feature_kind, not an isinstance check, so this module never needs to import paynt.pomdp.
    if colored_mdp.feature_kind == "pomdp" and not colored_mdp.posterior_aware:
        scores = paynt.utils.scoring.estimate_scheduler_difference_pomdp(
            colored_mdp, mdp.model, mdp.underlying_mdp_choice_map, inconsistent_assignments, choice_values, expected_visits)
    else:
        scores = paynt.utils.scoring.estimate_scheduler_difference(
            colored_mdp, mdp.model, mdp.underlying_mdp_choice_map, inconsistent_assignments, choice_values, expected_visits)
    return scores


def split_parameter_space(colored_mdp, task, node):
    '''
    AR splitting step: pick the highest-scoring inconsistent parameter and split node's parameter_space
    options for it into subspaces, wrapped as child search nodes. A free function rather than a ColoredMdp
    method, so it works uniformly across every colored-MDP variant without any of them carrying
    search-decision logic themselves, and so it can be passed around as a plain callable on a future
    multiprocessing path.
    :param colored_mdp anything exposing .parameter_space/.coloring -- any ColoredMdp qualifies
    :param task the Task currently being solved (not read from colored_mdp -- it doesn't carry one)
    :param node the SearchNode currently being split
    '''
    mdp = node.mdp
    assert not mdp.is_deterministic

    # split wrt last undecided result
    result = node.analysis_result.undecided_result()
    parameter_assignments = result.primary_selection
    scores = scheduler_scores(colored_mdp, task, mdp, result.prop, result.primary.result, result.primary_selection)
    if scores is None:
        scores = {parameter:0 for parameter in range(mdp.parameter_space.num_parameters) if mdp.parameter_space.parameter_num_options(parameter) > 1}

    splitters = paynt.utils.scoring.parameters_with_max_score(scores)
    splitter = splitters[0]
    if len(parameter_assignments[splitter]) > 1:
        core_suboptions,other_suboptions = mdp.parameter_space.suboptions_enumerate(splitter, parameter_assignments[splitter])
    else:
        assert mdp.parameter_space.parameter_num_options(splitter) > 1
        core_suboptions = mdp.parameter_space.suboptions_half(splitter)
        other_suboptions = []

    if len(other_suboptions) == 0:
        suboptions = core_suboptions
    else:
        suboptions = [other_suboptions] + core_suboptions  # DFS solves core first

    # construct corresponding child search nodes (SearchNode.split snapshots node's ParentInfo-relevant
    # state and hands it to each freshly-split child, same as add_parent_info used to do manually here)
    return node.split(splitter, suboptions)


class SynthesizerAR(paynt.synthesizer.synthesizer.Synthesizer):

    @property
    def method_name(self):
        return "AR"

    def check_specification(self, node):
        ''' Check specification for mdp or smg based on self.colored_mdp '''
        mdp = node.mdp

        if self.colored_mdp.feature_kind == "posmg":
            model = self.colored_mdp.create_smg_from_mdp(mdp)
        else:
            model = mdp

        # check constraints
        admissible_assignment = None
        spec = self.task.specification
        if node.constraint_indices is None:
            node.constraint_indices = spec.all_constraint_indices()
        results = [None for _ in spec.constraints]
        for index in node.constraint_indices:
            constraint = spec.constraints[index]
            result = paynt.specification.property_result.MdpPropertyResult(constraint)
            results[index] = result

            # check primary direction
            result.primary = model.model_check_property(constraint)
            if result.primary.sat is False:
                result.sat = False
                break

            # check if the primary scheduler is consistent
            result.primary_selection,consistent = self.colored_mdp.scheduler_is_consistent(mdp, node, result.primary.result, self.task.specification)
            if consistent:
                assignment = node.parameter_space.assume_options_copy(result.primary_selection)
                dtmc = self.colored_mdp.build_assignment(assignment)
                res = dtmc.check_specification(self.task.specification)
                if res.accepting_dtmc(self.task.specification):
                    result.sat = True
                    admissible_assignment = assignment

            # primary direction is SAT: check secondary direction to see whether all SAT
            result.secondary = model.model_check_property(constraint, alt=True)
            if mdp.is_deterministic and result.primary.value != result.secondary.value:
                logger.warning("WARNING: model is deterministic but min<max")
            if result.secondary.sat:
                result.sat = True
                continue

        spec_result = paynt.specification.property_result.MdpSpecificationResult()
        spec_result.constraints_result = paynt.specification.property_result.ConstraintsResult(results)

        # check optimality
        if spec.has_optimality and not spec_result.constraints_result.sat is False:
            opt = spec.optimality
            result = paynt.specification.property_result.MdpOptimalityResult(opt)

            # check primary direction
            result.primary = model.model_check_property(opt)
            if not result.primary.improves_optimum:
                # OPT <= LB
                result.can_improve = False
            else:
                # LB < OPT, check if LB is tight
                result.primary_selection,consistent = self.colored_mdp.scheduler_is_consistent(mdp, node, result.primary.result, self.task.specification)
                result.can_improve = True
                if consistent:
                    # LB < OPT and it's tight, double-check the constraints and the value on the DTMC
                    result.can_improve = False
                    assignment = node.parameter_space.assume_options_copy(result.primary_selection)
                    dtmc = self.colored_mdp.build_assignment(assignment)
                    res = dtmc.check_specification(self.task.specification)
                    if res.constraints_result.sat and spec.optimality.improves_optimum(res.optimality_result.value):
                        result.improving_assignment = assignment
                        result.improving_value = res.optimality_result.value
            spec_result.optimality_result = result

        spec_result.evaluate(node.parameter_space, admissible_assignment)
        node.analysis_result = spec_result

    def verify_parameter_space(self, node):
        node.mdp, node.selected_choices = self.colored_mdp.build(node.parameter_space)

        # TODO include iteration_game in iteration? is it necessary?
        if self.colored_mdp.feature_kind == "posmg":
            self.stat.iteration_game(node.mdp.states)
        else:
            self.stat.iteration(node.mdp)

        self.check_specification(node)

    def update_optimum(self, node):
        ia = node.analysis_result.improving_assignment
        if ia is None:
            return
        if not self.task.specification.has_optimality:
            self.best_assignment = ia
            return
        iv = node.analysis_result.improving_value
        if not self.task.specification.optimality.improves_optimum(iv):
            return
        self.task.specification.optimality.update_optimum(iv)
        self.best_assignment = ia
        self.best_assignment_value = iv
        # logger.info(f"value {round(iv,4)} achieved after {round(paynt.utils.timer.GlobalTimer.read(),2)} seconds")
        if self.colored_mdp.feature_kind == "pomdp":
            self.stat.new_fsc_found(node.analysis_result.improving_value, ia, self.colored_mdp.policy_size(ia))

    def synthesize_one(self, node):
        nodes = [node]
        while nodes:
            if self.resource_limit_reached():
                break
            node = nodes.pop(-1)
            self.verify_parameter_space(node)
            self.update_optimum(node)
            if not self.task.specification.has_optimality and self.best_assignment is not None:
                break
            # break
            if node.analysis_result.can_improve is False:
                self.explore(node.parameter_space)
                continue
            # undecided
            child_nodes = self.split_undecided_space(node)
            nodes = nodes + child_nodes
        return self.best_assignment

    def split_undecided_space(self, node):
        '''
        Overridable hook: the default just delegates to the shared split_parameter_space free function.
        DtSynthesizer overrides this since decision-tree splitting classifies parameters by kind
        (action/decision/variable) rather than by scored inconsistency variance -- a genuinely different
        algorithm, not a performance variant of this one (unlike POMDP's scheduler_scores specialization).
        '''
        return split_parameter_space(self.colored_mdp, self.task, node)
