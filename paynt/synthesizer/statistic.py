import stormpy.storage

import paynt.utils.profiler

import math

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

    # parameters
    status_period = 3
    whole_synthesis_timer = paynt.utils.profiler.Timer()
    
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

        self.feasible = None
        self.assignment = None

        # MDP family
        self.num_mdps_total = None
        self.num_mdps_sat = None
        self.num_policies = None
        self.num_policies_merged = None
        self.num_policies_yes = None

        self.synthesis_time = paynt.utils.profiler.Timer()
        self.status_horizon = Statistic.status_period


    def start(self):
        self.synthesis_time.start()

    
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
        time_elapsed = round(self.whole_synthesis_timer.read(),1)
        # print(f'new opt: {value}')
        # print(f'new opt: {value}, elapsed {time_elapsed}s')
        # print(f'-----------PAYNT----------- \
              # \nValue = {value} | Time elapsed = {time_elapsed}s | FSC size = {size}\nFSC = {assignment}\n', flush=True)

    
    def status(self):
        ret_str = "> "
        discarded = self.quotient.discarded if self.quotient.discarded is not None else 0
        fraction_explored = (self.synthesizer.explored + discarded) / self.quotient.design_space.size
        time_estimate = safe_division(self.synthesis_time.read(), fraction_explored)
        percentage_explored = int(fraction_explored * 100000) / 1000.0
        ret_str += f"Progress {percentage_explored}%"
        
        time_elapsed = int(self.synthesis_time.read())
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

        iters = [self.iterations_game,self.iterations_mdp,self.iterations_dtmc]
        iters = [str(i) for i in iters if i is not None]
        ret_str += ", iters = (" + ", ".join(iters) + ")"
        
        spec = self.quotient.specification
        if spec.has_optimality and spec.optimality.optimum is not None:
            optimum = round(spec.optimality.optimum,3)
            ret_str += f", opt = {optimum}"
        return ret_str


    def print_status(self):
        if not self.synthesis_time.read() > self.status_horizon:
            return
        print(self.status(), flush=True)
        self.status_horizon = self.synthesis_time.read() + Statistic.status_period


    def finished(self, assignment):

        self.synthesis_time.stop()
        self.feasible = False
        self.assignment = None
        if assignment is not None:
            self.feasible = True
            self.assignment = str(assignment)
        self.optimum = None
        if self.quotient.specification.has_optimality:
            self.optimum = self.quotient.specification.optimality.optimum

    def get_summary(self):
        spec = self.quotient.specification
        specification = "\n".join([f"constraint {i + 1}: {str(f)}" for i,f in enumerate(spec.constraints)]) + "\n"
        specification += f"optimality objective: {str(spec.optimality)}\n" if spec.has_optimality else ""

        fraction_explored = int((self.synthesizer.explored / self.quotient.design_space.size) * 100)
        explored = f"explored: {fraction_explored} %"

        super_quotient_states = self.quotient.quotient_mdp.nr_states
        super_quotient_actions = self.quotient.quotient_mdp.nr_choices

        design_space = f"number of holes: {self.quotient.design_space.num_holes}, family size: {self.quotient.design_space.size}, super quotient: {super_quotient_states} states / {super_quotient_actions} actions"
        timing = f"method: {self.synthesizer.method_name}, synthesis time: {round(self.synthesis_time.time, 2)} s"

        family_stats = ""
        if self.iterations_game is not None:
            avg_size = round(safe_division(self.acc_size_game, self.iterations_game))
            type_stats = f"Game stats: avg MDP size: {avg_size}, iterations: {self.iterations_game}" 
            family_stats += f"{type_stats}\n"

        if self.iterations_mdp is not None:
            avg_size = round(safe_division(self.acc_size_mdp, self.iterations_mdp))
            type_stats = f"AR stats: avg MDP size: {avg_size}, iterations: {self.iterations_mdp}"
            family_stats += f"{type_stats}\n"

        if self.iterations_dtmc is not None:
            avg_size = round(safe_division(self.acc_size_mdp, self.iterations_dtmc))
            type_stats = f"CEGIS stats: avg DTMC size: {avg_size}, iterations: {self.iterations_dtmc}"
            family_stats += f"{type_stats}\n"

        feasible = "yes" if self.feasible else "no"
        result = f"feasible: {feasible}" if self.optimum is None else f"optimal: {round(self.optimum, 6)}"
        # assignment = f"hole assignment: {str(self.assignment)}\n" if self.assignment else ""
        assignment = ""

        sep = "--------------------\n"
        summary = f"{sep}Synthesis summary\n" \
                f"{specification}\n{timing}\n{design_space}\n{explored}\n" \
                f"{family_stats}\n{result}\n{assignment}" \
                f"{sep}"
        return summary
    
    def print(self):    
        print(self.get_summary())


    def print_mdp_family_table_entries(self):
        model_info = "model info:\t"
        model_info += "\t".join(["states","actions","MDPs","SAT MDPs","SAT %",])
        print(model_info)
        print("\t\t",end="")
        print(self.quotient.quotient_mdp.nr_states,end="\t")
        print(self.quotient.quotient_mdp.nr_choices,end="\t")
        print(self.num_mdps_total,end="\t")
        print(self.num_mdps_sat,end="\t")
        sat_by_total_percentage = round(self.num_mdps_sat/self.num_mdps_total*100,0)
        print(sat_by_total_percentage)
        

        synt_stats_header = "synt info:\t"
        synt_stats_header += "\t".join(["policies","merged","merged/SAT %","yes nodes","time","game iters","MDP iters", "iters/MDPs"])
        print(synt_stats_header)
        print("\t\t",end="")
        print(self.num_policies,end="\t")
        print(self.num_policies_merged,end="\t")
        merged_by_sat_percentage = round(self.num_policies_merged/self.num_mdps_sat*100,1)
        print(merged_by_sat_percentage,end="\t")
        print(self.num_policies_yes,end="\t")
        synthesis_time = round(self.synthesis_time.time,0)
        print(synthesis_time,end="\t")
        print(self.iterations_game,end="\t")
        print(self.iterations_mdp,end="\t")
        iters_by_mdp = round((self.iterations_game+self.iterations_mdp)/self.num_mdps_total,2)
        print(iters_by_mdp)
        print()
