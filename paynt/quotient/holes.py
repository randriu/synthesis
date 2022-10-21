import stormpy.synthesis

from .smt import FamilyEncoding

import math
import itertools

import logging
logger = logging.getLogger(__name__)

class Hole:
    '''
    Hole with a name, a list of options and corresponding option labels.
    Options for each hole are simply indices of the corresponding hole
      assignment, therefore, their order does not matter.
      # TODO maybe store options as bitmaps?
    Each hole is identified by its position hole_index in Holes, therefore,
      this order must be preserved in the refining process.
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

    @property
    def is_trivial(self):
        return self.size == 1

    @property
    def is_unrefined(self):
        return self.size == len(self.option_labels)

    def __str__(self):
        labels = [self.option_labels[option] for option in self.options]
        if self.size == 1:
            return"{}={}".format(self.name,labels[0]) 
        else:
            return self.name + ": {" + ",".join(labels) + "}"

    def assume_options(self, options):
        assert len(options) > 0
        self.options = options

    def copy(self):
        # note that the copy is shallow since after assuming some options
        # the corresponding list is replaced
        return Hole(self.name, self.options, self.option_labels)



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
        ''' Create a shallow copy of this list of holes. '''
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
        '''
        :return iteratable Cartesian product of hole options
        '''
        return itertools.product(*[hole.options for hole in self])

    def construct_assignment(self, combination):
        ''' Convert hole option combination to a hole assignment. '''
        combination = list(combination)
        suboptions = [[option] for option in combination]
        holes = self.copy()
        holes.assume_options(suboptions)
        return holes

    def subholes(self, hole_index, options):
        '''
        Construct a semi-shallow copy of self with only one modified hole
          @hole_index having selected @options
        :note this is a performance/memory optimization associated with creating
          subfamilies wrt one splitter having restricted options
        '''
        subhole = self[hole_index].copy()
        subhole.assume_options(options)
        
        shallow_copy = Holes(self)
        shallow_copy[hole_index] = subhole
        return shallow_copy


class ParentInfo():
    '''
    Container for stuff to be remembered when splitting an undecided family
    into subfamilies. Generally used to speed-up work with the subfamilies.
    :note it is better to store these things in a separate container instead
      of having a reference to the parent family (that will never be considered
      again) for the purposes of memory efficiency.
    '''
    def __init__(self):
        # list of constraint indices still undecided in this family
        self.property_indices = None
        # for each undecided property contains analysis results
        self.analysis_hints = None

        # how many refinements were needed to create this family
        self.refinement_depth = None

        # explicit list of all non-default actions in the MDP
        self.selected_actions = None
        # for each hole and for each option explicit list of all non-default actions in the MDP
        self.hole_selected_actions = None
        # index of a hole used to split the family
        self.splitter = None


class DesignSpace(Holes):
    '''
    List of holes supplied with
    - a list of constraint indices to investigate in this design space
    - (optionally) z3 encoding of this design space
    :note z3 (re-)encoding construction must be invoked manually
    '''

    # whether hints will be stored for subsequent MDP model checking
    store_hints = True
    
    def __init__(self, holes = [], parent_info = None):
        super().__init__(holes)

        self.mdp = None
        
        # SMT encoding
        self.encoding = None

        self.hole_selected_actions = None
        self.selected_actions = None
        self.refinement_depth = 0
        self.property_indices = None

        self.analysis_result = None
        self.splitter = None
        self.parent_info = parent_info
        if parent_info is not None:
            self.refinement_depth = parent_info.refinement_depth + 1
            self.property_indices = parent_info.property_indices

    def copy(self):
        return DesignSpace(super().copy())

    
    def generalize_hint(self, hint):
        hint_global = dict()
        hint = list(hint.get_values())
        for state in range(self.mdp.states):
            hint_global[self.mdp.quotient_state_map[state]] = hint[state]
        return hint_global

    
    def generalize_hints(self, result):
        hint_prim = self.generalize_hint(result.primary.result)
        hint_seco = self.generalize_hint(result.secondary.result) if result.secondary is not None else None
        return (hint_prim, hint_seco)

    
    def collect_analysis_hints(self, specification):
        res = self.analysis_result
        analysis_hints = dict()
        for index in res.constraints_result.undecided_constraints:
            prop = specification.constraints[index]
            hints = self.generalize_hints(res.constraints_result.results[index])
            analysis_hints[prop] = hints
        if res.optimality_result is not None:
            prop = specification.optimality
            hints = self.generalize_hints(res.optimality_result)
            analysis_hints[prop] = hints
        return analysis_hints

    
    def translate_analysis_hint(self, hint):
        if hint is None:
            return None
        translated_hint = [0] * self.mdp.states
        for state in range(self.mdp.states):
            global_state = self.mdp.quotient_state_map[state]
            translated_hint[state] = hint[global_state]
        return translated_hint

    
    def translate_analysis_hints(self):
        if not DesignSpace.store_hints or self.parent_info is None:
            return None

        analysis_hints = dict()
        for prop,hints in self.parent_info.analysis_hints.items():
            hint_prim,hint_seco = hints
            translated_hint_prim = self.translate_analysis_hint(hint_prim)
            translated_hint_seco = self.translate_analysis_hint(hint_seco)
            analysis_hints[prop] = (translated_hint_prim,translated_hint_seco)

        return analysis_hints

    def collect_parent_info(self, specification):
        pi = ParentInfo()
        pi.hole_selected_actions = self.hole_selected_actions
        pi.selected_actions = self.selected_actions
        pi.refinement_depth = self.refinement_depth
        pi.analysis_hints = self.collect_analysis_hints(specification)
        cr = self.analysis_result.constraints_result
        pi.property_indices = cr.undecided_constraints if cr is not None else []
        pi.splitter = self.splitter
        pi.mdp = self.mdp
        return pi

    def encode(self, smt_solver):
        if self.encoding is None:
            self.encoding = FamilyEncoding(smt_solver, self)




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
