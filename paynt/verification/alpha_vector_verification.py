
import payntbind
import stormpy
from paynt.parser.alpha_vector_parser import AlphaVectorSet

import logging
logger = logging.getLogger(__name__)


class AlphaVectorVerification:

    def __init__(self, pomdp_quotient):
        self.quotient = pomdp_quotient


    def verify_alpha_vectors(self, alpha_vector_set):
        
        alpha_vector_bind = payntbind.synthesis.AlphaVectorsSet(alpha_vector_set.alpha_vectors, alpha_vector_set.alpha_vector_actions)

        alpha_vector_explorer = payntbind.synthesis.BeliefMCExplorer(self.quotient.pomdp)

        result = alpha_vector_explorer.check_alpha_vectors(self.quotient.specification.stormpy_formulae()[0], alpha_vector_bind, 1000000)

        logger.info(f"Alpha vector verified value: {result.upper_bound}")
        logger.info(f"explored MC number of states: {result.induced_mc_from_scheduler.nr_states}")