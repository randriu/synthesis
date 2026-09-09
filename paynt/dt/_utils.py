from __future__ import annotations

from typing import Any

import json

import stormpy

import paynt.dt.decision_tree

import logging
logger = logging.getLogger(__name__)

# TODO make this so that it works for POMDP observation valuations as well
def get_state_valuations(model : Any) -> tuple[list[str], list[list[Any]]]:
    ''' Identify variable names and extract state valuation in the same order. '''
    assert model.has_state_valuations(), "model has no state valuations"
    # get name
    sv = model.state_valuations
    variable_names : list[str] | None = None
    state_valuations = []
    for state in range(model.nr_states):
        valuation = json.loads(str(sv.get_json(state)))
        if variable_names is None:
            variable_names = list(valuation.keys())
        state_valuations.append([valuation[var_name] for var_name in variable_names])

    assert variable_names is not None
    return variable_names, state_valuations

def simplify_tree(tree : paynt.dt.decision_tree.DecisionTree | None, cmdp_factory : Any) -> None:
    ''' Simplify the tree recursively by removing irrelavant leaf nodes.'''
    if tree is None:
        return

    relevant_state_valuations = [cmdp_factory.relevant_state_valuations[state] for state in cmdp_factory.state_is_relevant_bv]
    tree.simplify(relevant_state_valuations)

    return