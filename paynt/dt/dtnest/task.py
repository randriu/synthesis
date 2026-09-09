from __future__ import annotations

from typing import Any

import paynt.specification.property
from paynt.dt.task import DtTask

class DtNestTask(DtTask):

    def __init__(
        self, properties : list[Any], error_threshold : float, tree_depth : int = 7, initial_tree : Any = None,
        timeout : int | None = 600, use_exact : bool = False, max_subtree_depth : int = 7, **kwargs : Any
    ):

        super().__init__(properties, tree_depth, timeout=timeout, use_exact=use_exact, **kwargs)
        self.error_threshold = error_threshold
        self.initial_tree = initial_tree
        self.max_subtree_depth = max_subtree_depth

    @classmethod
    def from_specification(  # type: ignore[override]
        cls, specification : paynt.specification.property.Specification, tree_depth : int = 7, timeout : int | None = None,
        use_exact : bool = False, error_threshold : float = 0.05, initial_tree : Any = None, max_subtree_depth : int = 7,
        **kwargs : Any
    ) -> "DtNestTask":
        # see DtTask.from_specification's comment: super().from_specification uses cls.__new__(cls), so this
        # is really a DtNestTask at runtime whenever called as DtNestTask.from_specification(...)
        task : DtNestTask = super().from_specification(  # type: ignore[assignment]
            specification, tree_depth=tree_depth, timeout=timeout, use_exact=use_exact, **kwargs)
        task.error_threshold = error_threshold
        task.initial_tree = initial_tree
        task.max_subtree_depth = max_subtree_depth
        return task
