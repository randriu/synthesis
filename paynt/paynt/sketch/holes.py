import math
import itertools
import z3

from collections import defaultdict, OrderedDict

import logging
logger = logging.getLogger(__name__)


class Hole:
    '''
    Options for each hole are simply indices of the corresponding actions.
    Each hole can optionally contain a list of corresponding program expressions.

    '''
    def __init__(self, name, options, option_labels, expressions = None):
        self.options = options
        self.name = name
        self.option_labels = option_labels
        self.expressions = expressions

    @property
    def size(self):
        return len(self.options)

    def __str__(self):
        if self.size == 1:
            return"{}={}".format(self.name,self.option_labels[0]) 
        else:
            return self.name + ": {" + ",".join(self.option_labels) + "}"

    def copy(self):
        return Hole(self.name, self.options.copy(), self.option_labels.copy())

    def subhole(self, suboptions):
        hole = Hole(self.name, [], [])
        for index,option in enumerate(self.options):
            if option in suboptions:
                hole.options.append(option)
                hole.option_labels.append(self.option_labels[index])
        return hole

    def pick_any(self):
        return self.subhole([self.options[0]])



    

class HoleOptions(list):
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
        return math.prod([hole.size for hole in self])

    def copy(self):
        hole_options = HoleOptions()
        for hole in self:
            hole_options.append(hole.copy())
        return hole_options

    # def all_hole_combinations(self):
        # return itertools.product(*self.values())

    def __str__(self):
        return ", ".join([str(hole) for hole in self]) 

    def __repr__(self):
        return self.__str__()

    def assume_suboptions(self, hole_index, suboptions):
        result = self.copy()
        result[hole_index] = self[hole_index].subhole(suboptions)
        return result

    def pick_any(self):
        assignment = HoleOptions()
        for hole in self:
            assignment.append(hole.pick_any())
        return assignment

class DesignSpace(HoleOptions):
    '''
    Hole options supplied with
    - a list of constraints to investigate in this design space
    - (optionally) z3 encoding
    '''

    # z3 solver
    solver = None
    # mapping of z3 variables to hole names
    solver_var_to_hole = None

    # mapping of holes to their indices
    # hole_indices = None
    # mapping of hole options to their indices for each hole
    hole_option_indices = None

    def __init__(self, hole_options, properties = None):
        super().__init__(hole_options)
        self.properties = properties
        self.encoding = None

    def copy(self):
        return DesignSpace(super().copy())

    def set_properties(self, properties):
        self.properties = properties

    def z3_initialize(self):
        ''' Use this design space as a baseline for future refinements. '''
        DesignSpace.solver = z3.Solver()
        DesignSpace.solver_var_to_hole = OrderedDict()
        for hole, options in self.items():
            var = z3.Int(hole)
            DesignSpace.solver.add(var >= 0)
            DesignSpace.solver.add(var < len(options))
            DesignSpace.solver_var_to_hole[var] = hole

        # map holes to their indices and hole options to their indices
        DesignSpace.hole_indices = {hole:index for index,hole in enumerate(self.holes)}
        DesignSpace.hole_option_indices = {}
        for hole, options in self.items():
            indices = {option:index for index,option in enumerate(options)}
            DesignSpace.hole_option_indices[hole] = indices

    def z3_encode(self):
        ''' Encode this design space. '''
        hole_clauses = dict()
        for var, hole in DesignSpace.solver_var_to_hole.items():
            hole_clauses[hole] = z3.Or(
                [var == DesignSpace.hole_option_indices[hole][option] for option in self[hole]]
            )
        self.encoding = z3.And(list(hole_clauses.values()))

    def pick_assignment(self):
        '''
        Pick any (feasible) hole assignment.
        :return None if no instance remains
        '''
        # get satisfiable assignment within this design space
        solver_result = DesignSpace.solver.check(self.encoding)
        if solver_result != z3.sat:
            # no further instances
            return None

        # construct the corresponding singleton (a single-member family)
        sat_model = DesignSpace.solver.model()
        assignment = HoleOptions()
        for var, hole in DesignSpace.solver_var_to_hole.items():
            assignment[hole] = [self[hole][sat_model[var].as_long()]]
        return assignment

    def exclude_assignment(self, assignment, conflict):
        '''
        Exclude assignment from all design spaces using provided conflict.
        :param assignment hole option that yielded DTMC of interest
        :param indices of relevant holes in the counterexample
        '''
        # FIXME
        counterexample_clauses = dict()
        for var, hole in DesignSpace.solver_var_to_hole.items():
            if DesignSpace.hole_indices[hole] in conflict:
                option_index = DesignSpace.hole_option_indices[hole][assignment[hole][0]]
                counterexample_clauses[hole] = (var == option_index)
            else:
                all_options = [var == DesignSpace.hole_option_indices[hole][option] for option in self[hole]]
                counterexample_clauses[hole] = z3.Or(all_options)
        counterexample_encoding = z3.Not(z3.And(list(counterexample_clauses.values())))
        DesignSpace.solver.add(counterexample_encoding)


class CombinationColoring:
    '''
    Dictionary of colors associated with different hole combinations.
    Note: color 0 is reserved for general hole-free objects.
    '''
    def __init__(self, holes):
        # these are hole options of the initial design space
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

    def get_hole_assignments(self, colors):
        ''' Collect all hole assignments associated with provided colors. '''
        hole_assignments = {}
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
