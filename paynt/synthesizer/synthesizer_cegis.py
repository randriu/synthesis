import paynt.synthesizer.synthesizer
import paynt.synthesizer.conflict_generator.dtmc
import paynt.synthesizer.conflict_generator.mdp
import paynt.family.smt

import logging
logger = logging.getLogger(__name__)


class SynthesizerCEGIS(paynt.synthesizer.synthesizer.Synthesizer):

    # CLI argument selecting conflict generator
    conflict_generator_type = None

    def __init__(self, quotient):
        super().__init__(quotient)

        self.conflict_generator = self.choose_conflict_generator(quotient)

        # assert that no reward formula is maximizing
        assert not self.quotient.specification.contains_maximizing_reward_properties, \
            "Cannot use CEGIS for maximizing reward formulae -- consider using AR or hybrid methods."

    
    def choose_conflict_generator(self, quotient):
        if SynthesizerCEGIS.conflict_generator_type == "mdp":
            conflict_generator = paynt.synthesizer.conflict_generator.mdp.ConflictGeneratorMdp(quotient)
        else:
            # default conflict generator
            conflict_generator = paynt.synthesizer.conflict_generator.dtmc.ConflictGeneratorDtmc(quotient)
        return conflict_generator

    
    @property
    def method_name(self):
        return "CEGIS " + self.conflict_generator.name

    
    def collect_conflict_requests(self, family, mc_result):
        '''
        Construct conflict request wrt each unsatisfiable property,
            pack such properties as well as their MDP results (if available)
        '''
        conflict_requests = []
        for index in family.constraint_indices:
            member_result = mc_result.constraints_result.results[index]
            if member_result.sat:
                continue
            prop = self.quotient.specification.constraints[index]
            family_result = family.analysis_result.constraints_result.results[index] if family.analysis_result is not None else None
            conflict_requests.append( (index,prop,family_result) )
        if self.quotient.specification.has_optimality:
            member_result = mc_result.optimality_result
            index = len(self.quotient.specification.constraints)
            prop = self.quotient.specification.optimality
            family_result = family.analysis_result.optimality_result if family.analysis_result is not None else None
            conflict_requests.append( (index,prop,family_result) )

        return conflict_requests


    def analyze_family_assignment_cegis(self, family, assignment):
        """
        :return (1) list of conflicts to exclude from design space (might be empty)
        :return (2) accepting assignment (or None)
        """
        assert family.mdp is not None, "analyzed family does not have an associated quotient MDP"

        dtmc = self.quotient.build_assignment(assignment)
        self.stat.iteration(dtmc)
        result = dtmc.check_specification(self.quotient.specification, family.constraint_indices, short_evaluation=True)
        # analyze model checking results
        accepting_assignment = None
        accepting,improving_value = result.accepting_dtmc(self.quotient.specification)
        if accepting:
            accepting_assignment = assignment
        if improving_value is not None:
            self.quotient.specification.optimality.update_optimum(improving_value)
        if accepting and not self.quotient.specification.can_be_improved():
            return [], accepting_assignment

        conflict_requests = self.collect_conflict_requests(family, result)
        conflicts = self.conflict_generator.construct_conflicts(family, assignment, dtmc, conflict_requests)

        return conflicts, accepting_assignment


    def synthesize_one(self, family):

        # build the quotient, map mdp states to hole indices
        self.quotient.build(family)
        self.conflict_generator.initialize()

        # use sketch design space as a SAT baseline (TODO why?)
        smt_solver = paynt.family.smt.SmtSolver(self.quotient.family)
        
        # CEGIS loop
        assignment = smt_solver.pick_assignment(family)
        while assignment is not None:
            
            conflicts, accepting_assignment = self.analyze_family_assignment_cegis(family, assignment)
            if accepting_assignment is not None:
                self.best_assignment = accepting_assignment
                if not self.quotient.specification.can_be_improved():
                    return self.best_assignment

            pruned = smt_solver.exclude_conflicts(family, assignment, conflicts)
            self.explored += pruned
            
            # construct next assignment
            assignment = smt_solver.pick_assignment(family)
        return self.best_assignment
