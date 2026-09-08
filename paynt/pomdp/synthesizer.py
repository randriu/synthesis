'''
Driver for FSC synthesis over a POMDP: repeatedly re-unfolds the agent's imperfect-information strategy at
increasing memory sizes and runs AR or Hybrid against each unfolding, keeping the best assignment found so
far across memory sizes. SAYNT (Storm-guided synthesis) is a separate driver,
paynt.pomdp.saynt.SayntSynthesizer, since it needs a fundamentally different (interactive, threaded)
control flow -- see that module instead if you're looking for --storm-pomdp.
'''

import paynt.synthesizer.synthesizer_ar
import paynt.synthesizer.synthesizer_hybrid

import logging
logger = logging.getLogger(__name__)


class PomdpSynthesizer:

    def __init__(self, colored_mdp_factory, method):
        self.colored_mdp_factory = colored_mdp_factory
        self.colored_mdp = colored_mdp_factory.colored_mdp
        self.task = colored_mdp_factory.task
        self.synthesizer = None
        if method == "ar":
            self.synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR
        elif method == "hybrid":
            self.synthesizer = paynt.synthesizer.synthesizer_hybrid.SynthesizerHybrid
        self.total_iters = 0

    def synthesize(self, parameter_space=None, print_stats=True):
        if parameter_space is None:
            parameter_space = self.colored_mdp.parameter_space
        synthesizer = self.synthesizer(self.colored_mdp, self.task)
        assignment = synthesizer.synthesize(parameter_space, keep_optimum=True, print_stats=print_stats)
        iters_mdp = synthesizer.stat.iterations_mdp if synthesizer.stat.iterations_mdp is not None else 0
        self.total_iters += iters_mdp
        return assignment

    def strategy_iterative(self, unfold_imperfect_only):
        '''
        @param unfold_imperfect_only if True, only imperfect observations will be unfolded
        '''
        mem_size = self.colored_mdp_factory.task.memory_size
        opt = self.task.specification.optimality.optimum
        while True:
            logger.info("Synthesizing optimal k={} controller ...".format(mem_size))
            if unfold_imperfect_only:
                self.colored_mdp = self.colored_mdp_factory.set_imperfect_memory_size(mem_size)
            else:
                self.colored_mdp = self.colored_mdp_factory.set_global_memory_size(mem_size)

            self.synthesize(self.colored_mdp.parameter_space)

            opt_old = opt
            opt = self.task.specification.optimality.optimum

            mem_size += 1

    def run(self, optimum_threshold=None):
        self.strategy_iterative(unfold_imperfect_only=True)

        if self.task.export_synthesis_filename_base is not None:
            # TODO add export option for pure PAYNT synthesis
            logger.info("--export-synthesis is not yet supported for plain PAYNT POMDP synthesis (only for SAYNT)")
