"""
Colored MDP representing a decentralized POMDP (Dec-POMDP): each of several cooperating agents has its own
imperfect-information strategy, unfolded into its own FSC template (see DecPomdpColoredMdpFactory). Unlike
a POSMG, all agents share one objective -- there is no adversarial player, so the induced model is
verified as a plain MDP with no representation-level overrides needed.
"""

from __future__ import annotations

from typing import Any

import paynt.colored_mdp
import paynt.parameter_space.parameter_space

import logging

logger = logging.getLogger(__name__)


class DecPomdpColoredMdp(paynt.colored_mdp.ColoredMdp):

    feature_kind = "decpomdp"

    def __init__(self, underlying_mdp: Any, parameter_space: paynt.parameter_space.parameter_space.ParameterSpace, coloring: Any, use_exact: bool):
        super().__init__(underlying_mdp, parameter_space, coloring, use_exact)
