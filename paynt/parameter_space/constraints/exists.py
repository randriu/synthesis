"""ExistsConstraint: the plain existential case -- every parameter within its currently-allowed options, and (for SMPMC) a solution must be viable."""

from __future__ import annotations

from typing import Any

from paynt.parameter_space.constraints.constraint import Constraint, ConstraintContext


class ExistsConstraint(Constraint):
    name = "exists"

    def build(self, ctx: ConstraintContext) -> list[Any]:
        return ctx.base_clauses()
