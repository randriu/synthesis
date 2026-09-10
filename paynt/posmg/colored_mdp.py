"""
Colored MDP representing a partially observable stochastic multiplayer game (POSMG): the optimizing
player's imperfect-information strategy is unfolded into an FSC template (see PosmgColoredMdpFactory), but
-- unlike a POMDP -- the other players' choices are adversarial rather than don't-care, so the induced
model must be verified as a game rather than as a plain MDP.
"""

from __future__ import annotations

from typing import Any

import stormpy

import paynt.colored_mdp
import paynt.parameter_space.parameter_space
import paynt.underlying_model.underlying_model


class PosmgColoredMdp(paynt.colored_mdp.ColoredMdp):

    feature_kind = "posmg"

    def __init__(
        self, underlying_mdp: Any, parameter_space: paynt.parameter_space.parameter_space.ParameterSpace, coloring: Any, use_exact: bool, posmg_manager: Any
    ):
        super().__init__(underlying_mdp, parameter_space, coloring, use_exact)
        # needed by create_smg_from_mdp to recover each state's player index -- the coloring/parameter_space
        # alone don't carry this
        self.posmg_manager = posmg_manager

    def create_smg_from_mdp(self, mdp: paynt.underlying_model.underlying_model.SubMdp) -> paynt.underlying_model.underlying_model.Smg:
        """Re-attach game (player-indication) structure to a restricted sub-MDP so it can be verified as a
        game rather than as a plain MDP."""
        underlying_player_indications = self.posmg_manager.get_state_player_indications()

        transition_matrix = mdp.model.transition_matrix
        state_labeling = mdp.model.labeling
        components = stormpy.SparseModelComponents(transition_matrix=transition_matrix, state_labeling=state_labeling)

        if mdp.model.has_choice_labeling():
            components.choice_labeling = mdp.model.choice_labeling

        state_player_indications = []
        for state in range(mdp.states):
            underlying_mdp_state = mdp.underlying_mdp_state_map[state]
            player = underlying_player_indications[underlying_mdp_state]
            state_player_indications.append(player)
        components.state_player_indications = state_player_indications

        return paynt.underlying_model.underlying_model.Smg(stormpy.storage.SparseSmg(components))

    def scheduler_selection(self, mdp: paynt.underlying_model.underlying_model.SubMdp, scheduler: Any) -> list[list[int]]:
        """Get parameter options involved in the scheduler selection. Unlike the base ColoredMdp, this
        keeps unreachable choices rather than discarding them."""
        assert scheduler.memoryless and scheduler.deterministic
        state_to_choice = paynt.underlying_model.underlying_model.ModelIndex.scheduler_to_state_to_choice(
            self.underlying_mdp, self.choice_destinations, mdp, scheduler, discard_unreachable_choices=False
        )
        choices = paynt.underlying_model.underlying_model.ModelIndex.state_to_choice_to_choices(self.underlying_mdp, state_to_choice)
        return self.coloring.collectHoleOptions(choices)
