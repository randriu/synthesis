"""The final result of a completed synthesis run for a SynthesisTask.

Feature-specific results subclass this to add their own fields -- e.g. paynt.dt.result.DtResult adds the synthesized tree.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import paynt.parameter_space.parameter_space


@dataclass
class Result:
    success: bool
    # the achieved optimum, or None if the specification has no optimality objective
    value: float | None = None
    # the winning parameter assignment, or None if none was found
    assignment: paynt.parameter_space.parameter_space.ParameterSpace | None = None
    # the choices of the underlying MDP the solution stands for, as a mask (a stormpy BitVector), or None if there is no assignment
    selected_choices: Any = None
