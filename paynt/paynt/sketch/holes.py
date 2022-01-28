import math
import itertools

import sys
import pycvc5   # comment this import if you don't have CVC5 installed
import z3

import stormpy.synthesis

from ..profiler import Profiler

import logging
logger = logging.getLogger(__name__)

class Hole:
    '''
    Hole with a name, a list of options and corresponding option labels.
    Options for each hole are simply indices of the corresponding hole assignment.
    Each hole is identified by its position in Holes, therefore, this order must
      be preserved in the refining process.
    Option labels are not refined when assuming suboptions so that the correct
      label can be accessed by the value of an option.
    '''
    def __init__(self, name, options, option_labels):
        self.name = name
        self.options = options
        self.option_labels = option_labels

    @property
    def size(self):
        return len(self.options)

    def __str__(self):
        labels = [self.option_labels[option] for option in self.options]
        if self.size == 1:
            return"{}={}".format(self.name,labels[0]) 
        else:
            return self.name + ": {" + ",".join(labels) + "}"

    def copy(self):
        return Hole(self.name, self.options.copy(), self.option_labels)

    def assume_options(self, options):
        self.options = options

    @property
    def is_trivial(self):
        return len(self.options) == 1

    @property
    def is_unrefined(self):
        return len(self.options) == len(self.option_labels)


class Holes(list):
    ''' List of holes. '''

    def __init__(self, *args):
        super().__init__(*args)

    @property
    def num_holes(self):
        return len(self)

    @property
    def hole_indices(self):
        return list(range(len(self)))

    @property
    def size(self):
        ''' Family size. '''
        return math.prod([hole.size for hole in self])

    def __str__(self):
        return ", ".join([str(hole) for hole in self]) 

    def copy(self):
        return Holes([hole.copy() for hole in self])

    def assume_hole_options(self, hole_index, options):
        ''' Assume suboptions of a certain hole. '''
        self[hole_index].assume_options(options)

    def assume_options(self, hole_options):
        ''' Assume suboptions for each hole. '''
        for hole_index,hole in enumerate(self):
            hole.assume_options(hole_options[hole_index])

    def pick_any(self):
        suboptions = [[hole.options[0]] for hole in self]
        holes = self.copy()
        holes.assume_options(suboptions)
        return holes

    def includes(self, hole_assignment):
        '''
        :return True if this family contains hole_assignment
        '''
        for hole_index,option in hole_assignment.items():
            if not option in self[hole_index].options:
                return False
        return True

    def all_combinations(self):
        return itertools.product(*[hole.options for hole in self])

    def construct_assignment(self, combination):
        combination = list(combination)
        suboptions = [[option] for option in combination]
        holes = self.copy()
        holes.assume_options(suboptions)
        return holes




class DesignSpace(Holes):
    '''
    List of holes supplied with
    - a list of constraint indices to investigate in this design space
    - (optionally) z3 encoding of this design space
    :note z3 (re-)encoding construction must be invoked manually
    '''

    # z3 solver containing description of the complete design space
    solver = None
    # for each hole, a corresponding solver variable
    solver_vars = None
    # for each hole, a list of equalities [h==opt1,h==opt2,...]
    solver_clauses = None

    # SMT solver
    use_python_z3 = False
    use_storm_z3 = False
    use_cvc = False
    solver_depth = 0

    def __init__(self, holes = []):
        super().__init__(holes.copy())
        self.property_indices = None

        self.mdp = None
        self.analysis_result = None
        self.analysis_hints = None
        
        self.hole_clauses = None
        self.encoding = None

        self.refinement_depth = 0

    def copy(self):
        ds = DesignSpace(super().copy())
        ds.property_indices = self.property_indices.copy()
        return ds

    def set_analysis_hints(self, property_indices, analysis_hints):
        self.property_indices = property_indices
        self.analysis_hints = analysis_hints

    def translate_analysis_hint(self, hint):
        if hint is None:
            return None
        translated_hint = [0] * self.mdp.states
        for state in range(self.mdp.states):
            translated_hint[state] = hint[self.mdp.quotient_state_map[state]]
        return translated_hint

    def translate_analysis_hints(self):
        if self.analysis_hints is None:
            return None

        analysis_hints = dict()
        for prop,hints in self.analysis_hints.items():
            hint_prim,hint_seco = hints
            hint_prim = self.translate_analysis_hint(hint_prim)
            hint_seco = self.translate_analysis_hint(hint_seco)
            analysis_hints[prop] = (hint_prim,hint_seco) # no swap?
            # use primary hint for the secondary direction and vice versa
            # analysis_hints[prop] = (hint_seco,hint_prim) # swap?
        self.mdp.analysis_hints = analysis_hints

    def sat_initialize(self):
        ''' Use this design space as a baseline for future refinements. '''

        DesignSpace.solver_depth = 0
        if "pycvc5" in sys.modules:
            DesignSpace.use_cvc = True
        else:
            DesignSpace.use_python_z3 = True
            DesignSpace.use_storm_z3 = False

        DesignSpace.solver_clauses = []
        if DesignSpace.use_python_z3:
            logger.debug("Using Python Z3 for SMT solving.")
            DesignSpace.solver = z3.Solver()
            DesignSpace.solver_vars = [z3.Int(hole_index) for hole_index in self.hole_indices]
            for hole_index,hole in enumerate(self):
                var = DesignSpace.solver_vars[hole_index]
                clauses = [var == option for option in hole.options]
                DesignSpace.solver_clauses.append(clauses)
        elif DesignSpace.use_storm_z3:
            logger.debug("Using Storm Z3 for SMT solving.")
            expression_manager = stormpy.storage.ExpressionManager()
            DesignSpace.solver = stormpy.utility.Z3SmtSolver(expression_manager)
            DesignSpace.solver_vars = [expression_manager.create_integer_variable(str(hole_index)) for hole_index in self.hole_indices]
            for hole_index,hole in enumerate(self):
                var = DesignSpace.solver_vars[hole_index].get_expression()
                clauses = [stormpy.storage.Expression.Eq(var,expression_manager.create_integer(option)) for option in hole.options]
                DesignSpace.solver_clauses.append(clauses)
        elif DesignSpace.use_cvc:
            logger.debug("Using CVC5 for SMT solving.")
            DesignSpace.solver = pycvc5.Solver()
            DesignSpace.solver.setOption("produce-models", "true")
            DesignSpace.solver.setOption("produce-assertions", "true")
            # DesignSpace.solver.setLogic("ALL")
            # DesignSpace.solver.setLogic("QF_ALL")
            DesignSpace.solver.setLogic("QF_DT")
            # DesignSpace.solver.setLogic("QF_UFDT")
            # DesignSpace.solver.setLogic("QF_UFLIA")
            intSort = DesignSpace.solver.getIntegerSort()
            DesignSpace.solver_vars = [DesignSpace.solver.mkConst(intSort, str(hole_index)) for hole_index in self.hole_indices]
            for hole_index,hole in enumerate(self):
                var = DesignSpace.solver_vars[hole_index]
                clauses = [DesignSpace.solver.mkTerm(pycvc5.Kind.Equal, var, DesignSpace.solver.mkInteger(option)) for option in hole.options]
                DesignSpace.solver_clauses.append(clauses)
        else:
            raise RuntimeError("Need to enable at least one SMT solver.")
    
    @property
    def encoded(self):
        return self.encoding is not None
        
    def encode(self):
        ''' Encode this design space. '''
        Profiler.start("encode")
        self.hole_clauses = []
        for hole_index,hole in enumerate(self):
            all_clauses = DesignSpace.solver_clauses[hole_index]
            clauses = [all_clauses[option] for option in hole.options]
            if len(clauses) == 1:
                or_clause = clauses[0]
            else:
                if DesignSpace.use_python_z3:
                    or_clause = z3.Or(clauses)
                elif DesignSpace.use_storm_z3:
                    or_clause = stormpy.storage.Expression.Disjunction(clauses)
                elif DesignSpace.use_cvc:
                    or_clause = DesignSpace.solver.mkTerm(pycvc5.Kind.Or, clauses)
                else:
                    pass
            self.hole_clauses.append(or_clause)

        if len(self.hole_clauses) == 1:
            self.encoding = self.hole_clauses[0]
        else:
            if DesignSpace.use_python_z3:
                self.encoding = z3.And(self.hole_clauses)
            elif DesignSpace.use_storm_z3:
                self.encoding = stormpy.storage.Expression.Conjunction(self.hole_clauses)
            elif DesignSpace.use_cvc:
                self.encoding = DesignSpace.solver.mkTerm(pycvc5.Kind.And, self.hole_clauses)
            else:
                pass

        Profiler.resume()

    def pick_assignment(self):
        '''
        Pick any (feasible) hole assignment.
        :return None if no instance remains
        '''
        # get satisfiable assignment within this design space
        if not self.encoded:
            self.encode()
        
        Profiler.start("pick_assignment")
        if DesignSpace.use_python_z3:
            Profiler.start("    SMT check")
            solver_result = DesignSpace.solver.check(self.encoding)
            Profiler.resume()
            if solver_result == z3.unsat:
                Profiler.resume()
                return None
            Profiler.start("    SMT model")
            sat_model = DesignSpace.solver.model()
            hole_options = []
            for hole_index,var in enumerate(DesignSpace.solver_vars):
                option = sat_model[var].as_long()
                hole_options.append([option])
            Profiler.resume()
        elif DesignSpace.use_storm_z3:
            Profiler.start("    SMT check")
            solver_result = DesignSpace.solver.check_with_assumptions(set([self.encoding]))
            Profiler.resume()
            if solver_result == stormpy.utility.SmtCheckResult.Unsat:
                Profiler.resume()
                return None
            Profiler.start("    SMT model")
            solver_model = DesignSpace.solver.model
            hole_options = []
            for hole_index,var in enumerate(DesignSpace.solver_vars):
                option = solver_model.get_integer_value(var)
                hole_options.append([option])
            Profiler.resume()
        elif DesignSpace.use_cvc:
            Profiler.start("    SMT check")
            solver_result = DesignSpace.solver.checkSatAssuming(self.encoding)
            Profiler.resume()
            if solver_result.isUnsat():
                Profiler.resume()
                return None
            Profiler.start("    SMT model")
            hole_options = []
            for hole_index,var in enumerate(DesignSpace.solver_vars):
                option = DesignSpace.solver.getValue(var).getIntegerValue()
                hole_options.append([option])
            Profiler.resume()
        else:
            pass            
        
        Profiler.start("    assignment construction")
        assignment = self.copy()
        assignment.assume_options(hole_options)
        Profiler.resume()

        Profiler.resume()
        return assignment

    def exclude_assignment(self, assignment, conflict):
        '''
        Exclude assignment from the design space using provided conflict.
        :param assignment hole assignment that yielded unsatisfiable DTMC
        :param conflict indices of relevant holes in the corresponding counterexample
        :return estimate of pruned assignments
        '''
        pruning_estimate = 1
        counterexample_clauses = []
        for hole_index,var in enumerate(DesignSpace.solver_vars):
            if hole_index in conflict:
                option = assignment[hole_index].options[0]
                counterexample_clauses.append(DesignSpace.solver_clauses[hole_index][option])
            else:
                if not self[hole_index].is_unrefined:
                    counterexample_clauses.append(self.hole_clauses[hole_index])
                pruning_estimate *= self[hole_index].size
        assert len(counterexample_clauses) > 0  # not sure about this

        if DesignSpace.use_python_z3:
            counterexample_encoding = z3.Not(z3.And(counterexample_clauses))
            DesignSpace.solver.add(counterexample_encoding)
        elif DesignSpace.use_storm_z3:
            conflict_encoding = stormpy.storage.Expression.Conjunction(counterexample_clauses)
            counterexample_encoding = stormpy.storage.Expression.Not(conflict_encoding)
            DesignSpace.solver.add(counterexample_encoding)
        elif DesignSpace.use_cvc:
            if len(counterexample_clauses) == 1:
                counterexample_encoding = counterexample_clauses[0].notTerm()
            else:
                counterexample_encoding = DesignSpace.solver.mkTerm(pycvc5.Kind.And, counterexample_clauses).notTerm()
            DesignSpace.solver.assertFormula(counterexample_encoding)
        else:
            pass

        return pruning_estimate

    def sat_level(self):
        ''' Reset solver depth level to correspond to refinement level. '''

        if self.refinement_depth == 0:
            # fresh family, nothing to do
            return

        # reset to the scope of the parent (refinement_depth - 1)
        while DesignSpace.solver_depth >= self.refinement_depth:
            if DesignSpace.use_storm_z3:
                DesignSpace.solver.pop(1)
            else:
                DesignSpace.solver.pop()
            DesignSpace.solver_depth -= 1

        # create new scope
        DesignSpace.solver.push()
        DesignSpace.solver_depth += 1
                




class CombinationColoring:
    '''
    Dictionary of colors associated with different hole combinations.
    Note: color 0 is reserved for general hole-free objects.
    '''
    def __init__(self, holes):
        '''
        :param holes of the initial design space
        '''
        self.holes = holes
        self.coloring = {}
        self.reverse_coloring = {}

    @property
    def colors(self):
        return len(self.coloring)

    def get_or_make_color(self, hole_assignment):
        new_color = self.colors + 1
        color = self.coloring.get(hole_assignment, new_color)
        if color == new_color:
            self.coloring[hole_assignment] = color
            self.reverse_coloring[color] = hole_assignment
        return color

    def subcolors(self, subspace):
        ''' Collect colors that are valid within the provided design subspace. '''
        colors = set()
        for combination,color in self.coloring.items():
            contained = True
            for hole_index,hole in enumerate(subspace):
                if combination[hole_index] is None:
                    continue
                if combination[hole_index] not in hole.options:
                    contained = False
                    break
            if contained:
                colors.add(color)

        return colors

    def subcolors_proper(self, hole_index, options):
        colors = set()
        for combination,color in self.coloring.items():
            if combination[hole_index] in options:
                colors.add(color)
        return colors

    def get_hole_assignments(self, colors):
        ''' Collect all hole assignments associated with provided colors. '''
        hole_assignments = [set() for hole in self.holes]

        for color in colors:
            if color == 0:
                continue
            combination = self.reverse_coloring[color]
            for hole_index,assignment in enumerate(combination):
                if assignment is None:
                    continue
                hole_assignments[hole_index].add(assignment)
        hole_assignments = [list(assignments) for assignments in hole_assignments]

        return hole_assignments
