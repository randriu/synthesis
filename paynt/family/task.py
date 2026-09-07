import paynt.task


class FamilyTask(paynt.task.Task):

    def __init__(self, properties, memory_size=1, **kwargs):
        super().__init__(properties, **kwargs)
        # implicit initial size for scheduler-memory unfolding, consumed by FamilyColoredMdpFactory (and
        # PomdpFamilyColoredMdpFactory) at construction time
        self.memory_size = memory_size

    @classmethod
    def from_specification(cls, specification, memory_size=1, **kwargs):
        task = super().from_specification(specification, **kwargs)
        task.memory_size = memory_size
        return task
