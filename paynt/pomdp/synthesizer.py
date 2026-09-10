'''
Driver for FSC synthesis over a POMDP: repeatedly re-unfolds the agent's imperfect-information strategy at
increasing memory sizes and runs AR or Hybrid against each unfolding, keeping the best assignment found so
far across memory sizes. SAYNT (Storm-guided synthesis) is a separate driver,
paynt.pomdp.saynt.SayntSynthesizer, since it needs a fundamentally different (interactive, threaded)
control flow -- see that module instead if you're looking for --storm-pomdp.
'''

from __future__ import annotations

from typing import Any

import paynt.pomdp.factory
import paynt.pomdp.task
import paynt.pomdp.colored_mdp
import paynt.parameter_space.parameter_space
import paynt.synthesizer.synthesizer_ar
import paynt.synthesizer.synthesizer_hybrid
import paynt.utils.timer
import paynt.pomdp.result

import logging
logger = logging.getLogger(__name__)


class PomdpSynthesizer:

    def __init__(self, colored_mdp_factory : paynt.pomdp.factory.PomdpColoredMdpFactory, method : str):
        self.colored_mdp_factory = colored_mdp_factory
        self.colored_mdp = colored_mdp_factory.colored_mdp
        self.task : paynt.pomdp.task.PomdpTask = colored_mdp_factory.task
        self.synthesizer : type[paynt.synthesizer.synthesizer_ar.SynthesizerAR] | None = None
        if method == "ar":
            self.synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR
        elif method == "hybrid":
            self.synthesizer = paynt.synthesizer.synthesizer_hybrid.SynthesizerHybrid
        self.total_iters = 0
        # best assignment/value found so far across memory-size iterations -- strategy_iterative constructs a
        # fresh inner synthesizer per iteration and discards it, so this is the only place these survive once
        # a later, larger-memory iteration doesn't improve on an earlier one. best_colored_mdp is the specific
        # PomdpColoredMdp instance (i.e. memory-size unfolding) that produced best_assignment -- needed
        # because parameter indices are tied to one specific unfolding, and self.colored_mdp gets reassigned
        # to a fresh (larger) unfolding on every later iteration, so it can't be relied on to still match
        # best_assignment by the time synthesis finishes.
        self.best_assignment : paynt.parameter_space.parameter_space.ParameterSpace | None = None
        self.best_assignment_value : Any = None
        self.best_colored_mdp : paynt.pomdp.colored_mdp.PomdpColoredMdp | None = None

    def synthesize(self, parameter_space : paynt.parameter_space.parameter_space.ParameterSpace | None = None, print_stats : bool = True) -> paynt.parameter_space.parameter_space.ParameterSpace | None:
        if parameter_space is None:
            parameter_space = self.colored_mdp.parameter_space
        assert self.synthesizer is not None
        synthesizer = self.synthesizer(self.colored_mdp, self.task)
        assignment = synthesizer.synthesize(parameter_space, keep_optimum=True, print_stats=print_stats)
        if assignment is not None:
            # keep_optimum=True means this only fires when the assignment genuinely improves on
            # self.task.specification.optimality's current (cross-iteration) optimum
            self.best_assignment = assignment
            self.best_assignment_value = synthesizer.best_assignment_value
            self.best_colored_mdp = self.colored_mdp
        assert synthesizer.stat is not None
        iters_mdp = synthesizer.stat.iterations_mdp if synthesizer.stat.iterations_mdp is not None else 0
        self.total_iters += iters_mdp
        return assignment

    def strategy_iterative(self, unfold_imperfect_only : bool) -> None:
        '''
        @param unfold_imperfect_only if True, only imperfect observations will be unfolded
        '''
        mem_size = self.colored_mdp_factory.task.memory_size
        while True:
            if paynt.utils.timer.GlobalTimer.time_limit_reached():
                break
            logger.info("Synthesizing optimal k={} controller ...".format(mem_size))
            if unfold_imperfect_only:
                self.colored_mdp = self.colored_mdp_factory.set_imperfect_memory_size(mem_size)
            else:
                self.colored_mdp = self.colored_mdp_factory.set_global_memory_size(mem_size)

            self.synthesize(self.colored_mdp.parameter_space)

            mem_size += 1

    def run(self, optimum_threshold : Any = None) -> paynt.pomdp.result.PomdpResult:
        self.strategy_iterative(unfold_imperfect_only=True)

        if self.task.export_synthesis_filename_base is not None:
            # TODO add export option for pure PAYNT synthesis
            logger.info("--export-synthesis is not yet supported for plain PAYNT POMDP synthesis (only for SAYNT)")

        fsc = None
        if self.best_assignment is not None:
            assert self.best_colored_mdp is not None
            fsc = self.best_colored_mdp.assignment_to_fsc(self.best_assignment)
        return paynt.pomdp.result.PomdpResult(
            success=self.best_assignment is not None, value=self.best_assignment_value,
            assignment=self.best_assignment, fsc=fsc)
