import math
import itertools
import z3

from collections import defaultdict, OrderedDict

import logging
logger = logging.getLogger(__name__)


class HoleOptions(OrderedDict):
    ''' Mapping of hole names to hole options. '''

    # TODO maybe make hole options as a list of indices?
    
    def __init__(self, *args):
        super().__init__(*args)

    @property
    def holes(self):
        return list(self.keys())

    @property
    def hole_count(self):
        return len(self.holes)

    @property
    def size(self):
        return math.prod([len(v) for v in self.values()])

    def all_hole_combinations(self):
        return itertools.product(*self.values())

    def __str__(self):
        hole_options = []
        for hole,options in self.items():
            if len(options) > 1:
                options = "{" + ",".join([str(o) for o in options]) + "}"
                hole_options.append("{}: {}".format(hole,options))
            else:
                hole_options.append("{}={}".format(hole,options[0]))
        return ", ".join(hole_options)

    def __repr__(self):
        return self.__str__()

    def pick_any(self):
        assignment = HoleOptions()
        for hole in self.holes:
            assignment[hole] = [self[hole][0]]
        return assignment

    def index_map(self, subspace):
        '''
        Map options of a supplied subspace to indices of the corresponding
        options in this design space.
        '''
        result = OrderedDict()
        for hole,values in subspace.items():
            result[hole] = []
            for v in values:
                for index, ref in enumerate(self[hole]):
                    if ref == v:
                        result[hole].append(index)
        return result
    

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
    hole_indices = None
    # mapping of hole options to their indices for each hole
    hole_option_indices = None

    def __init__(self, hole_options, properties = None):
        super().__init__(hole_options)   
        self.properties = properties
        self.encoding = None

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
    def __init__(self, hole_options):
        # these are hole options of the initial design space
        self.hole_options = hole_options

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
        indexed_subspace = self.hole_options.index_map(subspace)
        colors = set()
        for combination,color in self.coloring.items():
            contained = True
            for hole, assignment in zip(indexed_subspace.keys(), combination):
                if assignment is None:
                    continue
                if assignment not in indexed_subspace[hole]:
                    contained = False
                    break
            if contained:
                colors.add(color)

        return colors

    def get_hole_assignments(self, colors):
        ''' Collect all hole assignments associated with provided colors. '''
        hole_assignments = {}
        for color in colors:
            if color == 0:
                continue
            combination = self.reverse_coloring[color]
            for hole, assignment in zip(self.hole_options.holes, combination):
                if assignment is None:
                    continue
                assignments = hole_assignments.get(hole, set())
                assignments.add(assignment)
                hole_assignments[hole] = assignments
        return hole_assignments
