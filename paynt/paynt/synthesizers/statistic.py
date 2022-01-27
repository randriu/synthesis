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

    def __init__(self, sketch, synthesizer):
        
        self.synthesizer = synthesizer

        self.design_space = sketch.design_space
        self.specification = sketch.specification

        self.super_quotient_states = sketch.quotient.quotient_mdp.nr_states
        self.super_quotient_actions = sketch.quotient.quotient_mdp.nr_choices
        
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

        self.stage_factor = None

        self.timer = Timer()

        self.status_period = 1
        self.status_time = self.status_period

    def start(self):
        self.timer.start()

    def stop(self):
        self.timer.stop()

    def iteration_dtmc(self, size_dtmc):
        self.iterations_dtmc += 1
        self.acc_size_dtmc += size_dtmc
        self.print_status()

    def iteration_mdp(self, size_mdp):
        self.iterations_mdp += 1
        self.acc_size_mdp += size_mdp
        self.print_status()

    def check_dtmc(self):
        self.checks_dtmc += 1

    def check_mdp(self):
        self.checks_mdp += 1

    def hybrid(self, stage_factor):
        self.stage_factor = stage_factor

    def status(self):
        fraction_rejected = self.synthesizer.explored / self.design_space.size
        time_estimate = safe_division(self.timer.read(), fraction_rejected)
        percentage_rejected = int(fraction_rejected * 1000000) / 10000.0
        # percentage_rejected = fraction_rejected * 100
        time_elapsed = round(self.timer.read(),1)
        time_estimate = round(time_estimate,1)
        iters = self.iterations_mdp # + self.iterations_dtmc
        avg_size_mdp = safe_division(self.acc_size_mdp, self.iterations_mdp)
        optimum = "-"
        threshold = "-"
        if self.specification.has_optimality and self.specification.optimality.optimum is not None:
            optimum = round(self.specification.optimality.optimum,5)
            threshold = round(self.specification.optimality.threshold,5)
        sat_size = "-"
        ds = self.synthesizer.sketch.design_space
        if ds.use_cvc:
            sat_size = len(ds.solver.getAssertions())
        elif ds.use_python_z3:
            sat_size = len(ds.solver.assertions())
        return f"> Processed {percentage_rejected}% members, elapsed {time_elapsed} s, ETA: {time_estimate} s [{iters} iters], *={optimum}, SAT={sat_size}"

    def print_status(self):
        if self.timer.read() > self.status_time:
            logger.info(self.status())
            self.status_time += self.status_period


    def finished(self, assignment):

        self.timer.stop()
        self.feasible = False
        self.assignment = None
        if assignment is not None:
            self.feasible = True
            self.assignment = str(assignment)
        self.optimum = None
        if self.specification.has_optimality:
            self.optimum = self.specification.optimality.optimum

        self.avg_size_dtmc = safe_division(self.acc_size_dtmc, self.iterations_dtmc)
        self.avg_size_mdp = safe_division(self.acc_size_mdp, self.iterations_mdp)

    def get_summary(self):
        sep = "--------------------"
        summary = f"{sep}\n{self.get_long_summary()}"
        return summary

    def get_long_summary(self):
        specification = "\n".join([f"constraint {i + 1}: {str(f)}" for i,f in enumerate(self.specification.constraints)]) + "\n"
        specification += f"optimality objective: {str(self.specification.optimality)}\n" if self.specification.has_optimality else ""

        fraction_explored = int((self.synthesizer.explored / self.design_space.size) * 100)
        explored = f"explored: {fraction_explored} %"

        design_space = f"number of holes: {self.design_space.num_holes}, family size: {self.design_space.size}, super quotient: {self.super_quotient_states} states / {self.super_quotient_actions} actions"
        timing = f"method: {self.synthesizer.method_name}, synthesis time: {round(self.timer.time, 2)} s"

        family_stats = ""
        ar_stats = f"AR stats: avg MDP size: {round(self.avg_size_mdp)}, iterations: {self.iterations_mdp}" 
        cegis_stats = f"CEGIS stats: avg DTMC size: {round(self.avg_size_dtmc)}, iterations: {self.iterations_dtmc}"
        if self.iterations_mdp > 0:
            family_stats += f"{ar_stats}\n"
        if self.iterations_dtmc > 0:
            family_stats += f"{cegis_stats}\n"

        feasible = "yes" if self.feasible else "no"
        result = f"feasible: {feasible}" if self.optimum is None else f"optimal: {round(self.optimum, 6)}"
        # assignment = f"hole assignment: {str(self.assignment)}\n" if self.assignment else ""
        assignment = ""

        summary = f"{specification}\n{timing}\n{design_space}\n{explored}\n" \
                  f"{family_stats}\n{result}\n{assignment}"
        return summary
