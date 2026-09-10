from __future__ import annotations

from typing import Any

import paynt.task
import paynt.specification.property


class PomdpTask(paynt.task.Task):

    def __init__(self, properties : list[Any], memory_size : int = 1, posterior_aware : bool = False, **kwargs : Any):
        super().__init__(properties, **kwargs)
        # implicit initial size for FSC memory unfolding, consumed by PomdpColoredMdpFactory/
        # DecPomdpColoredMdpFactory at construction time
        self.memory_size = memory_size
        # if True, posterior-aware unfolding is applied (POMDP only, ignored by Dec-POMDP)
        self.posterior_aware = posterior_aware

    @classmethod
    def from_specification(  # type: ignore[override]
        cls, specification : paynt.specification.property.Specification, memory_size : int = 1, posterior_aware : bool = False, **kwargs : Any
    ) -> "PomdpTask":
        # see DtTask.from_specification's comment: super().from_specification uses cls.__new__(cls), so this
        # is really a PomdpTask at runtime whenever called as PomdpTask.from_specification(...)
        task : PomdpTask = super().from_specification(specification, **kwargs)  # type: ignore[assignment]
        task.memory_size = memory_size
        task.posterior_aware = posterior_aware
        return task
