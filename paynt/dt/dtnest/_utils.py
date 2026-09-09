from __future__ import annotations

from typing import Any, Literal

import payntbind
import stormpy

import paynt.specification.property
from ..decision_tree import DecisionTree, DecisionTreeNode

from math import floor

from sklearn import tree

import logging
logger = logging.getLogger(__name__)


def reduce_constraint_to_optimality(specification : paynt.specification.property.Specification) -> tuple[paynt.specification.property.Specification, paynt.specification.property.Property]:
    '''
    dtnest has no mechanism to check a constraint directly -- it always works from a single optimality-shaped
    query: a numeric target to approximate, plus a real optimal scheduler to seed its initial tree from. A
    specification with no optimality objective but exactly one constraint (e.g. P>=0.95 [F "goal"]) can still
    be handled: the constraint's own Property.formula is already the bound-free, direction-correct
    quantitative formula (computed once from the original comparison operator in Property.__init__), so
    building an OptimalityProperty from it is exactly "drop the bound, keep the direction" (P>=0.95 becomes
    Pmax=?).
    :returns (new_specification, constraint) -- new_specification is a single-optimality-property
        specification usable by the rest of DtNest.run() exactly like a genuine optimality objective;
        the caller uses constraint.threshold/.minimizing to drive DtNest's own epsilon-based acceptance
        test at the user's real, original threshold (see classify_constraint_threshold below), instead of
        silently discarding it in favor of chasing epsilon-close-to-the-true-optimum
    '''
    assert specification.optimality is None
    assert len(specification.constraints) == 1
    constraint = specification.constraints[0]
    raw_property = stormpy.Property("", constraint.formula.clone())
    optimality_property = paynt.specification.property.construct_property(raw_property, relative_error=0, use_exact=constraint.use_exact)
    new_specification = paynt.specification.property.Specification([optimality_property])
    return new_specification, constraint


def classify_constraint_threshold(
    opt_result_value : float, random_result_value : float | None, user_threshold : float, minimizing : bool
) -> tuple[Literal["unsat", "trivial", "ok"], float | None]:
    '''
    Relate a constraint's own threshold (e.g. the 0.95 in P>=0.95) to what DtNest can already compute --
    the true optimum (opt_result_value) and, usually, the random/don't-care scheduler's value
    (random_result_value) -- to decide how DtNest's epsilon-based acceptance test should treat it:
    :returns ("unsat", None) if even the optimal scheduler cannot clear the threshold -- no admissible tree exists
    :returns ("trivial", None) if the random/don't-care scheduler already clears the threshold on its own --
        no search needed, the trivial random tree already satisfies the request
    :returns ("ok", epsilon) otherwise, where epsilon is the value that reproduces
        eps_optimum_threshold == user_threshold exactly through the same formulas already used for a plain
        optimality objective (see synthesize_subtrees) -- i.e. the constraint is treated as "accept any tree
        whose value clears user_threshold", not "get epsilon-close to the unconstrained optimum"
    '''
    def clears(value : float) -> bool:
        return value <= user_threshold if minimizing else value >= user_threshold

    if not clears(opt_result_value):
        return "unsat", None
    if random_result_value is not None:
        if clears(random_result_value):
            return "trivial", None
        # opt clears and random doesn't, so opt != random -- safe to divide
        return "ok", (opt_result_value - user_threshold) / (opt_result_value - random_result_value)
    # no random baseline to interpolate against or compare trivial-satisfaction with
    if opt_result_value == 0:
        # opt*(1+epsilon) can only ever reproduce 0 itself; clears(opt_result_value) already confirmed
        # user_threshold is on the lenient side of 0, so treat this as already exactly at the boundary
        logger.warning(
            "requested threshold cannot be related to the optimum via a relative epsilon (optimal value is "
            "exactly 0 and no random/don't-care baseline is available) -- requiring an exact match instead")
        return "ok", 0.0
    return "ok", (user_threshold - opt_result_value) / opt_result_value


def dt_to_state_to_actions(decision_tree : DecisionTree, colored_mdp : Any, reachable_states : Any = None) -> list[int]:
    if reachable_states is None:
        reachable_states = stormpy.BitVector(colored_mdp.underlying_mdp.nr_states, True)
    state_to_action = []
    nci = colored_mdp.underlying_mdp.nondeterministic_choice_indices.copy()
    for state in range(colored_mdp.underlying_mdp.nr_states):
        if colored_mdp.state_is_relevant_bv.get(state) and reachable_states.get(state):
            action_index = get_action_for_state(decision_tree.root, colored_mdp, state, colored_mdp.relevant_state_valuations[state], nci)
            state_to_action.append(colored_mdp.choice_to_action[nci[state] + action_index])
        else:
            state_to_action.append(-1)

    return state_to_action


def get_action_for_state(node : DecisionTreeNode, colored_mdp : Any, state : int, state_valuation : list[Any], nci : Any) -> int:
    if node.is_terminal:
        action_index = node.action
        index = 0
        for choice in range(nci[state],nci[state+1]):
            if colored_mdp.choice_to_action[choice] == action_index:
                return index
            index += 1
        else:
            # TODO as far as I know this happens only because of unreachable states not being included in the tree
            # for now we will treat this by using the __random__ action but it can lead to strange behaviour
            index = 0
            for choice in range(nci[state],nci[state+1]):
                if colored_mdp.action_labels[colored_mdp.choice_to_action[choice]] == "__random__":
                    return index
                index += 1
            assert False
    # node is not terminal here (handled above), so variable/variable_bound/child_true/child_false are all
    # guaranteed set -- decision_tree.py's own fields are typed Optional since they're genuinely None before
    # a node has children, but this function only ever recurses past that point
    assert node.variable is not None and node.variable_bound is not None
    assert node.child_true is not None and node.child_false is not None
    var = colored_mdp.variables[node.variable]
    bound = var.domain[node.variable_bound]
    if state_valuation[node.variable] <= bound:
        return get_action_for_state(node.child_true, colored_mdp, state, state_valuation, nci)
    else:
        return get_action_for_state(node.child_false, colored_mdp, state, state_valuation, nci)


def get_states_satisfying_predicate(dt_colored_mdp_factory : Any, node : DecisionTreeNode, current_states : Any, leq : bool = True) -> Any:
    bound = dt_colored_mdp_factory.variables[node.variable].domain[node.variable_bound]
    for state,state_valuation in enumerate(dt_colored_mdp_factory.relevant_state_valuations):
        if not current_states.get(state):
            continue
        if leq and state_valuation[node.variable] > bound:
            current_states.set(state, False)
        elif not leq and state_valuation[node.variable] <= bound:
            current_states.set(state, False)
    return current_states

def get_state_space_for_tree_helper_node(dt_colored_mdp_factory : Any, node_id : int) -> Any:
    node = dt_colored_mdp_factory.tree_helper_tree.collect_nodes(lambda node : node.identifier == node_id)[0]
    current_node = node
    states = stormpy.storage.BitVector(dt_colored_mdp_factory.underlying_mdp.nr_states, True)
    while current_node.parent is not None:
        parent_node = current_node.parent
        if parent_node.child_true.identifier == current_node.identifier:
            states = get_states_satisfying_predicate(dt_colored_mdp_factory, parent_node, states, leq=True)
        else:
            states = get_states_satisfying_predicate(dt_colored_mdp_factory, parent_node, states, leq=False)
        current_node = parent_node
    return states

def get_chosen_action_for_state_from_tree_helper(dt_colored_mdp_factory : Any, state : int, tree : DecisionTree) -> str:
    state_valuation = dt_colored_mdp_factory.relevant_state_valuations[state]
    current_node = tree.root
    while not current_node.is_terminal:
        assert current_node.variable is not None and current_node.variable_bound is not None
        assert current_node.child_true is not None and current_node.child_false is not None
        bound = dt_colored_mdp_factory.variables[current_node.variable].domain[current_node.variable_bound]
        next_node = current_node.child_true if state_valuation[current_node.variable] <= bound else current_node.child_false
        assert next_node is not None
        current_node = next_node
    assert current_node.action is not None
    return dt_colored_mdp_factory.action_labels[current_node.action]

def get_selected_choices_from_tree_helper(dt_colored_mdp_factory : Any, state_to_exclude : Any, tree : DecisionTree | None = None) -> Any:
    if tree is None:
        tree = dt_colored_mdp_factory.tree_helper_tree
    selected_choices = stormpy.storage.BitVector(dt_colored_mdp_factory.underlying_mdp.nr_choices, False)
    mdp_nci = dt_colored_mdp_factory.underlying_mdp.nondeterministic_choice_indices.copy()
    for state in range(dt_colored_mdp_factory.underlying_mdp.nr_states):
        if state_to_exclude.get(state) or dt_colored_mdp_factory.state_is_relevant_bv.get(state) == False:
            for choice in range(mdp_nci[state],mdp_nci[state+1]):
                selected_choices.set(choice, True)
            continue
        chosen_action_label = get_chosen_action_for_state_from_tree_helper(dt_colored_mdp_factory, state, tree)
        action_index = dt_colored_mdp_factory.action_labels.index(chosen_action_label)
        for choice in range(mdp_nci[state],mdp_nci[state+1]):
            if dt_colored_mdp_factory.choice_to_action[choice] == action_index:
                selected_choices.set(choice, True)
                break
        else:
            # TODO as far as I know this happens only because of unreachable states not being included in the tree
            # for now we will treat this by using the __random__ action but it can lead to strange behaviour
            for choice in range(mdp_nci[state],mdp_nci[state+1]):
                if dt_colored_mdp_factory.action_labels[dt_colored_mdp_factory.choice_to_action[choice]] == "__random__":
                    selected_choices.set(choice, True)
                    break
            continue
            assert False, f"no choice for state {state} even though action {chosen_action_label} was chosen"

    return selected_choices


def build_tree_helper_tree(dt_colored_mdp_factory : Any, tree_helper : Any = None) -> DecisionTree:
    if tree_helper is None:
        tree_helper = dt_colored_mdp_factory.tree_helper
    helper_tree = DecisionTree(dt_colored_mdp_factory.action_labels,dt_colored_mdp_factory.variables)
    helper_tree.build_from_tree_helper(tree_helper)
    return helper_tree

# unfixed_states is a bitvector of states that should be left unfixed in the submdp
def get_submdp_from_unfixed_states(dt_colored_mdp_factory : Any, unfixed_states : Any = None) -> Any:
    if unfixed_states is None:
        unfixed_states = stormpy.storage.BitVector(dt_colored_mdp_factory.underlying_mdp.nr_states, False)
    selected_choices = get_selected_choices_from_tree_helper(dt_colored_mdp_factory, unfixed_states)
    submdp = dt_colored_mdp_factory.build_from_choice_mask(selected_choices)
    return submdp

# in dtNest, there might be an MDP for a subtree with no relevant states, in that case we want to replace this subtree with a random action
def create_uniform_random_tree(dt_colored_mdp_factory : Any) -> DecisionTree:
    decision_tree = DecisionTree(dt_colored_mdp_factory.action_labels,dt_colored_mdp_factory.variables)
    decision_tree.random_tree()
    return decision_tree


def state_to_choice_to_state_to_action(state_to_choice : list[int | None], colored_mdp : Any) -> list[int]:
    state_to_action = []
    for state in range(colored_mdp.underlying_mdp.nr_states):
        if state_to_choice[state] is None or not colored_mdp.state_is_relevant_bv.get(state):
            state_to_action.append(-1)
        else:
            state_to_action.append(colored_mdp.choice_to_action[state_to_choice[state]])

    return state_to_action

def scikit_tree_to_tree_helper(clf : Any, variables : list[Any], action_labels : list[str]) -> list[dict[str, Any]]:
    helper = []
    num_nodes = clf.tree_.node_count

    for i in range(num_nodes):
        if clf.tree_.children_left[i] == -1: # leaf node
            # we will determinize the scikit leaf node by choosing the action with the highest representation in the leaf node
            chosen_idx = clf.tree_.value[i].argmax()
            helper.append({'id': i, 'leaf': True, 'chosen': [action_labels[chosen_idx]]})
            continue

        variable = variables[clf.tree_.feature[i]].name
        threshold = floor(clf.tree_.threshold[i])

        helper.append({'id': i, 'leaf': False, 'chosen': (variable, threshold), 'children': [int(clf.tree_.children_left[i]), int(clf.tree_.children_right[i])]})

    return helper

def run_scikit_learn_tree(
    state_valuations : list[Any], state_to_action : list[int], variables : list[Any], action_labels : list[str],
    filter_unreachable : bool = True, max_depth : int | None = None, min_samples_leaf : int = 1
) -> list[dict[str, Any]]:

    X = state_valuations
    Y = state_to_action

    if filter_unreachable:
        X = [x for j, x in enumerate(state_valuations) if state_to_action[j] != -1]
        Y = [y for j, y in enumerate(state_to_action) if state_to_action[j] != -1]

    adjusted_action_labels = [x for i, x in enumerate(action_labels) if i in Y]

    clf = tree.DecisionTreeClassifier(max_depth=max_depth, min_samples_leaf=min_samples_leaf)
    clf = clf.fit(X, Y)

    scikit_tree_helper = scikit_tree_to_tree_helper(clf, variables, adjusted_action_labels)
    
    return scikit_tree_helper