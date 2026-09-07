import paynt.task


class PomdpTask(paynt.task.Task):

    def __init__(self, properties, memory_size=1, posterior_aware=False, **kwargs):
        super().__init__(properties, **kwargs)
        # implicit initial size for FSC memory unfolding, consumed by PomdpColoredMdpFactory/
        # DecPomdpColoredMdpFactory at construction time
        self.memory_size = memory_size
        # if True, posterior-aware unfolding is applied (POMDP only, ignored by Dec-POMDP)
        self.posterior_aware = posterior_aware

    @classmethod
    def from_specification(cls, specification, memory_size=1, posterior_aware=False, **kwargs):
        task = super().from_specification(specification, **kwargs)
        task.memory_size = memory_size
        task.posterior_aware = posterior_aware
        return task
