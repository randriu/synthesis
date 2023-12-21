import sys
import z3

# import pycvc5 if installed
import importlib
if importlib.util.find_spec('pycvc5') is not None:
    import pycvc5

import logging
logger = logging.getLogger(__name__)


class FamilyEncoding():

    def __init__(self, smt_solver, family):

        self.smt_solver = smt_solver
        self.family = family

        # for each hole, a formula encoding its possible options
        self.hole_clauses = None
        # SMT formula describing the family
        self.encoding = None
        # set to False as soon as pick_assignment returns None
        self.has_assignments = True

        hole_clauses = []
        for hole in range(family.num_holes):
            all_clauses = smt_solver.solver_clauses[hole]
            clauses = [all_clauses[option] for option in family.hole_options(hole)]
            if len(clauses) == 1:
                or_clause = clauses[0]
            else:
                if smt_solver.use_python_z3:
                    or_clause = z3.Or(clauses)
                elif smt_solver.use_cvc:
                    smt_solver = smt_solver.solver.mkTerm(pycvc5.Kind.Or, clauses)
                else:
                    pass
            hole_clauses.append(or_clause)

        if len(hole_clauses) == 1:
            encoding = hole_clauses[0]
        else:
            if smt_solver.use_python_z3:
                encoding = z3.And(hole_clauses)
            elif smt_solver.use_cvc:
                encoding = smt_solver.solver.mkTerm(pycvc5.Kind.And, hole_clauses)
            else:
                pass

        self.hole_clauses = hole_clauses
        self.encoding = encoding


    def pick_assignment(self):
        
        if not self.has_assignments:
            return None
        
        if self.smt_solver.use_python_z3:
            solver_result = self.smt_solver.solver.check(self.encoding)
            if solver_result == z3.unsat:
                self.has_assignments = False
                return None
            sat_model = self.smt_solver.solver.model()
            hole_options = []
            for hole_index,var in enumerate(self.smt_solver.solver_vars):
                option = sat_model[var].as_long()
                hole_options.append([option])
        elif self.smt_solver.use_cvc:
            solver_result = self.smt_solver.solver.checkSatAssuming(self.encoding)
            if solver_result.isUnsat():
                self.has_assignments = False
                return None
            hole_options = []
            for hole_index,var in enumerate(self.smt_solver.solver_vars):
                option = self.smt_solver.solver.getValue(var).getIntegerValue()
                hole_options.append([option])
        else:
            pass            
        
        assignment = self.family.assume_options_copy(hole_options)
        return assignment

        
class SmtSolver():

    def __init__(self, family):

        # SMT solver containing description of the unexplored design space
        self.solver = None
        # SMT solver choice
        self.use_python_z3 = False
        self.use_cvc = False
    
        # for each hole contains a corresponding solver variable
        self.solver_vars = None
        # for each hole contains a list of equalities [h==opt1,h==opt2,...],
        #   where h is the corresponding solver variable
        self.solver_clauses = None

        # current depth of push/pop solving
        self.solver_depth = 0

        # choose solver
        if "pycvc5" in sys.modules:
            logger.debug("using CVC5 for SMT solving.")
            self.use_cvc = True
        else:
            logger.debug("using Python Z3 for SMT solving.")
            self.use_python_z3 = True

        # create solver, solver variables
        self.solver_clauses = []
        if self.use_python_z3:
            self.solver = z3.Solver()
            self.solver_vars = [z3.Int(hole) for hole in range(family.num_holes)]
        elif self.use_cvc:
            self.solver = pycvc5.Solver()
            self.solver.setOption("produce-models", "true")
            self.solver.setOption("produce-assertions", "true")
            # self.solver.setLogic("ALL")
            # self.solver.setLogic("QF_ALL")
            self.solver.setLogic("QF_DT")
            # self.solver.setLogic("QF_UFDT")
            # self.solver.setLogic("QF_UFLIA")
            intSort = self.solver.getIntegerSort()
            self.solver_vars = [self.solver.mkConst(intSort, str(hole)) for hole in range(family.num_holes)]
        else:
            raise RuntimeError("Need to enable at least one SMT solver.")

        # create solver clauses
        self.solver_clauses = []
        for hole in range(family.num_holes):
            var = self.solver_vars[hole]
            clauses = [self.create_hole_clause(hole,option) for option in family.hole_options(hole)]
            self.solver_clauses.append(clauses)


    def create_hole_clause(self, hole, option):
        var = self.solver_vars[hole]
        if self.use_python_z3:
            return var == option
        elif self.use_cvc:
            return self.solver.mkTerm(pycvc5.Kind.Equal, var, self.solver.mkInteger(option))
        else:
            return None


    def pick_assignment(self, family):
        '''
        :return unexplored hole assignment from the family
            (or None if no instance remains)
        '''
        family.encode(self)
        return family.encoding.pick_assignment()

    def pick_assignment_priority(self, family, priority_subfamily):

        if priority_subfamily is None:
            return self.pick_assignment(family)

        # explore priority subfamily first
        assignment = self.pick_assignment(priority_subfamily)
        if assignment is not None:
            return assignment

        # explore remaining members
        return self.pick_assignment(family)
    
    
    def exclude_conflicts(self, family, assignment, conflicts):
        '''
        :param conflicts a list of conflicts (may be empty)
        :return estimate of pruned assignments
        '''
        pruning_estimate = 0
        for conflict in conflicts:
            pruning_estimate += self.exclude_conflict(family, assignment, conflict)
        return pruning_estimate
    
    
    def exclude_conflict(self, family, assignment, conflict):
        '''
        Exclude assignment from the family encoding using provided conflict.
        :param family base family
        :param assignment hole assignment that yielded unsatisfiable DTMC
        :param conflict indices of relevant holes in the corresponding counterexample
        :return estimate of pruned assignments
        '''
        assert family.encoding is not None
        
        if family.encoding is None:
            family.encoding = FamilyEncoding(self, family)

        pruning_estimate = 1
        counterexample_clauses = []
        for hole,var in enumerate(self.solver_vars):
            if hole in conflict:
                option = assignment.hole_options(hole)[0]
                counterexample_clauses.append(self.solver_clauses[hole][option])
            else:
                if family.hole_num_options(hole) < family.hole_num_options_total(hole):
                    counterexample_clauses.append(family.encoding.hole_clauses[hole])
                pruning_estimate *= family.hole_num_options(hole)

        if self.use_python_z3:
            if len(counterexample_clauses) == 0:
                counterexample_encoding = False
            else:
                counterexample_encoding = z3.Not(z3.And(counterexample_clauses))
            self.solver.add(counterexample_encoding)
        elif self.use_cvc:
            if len(counterexample_clauses) == 0:
                counterexample_encoding = self.solver.mkFalse()
            elif len(counterexample_clauses) == 1:
                counterexample_encoding = counterexample_clauses[0].notTerm()
            else:
                counterexample_encoding = self.solver.mkTerm(pycvc5.Kind.And, counterexample_clauses).notTerm()
            self.solver.assertFormula(counterexample_encoding)
        else:
            pass

        return pruning_estimate


    def level(self, refinement_depth):
        ''' Reset solver depth level to correspond to refinement level. '''

        if refinement_depth == 0:
            # fresh family, nothing to do
            return

        # reset to the scope of the parent (refinement_depth - 1)
        while self.solver_depth >= refinement_depth:
            self.solver.pop()
            self.solver_depth -= 1

        # create new scope
        self.solver.push()
        self.solver_depth += 1

