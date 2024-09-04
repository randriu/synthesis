import paynt.synthesizer.synthesizer_ar
import paynt.quotient.mdp

import stormpy
import payntbind

import logging
logger = logging.getLogger(__name__)

# import numpy

class SynthesizerDecisionTree(paynt.synthesizer.synthesizer_ar.SynthesizerAR):

    # tree depth
    tree_depth = 0
    # if set, all trees of size at most tree_depth will be enumerated
    tree_enumeration = False

    def __init__(self, *args):
        super().__init__(*args)

    @property
    def method_name(self):
        return "AR (decision tree)"


    def harmonize_inconsistent_scheduler(self, family):
        self.num_harmonizations += 1
        mdp = family.mdp
        result = family.analysis_result.undecided_result()
        mdp_choice_values = self.quotient.choice_values(mdp.model, result.prop, result.primary.result.get_values())
        state_to_choice = self.quotient.scheduler_to_state_to_choice(mdp, result.primary.result.scheduler)
        choices_reduced = stormpy.BitVector(family.scheduler_choices)

        choices_support = result.primary.result.scheduler.compute_action_support(mdp.model.nondeterministic_choice_indices)
        expected_visits = self.quotient.compute_expected_visits(mdp.model, result.prop, choices_support)
        assert len(expected_visits) == mdp.model.nr_states
        state_score = [0] * mdp.model.nr_states
        ndi = mdp.model.nondeterministic_choice_indices
        for mdp_state in range(mdp.model.nr_states):
            if state_to_choice[mdp.quotient_state_map[mdp_state]] is None:
                # state is unreachable in the DTMC induced by the scheduler
                continue
            state_min = state_max = mdp_choice_values[ndi[mdp_state]]
            for choice in range(ndi[mdp_state]+1,ndi[mdp_state+1]):
                if state_min is None or mdp_choice_values[choice] < state_min:
                    state_min = mdp_choice_values[choice]
                if state_max is None or mdp_choice_values[choice] > state_max:
                    state_max = mdp_choice_values[choice]
            divisor = None
            max_diff = state_max-state_min
            if abs(state_min) > 0.001:
                state_diff = abs(max_diff/state_min)
            elif abs(state_max) > 0.001:
                state_diff = abs(max_diff/state_max)
            else:
                state_diff = 0
            state_score[mdp_state] = state_diff
            state_score[mdp_state] *= expected_visits[mdp_state]
        threshold = 0
        # threshold = numpy.quantile(state_score,0.2) # keep some percentage
        for mdp_state,score in enumerate(state_score):
            quotient_state = mdp.quotient_state_map[mdp_state]
            if state_to_choice[quotient_state] is not None and score <= threshold:
                choices_reduced.set(state_to_choice[quotient_state],False)

        consistent,hole_selection = self.quotient.are_choices_consistent(choices_reduced, family.family)
        if not consistent:
            return
        # logger.info(f"harmonization is SAT")
        spec = self.quotient.specification
        assignment = family.assume_options_copy(hole_selection)
        dtmc = self.quotient.build_assignment(assignment)
        res = dtmc.check_specification(spec)
        if res.constraints_result.sat:
            if not spec.has_optimality:
                family.analysis_result.improving_assignment = assignment
                family.analysis_result.can_improve = False
            else:
                assignment_value = res.optimality_result.value
                if spec.optimality.improves_optimum(assignment_value):
                    logger.info(f"harmonization achieved value {res.optimality_result.value}")
                    self.num_harmonization_succeeded += 1
                    family.analysis_result.improving_assignment = assignment
                    family.analysis_result.improving_value = assignment_value
                    family.analysis_result.can_improve = True

                    family_value = family.analysis_result.optimality_result.primary.value
                    if(abs(family_value-assignment_value) < 0.001):
                        logger.info(f"harmonization leads to family skip")
                        self.num_harmonization_skip += 1
                        family.analysis_result.can_improve = False

    def verify_family(self, family):
        self.num_families_considered += 1

        self.quotient.build(family)
        if family.mdp is None:
            self.num_families_skipped += 1
            return

        if family.parent_info is not None:
            for choice in family.parent_info.scheduler_choices:
                if not family.selected_choices[choice]:
                    break
            else:
                # scheduler preserved in the sub-family
                self.num_schedulers_preserved += 1
                family.analysis_result = family.parent_info.analysis_result
                family.scheduler_choices = family.parent_info.scheduler_choices
                # print("DTMC size = ", family.scheduler_choices.number_of_set_bits())
                consistent,hole_selection = self.quotient.are_choices_consistent(family.scheduler_choices, family)
                # print("consistent (same parent) ", consistent)
                assert not consistent
                family.analysis_result.optimality_result.primary_selection = hole_selection
                return

        self.num_families_model_checked += 1
        self.check_specification_for_mdp(family)
        if not family.analysis_result.can_improve:
            return
        # self.harmonize_inconsistent_scheduler(family)


    def synthesize_tree(self, depth:int):
        logger.debug(f"synthesizing tree of depth {depth}")
        self.quotient.decision_tree.set_depth(depth)
        self.quotient.build_coloring()
        self.synthesize(keep_optimum=True)

    def run(self, optimum_threshold=None, export_evaluation=None):
        paynt_mdp = paynt.models.models.Mdp(self.quotient.quotient_mdp)
        mc_result = paynt_mdp.model_check_property(self.quotient.get_property())
        logger.info(f"the optimal scheduler has value: {mc_result}")

        self.num_families_considered = 0
        self.num_families_skipped = 0
        self.num_families_model_checked = 0
        self.num_schedulers_preserved = 0
        self.num_harmonizations = 0
        self.num_harmonization_succeeded = 0
        self.num_harmonization_skip = 0

        if self.quotient.specification.has_optimality:
            epsilon = 1e-1
            mc_result_positive = mc_result.value > 0
            if self.quotient.specification.optimality.maximizing == mc_result_positive:
                epsilon *= -1
            # optimum_threshold = mc_result.value * (1 + epsilon)

        self.set_optimality_threshold(optimum_threshold)
        self.best_assignment = None
        self.best_assignment_value = None

        if not SynthesizerDecisionTree.tree_enumeration:
            self.synthesize_tree(SynthesizerDecisionTree.tree_depth)
        else:
            for depth in range(SynthesizerDecisionTree.tree_depth+1):
                self.synthesize_tree(depth)

        logger.info(f"the optimal scheduler has value: {mc_result}")
        if self.best_assignment is not None:
            logger.info(f"admissible assignment found: {self.best_assignment}")
            if self.quotient.specification.has_optimality:
                logger.info(f"best assignment has value {self.quotient.specification.optimality.optimum}")
        else:
            logger.info("no admissible assignment found")

        print()
        logger.info(f"families considered: {self.num_families_considered}")
        logger.info(f"families skipped by construction: {self.num_families_skipped}")
        logger.info(f"families model checked: {self.num_families_model_checked}")
        logger.info(f"families with schedulers preserved: {self.num_schedulers_preserved}")
        logger.info(f"harmonizations attempted: {self.num_harmonizations}")
        logger.info(f"harmonizations succeeded: {self.num_harmonization_succeeded}")
        logger.info(f"harmonizations lead to family skip: {self.num_harmonization_skip}")

        print()
        time_total = self.stat.synthesis_timer_total.read()
        for name,time in self.quotient.coloring.getProfilingInfo():
            time_percent = round(time/time_total*100,1)
            print(f"{name} = {time} s ({time_percent} %)")
        print()

        return self.best_assignment
