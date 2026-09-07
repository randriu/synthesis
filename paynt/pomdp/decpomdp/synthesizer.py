'''
Driver for FSC synthesis over a Dec-POMDP: repeatedly re-unfolds every agent's imperfect-information
strategy at increasing memory sizes and runs SynthesizerAR (the shared AR engine) against each unfolding,
keeping the best assignment found so far across memory sizes.
'''

import paynt.synthesizer.synthesizer_ar

import logging
logger = logging.getLogger(__name__)


class DecPomdpSynthesizer:

    def __init__(self, colored_mdp_factory):
        self.colored_mdp_factory = colored_mdp_factory
        self.colored_mdp = colored_mdp_factory.colored_mdp
        self.task = colored_mdp_factory.task
        # TODO add support for more engines
        self.synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR
        self.total_iters = 0

    def synthesize(self, parameter_space, print_stats=True):
        synthesizer = self.synthesizer(self.colored_mdp, self.task)
        parameter_space.constraint_indices = self.colored_mdp.parameter_space.constraint_indices
        assignment = synthesizer.synthesize(parameter_space, keep_optimum=True, print_stats=print_stats)
        if synthesizer.stat.iterations_mdp is not None:
            self.total_iters += synthesizer.stat.iterations_mdp
        return assignment

    def strategy_iterative(self):
        ''' Unfolds imperfect (multi-state) observations for every agent at increasing memory sizes. '''
        mem_size = self.colored_mdp_factory.task.memory_size
        opt = self.task.specification.optimality.optimum
        while True:
            logger.info("Synthesizing optimal k={} controller ...".format(mem_size))

            if mem_size > self.colored_mdp_factory.current_memory_size:
                self.colored_mdp = self.colored_mdp_factory.set_imperfect_memory_size(mem_size)

            self.synthesize(self.colored_mdp.parameter_space)

            opt_old = opt
            opt = self.task.specification.optimality.optimum

            mem_size += 1

    def run(self, optimum_threshold=None):
        self.strategy_iterative()
