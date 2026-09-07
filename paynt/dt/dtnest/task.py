
from paynt.dt.task import DtTask

class DtNestTask(DtTask):

    def __init__(
        self, properties, error_threshold, tree_depth=7, initial_tree=None, timeout=600, use_exact=False,
        max_subtree_depth=7, **kwargs
    ):

        super().__init__(properties, tree_depth, timeout=timeout, use_exact=use_exact, **kwargs)
        self.error_threshold = error_threshold
        self.initial_tree = initial_tree
        self.max_subtree_depth = max_subtree_depth

    @classmethod
    def from_specification(
        cls, specification, tree_depth=7, timeout=None, use_exact=False,
        error_threshold=0.05, initial_tree=None, max_subtree_depth=7,
        **kwargs
    ):
        task = super().from_specification(specification, tree_depth=tree_depth, timeout=timeout, use_exact=use_exact, **kwargs)
        task.error_threshold = error_threshold
        task.initial_tree = initial_tree
        task.max_subtree_depth = max_subtree_depth
        return task
