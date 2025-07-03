import payntbind.synthesis

import paynt.family.smt

import math
import random
import itertools

import logging
logger = logging.getLogger(__name__)


class ParentInfo():
    '''
    Container for stuff to be remembered when splitting an undecided family into subfamilies. Generally used to
    speed-up work with the subfamilies.
    :note it is better to store these things in a separate container instead
        of having a reference to the parent family (that will never be considered again) for memory efficiency.
    '''
    def __init__(self):
        pass
        self.selected_choices = None
        self.constraint_indices = None
        self.refinement_depth = None


class Family:

    def __init__(self, other=None):
        if other is None:
            self.family = payntbind.synthesis.Family()
            self.hole_to_name = []
            self.hole_to_option_labels = []
        else:
            self.family = payntbind.synthesis.Family(other.family)
            self.hole_to_name = other.hole_to_name
            self.hole_to_option_labels = other.hole_to_option_labels

        self.parent_info = None
        self.refinement_depth = 0
        self.constraint_indices = None

        self.selected_choices = None
        self.mdp = None
        self.analysis_result = None
        self.encoding = None

    def add_parent_info(self, parent_info):
        self.parent_info = parent_info
        self.refinement_depth = parent_info.refinement_depth + 1
        self.constraint_indices = parent_info.constraint_indices

    @property
    def num_holes(self):
        return self.family.numHoles()

    def add_hole(self, name, option_labels):
        self.hole_to_name.append(name)
        self.hole_to_option_labels.append(option_labels)
        self.family.addHole(len(option_labels))

    def hole_name(self, hole):
        return self.hole_to_name[hole]

    def hole_options(self, hole):
        return self.family.holeOptions(hole)

    def hole_num_options(self, hole):
        return self.family.holeNumOptions(hole)

    def hole_num_options_total(self, hole):
        return self.family.holeNumOptionsTotal(hole)

    def hole_set_options(self, hole, options):
        self.family.holeSetOptions(hole,options)

    @property
    def size(self):
        return math.prod([self.family.holeNumOptions(hole) for hole in range(self.num_holes)])

    INT_PRINT_MAX_ORDER = 5

    @property
    def size_or_order(self):
        order = int(math.fsum([math.log10(self.family.holeNumOptions(hole)) for hole in range(self.num_holes)]))
        if order <= Family.INT_PRINT_MAX_ORDER:
            return self.size
        return f"1e{order}"

    def hole_options_to_string(self, hole, options):
        name = self.hole_name(hole)
        labels = [str(self.hole_to_option_labels[hole][option]) for option in options]
        if len(labels) == 1:
            return f"{name}={labels[0]}"
        else:
            return name + ": {" + ",".join(labels) + "}"

    def __str__(self):
        hole_strings = []
        for hole in range(self.num_holes):
            options = self.hole_options(hole)
            hole_str = self.hole_options_to_string(hole,options)
            hole_strings.append(hole_str)
        return ", ".join(hole_strings)

    def copy(self):
        return Family(self)

    def assume_hole_options_copy(self, hole, options):
        '''
        Create a copy and assume suboptions for a given hole.
        @note this does not check whether @options are actually suboptions of this hole.
        '''
        subfamily = self.copy()
        subfamily.hole_set_options(hole,options)
        return subfamily

    def assume_options_copy(self, hole_options):
        '''
        Create a copy and assume suboptions for each hole.
        @note this does not check whether suboptions are actually suboptions of any given hole.
        '''
        subfamily = self.copy()
        for hole,options in enumerate(hole_options):
            subfamily.hole_set_options(hole,options)
        return subfamily

    def split(self, splitter, suboptions):
        return [self.assume_hole_options_copy(splitter,options) for options in suboptions]

    def pick_any(self):
        hole_options = [[self.hole_options(hole)[0]] for hole in range(self.num_holes)]
        return self.assume_options_copy(hole_options)

    def pick_random(self):
        hole_options = [[random.choice(self.hole_options(hole))] for hole in range(self.num_holes)]
        return self.assume_options_copy(hole_options)

    def all_combinations(self):
        '''
        :returns iteratable Cartesian product of hole options
        '''
        all_options = []
        for hole in range(self.num_holes):
            options = self.hole_options(hole)
            all_options.append(options)
        return itertools.product(*all_options)

    def construct_assignment(self, combination):
        ''' Convert hole option combination to a hole assignment. '''
        combination = list(combination)
        suboptions = [[option] for option in combination]
        assignment = self.assume_options_copy(suboptions)
        return assignment

    def collect_parent_info(self, specification):
        pi = ParentInfo()
        pi.selected_choices = self.selected_choices
        pi.refinement_depth = self.refinement_depth
        cr = self.analysis_result.constraints_result
        pi.constraint_indices = cr.undecided_constraints if cr is not None else []
        return pi

    def encode(self, smt_solver):
        if self.encoding is None:
            self.encoding = paynt.family.smt.FamilyEncoding(smt_solver, self)
