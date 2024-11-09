import stormpy

from .statistic import Statistic
from .synthesizer_ar import SynthesizerAR
from .synthesizer_ar_storm import SynthesizerARStorm
from .synthesizer_hybrid import SynthesizerHybrid
from .synthesizer_multicore_ar import SynthesizerMultiCoreAR

import paynt.quotient.quotient
import paynt.quotient.decpomdp
import paynt.verification.property

import logging 
logger = logging.getLogger(__name__)



class SynthesizerDecPomdp:

    def __init__(self, quotient):
        self.quotient = quotient
        # TODO add support for more engines
        self.synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR
        self.total_iters = 0


    def synthesize(self, family, print_stats=True):
        synthesizer = self.synthesizer(self.quotient)   
        family.constraint_indices = self.quotient.family.constraint_indices
        assignment = synthesizer.synthesize(family, keep_optimum=True, print_stats=print_stats)
        self.total_iters += synthesizer.stat.iterations_mdp
        return assignment

    def strategy_iterative(self, unfold_imperfect_only):
        '''
        @param unfold_imperfect_only if True, only imperfect observations will be unfolded
        '''
            
        mem_size = paynt.quotient.decpomdp.DecPomdpQuotient.initial_memory_size
        opt = self.quotient.specification.optimality.optimum
        while True:
            
            logger.info("Synthesizing optimal k={} controller ...".format(mem_size))
            if mem_size > self.quotient.current_memory_size:
                if unfold_imperfect_only:
                    self.quotient.set_imperfect_memory_size(mem_size)
                else:
                    self.quotient.set_global_memory_size(mem_size)
            
            self.synthesize(self.quotient.family)

            opt_old = opt
            opt = self.quotient.specification.optimality.optimum

            mem_size += 1

            #break


    def run(self, optimum_threshold=None):
        self.strategy_iterative(unfold_imperfect_only=True)
