
import payntbind
import stormpy
from paynt.parser.alpha_vector_parser import AlphaVectorSet

import logging
logger = logging.getLogger(__name__)


class AlphaVectorVerification:

    def __init__(self, pomdp_quotient):
        self.quotient = pomdp_quotient

    # calls belief unrolling in Storm with the given set of alpha vectors and verifies them with respect to the undiscounted property
    # this verification assumes the alpha vectors were obtained on a cassandra pomdp generated from the model using the --export pomdp functionality
    def verify_alpha_vectors(self, alpha_vector_set):

        number_of_belief_threshold = 1000000 # number of beliefs to be unfolded before cut-offs are applied
        dummy_value = 20 # for reward specifications BeliefMCExplorer uses this value instead of Storm cut-offs, can be useful when getting inf/-inf
        
        alpha_vector_bind = payntbind.synthesis.AlphaVectorsSet(alpha_vector_set.alpha_vectors, alpha_vector_set.alpha_vector_actions)

        alpha_vector_explorer = payntbind.synthesis.BeliefMCExplorer(self.quotient.pomdp, number_of_belief_threshold)

        result = alpha_vector_explorer.check_alpha_vectors(self.quotient.specification.stormpy_formulae()[0], alpha_vector_bind)

        logger.info(f"Alpha vector verified value: {result.upper_bound}")
        logger.info(f"explored MC number of states: {result.induced_mc_from_scheduler.nr_states}")