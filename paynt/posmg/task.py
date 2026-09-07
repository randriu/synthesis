import paynt.task


class PosmgTask(paynt.task.Task):

    def __init__(self, properties, memory_size=1, **kwargs):
        super().__init__(properties, **kwargs)
        # implicit initial size for FSC memory unfolding, consumed by PosmgColoredMdpFactory at
        # construction time
        self.memory_size = memory_size

    @classmethod
    def from_specification(cls, specification, memory_size=1, **kwargs):
        task = super().from_specification(specification, **kwargs)
        task.memory_size = memory_size
        return task
