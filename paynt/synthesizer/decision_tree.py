import paynt.synthesizer.synthesizer_ar
import paynt.quotient.mdp

import logging
logger = logging.getLogger(__name__)

class SynthesizerDecisionTree(paynt.synthesizer.synthesizer_ar.SynthesizerAR):

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


    def set_decision_tree(self):
        dt = self.quotient.decision_tree

        # model = "maze"
        model = "obstacles"

        if model == "maze":
            self.quotient.decide(dt.root,"clk")
            main = dt.root.child_false

            # decide(decide, "y")
            # decide(decide.child_true, "x")
            # decide(decide.child_true.child_true, "x")

            # decide(main,"y")
            # decide(main.child_false,"x")
            # decide(main.child_true,"x")
            # decide(main.child_true.child_true,"x")

            self.quotient.decide(main, "y")
            self.quotient.decide(main.child_false, "x")
            self.quotient.decide(main.child_false.child_true, "x")
            self.quotient.decide(main.child_true, "x")
            self.quotient.decide(main.child_true.child_true, "x")

        if model == "obstacles":
            self.quotient.decide(dt.root, "x")
            self.quotient.decide(dt.root.child_true, "x")
            self.quotient.decide(dt.root.child_true.child_true, "y")
            self.quotient.decide(dt.root.child_true.child_false, "y")
            self.quotient.decide(dt.root.child_false, "x")
            self.quotient.decide(dt.root.child_false.child_true, "y")
            self.quotient.decide(dt.root.child_false.child_false, "y")


    def evaluate_tree(self):
        # self.quotient.build_coloring()
        self.quotient.build_coloring_full()
        assignment = self.synthesize(keep_optimum=True, print_stats=True)
        if assignment is not None:
            self.best_assignment = assignment
            self.best_configuration = self.configuration.copy()
            if self.quotient.specification.has_optimality:
                logger.info(f"new optimum found:  {self.quotient.specification.optimality.optimum}")
        print("synthesized, OK")
        exit()
        

    def configuration_init(self):
        self.configuration = [0 for node in self.quotient.decision_tree.collect_nonterminals()]

    def configuration_next(self):
        num_variables = len(self.quotient.decision_tree.variables)
        for node_index,variable in reversed(list(enumerate(self.configuration))):
            variable_new = (variable+1) % num_variables
            self.configuration[node_index] = variable_new
            if variable_new != 0:
                return True
        return False

    def configuration_evaluate(self):
        logger.debug(f"synthesizing configuration: {self.configuration}")
        nodes = self.quotient.decision_tree.collect_nonterminals()
        for node,variable in zip(nodes,self.configuration):
            node.set_variable(variable)
        self.evaluate_tree()

    def iterate_tree(self, depth:int):
        self.quotient.decision_tree.set_depth(depth)
        self.configuration_init()
        while True:
            self.configuration_evaluate()
            configuration_valid = self.configuration_next()
            if not configuration_valid:
                break

    def iterate_trees(self, max_depth:int):
        for depth in range(max_depth+1):
            self.iterate_tree(depth)


    def run(self, optimum_threshold=None, export_evaluation=None):
        paynt_mdp = paynt.models.models.Mdp(self.quotient.quotient_mdp)
        mc_result = paynt_mdp.model_check_property(self.quotient.get_property())
        logger.info(f"optimal scheduler has value: {mc_result}")

        if self.quotient.specification.has_optimality:
            # optimum_threshold = mc_result.value * (1 + 0.1)
            # optimum_threshold = mc_result.value * (1 - 0.1)
            # optimum_threshold = 7
            pass

        if self.quotient.specification.has_optimality and optimum_threshold is not None:
            self.quotient.specification.optimality.update_optimum(optimum_threshold)
            logger.debug(f"optimality threshold set to {optimum_threshold}")

        self.best_assignment = None
        self.best_configuration = None
        # self.iterate_trees(max_depth = 3)
        self.iterate_tree(2)

        if self.best_assignment is not None:
            logger.info(f"admissible assignment found: {self.best_assignment}")
            logger.info(f"assignment was constructed for the following configuration: {self.best_configuration}")
            if self.quotient.specification.has_optimality:
                logger.info(f"best assignment has value {self.quotient.specification.optimality.optimum}")
        else:
            logger.info("no admissible assignment found")

        # print("payntbind::selectCompatibleChoices = ", self.quotient.coloring.selectCompatibleChoicesTime())

        return self.best_assignment
