from __future__ import annotations

from typing import Any

import paynt.task
import paynt.specification.property


class FamilyTask(paynt.task.Task):

    def __init__(self, properties: list[Any], memory_size: int = 1, **kwargs: Any):
        super().__init__(properties, **kwargs)
        # implicit initial size for scheduler-memory unfolding, consumed by FamilyColoredMdpFactory (and
        # PomdpFamilyColoredMdpFactory) at construction time
        self.memory_size = memory_size

    @classmethod
    def from_specification(  # type: ignore[override]
        cls, specification: paynt.specification.property.Specification, memory_size: int = 1, **kwargs: Any
    ) -> FamilyTask:
        task: FamilyTask = super().from_specification(specification, **kwargs)  # type: ignore[assignment]
        task.memory_size = memory_size
        return task
