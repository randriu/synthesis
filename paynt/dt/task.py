from __future__ import annotations

from typing import Any

import paynt.task
import paynt.specification.property


class DtTask(paynt.task.Task):

    def __init__(
        self, properties : list[Any], tree_depth : int, timeout : int | None = 900, use_exact : bool = False,
        tree_enumeration : bool = False, scheduler_path : str | None = None, add_dont_care_action : bool = True,
        **kwargs : Any
    ):
        super().__init__(properties, timeout=timeout, use_exact=use_exact, **kwargs)
        self.tree_depth = tree_depth
        self.tree_enumeration = tree_enumeration
        # path to a JSON scheduler file to be mapped to a decision tree (CLI's --tree-map-scheduler)
        self.scheduler_path = scheduler_path
        # if true, an explicit action executing a random choice of an available action will be added to
        # each state (consumed by DtColoredMdpFactory at construction time)
        self.add_dont_care_action = add_dont_care_action
        # an already-in-memory scheduler to map (distinct from scheduler_path above, which is a file path
        # loaded by the CLI's own run loop) -- the library-facing entry point used by paynt.dt.api.get_synthesizer
        self.scheduler_to_map : Any = None

    def set_scheduler_to_map(self, scheduler : Any) -> None:
        self.scheduler_to_map = scheduler

    @property
    def has_scheduler_to_map(self) -> bool:
        return self.scheduler_to_map is not None

    @classmethod
    def from_specification(  # type: ignore[override]
        cls, specification : paynt.specification.property.Specification, tree_depth : int = 0, timeout : int | None = None,
        use_exact : bool = False, tree_enumeration : bool = False, scheduler_path : str | None = None,
        add_dont_care_action : bool = True, **kwargs : Any
    ) -> "DtTask":
        # super().from_specification uses cls.__new__(cls), so this is really a DtTask at runtime whenever
        # called as DtTask.from_specification(...) -- mypy only sees the base class's own declared return type
        task : DtTask = super().from_specification(specification, timeout=timeout, use_exact=use_exact, **kwargs)  # type: ignore[assignment]
        task.tree_depth = tree_depth
        task.tree_enumeration = tree_enumeration
        task.scheduler_path = scheduler_path
        task.add_dont_care_action = add_dont_care_action
        task.scheduler_to_map = None
        return task
