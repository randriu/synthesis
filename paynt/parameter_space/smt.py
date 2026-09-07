import sys
import z3

# import pycvc5 if installed
import importlib
if importlib.util.find_spec('pycvc5') is not None:
    import pycvc5

import logging
logger = logging.getLogger(__name__)


class ParameterSpaceEncoding():

    def __init__(self, smt_solver, parameter_space):

        self.smt_solver = smt_solver
        self.parameter_space = parameter_space

        # for each parameter, a formula encoding its possible options
        self.parameter_clauses = None
        # SMT formula describing the parameter_space
        self.encoding = None
        # set to False as soon as pick_assignment returns None
        self.has_assignments = True

        parameter_clauses = []
        for parameter in range(parameter_space.num_parameters):
            all_clauses = smt_solver.solver_clauses[parameter]
            clauses = [all_clauses[option] for option in parameter_space.parameter_options(parameter)]
            if len(clauses) == 1:
                or_clause = clauses[0]
            else:
                if smt_solver.use_python_z3:
                    or_clause = z3.Or(clauses)
                elif smt_solver.use_cvc:
                    smt_solver = smt_solver.solver.mkTerm(pycvc5.Kind.Or, clauses)
                else:
                    pass
            parameter_clauses.append(or_clause)

        if len(parameter_clauses) == 1:
            encoding = parameter_clauses[0]
        else:
            if smt_solver.use_python_z3:
                encoding = z3.And(parameter_clauses)
            elif smt_solver.use_cvc:
                encoding = smt_solver.solver.mkTerm(pycvc5.Kind.And, parameter_clauses)
            else:
                pass

        self.parameter_clauses = parameter_clauses
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
            parameter_options = []
            for parameter_index,var in enumerate(self.smt_solver.solver_vars):
                option = sat_model[var].as_long()
                parameter_options.append([option])
        elif self.smt_solver.use_cvc:
            solver_result = self.smt_solver.solver.checkSatAssuming(self.encoding)
            if solver_result.isUnsat():
                self.has_assignments = False
                return None
            parameter_options = []
            for parameter_index,var in enumerate(self.smt_solver.solver_vars):
                option = self.smt_solver.solver.getValue(var).getIntegerValue()
                parameter_options.append([option])
        else:
            pass

        assignment = self.parameter_space.assume_options_copy(parameter_options)
        return assignment


class SmtSolver():

    def __init__(self, parameter_space):

        # SMT solver containing description of the unexplored design space
        self.solver = None
        # SMT solver choice
        self.use_python_z3 = False
        self.use_cvc = False

        # for each parameter contains a corresponding solver variable
        self.solver_vars = None
        # for each parameter contains a list of equalities [p==opt1,p==opt2,...],
        #   where p is the corresponding solver variable
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
            self.solver_vars = [z3.Int(parameter) for parameter in range(parameter_space.num_parameters)]
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
            self.solver_vars = [self.solver.mkConst(intSort, str(parameter)) for parameter in range(parameter_space.num_parameters)]
        else:
            raise RuntimeError("Need to enable at least one SMT solver.")

        # create solver clauses
        self.solver_clauses = []
        for parameter in range(parameter_space.num_parameters):
            var = self.solver_vars[parameter]
            clauses = [self.create_parameter_clause(parameter,option) for option in parameter_space.parameter_options(parameter)]
            self.solver_clauses.append(clauses)


    def create_parameter_clause(self, parameter, option):
        var = self.solver_vars[parameter]
        if self.use_python_z3:
            return var == option
        elif self.use_cvc:
            return self.solver.mkTerm(pycvc5.Kind.Equal, var, self.solver.mkInteger(option))
        else:
            return None


    def pick_assignment(self, parameter_space):
        '''
        :return unexplored parameter assignment from the parameter_space
            (or None if no instance remains)
        '''
        parameter_space.encode(self)
        return parameter_space.encoding.pick_assignment()

    def pick_assignment_priority(self, parameter_space, priority_parameter_subspace):

        if priority_parameter_subspace is None:
            return self.pick_assignment(parameter_space)

        # explore priority parameter subspace first
        assignment = self.pick_assignment(priority_parameter_subspace)
        if assignment is not None:
            return assignment

        # explore remaining members
        return self.pick_assignment(parameter_space)


    def exclude_conflicts(self, parameter_space, assignment, conflicts):
        '''
        :param conflicts a list of conflicts (may be empty)
        :return estimate of pruned assignments
        '''
        pruning_estimate = 0
        for conflict in conflicts:
            pruning_estimate += self.exclude_conflict(parameter_space, assignment, conflict)
        return pruning_estimate


    def exclude_conflict(self, parameter_space, assignment, conflict):
        '''
        Exclude assignment from the parameter_space encoding using provided conflict.
        :param parameter_space base parameter_space
        :param assignment parameter assignment that yielded unsatisfiable DTMC
        :param conflict indices of relevant parameters in the corresponding counterexample
        :return estimate of pruned assignments
        '''
        assert parameter_space.encoding is not None

        if parameter_space.encoding is None:
            parameter_space.encoding = ParameterSpaceEncoding(self, parameter_space)

        pruning_estimate = 1
        counterexample_clauses = []
        for parameter,var in enumerate(self.solver_vars):
            if parameter in conflict:
                option = assignment.parameter_options(parameter)[0]
                counterexample_clauses.append(self.solver_clauses[parameter][option])
            else:
                if parameter_space.parameter_num_options(parameter) < parameter_space.parameter_num_options_total(parameter):
                    counterexample_clauses.append(parameter_space.encoding.parameter_clauses[parameter])
                pruning_estimate *= parameter_space.parameter_num_options(parameter)

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
            # fresh parameter_space, nothing to do
            return

        # reset to the scope of the parent (refinement_depth - 1)
        while self.solver_depth >= refinement_depth:
            self.solver.pop()
            self.solver_depth -= 1

        # create new scope
        self.solver.push()
        self.solver_depth += 1
