from ..profiler import Timer
from .helpers import readable_assignment


class Statistic:
    """General computation stats."""

    def __init__(self, method, formulae, holes_count, opt_setting, short_summary=False):
        self.method = method
        self.short_summary = short_summary
        self.timer = Timer()
        self.timer.start()
        self.feasible = False
        self.assignment = {}
        self.iterations = (0, 0)
        self.optimal_value = 0.0
        self.formulae = formulae
        self.holes_count = holes_count
        self.opt_setting = opt_setting
        self.family_size = 0
        self.super_mdp_size, self.mdp_checks, self.avg_mdp_size = 0, 0, 0
        self.avg_dtmc_size, self.dtmc_checks = 0, 0
        self.ce_quality = None

    def finished(
            self, assignment, iterations, optimal_value, family_size, super_mdp_size,
            avg_mdp_size, mdp_checks, avg_dtmc_size, dtmc_checks, ce_quality=""
    ):
        self.timer.stop()
        self.feasible = assignment is not None
        self.assignment = assignment
        self.iterations = iterations
        self.optimal_value = optimal_value
        self.family_size = family_size
        self.super_mdp_size = super_mdp_size
        self.avg_mdp_size = round(avg_mdp_size, 2)
        self.mdp_checks = mdp_checks
        self.avg_dtmc_size = round(avg_dtmc_size, 2)
        self.dtmc_checks = dtmc_checks
        self.ce_quality = ce_quality

    def get_long_summary(self):
        formulae = self.formulae if self.optimal_value is None else self.formulae[:-1]
        formulae = "\n".join([f"formula {i + 1}: {formula}" for i, formula in enumerate(formulae)]) + "\n"
        formulae += f"optimal setting: {self.opt_setting}\n" if self.optimal_value else ""

        timing = f"method: {self.method}, synthesis time: {round(self.timer.time, 2)} s"
        design_space = f"number of holes: {self.holes_count}, family size: {self.family_size}"

        mdp_stats = f"super MDP size: {self.super_mdp_size}, average MDP size: {round(self.avg_mdp_size)}, " \
                    f"MPD checks: {self.mdp_checks}, iterations: {self.iterations[0]}"
        dtmc_stats = f"average DTMC size: {round(self.avg_dtmc_size)}, " \
                     f"DTMC checks: {self.dtmc_checks}, iterations: {self.iterations[1]}"
        family_stats = ""
        if self.method == "CEGAR" or self.method == "Hybrid":
            family_stats += f"{mdp_stats}\n"
        if self.method != "CEGAR":
            family_stats += f"{dtmc_stats}\n"

        feasible = "yes" if self.feasible else "no"
        result = f"feasible: {feasible}" if self.optimal_value is None else f"optimal: {round(self.optimal_value, 6)}"
        assignment = f"hole assignment: {self.assignment}\n" if self.assignment else ""

        summary = f"{formulae}\n{timing}\n{design_space}\n" \
                  f"{family_stats}{self.ce_quality}\n{result}\n{assignment}"
        return summary

    def get_short_summary(self):
        if self.optimal_value is None:
            result = "F" if self.feasible else "U"
        else:
            result = f"opt = {round(self.optimal_value, 6)}"
        if self.method == "CEGAR":
            iters = self.iterations[0]
        elif self.method == "CEGIS" or self.method == "1-by-1":
            iters = self.iterations[1]
        else:
            iters = (self.iterations[0], self.iterations[1])
        thresholds = [round(float(f.threshold), 10) for f in self.formulae]

        return f"> T = {thresholds} - {self.method}: {result} ({iters} iters, {round(self.timer.time, 2)} sec)"

    def __str__(self):
        sep = "--------------------"
        summary = f"{sep}\n{self.get_long_summary()}"
        if self.short_summary:
            summary += f"\n{sep}\n{self.get_short_summary()}\n"
        return summary
