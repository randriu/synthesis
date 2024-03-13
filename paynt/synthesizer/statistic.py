import stormpy.storage

import paynt.utils.profiler
import paynt.synthesizer.synthesizer

import math

import logging
logger = logging.getLogger(__name__)

# zero approximation to avoid zero division exception
APPROX_ZERO = 0.000001

def safe_division(dividend, divisor):
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
    synthesis_timer_total = paynt.utils.profiler.Timer()
    
    def __init__(self, synthesizer):
        
        self.synthesizer = synthesizer
        self.quotient = self.synthesizer.quotient

        self.iterations_dtmc = None
        self.acc_size_dtmc = 0
        self.avg_size_dtmc = 0

        self.iterations_mdp = None
        self.acc_size_mdp = 0
        self.avg_size_mdp = 0

        self.iterations_game = None
        self.acc_size_game = 0
        self.avg_size_game = 0

        self.synthesized_assignment = None
        self.job_type = None

        # MDP family
        self.num_mdps_total = None
        self.num_mdps_sat = None
        self.num_tree_nodes = None
        self.num_tree_nodes_merged = None
        self.num_policies = None
        self.num_policies_merged = None

        self.family_size = None
        self.synthesis_timer = paynt.utils.profiler.Timer()
        self.status_horizon = Statistic.status_period_seconds


    def start(self, family):
        self.family_size = family.size
        self.synthesis_timer.start()
        if not self.synthesis_timer_total.running:
            self.synthesis_timer_total.start()
    
    def iteration(self, model):
        ''' Identify the type of the model and count corresponding iteration. '''
        if isinstance(model, paynt.quotient.models.MarkovChain):
            model = model.model
        if type(model) == stormpy.storage.SparseDtmc:
            self.iteration_dtmc(model.nr_states)
        elif type(model) == stormpy.storage.SparseMdp:
            self.iteration_mdp(model.nr_states)
        else:
            logger.debug(f"unknown model type {type(model)}")

    def iteration_dtmc(self, size_dtmc):
        if self.iterations_dtmc is None:
            self.iterations_dtmc = 0
        self.iterations_dtmc += 1
        self.acc_size_dtmc += size_dtmc
        self.print_status()

    def iteration_mdp(self, size_mdp):
        if self.iterations_mdp is None:
            self.iterations_mdp = 0
        self.iterations_mdp += 1
        self.acc_size_mdp += size_mdp
        self.print_status()

    def iteration_game(self, size_game):
        if self.iterations_game is None:
            self.iterations_game = 0
        self.iterations_game += 1
        self.acc_size_game += size_game
        self.print_status()

    def new_fsc_found(self, value, assignment, size):
        time_elapsed = round(self.synthesis_timer_total.read(),1)
        # print(f'new opt: {value}')
        # print(f'new opt: {value}, elapsed {time_elapsed}s')
        # print(f'-----------PAYNT----------- \
              # \nValue = {value} | Time elapsed = {time_elapsed}s | FSC size = {size}\nFSC = {assignment}\n', flush=True)

    
    def status(self):
        ret_str = "> "
        discarded = self.quotient.discarded
        fraction_explored = (self.synthesizer.explored + discarded) / self.family_size
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

        iters = []
        if self.iterations_game is not None:
            iters += [f"game: {self.iterations_game}"]
        if self.iterations_mdp is not None:
            iters += [f"MDP: {self.iterations_mdp}"]
        if self.iterations_dtmc is not None:
            iters += [f"DTMC: {self.iterations_dtmc}"]
        ret_str += ", iters = {" + ", ".join(iters) + "}"
        
        spec = self.quotient.specification
        if spec.has_optimality and spec.optimality.optimum is not None:
            optimum = round(spec.optimality.optimum,3)
            ret_str += f", opt = {optimum}"
        return ret_str


    def print_status(self):
        if not self.synthesis_timer.read() > self.status_horizon:
            return
        print(self.status(), flush=True)
        self.status_horizon = self.synthesis_timer.read() + Statistic.status_period_seconds


    def finished_synthesis(self, assignment):
        self.job_type = "synthesis"
        self.synthesis_timer.stop()
        self.synthesized_assignment = assignment

    def finished_evaluation(self, evaluations):
        self.job_type = "evaluation"
        self.synthesis_timer.stop()
        self.evaluations = evaluations
        

    def get_summary_specification(self):
        spec = self.quotient.specification
        specification = ""
        if len(spec.constraints) > 0:
            specification += "\n".join([f"constraint {i + 1}: {str(f)}" for i,f in enumerate(spec.constraints)]) + "\n"
        if spec.has_optimality:
            specification += f"optimality objective: {str(spec.optimality)}\n"
        return specification

    def get_summary_iterations(self):
        iterations = ""
        if self.iterations_game is not None:
            avg_size = round(safe_division(self.acc_size_game, self.iterations_game))
            type_stats = f"Game stats: avg MDP size: {avg_size}, iterations: {self.iterations_game}" 
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

    def get_summary_synthesis(self):
        spec = self.quotient.specification
        if spec.has_optimality and spec.optimality.optimum is not None:
            optimum = round(spec.optimality.optimum, 6)
            return f"optimum: {optimum}"
        else:
            feasible = "yes" if self.synthesized_assignment is not None else "no"
            return f"feasible: {feasible}"

    def get_summary_evaluation(self):
        if not self.evaluations or not isinstance(self.evaluations[0], paynt.synthesizer.synthesizer.FamilyEvaluation):
            return ""
        members_sat = sum( [evaluation.family.size for evaluation in self.evaluations if evaluation.sat ])
        members_total = self.quotient.design_space.size
        members_sat_percentage = int(round(members_sat/members_total*100,0))
        return f"satisfied {members_sat}/{members_total} members ({members_sat_percentage}%)"

    
    def get_summary(self):
        specification = self.get_summary_specification()

        fraction_explored = int((self.synthesizer.explored / self.family_size) * 100)
        explored = f"explored: {fraction_explored} %"

        quotient_states = self.quotient.quotient_mdp.nr_states
        quotient_actions = self.quotient.quotient_mdp.nr_choices
        design_space = f"number of holes: {self.quotient.design_space.num_holes}, family size: {self.quotient.design_space.size_or_order}, quotient: {quotient_states} states / {quotient_actions} actions"
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
    
    def print(self):    
        print(self.get_summary(),end="")
        # self.print_mdp_family_table_entries()


    def print_mdp_family_table_entries(self):
        model_info = "model info:\t"
        model_info += "\t".join(["states","choices","MDPs","states*MDPs","SAT MDPs","SAT %",])
        print(model_info)
        # print("\t\t",end="")
        print(self.quotient.quotient_mdp.nr_states,end=" ")
        print(self.quotient.quotient_mdp.nr_choices,end=" ")
        print(self.num_mdps_total,end=" ")
        print(self.quotient.quotient_mdp.nr_states*self.num_mdps_total,end=" ")
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
        iters_by_mdp = round((self.iterations_game+self.iterations_mdp)/self.num_mdps_total*100,2)
        print(iters_by_mdp)
        print()
