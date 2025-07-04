import paynt.synthesizer.statistic

import logging
logger = logging.getLogger(__name__)


class StatisticIpompdp(paynt.synthesizer.statistic.Statistic):

    def start(self):
        logger.info('synthesis initiated')
        self.synthesis_timer.start()

    def finished_synthesis(self, synthesized_optimum):
        self.synthesis_timer.stop()
        self.optimum = synthesized_optimum

    def get_summary(self):
        specification = self.get_summary_specification()

        timing = f"method: {self.synthesizer.method_name}, synthesis time: {round(self.synthesis_timer.time, 2)} s"
        game_abstraction = f"game abstraction: {self.quotient.game_abstraction.nr_states} states / {self.quotient.game_abstraction.nr_choices} actions"
        iterations = self.get_summary_iterations()
        optimum = round(self.optimum, 6) if self.optimum is not None else ''
        result = f"optimum: {optimum}"

        sep = "--------------------\n"
        summary = f"{sep}"\
                f"Synthesis summary:\n" \
                f"{specification}\n{timing}\n" \
                f"{game_abstraction}\n" \
                f"{iterations}\n{result}\n"\
                f"{sep}"
        return summary
