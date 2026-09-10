from __future__ import annotations

from collections.abc import Iterable, Iterator

import payntbind.synthesis

import math
import random
import itertools

import logging

logger = logging.getLogger(__name__)


class ParameterSpace:
    """
    A pure value: the parameter-domain data (V of the colored MDP C = (M, V, kappa)) -- which parameters
    exist, their names/option labels, and (via native) which options are currently assumed for each. Carries
    no notion of search progress or lifetime -- that lives on paynt.synthesizer.search_node.SearchNode, which
    wraps a ParameterSpace alongside a built MDP, model-checking results, and other search-time bookkeeping.
    """

    def __init__(self, other: ParameterSpace | None = None):
        if other is None:
            self.native = payntbind.synthesis.Family()
            self.parameter_to_name: list[str] = []
            self.parameter_to_option_labels: list[list] = []
        else:
            self.native = payntbind.synthesis.Family(other.native)
            self.parameter_to_name = other.parameter_to_name
            self.parameter_to_option_labels = other.parameter_to_option_labels

    @property
    def num_parameters(self) -> int:
        return self.native.numHoles()

    def add_parameter(self, name: str, option_labels: list) -> None:
        self.parameter_to_name.append(name)
        self.parameter_to_option_labels.append(option_labels)
        self.native.addHole(len(option_labels))

    def parameter_name(self, parameter: int) -> str:
        return self.parameter_to_name[parameter]

    def parameter_options(self, parameter: int) -> list[int]:
        return self.native.holeOptions(parameter)

    def parameter_num_options(self, parameter: int) -> int:
        return self.native.holeNumOptions(parameter)

    def parameter_num_options_total(self, parameter: int) -> int:
        return self.native.holeNumOptionsTotal(parameter)

    def parameter_set_options(self, parameter: int, options: list[int]) -> None:
        self.native.holeSetOptions(parameter, options)

    @property
    def size(self) -> int:
        return math.prod([self.native.holeNumOptions(parameter) for parameter in range(self.num_parameters)])

    INT_PRINT_MAX_ORDER = 5

    @property
    def size_or_order(self) -> int | str:
        order = int(math.fsum([math.log10(self.native.holeNumOptions(parameter)) for parameter in range(self.num_parameters)]))
        if order <= ParameterSpace.INT_PRINT_MAX_ORDER:
            return self.size
        return f"1e{order}"

    def parameter_options_to_string(self, parameter: int, options: list[int]) -> str:
        name = self.parameter_name(parameter)
        labels = [str(self.parameter_to_option_labels[parameter][option]) for option in options]
        if len(labels) == 1:
            return f"{name}={labels[0]}"
        return name + ": {" + ",".join(labels) + "}"

    def __str__(self) -> str:
        parameter_strings = []
        for parameter in range(self.num_parameters):
            options = self.parameter_options(parameter)
            parameter_str = self.parameter_options_to_string(parameter, options)
            parameter_strings.append(parameter_str)
        return ", ".join(parameter_strings)

    def copy(self) -> ParameterSpace:
        return ParameterSpace(self)

    def assume_parameter_options_copy(self, parameter: int, options: list[int]) -> ParameterSpace:
        """
        Create a copy and assume suboptions for a given parameter.
        @note this does not check whether @options are actually suboptions of this parameter.
        """
        parameter_subspace = self.copy()
        parameter_subspace.parameter_set_options(parameter, options)
        return parameter_subspace

    def assume_options_copy(self, parameter_options: list[list[int]]) -> ParameterSpace:
        """
        Create a copy and assume suboptions for each parameter.
        @note this does not check whether suboptions are actually suboptions of any given parameter.
        """
        parameter_subspace = self.copy()
        for parameter, options in enumerate(parameter_options):
            parameter_subspace.parameter_set_options(parameter, options)
        return parameter_subspace

    def split(self, splitter: int, suboptions: list[list[int]]) -> list[ParameterSpace]:
        return [self.assume_parameter_options_copy(splitter, options) for options in suboptions]

    def suboptions_half(self, splitter: int) -> list[list[int]]:
        """Split options of a splitter into two halves."""
        options = self.parameter_options(splitter)
        half = len(options) // 2
        return [options[:half], options[half:]]

    def suboptions_unique(self, splitter: int, used_options: list[int]) -> list[list[int]]:
        """Distribute used options of a splitter into different suboptions."""
        assert len(used_options) > 1
        suboptions = [[option] for option in used_options]
        index = 0
        for option in self.parameter_options(splitter):
            if option in used_options:
                continue
            suboptions[index].append(option)
            index = (index + 1) % len(suboptions)
        return suboptions

    def suboptions_enumerate(self, splitter: int, used_options: list[int]) -> tuple[list[list[int]], list[int]]:
        assert len(used_options) > 1
        core_suboptions = [[option] for option in used_options]
        other_suboptions = [option for option in self.parameter_options(splitter) if option not in used_options]
        return core_suboptions, other_suboptions

    def pick_any(self) -> ParameterSpace:
        parameter_options = [[self.parameter_options(parameter)[0]] for parameter in range(self.num_parameters)]
        return self.assume_options_copy(parameter_options)

    def pick_random(self) -> ParameterSpace:
        parameter_options = [[random.choice(self.parameter_options(parameter))] for parameter in range(self.num_parameters)]
        return self.assume_options_copy(parameter_options)

    def all_combinations(self) -> Iterator[tuple[int, ...]]:
        """
        :returns iteratable Cartesian product of parameter options
        """
        all_options = []
        for parameter in range(self.num_parameters):
            options = self.parameter_options(parameter)
            all_options.append(options)
        return itertools.product(*all_options)

    def construct_assignment(self, combination: Iterable[int]) -> ParameterSpace:
        """Convert parameter option combination to a parameter assignment."""
        combination = list(combination)
        suboptions = [[option] for option in combination]
        return self.assume_options_copy(suboptions)
