from ..profiler import Timer

import logging
logger = logging.getLogger(__name__)

# zero approximation to avoid zero division exception
APPROX_ZERO = 0.000001

def safe_division(dividend, divisor):
    """Safe division of dividend by operand
    :param number dividend: upper operand of the division
    :param number divisor: lower operand of the division, may be zero
    :return: safe value after division of approximated zero
    """
    try:
        return dividend / divisor
    except (ZeroDivisionError, ValueError):
        return dividend / APPROX_ZERO

class Statistic:
    """General computation stats."""

    def __init__(self, sketch, method_name):
        self.design_space = sketch.design_space
        
        self.properties = sketch.properties
        self.optimality_property = sketch.optimality_property

        self.method_name = method_name
        
        self.iterations_dtmc = 0
        self.acc_size_dtmc = 0
        self.avg_size_dtmc = 0
        self.checks_dtmc = 0

        self.super_mdp_size = 0

        self.iterations_mdp = 0
        self.acc_size_mdp = 0
        self.avg_size_mdp = 0
        self.checks_mdp = 0

        self.feasible = None
        self.assignment = None
        self.optimal_value = None

        self.timer = Timer()
        self.remaining = self.design_space.size

        self.status_period = 5
        self.status_time = 5

    def start(self):
        self.timer.start()

    def stop(self):
        self.timer.stop()

    def iteration_dtmc(self, size_dtmc):
        self.iterations_dtmc += 1
        self.acc_size_dtmc + size_dtmc
        self.print_status()

    def iteration_mdp(self, size_mdp):
        self.iterations_mdp += 1
        self.acc_size_mdp + size_mdp
        self.print_status()

    def check_dtmc(self):
        self.checks_dtmc += 1

    def check_mdp(self):
        self.checks_mdp += 1

    def pruned(self, pruned):
        self.remaining -= pruned

    def estimate(self):
        fraction_remaining = self.remaining / self.design_space.size
        fraction_rejected = 1 - fraction_remaining
        time_estimate = safe_division(self.timer.read(), fraction_rejected)
        return fraction_rejected, time_estimate

    def status(self):
        fraction_rejected, time_estimate = self.estimate()
        percentage_rejected = int(fraction_rejected * 100)
        time_elapsed = round(self.timer.read(),1)
        time_estimate = round(time_estimate,1)
        return f"> Processed {percentage_rejected}% members, elapsed {time_elapsed} s, ETA: {time_estimate} s"

    def print_status(self):
        if self.timer.read() > self.status_time:
            logger.info(self.status())
            self.status_time += self.status_period


    def finished(self, assignment):

        optimal_value = None
        if self.optimality_property is not None:
            optimal_value = self.optimality_property.optimal_value

        self.timer.stop()
        self.feasible = False
        self.assignment = False
        if assignment is not None:
            self.feasible = True
            # self.assignment = self.design_space.readable_assignment(assignment)
            self.assignment = str(assignment)
        self.optimal_value = optimal_value

        self.avg_size_dtmc = safe_division(self.acc_size_dtmc, self.checks_dtmc)
        self.avg_size_mdp = safe_division(self.acc_size_mdp, self.checks_mdp)

    def get_summary(self,short_summary):
        sep = "--------------------"
        summary = f"{sep}\n{self.get_long_summary()}"
        if short_summary:
            summary += f"\n{sep}\n{self.get_short_summary()}\n"
        return summary

    def get_long_summary(self):
        formulae = "\n".join([f"formula {i + 1}: {str(f)}" for i,f in enumerate(self.properties)]) + "\n"
        formulae += f"optimality formula: {str(self.optimality_property)}\n" if self.optimality_property is not None else ""

        design_space = f"number of holes: {self.design_space.hole_count}, family size: {self.design_space.size}"
        timing = f"method: {self.method_name}, synthesis time: {round(self.timer.time, 2)} s"

        mdp_stats = f"super MDP size: {self.super_mdp_size}, average MDP size: {round(self.avg_size_mdp)}, " \
                    f"MPD checks: {self.checks_mdp}, iterations: {self.iterations_mdp}"
        dtmc_stats = f"average DTMC size: {round(self.avg_size_dtmc)}, " \
                     f"DTMC checks: {self.checks_dtmc}, iterations: {self.iterations_dtmc}"
        family_stats = ""
        if self.iterations_mdp > 0:
            family_stats += f"{mdp_stats}\n"
        if self.iterations_dtmc > 0:
            family_stats += f"{dtmc_stats}\n"

        feasible = "yes" if self.feasible else "no"
        result = f"feasible: {feasible}" if self.optimal_value is None else f"optimal: {round(self.optimal_value, 6)}"
        assignment = f"hole assignment: {str(self.assignment)}\n" if self.assignment else ""

        summary = f"{formulae}\n{timing}\n{design_space}\n" \
                  f"{family_stats}\n{result}\n{assignment}"
        return summary

    def get_short_summary(self):
        # if self.optimal_value is None:
        #     result = "F" if self.feasible else "U"
        # else:
        #     result = f"opt = {round(self.optimal_value, 6)}"
        # if self.method == "CEGAR":
        #     iters = self.iterations[0]
        # elif self.method == "CEGIS" or self.method == "1-by-1":
        #     iters = self.iterations[1]
        # else:
        #     iters = (self.iterations[0], self.iterations[1])
        # thresholds = [round(float(f.threshold), 10) for f in self.formulae]

        # return f"> T = {thresholds} - {self.method}: {result} ({iters} iters, {round(self.timer.time, 2)} sec)"
        return ""
