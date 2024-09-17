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
    # TODO
    use_tree_hint = True

    def __init__(self, *args):
        super().__init__(*args)
        self.tree_hint = None
        self.tree_hint_size = None

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

            family_value = family.analysis_result.optimality_result.primary.value
            if(abs(family_value-assignment_value) < 1e-3):
                # logger.info(f"harmonization leads to family skip")
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


    def presplit(self, subfamily):
        family = self.quotient.family

        # fix subfamily first
        for hole in range(family.num_holes):
            all_options = family.hole_options(hole)
            if subfamily.hole_num_options(hole) == family.hole_num_options(hole):
                continue
            if not self.quotient.is_variable_hole[hole]:
                continue
            options = [option for option in all_options if option<=subfamily.hole_options(hole)[0]]
            subfamily.hole_set_options(hole,options)

        subfamilies = [subfamily]
        prototype_family = subfamily.copy()
        for hole in range(family.num_holes):
            if prototype_family.hole_num_options(hole) == family.hole_num_options(hole):
                continue;
            prototype_options = prototype_family.hole_options(hole)
            suboptions_list = []
            all_options = family.hole_options(hole)
            if not self.quotient.is_variable_hole[hole]:
                complement = [option for option in all_options if option not in prototype_options]
                suboptions_list.append(complement)
            else:
                complement = [option for option in all_options if option>prototype_options[-1]]
                if len(complement)>0:
                    suboptions_list.append(complement)

            for suboptions in suboptions_list:
                new_subfamily = prototype_family.copy()
                new_subfamily.hole_set_options(hole,suboptions)
                subfamilies.append(new_subfamily)
            prototype_family.hole_set_options(hole,all_options)
        return subfamilies

    def synthesize_tree(self, depth:int):
        self.quotient.set_depth(depth)
        self.synthesize(keep_optimum=True)

    def synthesize_tree_sequence(self, opt_result_value):
        self.tree_hint = None

        for depth in range(SynthesizerDecisionTree.tree_depth+1):
            self.quotient.set_depth(depth)
            best_assignment_old = self.best_assignment

            family = self.quotient.family
            self.explored = 0
            self.stat = paynt.synthesizer.statistic.Statistic(self)
            print()
            self.stat.start(family)
            families = [family]

            if self.tree_hint is not None and SynthesizerDecisionTree.use_tree_hint:
                subfamily = family.copy()
                # find the correct application point
                application_node = self.quotient.decision_tree.root
                # for _ in range(self.tree_hint_size,depth):
                #     application_node = application_node.child_true
                application_node.apply_hint(subfamily,self.tree_hint)

                # presplit
                # families = self.presplit(subfamily)
                # assert family.size == sum([f.size for f in families])

                # hint,
                families = [subfamily,family]

            for family in families:
                self.synthesize_one(family)
            self.stat.finished_synthesis()
            self.stat.print()

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

                self.tree_hint = self.quotient.decision_tree.root
                self.tree_hint.associate_assignment(self.best_assignment)
                self.tree_hint_size = depth

            if self.resource_limit_reached():
                break



    def run(self, optimum_threshold=None, export_evaluation=None):
        paynt_mdp = paynt.models.models.Mdp(self.quotient.quotient_mdp)
        mc_result = paynt_mdp.model_check_property(self.quotient.get_property())
        opt_result_value = mc_result.value
        logger.info(f"the optimal scheduler has value: {opt_result_value}")

        self.num_families_considered = 0
        self.num_families_skipped = 0
        self.num_families_model_checked = 0
        self.num_schedulers_preserved = 0
        self.num_harmonizations = 0
        self.num_harmonization_succeeded = 0
        self.num_harmonization_skip = 0

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
        logger.info(f"synthesis time: {round(time_total, 2)} s")

        print()
        logger.info(f"families considered: {self.num_families_considered}")
        logger.info(f"families skipped by construction: {self.num_families_skipped}")
        logger.info(f"families with schedulers preserved: {self.num_schedulers_preserved}")
        logger.info(f"families model checked: {self.num_families_model_checked}")
        logger.info(f"harmonizations attempted: {self.num_harmonizations}")
        logger.info(f"harmonizations succeeded: {self.num_harmonization_succeeded}")
        logger.info(f"harmonizations lead to family skip: {self.num_harmonization_skip}")

        print()
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
