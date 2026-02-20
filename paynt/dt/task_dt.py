

# TODO this will eventually inherit from general paynt_task Class


class TaskDT:

    def __init__(self, specification, tree_depth):

        self.pctl_task = specification
        self.tree_depth = tree_depth
        self.scheduler_to_map = None

    def set_scheduler_to_map(self, scheduler):
        self.scheduler_to_map = scheduler

    @property
    def has_scheduler_to_map(self):
        return self.scheduler_to_map is not None