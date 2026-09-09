from __future__ import annotations

from typing import Any, TYPE_CHECKING

import stormpy.storage

import paynt.utils.timer
import paynt.underlying_model.underlying_model

if TYPE_CHECKING:
    # synthesizer.py imports this module (for Statistic itself), so only import it for annotations to avoid
    # a circular import at runtime
    import paynt.synthesizer.synthesizer

import math

import logging
logger = logging.getLogger(__name__)

# zero approximation to avoid zero division exception
APPROX_ZERO = 0.000001

def safe_division(dividend : float, divisor : float) -> float:
    """Safe division of dividend by operand
    :param number dividend: upper operand of the division
    :param number divisor: lower operand of the division, may be zero
    :returns safe value after division of approximated zero
    """
    try:
        return dividend / divisor
    except (ZeroDivisionError, ValueError):
        return dividend / APPROX_ZERO

class Statistic:
    """General computation stats."""

    # parameters
    status_period_seconds = 3
    synthesis_timer_total = paynt.utils.timer.Timer()

    def __init__(self, synthesizer : "paynt.synthesizer.synthesizer.Synthesizer"):

        self.synthesizer = synthesizer
        self.colored_mdp = self.synthesizer.colored_mdp
        self.task = self.synthesizer.task

        self.iterations_dtmc : int | None = None
        self.acc_size_dtmc = 0
        self.avg_size_dtmc = 0

        self.iterations_mdp : int | None = None
        self.acc_size_mdp = 0
        self.avg_size_mdp = 0

        self.iterations_game : int | None = None
        self.acc_size_game = 0
        self.avg_size_game = 0

        self.synthesized_assignment : Any = None
        self.job_type : str | None = None
        # populated by finished_evaluation, read by get_summary_evaluation
        self.evaluations : list[Any] = []

        # MDP family (policy-tree synthesis): num_nodes/num_nodes_merged/num_leaves/num_leaves_merged/
        # postprocessing_time are set directly on a Statistic instance by
        # paynt.family.policy_tree_synthesizer.PolicyTreeSynthesizer.evaluate_all, not by this constructor --
        # declared here (rather than left as an undeclared dynamic attribute) purely so their type is known.
        # Kept as Any (not "int | None"): print_mdp_family_table_entries, the only reader, is a debug-only
        # utility that assumes (and always has assumed, pre-existing to this backfill) these are already
        # populated by the time it's called -- an Optional type would just force artificial asserts around
        # every arithmetic use below for a precondition nothing enforces at the type level anyway.
        self.num_mdps_total : Any = None
        self.num_mdps_sat : Any = None
        self.num_nodes : Any = None
        self.num_nodes_merged : Any = None
        self.num_leaves : Any = None
        self.num_leaves_merged : Any = None
        self.num_policies : Any = None
        self.num_policies_merged : Any = None
        self.postprocessing_time : Any = None

        self.parameter_space_size : int | None = None
        self.synthesis_timer = paynt.utils.timer.Timer()
        self.status_horizon = Statistic.status_period_seconds


    def start(self, parameter_space : Any) -> None:
        logger.info("synthesis initiated, design space: {}".format(parameter_space.size_or_order))
        self.parameter_space_size = parameter_space.size
        self.synthesis_timer.start()
        if not self.synthesis_timer_total.running:
            self.synthesis_timer_total.start()

    def iteration(self, model : Any) -> None:
        ''' Identify the type of the model and count corresponding iteration. '''
        if isinstance(model, paynt.underlying_model.underlying_model.Mdp):
            model = model.model
        if type(model) in [stormpy.storage.SparseDtmc, stormpy.storage.SparseExactDtmc]:
            self.iteration_dtmc(model.nr_states)
        elif type(model) in [stormpy.storage.SparseMdp, stormpy.storage.SparseExactMdp]:
            self.iteration_mdp(model.nr_states)
        else:
            logger.debug(f"unknown model type {type(model)}")

    def iteration_dtmc(self, size_dtmc : int) -> None:
        if self.iterations_dtmc is None:
            self.iterations_dtmc = 0
        self.iterations_dtmc += 1
        self.acc_size_dtmc += size_dtmc
        self.print_status()

    def iteration_mdp(self, size_mdp : int) -> None:
        if self.iterations_mdp is None:
            self.iterations_mdp = 0
        self.iterations_mdp += 1
        self.acc_size_mdp += size_mdp
        self.print_status()

    def iteration_game(self, size_game : int) -> None:
        if self.iterations_game is None:
            self.iterations_game = 0
        self.iterations_game += 1
        self.acc_size_game += size_game
        self.print_status()

    def new_fsc_found(self, value : Any, assignment : Any, size : int) -> None:
        time_elapsed = round(self.synthesis_timer_total.read(),1)
        # print(f'new opt: {value}')
        # print(f'new opt: {value}, elapsed {time_elapsed}s')
        # print(f'-----------PAYNT----------- \
              # \nValue = {value} | Time elapsed = {time_elapsed}s | FSC size = {size}\nFSC = {assignment}\n', flush=True)


    def status(self) -> str:
        ret_str = "> "
        fraction_explored = self.synthesizer.explored / self.parameter_space_size
        time_estimate = safe_division(self.synthesis_timer.read(), fraction_explored)
        percentage_explored = int(fraction_explored * 100000) / 1000.0
        ret_str += f"progress {percentage_explored}%"

        time_elapsed = int(self.synthesis_timer.read())
        ret_str += f", elapsed {time_elapsed} s"
        time_estimate = int(time_estimate)
        ret_str += f", estimated {time_estimate} s"
        time_estimate_hours = math.floor(time_estimate/3600)
        time_estimate_days = math.floor(time_estimate_hours/24)
        time_estimate_years = math.floor(time_estimate_days/365)
        if time_estimate_years > 0:
            s_ending = "s" if time_estimate_years > 1 else ""
            ret_str += f" ({time_estimate_years} year{s_ending})"
        elif time_estimate_days > 1:
            s_ending = "s" if time_estimate_days > 1 else ""
            ret_str += f" ({time_estimate_days} day{s_ending})"
        elif time_estimate_hours > 1:
            s_ending = "s" if time_estimate_hours > 1 else ""
            ret_str += f" ({time_estimate_hours} hour{s_ending})"

        iters : list[str] = []
        if self.iterations_game is not None:
            iters += [f"game: {self.iterations_game}"]
        if self.iterations_mdp is not None:
            iters += [f"MDP: {self.iterations_mdp}"]
        if self.iterations_dtmc is not None:
            iters += [f"DTMC: {self.iterations_dtmc}"]
        ret_str += ", iters = {" + ", ".join(iters) + "}"
        # ret_str += f", pres = {self.synthesizer.num_preserved}"

        spec = self.task.specification
        if spec.has_optimality:
            opt = self.synthesizer.best_assignment_value
            if opt is None:
                opt = spec.optimality.optimum
            if opt is not None:
                if not isinstance(opt, stormpy.Rational):
                    opt = round(opt, 4)
                ret_str += f", opt = {opt}"
        return ret_str


    def print_status(self) -> None:
        if not self.synthesis_timer.read() > self.status_horizon:
            return
        logger.info(self.status())
        self.status_horizon = self.synthesis_timer.read() + Statistic.status_period_seconds


    def finished_synthesis(self) -> None:
        self.job_type = "synthesis"
        self.synthesis_timer.stop()
        self.synthesized_assignment = self.synthesizer.best_assignment

    def finished_evaluation(self, evaluations : list) -> None:
        self.job_type = "evaluation"
        self.synthesis_timer.stop()
        self.evaluations = evaluations


    def get_summary_specification(self) -> str:
        spec = self.task.specification
        specification = ""
        if len(spec.constraints) > 0:
            specification += "\n".join([f"constraint {i + 1}: {str(f)}" for i,f in enumerate(spec.constraints)]) + "\n"
        if spec.has_optimality:
            specification += f"optimality objective: {str(spec.optimality)}\n"
        return specification

    def get_summary_iterations(self) -> str:
        iterations = ""
        if self.iterations_game is not None:
            avg_size = round(safe_division(self.acc_size_game, self.iterations_game))
            type_stats = f"Game stats: avg game size: {avg_size}, iterations: {self.iterations_game}"
            iterations += f"{type_stats}\n"

        if self.iterations_mdp is not None:
            avg_size = round(safe_division(self.acc_size_mdp, self.iterations_mdp))
            type_stats = f"MDP stats: avg MDP size: {avg_size}, iterations: {self.iterations_mdp}"
            iterations += f"{type_stats}\n"

        if self.iterations_dtmc is not None:
            avg_size = round(safe_division(self.acc_size_dtmc, self.iterations_dtmc))
            type_stats = f"DTMC stats: avg DTMC size: {avg_size}, iterations: {self.iterations_dtmc}"
            iterations += f"{type_stats}\n"
        return iterations

    def get_summary_synthesis(self) -> str:
        spec = self.task.specification
        if spec.has_optimality and spec.optimality.optimum is not None:
            if isinstance(spec.optimality.optimum, stormpy.Rational):
                optimum = spec.optimality.optimum
            else:
                optimum = round(spec.optimality.optimum, 6)
            return f"optimum: {optimum}"
        else:
            feasible = "yes" if self.synthesized_assignment is not None else "no"
            return f"feasible: {feasible}"

    def get_summary_evaluation(self) -> str:
        import paynt.synthesizer.synthesizer
        if not self.evaluations or not isinstance(self.evaluations[0], paynt.synthesizer.synthesizer.ParameterSpaceEvaluation):
            return ""
        members_sat = sum( [evaluation.parameter_space.size for evaluation in self.evaluations if evaluation.sat ])
        members_total = self.colored_mdp.parameter_space.size
        members_sat_percentage = int(round(members_sat/members_total*100,0))
        return f"satisfied {members_sat}/{members_total} members ({members_sat_percentage}%)"


    def get_summary(self) -> str:
        specification = self.get_summary_specification()

        fraction_explored = int((self.synthesizer.explored / self.parameter_space_size) * 100)
        explored = f"explored: {fraction_explored} %"

        underlying_mdp_states = self.colored_mdp.underlying_mdp.nr_states
        underlying_mdp_actions = self.colored_mdp.underlying_mdp.nr_choices
        design_space = f"number of holes: {self.colored_mdp.parameter_space.num_parameters}, parameter space size: {self.colored_mdp.parameter_space.size_or_order}, underlying MDP: {underlying_mdp_states} states / {underlying_mdp_actions} actions"
        timing = f"method: {self.synthesizer.method_name}, synthesis time: {round(self.synthesis_timer.time, 2)} s"

        iterations = self.get_summary_iterations()

        if self.job_type == "synthesis":
            result = self.get_summary_synthesis()
        else:
            result = self.get_summary_evaluation()

        sep = "--------------------\n"
        summary = f"{sep}"\
                f"Synthesis summary:\n" \
                f"{specification}\n{timing}\n{design_space}\n{explored}\n" \
                f"{iterations}\n{result}\n"\
                f"{sep}"
        return summary

    def print(self) -> None:
        logger.info(f'\n{self.get_summary()}')


    def print_mdp_family_table_entries(self) -> None:
        model_info = "model info:\t"
        model_info += "\t".join(["states","choices","MDPs","states*MDPs","SAT MDPs","SAT %",])
        print(model_info)
        # print("\t\t",end="")
        print(self.colored_mdp.underlying_mdp.nr_states,end=" ")
        print(self.colored_mdp.underlying_mdp.nr_choices,end=" ")
        print(self.num_mdps_total,end=" ")
        print(self.colored_mdp.underlying_mdp.nr_states*self.num_mdps_total,end=" ")
        print(self.num_mdps_sat,end=" ")
        sat_by_total_percentage = round(self.num_mdps_sat/self.num_mdps_total*100,2)
        print(sat_by_total_percentage)

        headers = [
            "time","nodes","nodes (merged)","leaves","leaves (merged)","leaves (merged) / MDPs %",
            "policies","policies (merged)","policies (merged) / SAT %","pp time","pp time %",
            "game iters","MDP iters","iters/MDPs %"]
        synt_stats_header = "synthesis info:\t" + "\t".join(headers)
        print(synt_stats_header)

        # print("\t\t",end="")
        synthesis_time = int(self.synthesis_timer.time)
        print(synthesis_time,end=" ")
        print(self.num_nodes,end=" ")
        print(self.num_nodes_merged,end=" ")

        print(self.num_leaves,end=" ")
        print(self.num_leaves_merged,end=" ")
        leaves_by_mdps = round(self.num_leaves_merged/self.num_mdps_total*100,2)
        print(leaves_by_mdps,end=" ")

        print(self.num_policies,end=" ")
        print(self.num_policies_merged,end=" ")
        policies_by_sat = "N/A"
        if self.num_mdps_sat > 0:
            policies_by_sat = round(self.num_policies_merged/self.num_mdps_sat*100,2)
        print(policies_by_sat,end=" ")
        print(self.postprocessing_time,end=" ")
        postprocessing_time_percentage = round(self.postprocessing_time/synthesis_time*100,2)
        print(postprocessing_time_percentage,end=" ")

        print(self.iterations_game,end=" ")
        print(self.iterations_mdp,end=" ")
        iters_by_mdp = round((self.iterations_game+self.iterations_mdp)/self.num_mdps_total*100,2)  # type: ignore[operator]
        print(iters_by_mdp)
        print()
