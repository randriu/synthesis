'''
Constructs a PosmgColoredMdp by unfolding the optimizing player's imperfect-information strategy into an
FSC template of a given memory size. Unlike the family/ factories, this must support re-unfolding at a
larger memory size after construction (PosmgSynthesizer.strategy_iterative increases it step by step), so
set_imperfect_memory_size is a public entry point, not just __init__-time setup: it produces a fresh
PosmgColoredMdp each time rather than mutating the previous one in place, and the caller reassigns.
'''

from __future__ import annotations

from typing import Any

import payntbind

import paynt.colored_mdp
import paynt.posmg.task
from paynt.posmg.colored_mdp import PosmgColoredMdp
import paynt.parameter_space.parameter_space

import logging
logger = logging.getLogger(__name__)


class PosmgColoredMdpFactory:

    def __init__(self, posmg : Any, task : paynt.posmg.task.PosmgTask, use_exact : bool = False):
        self.posmg = posmg
        self.task = task
        self.use_exact = use_exact

        state_players = self.posmg.get_state_player_indications()
        state_obs = self.posmg.get_observations()

        specification = task.specification
        if not specification.has_optimality:
            self.optimizing_player = 0
        else:
            assert specification.optimality is not None
            assert specification.optimality.game_optimizing_player is not None
            self.optimizing_player = specification.optimality.game_optimizing_player

        # POSMG manager used for unfolding the memory model into the underlying MDP
        self.posmg_manager : Any = payntbind.synthesis.PosmgManager(self.posmg, self.optimizing_player)
        # optimizing player observations
        self.opt_player_observations = self.posmg_manager.get_observation_mapping()

        # number of actions available at each optimizing player observation
        self.actions_at_opt_player_observation : dict[int, int] = {obs:0 for obs in self.opt_player_observations}
        for state in range(self.posmg.nr_states):
            if state_players[state] == self.optimizing_player:
                obs = state_obs[state]
                if self.actions_at_opt_player_observation[obs] != 0:
                    assert self.posmg.get_nr_available_actions(state) == self.actions_at_opt_player_observation[obs]
                    continue
                self.actions_at_opt_player_observation[obs] = self.posmg.get_nr_available_actions(state)

        # labels of actions available at each posmg state
        self.action_labels_at_posmg_state : list[list[str]] = [[] for state in range(self.posmg.nr_states)]
        for state in range(self.posmg.nr_states):
            if self.action_labels_at_posmg_state[state] != []:
                continue
            actions = self.posmg.get_nr_available_actions(state)
            for offset in range(actions):
                choice = self.posmg.get_choice_index(state, offset)
                labels = self.posmg.choice_labeling.get_labels_of_choice(choice)
                assert len(labels) <= 1, "expected at most 1 label"
                if len(labels) == 0:
                    label = paynt.colored_mdp.ColoredMdp.EMPTY_LABEL
                else:
                    label = list(labels)[0]
                self.action_labels_at_posmg_state[state].append(label)

        # labels of actions available at each optimizing player observation
        self.action_labels_at_opt_player_observation : dict[int, list[str]] = {}
        for state in range(self.posmg.nr_states):
            if state_players[state] == self.optimizing_player:
                obs = state_obs[state]
                labels = self.action_labels_at_posmg_state[state]
                self.action_labels_at_opt_player_observation[obs] = labels

        # for each optimizing player observation, number of states associated with it
        self.opt_player_observation_states : dict[int, int] = {obs:0 for obs in self.opt_player_observations}
        for state in range(self.posmg.nr_states):
            if state_players[state] == self.optimizing_player:
                obs = state_obs[state]
                self.opt_player_observation_states[obs] += 1

        # number of memory states allocated to each optimizing player observation, and the current unfolding
        self.opt_player_observation_memory_size : dict[int, int] | None = None
        self.current_memory_size : int | None = None
        self.colored_mdp = self.set_imperfect_memory_size(task.memory_size)

    def set_manager_memory_vector(self) -> None:
        assert self.opt_player_observation_memory_size is not None
        for obs, memory in self.opt_player_observation_memory_size.items():
            self.posmg_manager.set_observation_memory_size(obs, memory)

    def set_imperfect_memory_size(self, memory_size : int) -> PosmgColoredMdp:
        ''' (Re-)unfold the optimizing player's FSC template at the given memory size, producing a fresh
        PosmgColoredMdp -- callers reassign their reference (e.g. self.colored_mdp =
        factory.set_imperfect_memory_size(k)) rather than relying on in-place mutation. '''
        self.opt_player_observation_memory_size = {
            obs:(memory_size if obs_states > 1 else 1) for obs, obs_states in self.opt_player_observation_states.items()}
        self.set_manager_memory_vector()
        self.current_memory_size = memory_size
        self.colored_mdp = self._unfold_memory()
        return self.colored_mdp

    def create_parameter_name(self, player : int, value : int, mem : int, is_action_parameter : bool) -> str:
        category = "A" if is_action_parameter else "M"
        if player == self.optimizing_player:
            return "{}(P{},O{},M{})".format(category,player,value,mem)
        else:
            return "{}(P{},S{},M{})".format(category,player,value,mem)

    def create_coloring(self, underlying_mdp : Any) -> tuple[paynt.parameter_space.parameter_space.ParameterSpace, list[list[tuple[int,int]]]]:
        ''' version where each state of non-optimizing players has its own action parameter '''
        assert self.opt_player_observation_memory_size is not None
        parameter_space = paynt.parameter_space.parameter_space.ParameterSpace()

        for opt_player_obs in self.opt_player_observations:
            # action parameters
            num_actions = self.actions_at_opt_player_observation[opt_player_obs]
            if num_actions > 1:
                option_labels = self.action_labels_at_opt_player_observation[opt_player_obs]
                for mem in range(self.opt_player_observation_memory_size[opt_player_obs]):
                    name = self.create_parameter_name(self.optimizing_player,opt_player_obs,mem,True)
                    parameter_space.add_parameter(name,option_labels)

            # memory parameters
            num_updates = self.posmg_manager.max_successor_memory_size[opt_player_obs]
            if num_updates > 1:
                option_labels = [str(x) for x in range(num_updates)]
                for mem in range(self.opt_player_observation_memory_size[opt_player_obs]):
                    name = self.create_parameter_name(self.optimizing_player,opt_player_obs,mem,False)
                    parameter_space.add_parameter(name,option_labels)

        for state in range(underlying_mdp.nr_states):
            underlying_game_state_player_indication = self.posmg_manager.get_state_player_indications()
            if underlying_game_state_player_indication[state] != self.optimizing_player:
                num_actions = self.posmg_manager.get_action_count(state)
                if num_actions > 1:
                    posmg_state = self.posmg_manager.state_prototype[state]
                    mem = self.posmg_manager.state_memory[state]
                    option_labels = self.action_labels_at_posmg_state[posmg_state]
                    name = self.create_parameter_name(underlying_game_state_player_indication[state],posmg_state,mem,True)
                    parameter_space.add_parameter(name,option_labels)

        # create the coloring
        assert self.posmg_manager.num_holes == parameter_space.num_parameters
        num_parameters = parameter_space.num_parameters
        choice_action_parameter = self.posmg_manager.row_action_hole
        choice_memory_parameter = self.posmg_manager.row_memory_hole
        choice_action_option = self.posmg_manager.row_action_option
        choice_memory_option = self.posmg_manager.row_memory_option
        choice_to_parameter_options = []
        for choice in range(underlying_mdp.nr_choices):
            parameter_options = []
            parameter = choice_action_parameter[choice]
            if parameter != num_parameters:
                parameter_options.append( (parameter,choice_action_option[choice]) )
            parameter = choice_memory_parameter[choice]
            if parameter != num_parameters:
                parameter_options.append( (parameter,choice_memory_option[choice]) )
            choice_to_parameter_options.append(parameter_options)

        return parameter_space, choice_to_parameter_options

    def _unfold_memory(self) -> PosmgColoredMdp:
        assert self.opt_player_observation_memory_size is not None
        logger.debug("unfolding {}-FSC template into one-sided POSMG...".format(max(self.opt_player_observation_memory_size.values())))
        underlying_mdp = self.posmg_manager.construct_mdp()
        logger.debug(f"constructed underlying MDP having {underlying_mdp.nr_states} states and {underlying_mdp.nr_choices} actions.")

        parameter_space, choice_to_parameter_options = self.create_coloring(underlying_mdp)
        coloring = payntbind.synthesis.Coloring(
            parameter_space.native, underlying_mdp.nondeterministic_choice_indices, choice_to_parameter_options)

        colored_mdp = PosmgColoredMdp(
            underlying_mdp, parameter_space, coloring, self.use_exact, self.posmg_manager)
        return colored_mdp
