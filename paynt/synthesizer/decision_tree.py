import paynt.synthesizer.synthesizer_ar
import paynt.quotient.mdp
import paynt.utils.timer

import stormpy
import payntbind

import logging
logger = logging.getLogger(__name__)

class SynthesizerDecisionTree(paynt.synthesizer.synthesizer_ar.SynthesizerAR):

    # tree depth
    tree_depth = 0
    # if set, all trees of size at most tree_depth will be enumerated
    tree_enumeration = False
    # if set, the optimal k-tree will be used to jumpstart the synthesis of the (k+1)-tree
    use_tree_hint = True

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
            # logger.info(f"harmonization achieved value {res.optimality_result.value}")
            self.num_harmonization_succeeded += 1
            family.analysis_result.improving_assignment = assignment
            family.analysis_result.improving_value = assignment_value
            family.analysis_result.can_improve = True
            self.update_optimum(family)


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

    def counters_reset(self):
        self.num_families_considered = 0
        self.num_families_skipped = 0
        self.num_families_model_checked = 0
        self.num_schedulers_preserved = 0
        self.num_harmonizations = 0
        self.num_harmonization_succeeded = 0

    def counters_print(self):
        logger.info(f"families considered: {self.num_families_considered}")
        logger.info(f"families skipped by construction: {self.num_families_skipped}")
        logger.info(f"families with schedulers preserved: {self.num_schedulers_preserved}")
        logger.info(f"families model checked: {self.num_families_model_checked}")
        logger.info(f"harmonizations attempted: {self.num_harmonizations}")
        logger.info(f"harmonizations succeeded: {self.num_harmonization_succeeded}")
        print()

    def synthesize_tree(self, depth:int):
        self.counters_reset()
        self.quotient.set_depth(depth)
        self.synthesize(keep_optimum=True)
        self.counters_print()

    def synthesize_tree_sequence(self, opt_result_value):
        tree_hint = None
        for depth in range(SynthesizerDecisionTree.tree_depth+1):
            print()
            self.quotient.set_depth(depth)
            best_assignment_old = self.best_assignment

            family = self.quotient.family
            self.explored = 0
            self.counters_reset()
            self.stat = paynt.synthesizer.statistic.Statistic(self)
            self.stat.start(family)
            self.synthesis_timer = paynt.utils.timer.Timer()
            self.synthesis_timer.start()
            families = [family]

            if SynthesizerDecisionTree.use_tree_hint and tree_hint is not None:
                subfamily = family.copy()
                self.quotient.decision_tree.root.apply_hint(subfamily,tree_hint)
                families = [subfamily,family]

            for family in families:
                self.synthesize_one(family)
            self.stat.finished_synthesis()
            self.stat.print()
            self.counters_print()

            new_assignment_synthesized = self.best_assignment != best_assignment_old
            if new_assignment_synthesized:
                logger.info("printing synthesized assignment below:")
                logger.info(self.best_assignment)

                if self.best_assignment is not None and self.best_assignment.size == 1:
                    dtmc = self.quotient.build_assignment(self.best_assignment)
                    result = dtmc.check_specification(self.quotient.specification)
                    logger.info(f"double-checking specification satisfiability: {result}")

                if abs( (self.best_assignment_value-opt_result_value)/opt_result_value ) < 1e-3:
                    break

                tree_hint = self.quotient.decision_tree.root
                tree_hint.associate_assignment(self.best_assignment)

            if self.resource_limit_reached():
                break


    def run(self, optimum_threshold=None):
        paynt_mdp = paynt.models.models.Mdp(self.quotient.quotient_mdp)
        mc_result = paynt_mdp.model_check_property(self.quotient.get_property())
        opt_result_value = mc_result.value
        logger.info(f"the optimal scheduler has value: {opt_result_value}")

        if self.quotient.specification.has_optimality:
            epsilon = 1e-1
            mc_result_positive = opt_result_value > 0
            if self.quotient.specification.optimality.maximizing == mc_result_positive:
                epsilon *= -1
            # optimum_threshold = opt_result_value * (1 + epsilon)

        self.set_optimality_threshold(optimum_threshold)
        self.best_assignment = None
        self.best_assignment_value = None

        if not SynthesizerDecisionTree.tree_enumeration:
            self.synthesize_tree(SynthesizerDecisionTree.tree_depth)
        else:
            self.synthesize_tree_sequence(opt_result_value)

        logger.info(f"the optimal scheduler has value: {opt_result_value}")
        if self.best_assignment is not None:
            logger.info(f"admissible assignment found: {self.best_assignment}")
            if self.quotient.specification.has_optimality:
                logger.info(f"best assignment has value {self.quotient.specification.optimality.optimum}")
        else:
            logger.info("no admissible assignment found")
        time_total = paynt.utils.timer.GlobalTimer.read()
        # logger.info(f"synthesis time: {round(time_total, 2)} s")

        print()
        for name,time in self.quotient.coloring.getProfilingInfo():
            time_percent = round(time/time_total*100,1)
            print(f"{name} = {time} s ({time_percent} %)")

        return self.best_assignment
