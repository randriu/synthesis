import paynt.task


class DtTask(paynt.task.Task):

    def __init__(
        self, properties, tree_depth, timeout=900, use_exact=False,
        tree_enumeration=False, scheduler_path=None, add_dont_care_action=True,
        **kwargs
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
        self.scheduler_to_map = None

    def set_scheduler_to_map(self, scheduler):
        self.scheduler_to_map = scheduler

    @property
    def has_scheduler_to_map(self):
        return self.scheduler_to_map is not None

    @classmethod
    def from_specification(
        cls, specification, tree_depth=0, timeout=None, use_exact=False,
        tree_enumeration=False, scheduler_path=None, add_dont_care_action=True,
        **kwargs
    ):
        task = super().from_specification(specification, timeout=timeout, use_exact=use_exact, **kwargs)
        task.tree_depth = tree_depth
        task.tree_enumeration = tree_enumeration
        task.scheduler_path = scheduler_path
        task.add_dont_care_action = add_dont_care_action
        task.scheduler_to_map = None
        return task
