"""
api - "User-friendly" API for PAYNT.

This module exposes high-level functions for programmatic use of PAYNT.
"""

from . import version


def get_version():
    """Return PAYNT version string."""

    return version()


def get_synthesizer(colored_mdp_factory, method="ar", fsc_synthesis=False, storm_control=None, dtnest=False):
    '''
    The one canonical synthesis dispatcher: reads colored_mdp_factory.colored_mdp.feature_kind and routes to
    the right synthesizer, so callers (paynt.cli, library users) never need to isinstance-check or import a
    specific feature package themselves.

    :param colored_mdp_factory the factory that produced the ColoredMdp to synthesize -- required (not just
        the bare ColoredMdp) so that FSC/tree-unfolding synthesizers (DT, POMDP, POSMG, Dec-POMDP, SAYNT) can
        re-unfold at a different depth/memory size later without the ColoredMdp needing to carry a
        back-reference to its own factory
    :param method the generic algorithm to fall back on when no feature-specific driver applies
        ("onebyone"/"ar"/"cegis"/"hybrid")
    :param fsc_synthesis for FSC-unfolding features (POMDP/POSMG/Dec-POMDP), enable incremental FSC
        synthesis over increasing memory sizes rather than plain synthesis over the current unfolding
    :param storm_control for POMDP with fsc_synthesis, an optional StormPOMDPControl to run SAYNT instead
        of plain PAYNT POMDP synthesis
    :param dtnest for decision trees, use the dtnest synthesizer instead of plain AR
    :return a synthesizer ready to .run()/.synthesize()/.evaluate()
    '''
    import paynt.synthesizer.synthesizer
    colored_mdp = colored_mdp_factory.colored_mdp
    task = colored_mdp_factory.task
    feature_kind = colored_mdp.feature_kind

    if feature_kind == "pomdp_family":
        # a family-of-POMDPs sketch isn't run through a Synthesizer at all (see e.g.
        # PomdpFamilyColoredMdp.build_dtmc_sketch instead)
        import logging
        logging.getLogger(__name__).info("nothing to do with the POMDP sketch, aborting...")
        exit(0)

    if feature_kind == "dt":
        from paynt.dt import DtSynthesizer
        from paynt.dt.dtnest import DtNest
        return DtNest(colored_mdp_factory) if dtnest else DtSynthesizer(colored_mdp_factory)

    if feature_kind == "pomdp" and fsc_synthesis:
        import paynt.pomdp
        if storm_control is not None:
            return paynt.pomdp.saynt.SayntSynthesizer(colored_mdp_factory, method, storm_control)
        return paynt.pomdp.PomdpSynthesizer(colored_mdp_factory, method)

    if feature_kind == "decpomdp" and fsc_synthesis:
        import paynt.pomdp
        return paynt.pomdp.decpomdp.DecPomdpSynthesizer(colored_mdp_factory)

    if feature_kind == "family":
        if method == "onebyone":
            return paynt.synthesizer.synthesizer.Synthesizer.for_method(colored_mdp, task, method)
        import paynt.family
        return paynt.family.PolicyTreeSynthesizer(colored_mdp, task)

    if feature_kind == "posmg" and fsc_synthesis:
        import paynt.posmg
        return paynt.posmg.PosmgSynthesizer(colored_mdp_factory)

    return paynt.synthesizer.synthesizer.Synthesizer.for_method(colored_mdp, task, method)


