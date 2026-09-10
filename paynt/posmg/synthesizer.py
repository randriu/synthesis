'''
Driver for FSC synthesis over a POSMG: repeatedly re-unfolds the optimizing player's imperfect-information
strategy at increasing memory sizes and runs SynthesizerAR (the shared AR engine) against each unfolding,
keeping the best assignment found so far across memory sizes.
'''

from __future__ import annotations

from typing import Any

import paynt.posmg.factory
import paynt.posmg.task
import paynt.parameter_space.parameter_space
import paynt.synthesizer.synthesizer_ar
import paynt.utils.timer
import paynt.result

import logging
logger = logging.getLogger(__name__)


class PosmgSynthesizer:

    def __init__(self, colored_mdp_factory : paynt.posmg.factory.PosmgColoredMdpFactory):
        self.colored_mdp_factory = colored_mdp_factory
        self.colored_mdp = colored_mdp_factory.colored_mdp
        self.task : paynt.posmg.task.PosmgTask = colored_mdp_factory.task
        # TODO add support for more engines
        self.synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR
        self.total_iters = 0
        # best assignment/value found so far across memory-size iterations -- strategy_iterative constructs a
        # fresh inner synthesizer per iteration and discards it, so this is the only place these survive once
        # a later, larger-memory iteration doesn't improve on an earlier one
        self.best_assignment : paynt.parameter_space.parameter_space.ParameterSpace | None = None
        self.best_assignment_value : Any = None

    def synthesize(
        self, parameter_space : paynt.parameter_space.parameter_space.ParameterSpace, print_stats : bool = True
    ) -> paynt.parameter_space.parameter_space.ParameterSpace | None:
        synthesizer = self.synthesizer(self.colored_mdp, self.task)
        assignment = synthesizer.synthesize(parameter_space, keep_optimum=True, print_stats=print_stats)
        if assignment is not None:
            # keep_optimum=True means this only fires when the assignment genuinely improves on
            # self.task.specification.optimality's current (cross-iteration) optimum
            self.best_assignment = assignment
            self.best_assignment_value = synthesizer.best_assignment_value
        assert synthesizer.stat is not None
        if synthesizer.stat.iterations_game is not None:
            self.total_iters += synthesizer.stat.iterations_game
        return assignment

    def strategy_iterative(self) -> None:
        mem_size = self.colored_mdp_factory.task.memory_size
        while True:
            if paynt.utils.timer.GlobalTimer.time_limit_reached():
                break
            logger.info("Synthesizing optimal k={} controller ...".format(mem_size))

            assert self.colored_mdp_factory.current_memory_size is not None
            if mem_size > self.colored_mdp_factory.current_memory_size:
                self.colored_mdp = self.colored_mdp_factory.set_imperfect_memory_size(mem_size)

            self.synthesize(self.colored_mdp.parameter_space)

            mem_size += 1

    def run(self, optimum_threshold : Any = None, export_evaluation : Any = None) -> paynt.result.Result:
        self.strategy_iterative()
        return paynt.result.Result(success=self.best_assignment is not None, value=self.best_assignment_value, assignment=self.best_assignment)
