import stormpy
import stormpy.synthesis
import stormpy.pomdp

from .models import MarkovChain,MDP,DTMC
from .holes import Hole,Holes,DesignSpace
from .quotient import QuotientContainer
from .quotient_pomdp import POMDPQuotientContainer

import paynt

import logging
logger = logging.getLogger(__name__)


class DecPomdpQuotientContainer(QuotientContainer):

    def __init__(self, decpomdp_manager):

        self.decpomdp_manager = decpomdp_manager
        logger.info(f"dec-POMDP has {decpomdp_manager.num_agents} agents")

        # see what happens if you uncomment the line below:
        # decpomdp_manager.apply_discount_factor_transformation()
        self.quotient = decpomdp_manager.construct_mdp()
        print("MDP has {} states".format(self.quotient.nr_states))
        print("transitions from state 1: ", self.quotient.transition_matrix.get_row(1))

        # construct specification
        reward_name = list(self.quotient.reward_models)[0]
        optimization_direction = "min" if decpomdp_manager.reward_minimizing else "max"
        formula_str = 'R{"' + reward_name + '"}' + optimization_direction + '=? [F "sink"]'
        formula = stormpy.parse_properties_without_context(formula_str)[0]
        optimality = paynt.quotient.property.OptimalityProperty(formula, 0)
        specification = paynt.quotient.property.Specification([],optimality)
        MarkovChain.initialize(specification)

        logger.debug("nothing to do, aborting...")
        exit()
        

        

