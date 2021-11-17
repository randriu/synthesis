import math
import itertools
import z3

from collections import defaultdict, OrderedDict

import logging
logger = logging.getLogger(__name__)


class Hole:
    '''
    Hole with a name, a list of options and corresponding option labels.
    Options for each hole are simply indices of the corresponding actions.
    Each hole is identified by its position in HoleOptions, so this order must
    be preserved in the refining process.

    '''
    def __init__(self, name, options, option_labels):
        self.name = name
        self.options = options
        self.option_labels = option_labels

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

    def __str__(self):
        return ", ".join([str(hole) for hole in self]) 

    def __repr__(self):
        return self.__str__()

    def copy(self):
        hole_options = HoleOptions()
        for hole in self:
            hole_options.append(hole.copy())
        return hole_options

    # def all_hole_combinations(self):
        # return itertools.product(*self.values())

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
    # solver variables that respect the hole order
    solver_vars = None

    def __init__(self, hole_options, properties = None):
        super().__init__(hole_options)
        self.properties = properties
        self.encoding = None

    def set_properties(self, properties):
        self.properties = properties

    def copy(self):
        design_space = DesignSpace(super().copy())
        design_space.set_properties(self.properties.copy())
        return design_space

    def z3_initialize(self):
        ''' Use this design space as a baseline for future refinements. '''
        DesignSpace.solver = z3.Solver()
        DesignSpace.solver_vars = []
        for hole_index, hole in enumerate(self):
            var = z3.Int(hole_index)
            DesignSpace.solver.add(var >= 0)
            DesignSpace.solver.add(var < hole.size)
            DesignSpace.solver_vars.append(var)

    def z3_encode(self):
        ''' Encode this design space. '''
        hole_clauses = dict()
        for hole_index,var in enumerate(DesignSpace.solver_vars):
            hole_clauses[hole_index] = z3.Or(
                [var == option for option in self[hole_index].options]
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

        # construct the corresponding singleton
        sat_model = DesignSpace.solver.model()
        assignment = HoleOptions()
        for hole_index,var, in enumerate(DesignSpace.solver_vars):
            hole = self[hole_index]
            option = sat_model[var].as_long()
            assignment.append(hole.subhole([option]))
        return assignment

    def exclude_assignment(self, assignment, conflict):
        '''
        Exclude assignment from the design space using provided conflict.
        :param assignment hole option that yielded unsatisfiable DTMC
        :param indices of relevant holes in the corresponding counterexample
        '''
        counterexample_clauses = dict()
        for hole_index,var in enumerate(DesignSpace.solver_vars):
            if hole_index in conflict:
                counterexample_clauses[hole_index] = (var == assignment[hole_index].options[0])
            else:
                all_options = [var == option for option in self[hole_index].options]
                counterexample_clauses[hole_index] = z3.Or(all_options)
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
