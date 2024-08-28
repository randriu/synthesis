import paynt.synthesizer.synthesizer_ar
import paynt.quotient.mdp

import logging
logger = logging.getLogger(__name__)

class SynthesizerDecisionTree(paynt.synthesizer.synthesizer_ar.SynthesizerAR):

    # tree depth
    tree_depth = 0
    # if set, all trees of size at most tree_depth will be enumerated
    tree_enumeration = False

    def __init__(self, *args):
        super().__init__(*args)
        self.best_assignment = None

    @property
    def method_name(self):
        return "AR (decision tree)"

    def verify_family(self, family):
        self.stat.iteration_smt()
        self.quotient.build(family)
        if family.mdp is None:
            return
        self.stat.iteration_mdp(family.mdp.states)
        res = self.quotient.check_specification_for_mdp(family.mdp, family.constraint_indices)
        if res.improving_assignment == "any":
            res.improving_assignment = family
        family.analysis_result = res

    def synthesize_tree(self, depth:int):
        logger.debug(f"synthesizing tree of depth {depth}")
        self.quotient.decision_tree.set_depth(depth)
        self.quotient.build_coloring()
        assignment = self.synthesize(keep_optimum=True)
        if assignment is not None:
            self.best_assignment = assignment
            if self.quotient.specification.has_optimality:
                logger.info(f"new optimum {self.quotient.specification.optimality.optimum} found, printing assignment below:")
            print(self.best_assignment)

    def run(self, optimum_threshold=None, export_evaluation=None):
        paynt_mdp = paynt.models.models.Mdp(self.quotient.quotient_mdp)
        mc_result = paynt_mdp.model_check_property(self.quotient.get_property())
        mc_result_positive = mc_result.value > 0
        logger.info(f"the optimal scheduler has value: {mc_result}")

        if self.quotient.specification.has_optimality:
            epsilon = 1e-1
            if self.quotient.specification.optimality.maximizing == mc_result_positive:
                epsilon *= -1
            # optimum_threshold = mc_result.value * (1 + epsilon)

        if self.quotient.specification.has_optimality and optimum_threshold is not None:
            self.quotient.specification.optimality.update_optimum(optimum_threshold)
            logger.debug(f"optimality threshold set to {optimum_threshold}")

        self.best_assignment = None
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

        for name,time in self.quotient.coloring.getProfilingInfo():
            time_percent = round(time / self.stat.synthesis_timer_total.read()*100,1)
            print(f"{name} = {time} s ({time_percent} %)")
        print()

        return self.best_assignment
