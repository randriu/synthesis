'''
Internal splitting-heuristic scoring, shared by every search algorithm that needs to estimate which
parameter to blame for an inconsistent scheduler (SynthesizerAR and its derivatives code, PolicyTreeSynthesizer --
two class hierarchies with no common base, which is why this cannot just be a method on one of them).
Lives under utils/ rather than as a top-level module since it is synthesis-internal support that a
library user never calls directly, not part of the public API.
'''

from __future__ import annotations

from typing import Any

import math

import payntbind

import paynt.colored_mdp


def estimate_scheduler_difference(
    colored_mdp : paynt.colored_mdp.ColoredMdp, mdp : Any, underlying_mdp_choice_map : list[int],
    inconsistent_assignments : dict[int, list[int]], choice_values : list[float], expected_visits : list[float]
) -> dict[int, float]:
    '''
    Default AR-splitting heuristic: estimate, per inconsistent parameter, how much the choice values
    differ across the parameter's options (weighted by expected visits). This is the generic
    implementation shared by every search algorithm; SynthesizerAR exposes it as an overridable hook
    so a specific colored MDP variant (e.g. POMDP) can plug in a specialized version, but the default
    -- and PolicyTreeSynthesizer, which never goes through SynthesizerAR -- both call this directly.
    :param colored_mdp the ColoredMdp providing the parameter space and coloring to score against
    '''
    return payntbind.synthesis.computeInconsistentParameterVariance(
        colored_mdp.parameter_space.native, mdp.nondeterministic_choice_indices, underlying_mdp_choice_map, choice_values,
        colored_mdp.coloring, inconsistent_assignments, expected_visits)


def estimate_scheduler_difference_pomdp(
    colored_mdp : paynt.colored_mdp.ColoredMdp, mdp : Any, underlying_mdp_choice_map : list[int],
    inconsistent_assignments : dict[int, list[int]], choice_values : list[float], expected_visits : list[float]
) -> dict[int, float]:
    '''
    POMDP specialized variant of estimate_scheduler_difference, hand-optimized for posterior-unaware
    unfolding using colored_mdp.parameter_option_to_actions (the reverse coloring built during unfolding) instead
    of the generic payntbind call. Dispatched by feature_kind rather than an isinstance check, so this module
    stays free of a paynt.pomdp import; posterior-aware POMDPs fall back to the generic implementation above,
    exactly like the pre-refactor PomdpQuotient.estimate_scheduler_difference did via super().
    '''
    # create inverse underlying-choice-to-restricted-choice map
    # TODO optimize this for multiple properties
    underlying_to_restricted_action_map : list[int | None] = [None] * colored_mdp.underlying_mdp.nr_choices
    for choice in range(mdp.nr_choices):
        underlying_to_restricted_action_map[underlying_mdp_choice_map[choice]] = choice

    # map choices to their origin states
    choice_to_state = []
    tm = mdp.transition_matrix
    for state in range(mdp.nr_states):
        for choice in tm.get_rows_for_group(state):
            choice_to_state.append(state)

    # for each parameter, compute its difference sum and a number of affected states
    inconsistent_differences : dict[int, float] = {}
    for parameter_index,options in inconsistent_assignments.items():
        difference_sum = 0.0
        states_affected = 0
        edges_0 = colored_mdp.parameter_option_to_actions[parameter_index][options[0]]  # type: ignore[attr-defined]
        for choice_index,_ in enumerate(edges_0):

            choice_0_global = edges_0[choice_index]
            choice_0 = underlying_to_restricted_action_map[choice_0_global]
            if choice_0 is None:
                continue

            source_state = choice_to_state[choice_0]
            source_state_visits = expected_visits[source_state]

            if source_state_visits == 0:
                continue

            state_values = []
            for option in options:
                assert len(colored_mdp.parameter_option_to_actions[parameter_index][option]) > choice_index  # type: ignore[attr-defined]
                choice_global = colored_mdp.parameter_option_to_actions[parameter_index][option][choice_index]  # type: ignore[attr-defined]
                choice = underlying_to_restricted_action_map[choice_global]
                choice_value = choice_values[choice]
                state_values.append(choice_value)

            min_value = min(state_values)
            max_value = max(state_values)
            difference = (max_value - min_value) * source_state_visits
            assert not math.isnan(difference)
            difference_sum += difference
            states_affected += 1

        if states_affected == 0:
            parameter_score = 0.0
        else:
            parameter_score = difference_sum / states_affected
        inconsistent_differences[parameter_index] = parameter_score

    return inconsistent_differences


def parameters_with_max_score(parameter_score : dict[int, float]) -> list[int]:
    max_score = max(parameter_score.values())
    with_max_score = [parameter_index for parameter_index in parameter_score if parameter_score[parameter_index] == max_score]
    return with_max_score
