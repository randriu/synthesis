"""
api - User-friendly API for PAYNT as a Python library.

This module exposes high-level functions for programmatic use of 
"""

from . import version
from . import quotient
from . import parser
from . import verification

import payntbind
import stormpy


def get_version():
    """Return PAYNT version string."""

    return version.__version__


def property_wrapper(properties):
    """Helper function to construct a PAYNT specification from a list of StormPy properties."""

    verification.property.Property.initialize(False)
    properties = [verification.property.construct_property(p, 0) for p in properties]
    specification = verification.property.Specification(properties)

    return specification


def create_colored_mdp(model, specification, use_exact=False):
    """Helper function to create a colored MDP from a StormPy model and a PAYNT specification."""

    parser.sketch.make_rewards_action_based(model) # needed for quotient MDP initialization
    quotient.mdp.MdpQuotient.add_dont_care_action = True # TODO this should be made into default bahviour I think

    if isinstance(model, payntbind.synthesis.Posmg):
        quotient_container = quotient.posmg.PosmgQuotient(model, specification, use_exact=use_exact)
    elif not model.is_partially_observable:
        quotient_container = quotient.mdp.MdpQuotient(model, specification, use_exact=use_exact)
    else:
        quotient_container = quotient.pomdp.PomdpQuotient(model, specification, None, use_exact=use_exact)

    return quotient_container


def model_checking(colored_mdp, property, extract_scheduler=True):
    """Wrapper on the StormPy model checking."""

    return stormpy.model_checking(colored_mdp.quotient_mdp, property, extract_scheduler=extract_scheduler)

