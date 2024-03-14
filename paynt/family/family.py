import payntbind.synthesis

import paynt.family.smt

import math
import random
import itertools

import logging
logger = logging.getLogger(__name__)


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
        assert len(options)>0
        self.family.holeSetOptions(hole,options)
        assert self.family.holeNumOptions(hole) == len(options)

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
        labels = [self.hole_to_option_labels[hole][option] for option in options]
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

    def assume_options_copy(self, hole_options):
        ''' Create a copy and assume suboptions for each hole. '''
        holes_copy = self.copy()
        for hole,options in enumerate(hole_options):
            holes_copy.hole_set_options(hole,options)
        return holes_copy

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

    def subholes(self, hole_index, options):
        '''
        Construct a semi-shallow copy of self with only one modified hole
          @hole_index having selected @options
        :note this is a performance/memory optimization associated with creating
          subfamilies wrt one splitter having restricted options
        '''
        shallow_copy = self.copy()
        shallow_copy.hole_set_options(hole_index,options)
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
        self.constraint_indices = None
        # for each undecided property contains analysis results
        self.analysis_hints = None

        # how many refinements were needed to create this family
        self.refinement_depth = None

        # index of a hole used to split the family
        self.splitter = None


class DesignSpace(Family):
    '''
    List of holes supplied with
    - a list of constraint indices to investigate in this design space
    - (optionally) z3 encoding of this design space
    :note z3 (re-)encoding construction must be invoked manually
    '''

    # whether hints will be stored for subsequent MDP model checking
    store_hints = True
    
    def __init__(self, family = None, parent_info = None):
        super().__init__(family)

        self.mdp = None
        
        # SMT encoding
        self.encoding = None

        self.refinement_depth = 0
        self.constraint_indices = None

        self.analysis_result = None
        self.splitter = None
        self.parent_info = parent_info
        if parent_info is not None:
            self.refinement_depth = parent_info.refinement_depth + 1
            self.constraint_indices = parent_info.constraint_indices

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
        pi.refinement_depth = self.refinement_depth
        pi.analysis_hints = self.collect_analysis_hints(specification)
        cr = self.analysis_result.constraints_result
        pi.constraint_indices = cr.undecided_constraints if cr is not None else []
        pi.splitter = self.splitter
        pi.mdp = self.mdp
        return pi

    def encode(self, smt_solver):
        if self.encoding is None:
            self.encoding = paynt.family.smt.FamilyEncoding(smt_solver, self)
