from .statistic import Statistic

import logging
logger = logging.getLogger(__name__)


class Synthesizer:

    # if True, some subfamilies can be discarded and some holes can be generalized
    incomplete_search = False

    # synthesis escape criterion
    use_optimum_update_timeout = False
    optimum_update_iters_limit = 100000
    
    def __init__(self, quotient):
        self.quotient = quotient
        self.stat = Statistic(self)
        self.explored = 0

        self.since_last_optimum_update = 0
    
    @property
    def method_name(self):
        ''' to be overridden '''
        pass
    
    def synthesize(self, family):
        ''' to be overridden '''
        pass
    
    def print_stats(self):
        self.stat.print()
    
    def run(self):
        # self.quotient.specification.optimality.update_optimum(0.9)
        self.quotient.design_space.property_indices = self.quotient.specification.all_constraint_indices()
        assignment = self.synthesize(self.quotient.design_space)


        print("")
        if assignment is not None:
            logger.info("Printing synthesized assignment below:")
            logger.info(str(assignment))
            dtmc = self.quotient.build_chain(assignment)
            spec = dtmc.check_specification(self.quotient.specification)
            logger.info("Double-checking specification satisfiability: {}".format(spec))
            if self.quotient.export_optimal_dtmc:
                self.quotient.export_result(dtmc)
        
        self.print_stats()
    
    def explore(self, family):
        self.explored += family.size
    
    def no_optimum_update_limit_reached(self):
        self.since_last_optimum_update += 1
        return Synthesizer.use_optimum_update_timeout and self.since_last_optimum_update > Synthesizer.optimum_update_iters_limit

