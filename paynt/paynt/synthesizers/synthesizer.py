import stormpy

from .statistic import Statistic
from .models import MarkovChain, DTMC, MDP
from .quotient import JaniQuotientContainer, POMDPQuotientContainer

from ..profiler import Timer,Profiler

from ..sketch.holes import Holes,DesignSpace

from stormpy.synthesis import CounterexampleGenerator

import logging
logger = logging.getLogger(__name__)


class Synthesizer:

    def __init__(self, sketch, quotient = None):
        self.sketch = sketch
        self.stat = Statistic(sketch, self.method_name)
        Profiler.initialize()

    @property
    def method_name(self):
        """ to be overridden """
        pass

    def print_stats(self):
        print(self.stat.get_summary())

    def synthesize(self, family):
        """ to be overridden """
        pass

    def run(self):
        return self.synthesize(self.sketch.design_space)

class Synthesizer1By1(Synthesizer):

    @property
    def method_name(self):
        return "1-by-1"

    def synthesize(self, family):

        self.stat.family(family)
        self.stat.start()

        satisfying_assignment = None
        for hole_combination in family.all_combinations():

            assignment = family.construct_assignment(hole_combination)
            dtmc = self.sketch.quotient.build_dtmc(assignment)
            self.stat.iteration_dtmc(dtmc.states)
            spec = dtmc.check_specification(self.sketch.specification, short_evaluation = True)
            self.stat.pruned(1)

            if not spec.constraints_result.all_sat:
                continue
            if not self.sketch.specification.has_optimality:
                satisfying_assignment = assignment
                break
            if spec.optimality_result.improves:
                self.sketch.specification.optimality.update_optimum(spec.optimality_result.value)
                satisfying_assignment = assignment

        self.stat.finished(satisfying_assignment)
        return satisfying_assignment


class SynthesizerAR(Synthesizer):

    @property
    def method_name(self):
        return "AR"

    def analyze_family_ar(self, family):
        """
        :return (1) family feasibility (True/False/None)
        :return (2) new satisfying assignment (or None)
        """
        # logger.debug("analyzing family {}".format(family))
        family.mdp = self.sketch.quotient.build(family)
        # print("family size: {}, mdp size: {}".format(family.size, family.mdp.states))
        self.stat.iteration_mdp(family.mdp.states)

        res = family.mdp.check_specification(self.sketch.specification, property_indices = family.property_indices, short_evaluation = True)
        family.analysis_result = res
        satisfying_assignment = None

        prim = res.optimality_result.primary.value
        seco = res.optimality_result.secondary.value if res.optimality_result.secondary is not None else "na"
        # print("{} - {}".format(seco,prim))
        # print("{} - {}".format(prim,seco))
        # exit()

        can_improve = res.constraints_result.feasibility is None
        if res.constraints_result.feasibility == True:
            if not self.sketch.specification.has_optimality:
                satisfying_assignment = family.pick_any()
                return True, satisfying_assignment
            else:
                can_improve = res.optimality_result.can_improve
                if res.optimality_result.optimum is not None:
                    self.sketch.specification.optimality.update_optimum(res.optimality_result.optimum)
                    satisfying_assignment = res.optimality_result.improving_assignment

        if not can_improve:
            self.stat.pruned(family.size)
            return False, satisfying_assignment

        feasibility = None if can_improve else False
        return feasibility, satisfying_assignment

    def split_family(self, family):
        # filter undecided constraints
        res = family.analysis_result
        undecided_constraints = [index for index in family.property_indices if res.constraints_result.results[index].feasibility == None]

        # split family wrt last undecided result
        if res.optimality_result is not None:
            split_result = res.optimality_result.primary.result
            split_result_sec = res.optimality_result.secondary.result
        else:
            split_result = res.constraints_result.results[undecided_constraints[-1]].primary.result
            split_result_sec = res.constraints_result.results[undecided_constraints[-1]].secondary.result
        subfamilies = self.sketch.quotient.split(family.mdp, split_result)
        # subfamilies = self.sketch.quotient.split_milan(family.mdp, split_result, split_result_sec)
        for subfamily in subfamilies:
            subfamily.property_indices = undecided_constraints
        return subfamilies

    def synthesize(self, family):

        self.stat.family(family)
        self.stat.start()

        satisfying_assignment = None
        families = [family]
        while families:
            family = families.pop(-1)

            feasibility,assignment = self.analyze_family_ar(family)
            if assignment is not None:
                satisfying_assignment = assignment
            if feasibility == True:
                break
            if feasibility == False:
                continue

            # undecided
            subfamilies = self.split_family(family)
            families = families + subfamilies


        self.stat.finished(satisfying_assignment)
        return satisfying_assignment


class SynthesizerCEGIS(Synthesizer):

    @property
    def method_name(self):
        return "CEGIS"

    def analyze_family_assignment_cegis(self, family, assignment, ce_generator):
        """
        :return (1) overall satisfiability (True/False)
        :return (2) whether this is an improving assignment
        """

        # logger.debug("analyzing assignment {}".format(assignment))

        # TODO: 1.Build DTMC
        #   = commentary:
        #       This should be done in c++ I think but I am not sure that
        #       I can re-implemented everything in c++ WDYT @Roman?
        # build DTMC
        dtmc = self.sketch.quotient.build_dtmc(assignment)

        self.stat.iteration_dtmc(dtmc.states)

        # TODO: 2.Model check all properties
        #  = commentary:
        #       When I am looking at that implementation I can re-implemented everything inside c++ also
        #       check_constraints method as so on...I think this one is okay :)
        # model check all properties
        spec = dtmc.check_specification(self.sketch.specification,
            property_indices = family.property_indices, short_evaluation = False)

        improving = False

        # TODO: 3. analyze model check results
        #  = commentary:
        #       Do I need representation of `self.sketch.specification` in C++? My idea is to store somehow
        #       optimal value and master (python), should then update value...
        # analyze model checking results
        if spec.constraints_result.all_sat:
            if not self.sketch.specification.has_optimality:
                return True, True
            if spec.optimality_result is not None and spec.optimality_result.improves:
                self.sketch.specification.optimality.update_optimum(spec.optimality_result.value)
                improving = True

        # TODO: 4. prepare DTMC
        #   = commentary:
        #       This one is easy...we can use prepare_dtmc() method from storm (easy)
        # collect all unsatisfiable properties
        ce_generator.prepare_dtmc(dtmc.model, dtmc.quotient_state_map)

        # TODO: 5. generation of conflicts
        #   = commentary:
        #       family.property_indices                                 - as method parameter
        #       self.sketch.specification.constraints[index].threshold  - also threshold as parameter
        #       What about family.analysis_result and this family.analysis_result.constraints_result.results[index].primary?
        #
        # construct conflict wrt each unsatisfiable property
        conflicts = []
        for index in family.property_indices:
            if spec.constraints_result.results[index].sat:
                continue
            threshold = self.sketch.specification.constraints[index].threshold
            bounds = None if family.analysis_result is None else family.analysis_result.constraints_result.results[index].primary
            conflict = ce_generator.construct_conflict(index, threshold, bounds)
            conflicts.append(conflict)

        # TODO: What is this code?? I see duplicity from the previous one...
        if self.sketch.specification.has_optimality and spec.optimality_result.sat == False:
            index = len(self.sketch.specification.constraints)
            threshold = self.sketch.specification.optimality.threshold
            bounds = None if family.analysis_result is None else family.analysis_result.optimality_result.primary.result
            conflict = ce_generator.construct_conflict(index, threshold, bounds)
            conflicts.append(conflict)

        # TODO: 5. Use of all conflicts to exclude the generalizations of assigment...
        #   = commentary:
        #       This one has to make master (python).
        # use conflicts to exclude the generalizations of this assignment
        pruned_estimate = 0
        for conflict in conflicts:
            pruned_estimate += family.exclude_assignment(assignment, conflict)

        # TODO: 6. Map return values of C++ method
        #   = commentary:
        #       For this is little bit tricky, but we can eliminate `pruned_estimate`
        #       (because master will take care) and we need create structure or
        #       Object,  which will consist of
        #        f.e. -> Object(boolean, boolean, Conflicts)
        #
        return False, improving, pruned_estimate

    def synthesize(self, family):
        self.stat.start()

        # map mdp states to hole indices
        quotient_relevant_holes = self.sketch.quotient.quotient_relevant_holes()

        # initialize CE generator
        formulae = self.sketch.specification.stormpy_formulae()
        ce_generator = CounterexampleGenerator(
            self.sketch.quotient.quotient_mdp, self.sketch.design_space.num_holes,
            quotient_relevant_holes, formulae)

        # encode family
        family.z3_initialize()
        family.z3_encode()

        # CEGIS loop
        satisfying_assignment = None

        pure_assignments = ['init']
        terminate = False

        # (assignment, assignment, assignment, assignment, None) <- termination point
        while pure_assignments[-1] is not None or terminate:
            pure_assignments = []
            # pure_assignments_options = []

            # 1. generation phase of specific number of assignments
            hole_name_list_list = []
            options_labels_list_list_list = []
            options_list_list_list = []

            for i in range(1):
                assigment = family.pick_assignment_and_exclude_naive_conflict()

                pure_assignments.append(assigment)  # for python

                hole_name_list = []
                options_labels_list_list = []
                options_list_list = []

                # Additional check TypeError: 'NoneType' object is not iterable
                if assigment is not None:
                    for hole in assigment:
                        hole_name_list.append(hole.name)
                        options_labels_list_list.append(hole.option_labels)
                        options_list_list.append(hole.options)

                hole_name_list_list.append(hole_name_list)
                options_labels_list_list_list.append(options_labels_list_list)
                options_list_list_list.append(options_list_list)

                # pure_assignments.append(assigment.get_pure_assignment()) # .get_pure_assignment() for c++

                # pure_assignments_options.append(assigment.get_pure_assignment_options())
                # for c++ code we have to use
                # pure_assignments.append(family.pick_assignment_and_exclude_naive_conflict().get_pure_assignment())

            # TODO: 2. analyze phase (this should be invoked in c++)
            if self.sketch.specification.optimality.optimum is None:
                current_optimality_value = 0.0
            else:
                current_optimality_value = self.sketch.specification.optimality.optimum
            # ce_generator.invoke_cegis_parallel_execution(
            #     hole_name_list_list,
            #     options_labels_list_list_list,
            #     options_list_list_list,
            #     self.sketch.quotient.quotient_mdp,
            #     self.sketch.quotient.default_actions,
            #     self.sketch.quotient.action_to_hole_options,
            #     # 2.point
            #     family.property_indices,
            #     self.sketch.specification.constraints,
            #     self.sketch.specification.has_optimality,
            #     # send one formula(i.e., "Pmax=? [F ("goal" & (c < 40))]")
            #     formulae[0],
            #     # 3. point
            #     self.sketch.specification.optimality.minimizing,
            #     current_optimality_value,
            #     self.sketch.specification.optimality.threshold,
            #     self.sketch.specification.optimality.epsilon,
            #     self.sketch.specification.optimality.reward,
            #     ce_generator
            # )

            for i in range(1):
                # (assignment, assignment, assignment, assignment, None) <- termination point
                if pure_assignments[i] is None:
                    break
                sat, improving, _ = self.analyze_family_assignment_cegis(family, pure_assignments[i], ce_generator)
                if improving:
                    satisfying_assignment = pure_assignments[i]
                if sat:
                    terminate = True
                    break

            # TODO: 3. Use of all conflicts to exclude the generalizations of assigment (value from slaves - c++)
            # for conflict in conflicts:
            #     pruned_estimate += family.exclude_assignment(pure_assignments, conflict)
            # break


        self.stat.finished(satisfying_assignment)
        return satisfying_assignment


# ----- Adaptivity ----- #
# idea: switch between ar/cegis, allocate more time to the more efficient method

class StageControl:

    # strategy
    strategy_equal = False

    def __init__(self, members_total):

        # pruning stats
        self.members_total = members_total
        self.pruned_ar = 0
        self.pruned_cegis = 0

        # timings
        self.timer_ar = Timer()
        self.timer_cegis = Timer()

        # multiplier to derive time allocated for cegis
        # time_ar * factor = time_cegis
        # =1 is fair, >1 favours cegis, <1 favours ar
        self.cegis_efficiency = 1


    @property
    def ar_running(self):
        return self.timer_ar.running

    def start_ar(self):
        # print(self.pruned_ar, self.pruned_cegis)
        # print(self.timer_ar.read(), self.timer_cegis.read())
        self.timer_cegis.stop()
        self.timer_ar.start()

    def start_cegis(self):
        self.timer_ar.stop()
        self.timer_cegis.start()

    def prune_ar(self, pruned):
        self.pruned_ar += pruned / self.members_total

    def prune_cegis(self, pruned):
        self.pruned_cegis += pruned / self.members_total

    def cegis_step(self):
        """
        :return True if cegis time is over
        """
        if self.timer_cegis.read() < self.timer_ar.read() * self.cegis_efficiency:
            return False

        # calculate average success rate, adjust cegis time allocation factor
        self.timer_cegis.stop()

        if StageControl.strategy_equal:
            return True

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
        return True


class SynthesizerHybrid(SynthesizerAR, SynthesizerCEGIS):

    @property
    def method_name(self):
        return "hybrid"

    def synthesize(self, family):
        self.stat.family(family)
        self.stat.start()

        self.stage_control = StageControl(family.size)

        quotient_relevant_holes = self.sketch.quotient.quotient_relevant_holes()
        formulae = self.sketch.specification.stormpy_formulae()
        ce_generator = CounterexampleGenerator(
            self.sketch.quotient.quotient_mdp, self.sketch.design_space.num_holes,
            quotient_relevant_holes, formulae)

        # encode family
        family.z3_initialize()

        # AR loop
        satisfying_assignment = None
        families = [family]
        while families:
            # MDP analysis
            self.stage_control.start_ar()

            # family = families.pop(-1) # DFS
            family = families.pop(0) # BFS

            feasibility,improving_assignment = self.analyze_family_ar(family)
            if improving_assignment is not None:
                satisfying_assignment = improving_assignment
            if feasibility == True:
                break
            if feasibility == False:
                self.stage_control.prune_ar(family.size)
                continue

            # undecided: initiate CEGIS
            self.stage_control.start_cegis()
            family.z3_encode()
            assignment = family.pick_assignment()
            sat = False
            while assignment is not None:

                sat, improving_assignment, _ = self.analyze_family_assignment_cegis(family, assignment, ce_generator)
                if improving_assignment is not None:
                    satisfying_assignment = improving_assignment
                if sat:
                    break
                # member is UNSAT
                if self.stage_control.cegis_step():
                    break

                # cegis still has time: check next assignment
                assignment = family.pick_assignment()

            if sat:
                break
            if assignment is None:
                # family is UNSAT
                self.stage_control.prune_cegis(family.size)
                self.stat.pruned(family.size)
                continue

            # CEGIS could not process the family: split
            self.stat.hybrid(self.stage_control.cegis_efficiency)
            subfamilies = self.split_family(family)
            families = families + subfamilies


        self.stat.finished(satisfying_assignment)
        return satisfying_assignment

