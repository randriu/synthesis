"""
api - User-friendly API for PAYNT as a Python library.

This module exposes high-level functions for programmatic use of 
"""

from . import version
from . import cli
from . import utils
from . import synthesizer
from . import quotient
from . import parser
from . import models
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


def dt_map_scheduler(colored_mdp, scheduler, tree_depth):
    """Helper function to map a scheduler to a decision tree using the DTMap algorithm. Returns a tuple (success, decision_tree)."""

    state_to_choice = payntbind.synthesis.schedulerToStateToGlobalChoice(scheduler, colored_mdp.quotient_mdp, [x for x in range(colored_mdp.quotient_mdp.nr_choices)])
    state_to_choice = colored_mdp.discard_unreachable_choices(state_to_choice)
    choices = colored_mdp.state_to_choice_to_choices(state_to_choice)

    dt_synthesizer = synthesizer.decision_tree.SynthesizerDecisionTree(colored_mdp)
    synthesizer.decision_tree.SynthesizerDecisionTree.tree_depth = tree_depth
    dt_synthesizer.map_scheduler(choices)

    return dt_synthesizer.best_tree is not None, dt_synthesizer.best_tree


def dtpaynt(colored_mdp, tree_depth):
    dt_synthesizer = synthesizer.decision_tree.SynthesizerDecisionTree(colored_mdp)
    dt_synthesizer.synthesize_tree(tree_depth)

    return dt_synthesizer.best_tree
