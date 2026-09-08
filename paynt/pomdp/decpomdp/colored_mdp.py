'''
Colored MDP representing a decentralized POMDP (Dec-POMDP): each of several cooperating agents has its own
imperfect-information strategy, unfolded into its own FSC template (see DecPomdpColoredMdpFactory). Unlike
a POSMG, all agents share one objective -- there is no adversarial player, so the induced model is
verified as a plain MDP with no representation-level overrides needed.
'''

import paynt.colored_mdp

import logging
logger = logging.getLogger(__name__)


class DecPomdpColoredMdp(paynt.colored_mdp.ColoredMdp):

    feature_kind = "decpomdp"

    def __init__(self, underlying_mdp, parameter_space, coloring, use_exact):
        super().__init__(underlying_mdp, parameter_space, coloring, use_exact)
