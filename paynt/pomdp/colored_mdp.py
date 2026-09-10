"""
Colored MDP representing a POMDP: the agent's imperfect-information strategy is unfolded into an FSC
template (see PomdpColoredMdpFactory). Beyond the base representation, a POMDP variant carries export/
policy/FSC/Q-value/belief methods that interpret a synthesized assignment back in terms of the original
POMDP (observations, memory nodes, beliefs) -- concerns specific to this representation, not to search.
"""

from __future__ import annotations

from typing import Any

import stormpy
import stormpy.pomdp
import collections

import paynt.colored_mdp
import paynt.parameter_space.parameter_space
import paynt.specification.property
from paynt.pomdp.fsc import FscFactored

import logging

logger = logging.getLogger(__name__)


class PomdpColoredMdp(paynt.colored_mdp.ColoredMdp):

    feature_kind = "pomdp"

    def __init__(
        self,
        underlying_mdp: Any,
        parameter_space: paynt.parameter_space.parameter_space.ParameterSpace,
        coloring: Any,
        use_exact: bool,
        pomdp: Any,
        pomdp_manager: Any,
        observation_labels: list[str],
        actions_at_observation: list[int],
        action_labels_at_observation: list[list[str]],
        observation_states: list[int],
        observation_memory_size: list[int],
        observation_action_parameters: list[list[int]],
        observation_memory_parameters: list[list[int]],
        parameter_option_to_actions: list[list[list[int]]],
        posterior_aware: bool,
    ):
        super().__init__(underlying_mdp, parameter_space, coloring, use_exact)
        # the original (folded) POMDP and the manager used to unfold it
        self.pomdp = pomdp
        self.pomdp_manager = pomdp_manager
        # a (simplified) label for each observation
        self.observation_labels = observation_labels
        # number of actions available at each observation, and their labels
        self.actions_at_observation = actions_at_observation
        self.action_labels_at_observation = action_labels_at_observation
        # for each observation, number of states associated with it
        self.observation_states = observation_states
        # number of memory states allocated to each observation, for this specific unfolding
        self.observation_memory_size = observation_memory_size
        # for each observation, the action/memory parameters belonging to it, for this specific unfolding
        self.observation_action_parameters = observation_action_parameters
        self.observation_memory_parameters = observation_memory_parameters
        # to each parameter-option pair, a list of actions colored by this combination (reverse coloring)
        self.parameter_option_to_actions = parameter_option_to_actions
        self.posterior_aware = posterior_aware

    @property
    def observations(self) -> int:
        return self.pomdp.nr_observations

    def collect_policy(self, dtmc: Any, mc_result: Any, specification: paynt.specification.property.Specification) -> list[list[dict[int, Any]]]:
        # TODO: move to a util file once SAYNT is reworked -- this interprets a model-checking result back
        # into a POMDP policy, it doesn't need to live on the representation itself
        # assuming single optimizing property
        assert specification.num_properties == 1 and specification.has_optimality
        dtmc_state_value = mc_result.optimality_result.result.get_values()

        # map states of the DTMC to their POMDP counterparts
        # label states with the value achieved in the state
        # group results by observation
        policy = []
        for obs in range(self.observations):
            mem_size = self.observation_memory_size[obs]
            mem_info: list[dict[int, Any]] = [{} for _ in range(mem_size)]
            policy.append(mem_info)

        for dtmc_state in range(dtmc.states):
            value = dtmc_state_value[dtmc_state]
            mdp_state = dtmc.underlying_mdp_state_map[dtmc_state]

            pomdp_state = self.pomdp_manager.state_prototype[mdp_state]
            memory_node = self.pomdp_manager.state_memory[mdp_state]
            observation = self.pomdp.get_observation(pomdp_state)

            policy[observation][memory_node][pomdp_state] = value

        return policy

    def extract_policy(
        self, assignment: paynt.parameter_space.parameter_space.ParameterSpace, specification: paynt.specification.property.Specification
    ) -> list[list[dict[int, Any]]]:
        # TODO: move to a util file once SAYNT is reworked
        dtmc = self.build_assignment(assignment)
        mc_result = dtmc.check_specification(specification)
        return self.collect_policy(dtmc, mc_result, specification)

    def policy_size(self, assignment: paynt.parameter_space.parameter_space.ParameterSpace) -> int:
        """
        Compute how many natural numbers are needed to encode the mu-FSC under the current memory model mu.
        """
        # going through the induced DTMC, too lazy to parse parameter names
        dtmc = self.build_assignment(assignment)

        # size of action function gamma:
        #   for each memory node, a list of prior-action pairs
        size_gamma = sum(self.observation_memory_size)  # explicit

        if not self.posterior_aware:
            # size of update function delta of a posterior-unaware FSC:
            #   for each memory node, a list of prior-update pairs
            size_delta = sum(self.observation_memory_size)  # explicit
            return size_gamma + size_delta

        # posterior-aware update selection
        # for each memory node and for each prior, collect a set of possible posteriors
        max_mem = max(self.observation_memory_size)
        memory_prior_posteriors: list[list[set[int]]] = [[set() for _ in range(self.observations)] for _ in range(max_mem)]
        for state in range(dtmc.states):
            mdp_state = dtmc.underlying_mdp_state_map[state]

            # get prior
            pomdp_state = self.pomdp_manager.state_prototype[mdp_state]
            memory_node = self.pomdp_manager.state_memory[mdp_state]
            prior = self.pomdp.get_observation(pomdp_state)

            # get posterior observations
            for entry in dtmc.model.transition_matrix.get_row(state):
                successor = entry.column
                mdp_successor = dtmc.underlying_mdp_state_map[successor]
                pomdp_successor = self.pomdp_manager.state_prototype[mdp_successor]
                posterior = self.pomdp.get_observation(pomdp_successor)
                memory_prior_posteriors[memory_node][prior].add(posterior)

        # size of update function delta of a posterior-aware FSC:
        #   for each memory node and for each possible prior, a list of posterior-action pairs
        #   assuming sparse representation (not including delimeters)
        size_delta = 0
        for n_prior_posteriors in memory_prior_posteriors:
            for n_z_posteriors in n_prior_posteriors:
                size_delta += 2 * len(n_z_posteriors)

        return size_gamma + size_delta

    def get_parameter_space_pomdp(self, mdp: Any) -> Any:
        """
        Constructs POMDP from a sub-MDP which contains maps to the original underlying (PO)MDP. Used for computing POMDP abstraction bounds.
        """
        no_obs = self.pomdp.nr_observations
        tm = mdp.model.transition_matrix
        components = stormpy.storage.SparseModelComponents(tm, mdp.model.labeling, mdp.model.reward_models)

        full_observ_list = []
        for state in range(self.pomdp.nr_states):
            obs = self.pomdp.get_observation(state)
            for mem in range(self.observation_memory_size[obs]):
                full_observ_list.append(obs + mem * no_obs)

        choice_labeling = stormpy.storage.ChoiceLabeling(mdp.model.nr_choices)

        # assign observations to states
        observ_list = []
        choice_labels = []
        for state in range(mdp.model.nr_states):
            original_state = mdp.underlying_mdp_state_map[state]
            observ_list.append(full_observ_list[original_state])
            actions = list(range(mdp.model.get_nr_available_actions(state)))
            choice_labels.append(actions)

        # construct labeling
        labels_list = [item for sublists in choice_labels for item in sublists]
        labels = list(set(labels_list))
        for label in labels:
            choice_labeling.add_label(str(label))
        for choice in range(mdp.model.nr_choices):
            choice_labeling.add_label_to_choice(str(labels_list[choice]), choice)

        components.choice_labeling = choice_labeling
        components.observability_classes = observ_list

        pomdp = stormpy.storage.SparsePomdp(components)
        return stormpy.pomdp.make_canonic(pomdp)

    def assignment_to_fsc(self, assignment: paynt.parameter_space.parameter_space.ParameterSpace) -> FscFactored:
        assert assignment.size == 1, "expected parameter space of size 1"
        num_nodes = max(self.observation_memory_size)
        fsc = FscFactored(num_nodes, self.observations, is_deterministic=True)
        fsc.observation_labels = self.observation_labels

        # collect action labels
        action_labels_set = set()
        for labels in self.action_labels_at_observation:
            action_labels_set.update(labels)
        all_action_labels = list(action_labels_set)
        fsc.action_labels = all_action_labels

        # map observations to unique indices of available actions
        action_label_indices = {label: index for index, label in enumerate(all_action_labels)}
        observation_to_actions: list[list[int]] = [[] for obs in range(self.observations)]
        for obs, action_labels in enumerate(self.action_labels_at_observation):
            observation_to_actions[obs] = [action_label_indices[label] for label in action_labels]

        fsc.fill_trivial_actions(observation_to_actions)
        fsc.fill_zero_updates()

        # convert parameter assignment to FSC
        for obs, parameters in enumerate(self.observation_action_parameters):
            for node, parameter in enumerate(parameters):
                option = assignment.parameter_options(parameter)[0]
                action_label = self.action_labels_at_observation[obs][option]
                action = action_label_indices[action_label]
                fsc.action_function[node][obs] = action
        for obs, parameters in enumerate(self.observation_memory_parameters):
            for node, parameter in enumerate(parameters):
                option = assignment.parameter_options(parameter)[0]
                fsc.update_function[node][obs] = option

        fsc.fill_implicit_actions_and_updates()
        fsc.check(observation_to_actions)
        return fsc

    def get_induced_dtmc_from_fsc(self, fsc: FscFactored) -> Any:
        # TODO maybe make this into payntbind function if it's slow
        if fsc.is_deterministic:
            fsc_copy = fsc.copy()
            fsc_copy.make_stochastic()
        else:
            fsc_copy = fsc
        action_function = fsc_copy.action_function
        update_function = fsc_copy.update_function
        action_labels = fsc_copy.action_labels
        assert action_labels is not None

        # compute the state space for the induced dtmc
        dtmc_states_map: dict[int, tuple[int, int]] = {}
        state_queue = [(self.pomdp.initial_states[0], 0)]
        dtmc_states_map[len(dtmc_states_map)] = (self.pomdp.initial_states[0], 0)

        while state_queue:
            current_state_memory_pair = state_queue.pop()

            # compute the successor states
            current_obs = self.pomdp.observations[current_state_memory_pair[0]]
            selected_actions = action_function[current_state_memory_pair[1]][current_obs]
            if selected_actions is None:
                continue
            selected_updates = update_function[current_state_memory_pair[1]][current_obs]
            if selected_updates is None:
                continue

            for selected_action in selected_actions.keys():
                for selected_update in selected_updates.keys():
                    selected_action_label = action_labels[selected_action]

                    choice_offset_for_selected_label = self.action_labels_at_observation[current_obs].index(selected_action_label)
                    choice_index = self.pomdp.get_choice_index(current_state_memory_pair[0], choice_offset_for_selected_label)

                    for entry in self.pomdp.transition_matrix.get_row(choice_index):
                        next_state = entry.column
                        next_state_memory_pair = (next_state, selected_update)
                        if next_state_memory_pair not in dtmc_states_map.values():
                            state_queue.append(next_state_memory_pair)
                            dtmc_states_map[len(dtmc_states_map)] = next_state_memory_pair

        # construct the transition matrix
        num_dtmc_states = len(dtmc_states_map)
        dtmc_tm_builder = stormpy.SparseMatrixBuilder(num_dtmc_states, num_dtmc_states, force_dimensions=True)
        state_action_rewards: dict[str, list[Any]] = {name: [] for name in self.pomdp.reward_models.keys()}
        for dtmc_state, current_state_memory_pair in dtmc_states_map.items():
            current_obs = self.pomdp.observations[current_state_memory_pair[0]]
            selected_actions = action_function[current_state_memory_pair[1]][current_obs]
            if selected_actions is None:
                for reward_name in self.pomdp.reward_models.keys():
                    state_action_rewards[reward_name].append(0)
                continue
            selected_updates = update_function[current_state_memory_pair[1]][current_obs]
            if selected_updates is None:
                for reward_name in self.pomdp.reward_models.keys():
                    state_action_rewards[reward_name].append(0)
                continue

            next_state_prob_map = dict.fromkeys(dtmc_states_map.keys(), 0)

            current_reward = dict.fromkeys(self.pomdp.reward_models.keys(), 0)

            for selected_action, action_prob in selected_actions.items():
                selected_action_label = action_labels[selected_action]
                choice_offset_for_selected_label = self.action_labels_at_observation[current_obs].index(selected_action_label)
                choice_index = self.pomdp.get_choice_index(current_state_memory_pair[0], choice_offset_for_selected_label)

                for reward_name, reward_model in self.pomdp.reward_models.items():
                    current_reward[reward_name] += reward_model.state_action_rewards[choice_index] * action_prob

                for selected_update, update_prob in selected_updates.items():

                    for entry in self.pomdp.transition_matrix.get_row(choice_index):
                        next_state = entry.column
                        next_state_memory_pair = (next_state, selected_update)
                        next_state_index_candidates = [index for index, state in dtmc_states_map.items() if state == next_state_memory_pair]
                        assert len(next_state_index_candidates) == 1, "expected unique state for given state memory pair"
                        next_state_index = next_state_index_candidates[0]
                        next_state_prob_map[next_state_index] += entry.value() * action_prob * update_prob

            for reward_name in self.pomdp.reward_models.keys():
                state_action_rewards[reward_name].append(current_reward[reward_name])

            for next_state_index, next_state_prob in next_state_prob_map.items():
                dtmc_tm_builder.add_next_value(dtmc_state, next_state_index, next_state_prob)

        dtmc_tm = dtmc_tm_builder.build()

        # construct the labeling
        dtmc_labeling = stormpy.storage.StateLabeling(num_dtmc_states)
        for label in self.pomdp.labeling.get_labels():
            dtmc_labeling.add_label(label)
        for dtmc_state, current_state_memory_pair in dtmc_states_map.items():
            for label in self.pomdp.labeling.get_labels_of_state(current_state_memory_pair[0]):
                if label == "init" and current_state_memory_pair != (self.pomdp.initial_states[0], 0):  # only (0,0) state is initital
                    continue
                dtmc_labeling.add_label_to_state(label, dtmc_state)

        # construct the reward structure
        dtmc_reward_models: dict[str, Any] = {}
        for reward_name in self.pomdp.reward_models.keys():
            # NOTE: this method has zero callers anywhere in the codebase; found via type-hint work that this
            # line referenced an unbound name (reward_model) -- fixed to what was clearly intended, but left
            # otherwise untouched since nothing currently exercises this code path to verify against
            assert self.pomdp.reward_models[reward_name].has_state_action_rewards, "currently this implementation expects state action rewards"
            dtmc_reward_models[reward_name] = stormpy.SparseRewardModel(optional_state_action_reward_vector=state_action_rewards[reward_name])

        components = stormpy.SparseModelComponents(transition_matrix=dtmc_tm, state_labeling=dtmc_labeling, reward_models=dtmc_reward_models)
        return stormpy.storage.SparseDtmc(components)

    def compute_qvalues(
        self, assignment: paynt.parameter_space.parameter_space.ParameterSpace, specification: paynt.specification.property.Specification
    ) -> list[list[Any]]:
        """
        Given an MDP obtained after applying an FSC to a POMDP, compute for each state s, (reachable) memory node n
        the Q-value Q(s,n).
        :param assignment parameter assignment encoding an FSC; it is assumed the assignment is the one obtained
            for the current unfolding
        :param specification the specification to compute Q-values under; must contain exactly one property
        :note Q(s,n) may be None if (s,n) exists in the unfolded POMDP but is not reachable in the induced DTMC
        """
        # TODO: move to a util file once SAYNT is reworked -- this doesn't need to live on the representation
        # model check
        submdp = self.build_assignment(assignment)
        assert specification.num_properties == 1, "expecting a single property"
        prop = specification.all_properties()[0]
        result = submdp.model_check_property(prop)
        state_submdp_to_value = result.result.get_values()

        # map states of a sub-MDP to the states of the underlying MDP to the state-memory pairs of the POMDPxFSC
        state_memory_value: dict[tuple[int, int], Any] = collections.defaultdict(lambda: None)
        for submdp_state, value in enumerate(state_submdp_to_value):
            mdp_state = submdp.underlying_mdp_state_map[submdp_state]
            pomdp_state = self.pomdp_manager.state_prototype[mdp_state]
            memory_node = self.pomdp_manager.state_memory[mdp_state]
            state_memory_value[(pomdp_state, memory_node)] = value

        # make this mapping total
        memory_size = 1 + max([memory for state, memory in state_memory_value.keys()])
        state_memory_value_total = [[None for memory in range(memory_size)] for state in range(self.pomdp.nr_states)]
        for state in range(self.pomdp.nr_states):
            for memory in range(memory_size):
                value = state_memory_value[(state, memory)]
                if value is None:
                    obs = self.pomdp.observations[state]
                    if memory < self.observation_memory_size[obs]:
                        # case 1: (s,n) exists but is not reachable in the induced DTMC
                        value = None
                    else:
                        # case 2: (s,n) does not exist because n memory was not allocated for s
                        # i.e. (s,n) has the same value as (s,0)
                        value = state_memory_value[(state, 0)]
                state_memory_value_total[state][memory] = value

        return state_memory_value_total

    def next_belief(self, belief: dict[int, float], action_label: str, next_obs: int) -> dict[int, float]:
        any_belief_state = list(belief.keys())[0]
        obs = self.pomdp.observations[any_belief_state]
        action = self.action_labels_at_observation[obs].index(action_label)
        new_belief_acc: dict[int, float] = collections.defaultdict(float)
        self.pomdp.nondeterministic_choice_indices.copy()
        for state, state_prob in belief.items():
            choice = self.pomdp.get_choice_index(state, action)
            for entry in self.pomdp.transition_matrix.get_row(choice):
                next_state = entry.column
                if self.pomdp.observations[next_state] == next_obs:
                    new_belief_acc[next_state] += state_prob * entry.value()
        prob_sum = sum(new_belief_acc.values())
        return {state: prob / prob_sum for state, prob in new_belief_acc.items()}
