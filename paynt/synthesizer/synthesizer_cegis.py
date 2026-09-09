import paynt.synthesizer.synthesizer
import paynt.synthesizer.conflict_generator.dtmc
import paynt.synthesizer.conflict_generator.mdp
import paynt.parameter_space.smt

import logging
logger = logging.getLogger(__name__)


class SynthesizerCEGIS(paynt.synthesizer.synthesizer.Synthesizer):

    def __init__(self, colored_mdp, task):
        super().__init__(colored_mdp, task)

        self.conflict_generator = self.choose_conflict_generator(colored_mdp, task)

        # assert that no reward formula is maximizing
        assert not self.task.specification.contains_maximizing_reward_properties, \
            "Cannot use CEGIS for maximizing reward formulae -- consider using AR or hybrid methods."


    def choose_conflict_generator(self, colored_mdp, task):
        if task.conflict_generator_type == "mdp":
            conflict_generator = paynt.synthesizer.conflict_generator.mdp.ConflictGeneratorMdp(colored_mdp, task)
        else:
            # default conflict generator
            conflict_generator = paynt.synthesizer.conflict_generator.dtmc.ConflictGeneratorDtmc(colored_mdp, task)
        return conflict_generator


    @property
    def method_name(self):
        return "CEGIS " + self.conflict_generator.name


    def collect_conflict_requests(self, node, mc_result):
        '''
        Construct conflict request wrt each unsatisfiable property,
            pack such properties as well as their MDP results (if available)
        '''
        conflict_requests = []
        for index in node.constraint_indices:
            member_result = mc_result.constraints_result.results[index]
            if member_result.sat:
                continue
            prop = self.task.specification.constraints[index]
            parameter_space_result = node.analysis_result.constraints_result.results[index] if node.analysis_result is not None else None
            conflict_requests.append( (index,prop,parameter_space_result) )
        if self.task.specification.has_optimality:
            member_result = mc_result.optimality_result
            index = len(self.task.specification.constraints)
            prop = self.task.specification.optimality
            parameter_space_result = node.analysis_result.optimality_result if node.analysis_result is not None else None
            conflict_requests.append( (index,prop,parameter_space_result) )

        return conflict_requests


    def analyze_parameter_space_assignment_cegis(self, node, assignment):
        """
        :return (1) list of conflicts to exclude from design space (might be empty)
        :return (2) accepting assignment (or None)
        """
        assert node.mdp is not None, "analyzed parameter space does not have an associated underlying MDP"

        dtmc = self.colored_mdp.build_assignment(assignment)
        self.stat.iteration(dtmc)
        result = dtmc.check_specification(self.task.specification, node.constraint_indices, short_evaluation=True)
        # analyze model checking results
        accepting_assignment = None
        accepting,improving_value = result.accepting_dtmc(self.task.specification)
        if accepting:
            accepting_assignment = assignment
        if improving_value is not None:
            self.task.specification.optimality.update_optimum(improving_value)
            self.best_assignment_value = improving_value
        if accepting and not self.task.specification.can_be_improved():
            return [], accepting_assignment

        conflict_requests = self.collect_conflict_requests(node, result)
        conflicts = self.conflict_generator.construct_conflicts(node, assignment, dtmc, conflict_requests)

        return conflicts, accepting_assignment


    def synthesize_one(self, node):

        # build the induced sub-MDP, mapping mdp states to parameter indices
        node.mdp, node.selected_choices = self.colored_mdp.build(node.parameter_space)
        self.conflict_generator.initialize()

        # use sketch design space as a SAT baseline (TODO why?)
        smt_solver = paynt.parameter_space.smt.SmtSolver(self.colored_mdp.parameter_space)

        # CEGIS loop
        assignment = smt_solver.pick_assignment(node)
        while assignment is not None:

            conflicts, accepting_assignment = self.analyze_parameter_space_assignment_cegis(node, assignment)
            if accepting_assignment is not None:
                self.best_assignment = accepting_assignment
                if not self.task.specification.can_be_improved():
                    return self.best_assignment

            pruned = smt_solver.exclude_conflicts(node, assignment, conflicts)
            self.explored += pruned

            # construct next assignment
            assignment = smt_solver.pick_assignment(node)
        return self.best_assignment
