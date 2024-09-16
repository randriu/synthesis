import paynt.synthesizer.synthesizer_ar
import paynt.quotient.mdp

import stormpy
import payntbind

import logging
logger = logging.getLogger(__name__)

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

    def verify_hole_selection(self, family, hole_selection):
        spec = self.quotient.specification
        assignment = family.assume_options_copy(hole_selection)
        dtmc = self.quotient.build_assignment(assignment)
        res = dtmc.check_specification(spec)
        if not res.constraints_result.sat:
            return
        if not spec.has_optimality:
            family.analysis_result.improving_assignment = assignment
            family.analysis_result.can_improve = False
            return
        assignment_value = res.optimality_result.value
        if spec.optimality.improves_optimum(assignment_value):
            logger.info(f"harmonization achieved value {res.optimality_result.value}")
            self.num_harmonization_succeeded += 1
            family.analysis_result.improving_assignment = assignment
            family.analysis_result.improving_value = assignment_value
            family.analysis_result.can_improve = True
            self.update_optimum(family)

            family_value = family.analysis_result.optimality_result.primary.value
            if(abs(family_value-assignment_value) < 1e-3):
                logger.info(f"harmonization leads to family skip")
                self.num_harmonization_skip += 1
                family.analysis_result.can_improve = False


    def harmonize_inconsistent_scheduler(self, family):
        self.num_harmonizations += 1
        mdp = family.mdp
        result = family.analysis_result.undecided_result()
        hole_selection = result.primary_selection
        harmonizing_hole = [hole for hole,options in enumerate(hole_selection) if len(options)>1][0]
        selection_1 = hole_selection.copy(); selection_1[harmonizing_hole] = [selection_1[harmonizing_hole][0]]
        selection_2 = hole_selection.copy(); selection_2[harmonizing_hole] = [selection_2[harmonizing_hole][1]]
        for selection in [selection_1,selection_2]:
            self.verify_hole_selection(family,selection)


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
                consistent,hole_selection = self.quotient.are_choices_consistent(family.scheduler_choices, family)
                assert not consistent
                family.analysis_result.optimality_result.primary_selection = hole_selection
                return

        self.num_families_model_checked += 1
        self.check_specification_for_mdp(family)
        if not family.analysis_result.can_improve:
            return
        self.harmonize_inconsistent_scheduler(family)


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
                if self.global_resource_limit_reached():
                    break
                # if self.best_assignment is not None:
                if self.best_assignment_value is not None and abs( (self.best_assignment_value-mc_result.value)/mc_result.value ) <1e-2:
                    break

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
        logger.info(f"families with schedulers preserved: {self.num_schedulers_preserved}")
        logger.info(f"families model checked: {self.num_families_model_checked}")
        logger.info(f"harmonizations attempted: {self.num_harmonizations}")
        logger.info(f"harmonizations succeeded: {self.num_harmonization_succeeded}")
        logger.info(f"harmonizations lead to family skip: {self.num_harmonization_skip}")

        print()
        time_total = self.stat.synthesis_timer_total.read()
        for name,time in self.quotient.coloring.getProfilingInfo():
            time_percent = round(time/time_total*100,1)
            print(f"{name} = {time} s ({time_percent} %)")
        print()

        # splits_total = sum(self.quotient.splitter_count)
        # if splits_total == 0: splits_total = 1
        # splitter_freq = [ round(splits/splits_total*100,1) for splits in self.quotient.splitter_count]
        # for hole,freq in enumerate(splitter_freq):
        #     print(self.quotient.family.hole_name(hole),freq)
        # print()

        return self.best_assignment
