"""
Colored MDP representing a decision-tree-parametrized MDP: the coloring maps each choice to the tree
node/branch that would select it, and a parameter's options are the decisions available at that tree node
(which variable to branch on, which action to take at a leaf). Unlike the FSC-unfolding representations
(POMDP/POSMG/Dec-POMDP), the tree structure itself is fixed by DtColoredMdpFactory.reset_tree(depth) --
this class holds one specific tree/coloring, not a range of memory sizes.
"""

from __future__ import annotations

from typing import Any


import paynt.colored_mdp
import paynt.parameter_space.parameter_space
import paynt.synthesizer.search_node
import paynt.dt.decision_tree
import paynt.underlying_model.underlying_model
from paynt.dt._utils import get_state_valuations

import logging

logger = logging.getLogger(__name__)


class DtColoredMdp(paynt.colored_mdp.ColoredMdp):

    feature_kind = "dt"

    # label for action executing a random action selection
    DONT_CARE_ACTION_LABEL = "__random__"

    def __init__(
        self,
        underlying_mdp: Any,
        parameter_space: paynt.parameter_space.parameter_space.ParameterSpace,
        coloring: Any,
        use_exact: bool,
        action_labels: list[str],
        choice_to_action: list[int],
        state_is_relevant: list[bool],
        state_is_relevant_bv: Any,
        variables: list[Any],
        relevant_state_valuations: list[Any],
        decision_tree: paynt.dt.decision_tree.DecisionTree,
        is_action_parameter: list[bool],
        is_decision_parameter: list[bool],
        is_variable_parameter: list[bool],
    ):
        super().__init__(underlying_mdp, parameter_space, coloring, use_exact)
        # MDP identity, stable across every reset_tree() call (not just this one tree/depth)
        self.action_labels = action_labels
        self.choice_to_action = choice_to_action
        self.state_is_relevant = state_is_relevant
        self.state_is_relevant_bv = state_is_relevant_bv
        self.variables = variables
        self.relevant_state_valuations = relevant_state_valuations
        # specific to this tree/depth
        self.decision_tree = decision_tree
        self.is_action_parameter = is_action_parameter
        self.is_decision_parameter = is_decision_parameter
        self.is_variable_parameter = is_variable_parameter
        # dtnest-only (paynt.dt.dtnest.synthesizer.DtNest): the externally-learned/incrementally-rebuilt tree
        # dtnest works from, distinct from decision_tree above (the AR-search's own tree template). Not part
        # of plain DtSynthesizer's contract -- declared here purely so their type is known at every dtnest
        # read site, not because every DtColoredMdp genuinely has one.
        self.tree_helper: Any = None
        self.tree_helper_tree: paynt.dt.decision_tree.DecisionTree | None = None

    def build_from_choice_mask(self, choices: Any) -> paynt.underlying_model.underlying_model.SubMdp:
        """Convenience used throughout dt/dtnest: restrict to a choice mask without needing a parameter space."""
        model, state_map, choice_map = paynt.underlying_model.underlying_model.SubmodelBuilder.restrict(
            self.underlying_mdp, choices, self.subsystem_builder_options
        )
        return paynt.underlying_model.underlying_model.SubMdp(model, state_map, choice_map)

    def build(
        self, parameter_space: paynt.parameter_space.parameter_space.ParameterSpace, parent_selected_choices: Any = None
    ) -> tuple[paynt.underlying_model.underlying_model.SubMdp, Any]:
        if parent_selected_choices is None:
            choices = self.coloring.selectCompatibleChoices(parameter_space.native)
        else:
            choices = self.coloring.selectCompatibleChoices(parameter_space.native, parent_selected_choices)
        assert choices.number_of_set_bits() > 0

        mdp = self.build_from_choice_mask(choices)
        mdp.parameter_space = parameter_space
        return mdp, choices

    def are_choices_consistent(self, choices: Any, parameter_space: paynt.parameter_space.parameter_space.ParameterSpace) -> tuple[bool, list[list[int]]]:
        """Separate method for profiling purposes."""
        consistent, parameter_selection = self.coloring.areChoicesConsistent(choices, parameter_space.native)
        for parameter, options in enumerate(parameter_selection):
            assert len(options) == len(set(options)), str(parameter_selection)
            for option in options:
                assert option in parameter_space.parameter_options(
                    parameter
                ), f"option {option} for parameter {parameter} ({parameter_space.parameter_name(parameter)}) is not in the parameter space"
        return consistent, parameter_selection

    def scheduler_is_consistent(
        self, mdp: Any, node: paynt.synthesizer.search_node.SearchNode, result: Any, specification: Any
    ) -> tuple[list[list[int]], bool]:
        """Get parameter options involved in the scheduler selection."""
        scheduler = result.scheduler
        assert scheduler.memoryless and scheduler.deterministic
        state_to_choice = paynt.underlying_model.underlying_model.ModelIndex.scheduler_to_state_to_choice(
            self.underlying_mdp, self.choice_destinations, mdp, scheduler
        )
        choices = paynt.underlying_model.underlying_model.ModelIndex.state_to_choice_to_choices(self.underlying_mdp, state_to_choice)
        if specification.is_single_property:
            node.scheduler_choices = choices  # type: ignore[attr-defined]
        consistent, parameter_selection = self.are_choices_consistent(choices, mdp.parameter_space)
        return parameter_selection, consistent

    def scheduler_json_to_choices(self, scheduler_json: list[Any], discard_unreachable_states: bool = False) -> tuple[Any, list[Any]]:
        variable_name, state_valuations = get_state_valuations(self.underlying_mdp)
        nci = self.underlying_mdp.nondeterministic_choice_indices.copy()
        assert self.underlying_mdp.nr_states == len(scheduler_json)
        state_to_choice = paynt.underlying_model.underlying_model.ModelIndex.empty_scheduler(self.underlying_mdp)
        for state_decision in scheduler_json:
            valuation = [state_decision["s"][name] for name in variable_name]
            for state, state_valuation in enumerate(state_valuations):  # noqa: B007 -- state used below
                if valuation == state_valuation:
                    break
            else:
                raise AssertionError("state valuation not found")

            actions = state_decision["c"]
            assert len(actions) == 1
            action_labels = actions[0]["labels"]
            assert len(action_labels) <= 1
            if len(action_labels) == 0:
                state_to_choice[state] = nci[state]
                continue
            action = self.action_labels.index(action_labels[0])
            # find a choice that executes this action
            for choice in range(nci[state], nci[state + 1]):
                if self.choice_to_action[choice] == action:
                    state_to_choice[state] = choice
                    break
            else:
                raise AssertionError("action is not available in the state")
        # enable implicit actions
        for state, existing_choice in enumerate(state_to_choice):
            if existing_choice is None:
                logger.warning(f"WARNING: scheduler has no action for state {state}")
                state_to_choice[state] = nci[state]

        if discard_unreachable_states:
            state_to_choice = paynt.underlying_model.underlying_model.ModelIndex.discard_unreachable_choices(
                self.underlying_mdp, self.choice_destinations, state_to_choice
            )
        # keep only relevant states
        state_to_choice = [choice if self.state_is_relevant[state] else None for state, choice in enumerate(state_to_choice)]
        choices = paynt.underlying_model.underlying_model.ModelIndex.state_to_choice_to_choices(self.underlying_mdp, state_to_choice)

        scheduler_json_relevant = []
        for state_decision in scheduler_json:
            valuation = [state_decision["s"][name] for name in variable_name]
            for state, state_valuation in enumerate(state_valuations):  # noqa: B007 -- state used below
                if valuation == state_valuation:
                    break
            if state_to_choice[state] is None:
                continue
            scheduler_json_relevant.append(state_decision)

        return choices, scheduler_json_relevant

    def get_random_choices(self) -> Any:
        """Gets all choices that represent random action, used to compute the value of uniformly random scheduler."""
        nci = self.underlying_mdp.nondeterministic_choice_indices.copy()
        state_to_choice = paynt.underlying_model.underlying_model.ModelIndex.empty_scheduler(self.underlying_mdp)
        random_action = self.action_labels.index(DtColoredMdp.DONT_CARE_ACTION_LABEL)
        for state in range(self.underlying_mdp.nr_states):
            for choice in range(nci[state], nci[state + 1]):
                if self.choice_to_action[choice] == random_action:
                    state_to_choice[state] = choice
                    break
        for state, existing_choice in enumerate(state_to_choice):
            if existing_choice is None:
                state_to_choice[state] = nci[state]

        return paynt.underlying_model.underlying_model.ModelIndex.state_to_choice_to_choices(self.underlying_mdp, state_to_choice)
