import paynt.synthesizer.synthesizer
import paynt.synthesizer.synthesizer_ar
import paynt.synthesizer.synthesizer_cegis

import paynt.parameter_space.smt
import paynt.utils.timer

import logging
logger = logging.getLogger(__name__)


class StageControl:
    '''
    AR-CEGIS adaptivity: switch between ar/cegis, allocate more time to
    the more efficient method
    '''

    # whether only AR is performed
    only_ar = False
    # whether 1 AR followed by only CEGIS is performed
    only_cegis = False
    # whether adaptive hybrid is enabled
    adaptive_hybrid = True

    def __init__(self, parameter_space_size):
        # timings
        self.timer_ar = paynt.utils.timer.Timer()
        self.timer_cegis = paynt.utils.timer.Timer()

        self.parameter_space_size = parameter_space_size
        self.pruned_ar = 0
        self.pruned_cegis = 0
        
        # multiplier to derive time allocated for cegis
        # time_ar * factor = time_cegis
        # =1 is fair, >1 favours cegis, <1 favours ar
        self.cegis_efficiency = 1

    def start_ar(self):
        self.timer_cegis.stop()
        self.timer_ar.start()

    def start_cegis(self):
        self.timer_ar.stop()
        self.timer_cegis.start()

    def prune_ar(self, pruned):
        self.pruned_ar += pruned / self.parameter_space_size

    def prune_cegis(self, pruned):
        self.pruned_cegis += pruned / self.parameter_space_size

    def cegis_has_time(self):
        """
        :return True if cegis still has some time
        """
        
        # whether only AR is performed
        if StageControl.only_ar:
            return False

        # whether only CEGIS is performed
        if StageControl.only_cegis:
            return True

        # whether CEGIS has more time
        if self.timer_cegis.read() < self.timer_ar.read() * self.cegis_efficiency:
            return True

        # stop CEGIS
        self.timer_cegis.stop()

        if StageControl.adaptive_hybrid:
            if self.pruned_ar == 0 and self.pruned_cegis == 0:
                self.cegis_efficiency = 1
            elif self.pruned_ar == 0 and self.pruned_cegis > 0:
                self.cegis_efficiency = 2
            elif self.pruned_ar > 0 and self.pruned_cegis == 0:
                self.cegis_efficiency = 0.5
            else:
                success_rate_cegis = self.pruned_cegis / self.timer_cegis.read()
                success_rate_ar = self.pruned_ar / self.timer_ar.read()
                self.cegis_efficiency = success_rate_cegis / success_rate_ar
        
        return False


class SynthesizerHybrid(paynt.synthesizer.synthesizer_ar.SynthesizerAR, paynt.synthesizer.synthesizer_cegis.SynthesizerCEGIS):

    @property
    def method_name(self):
        return "hybrid"

    def synthesize_one(self, parameter_space):

        self.conflict_generator.initialize()
        smt_solver = paynt.parameter_space.smt.SmtSolver(self.colored_mdp.parameter_space)

        # AR-CEGIS loop
        parameter_spaces = [parameter_space]
        self.stage_control = StageControl(parameter_space.size)
        while parameter_spaces:

            # initiate AR analysis
            self.stage_control.start_ar()

            # choose parameter space
            parameter_space = parameter_spaces.pop(-1)

            # reset SMT solver level
            smt_solver.level(parameter_space.refinement_depth)

            # analyze the parameter space
            self.verify_parameter_space(parameter_space)
            self.update_optimum(parameter_space)
            if parameter_space.analysis_result.can_improve == False:
                self.explore(parameter_space)
                self.stage_control.prune_ar(parameter_space.size)
                continue

            # undecided: initiate CEGIS analysis
            self.stage_control.start_cegis()

            # construct priority parameter subspace that corresponds to primary scheduler
            if parameter_space.analysis_result.optimality_result is not None:
                result = parameter_space.analysis_result.optimality_result
            else:
                result = parameter_space.analysis_result.constraints_result.results[0]
            priority_parameter_subspace = parameter_space.assume_options_copy(result.primary_selection)

            # explore parameter space assignments
            parameter_space_explored = False
            while True:

                if not self.stage_control.cegis_has_time():
                    break   # CEGIS timeout

                parameter_space.encode(smt_solver)
                # assignment = smt_solver.pick_assignment(parameter_space)
                assignment = smt_solver.pick_assignment_priority(parameter_space, priority_parameter_subspace)
                if assignment is None:
                    parameter_space_explored = True
                    break   # explored whole parameter space

                conflicts, accepting_assignment = self.analyze_parameter_space_assignment_cegis(parameter_space, assignment)
                pruned = smt_solver.exclude_conflicts(parameter_space, assignment, conflicts)
                self.explored += pruned
                self.stage_control.prune_cegis(pruned)

                if accepting_assignment is not None:
                    self.best_assignment = accepting_assignment
                    if not self.task.specification.can_be_improved:
                        return self.best_assignment

                # assignment is UNSAT: move on to the next assignment

            if parameter_space_explored:
                continue

            parameter_subspaces = self.split_undecided_space(parameter_space)
            parameter_spaces = parameter_spaces + parameter_subspaces

        return self.best_assignment
