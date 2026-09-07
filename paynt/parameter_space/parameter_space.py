import payntbind.synthesis

import paynt.parameter_space.smt

import math
import random
import itertools

import logging
logger = logging.getLogger(__name__)


class ParentInfo():
    '''
    Container for stuff to be remembered when splitting an undecided parameter space into subspaces. Generally
    used to speed-up work with the subspaces.
    :note it is better to store these things in a separate container instead
        of having a reference to the parent parameter space (that will never be considered again) for memory
        efficiency.
    '''
    def __init__(self):
        pass
        self.selected_choices = None
        self.constraint_indices = None
        self.refinement_depth = None


class ParameterSpace:

    def __init__(self, other=None):
        if other is None:
            self.native = payntbind.synthesis.Family()
            self.parameter_to_name = []
            self.parameter_to_option_labels = []
        else:
            self.native = payntbind.synthesis.Family(other.native)
            self.parameter_to_name = other.parameter_to_name
            self.parameter_to_option_labels = other.parameter_to_option_labels

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
    def num_parameters(self):
        return self.native.numHoles()

    def add_parameter(self, name, option_labels):
        self.parameter_to_name.append(name)
        self.parameter_to_option_labels.append(option_labels)
        self.native.addHole(len(option_labels))

    def parameter_name(self, parameter):
        return self.parameter_to_name[parameter]

    def parameter_options(self, parameter):
        return self.native.holeOptions(parameter)

    def parameter_num_options(self, parameter):
        return self.native.holeNumOptions(parameter)

    def parameter_num_options_total(self, parameter):
        return self.native.holeNumOptionsTotal(parameter)

    def parameter_set_options(self, parameter, options):
        self.native.holeSetOptions(parameter,options)

    @property
    def size(self):
        return math.prod([self.native.holeNumOptions(parameter) for parameter in range(self.num_parameters)])

    INT_PRINT_MAX_ORDER = 5

    @property
    def size_or_order(self):
        order = int(math.fsum([math.log10(self.native.holeNumOptions(parameter)) for parameter in range(self.num_parameters)]))
        if order <= ParameterSpace.INT_PRINT_MAX_ORDER:
            return self.size
        return f"1e{order}"

    def parameter_options_to_string(self, parameter, options):
        name = self.parameter_name(parameter)
        labels = [str(self.parameter_to_option_labels[parameter][option]) for option in options]
        if len(labels) == 1:
            return f"{name}={labels[0]}"
        else:
            return name + ": {" + ",".join(labels) + "}"

    def __str__(self):
        parameter_strings = []
        for parameter in range(self.num_parameters):
            options = self.parameter_options(parameter)
            parameter_str = self.parameter_options_to_string(parameter,options)
            parameter_strings.append(parameter_str)
        return ", ".join(parameter_strings)

    def copy(self):
        return ParameterSpace(self)

    def assume_parameter_options_copy(self, parameter, options):
        '''
        Create a copy and assume suboptions for a given parameter.
        @note this does not check whether @options are actually suboptions of this parameter.
        '''
        parameter_subspace = self.copy()
        parameter_subspace.parameter_set_options(parameter,options)
        return parameter_subspace

    def assume_options_copy(self, parameter_options):
        '''
        Create a copy and assume suboptions for each parameter.
        @note this does not check whether suboptions are actually suboptions of any given parameter.
        '''
        parameter_subspace = self.copy()
        for parameter,options in enumerate(parameter_options):
            parameter_subspace.parameter_set_options(parameter,options)
        return parameter_subspace

    def split(self, splitter, suboptions):
        return [self.assume_parameter_options_copy(splitter,options) for options in suboptions]

    def suboptions_half(self, splitter):
        ''' Split options of a splitter into two halves. '''
        options = self.parameter_options(splitter)
        half = len(options) // 2
        suboptions = [options[:half], options[half:]]
        return suboptions

    def suboptions_unique(self, splitter, used_options):
        ''' Distribute used options of a splitter into different suboptions. '''
        assert len(used_options) > 1
        suboptions = [[option] for option in used_options]
        index = 0
        for option in self.parameter_options(splitter):
            if option in used_options:
                continue
            suboptions[index].append(option)
            index = (index + 1) % len(suboptions)
        return suboptions

    def suboptions_enumerate(self, splitter, used_options):
        assert len(used_options) > 1
        core_suboptions = [[option] for option in used_options]
        other_suboptions = [option for option in self.parameter_options(splitter) if option not in used_options]
        return core_suboptions, other_suboptions

    def pick_any(self):
        parameter_options = [[self.parameter_options(parameter)[0]] for parameter in range(self.num_parameters)]
        return self.assume_options_copy(parameter_options)

    def pick_random(self):
        parameter_options = [[random.choice(self.parameter_options(parameter))] for parameter in range(self.num_parameters)]
        return self.assume_options_copy(parameter_options)

    def all_combinations(self):
        '''
        :returns iteratable Cartesian product of parameter options
        '''
        all_options = []
        for parameter in range(self.num_parameters):
            options = self.parameter_options(parameter)
            all_options.append(options)
        return itertools.product(*all_options)

    def construct_assignment(self, combination):
        ''' Convert parameter option combination to a parameter assignment. '''
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
            self.encoding = paynt.parameter_space.smt.ParameterSpaceEncoding(smt_solver, self)
