
import paynt.verification.property

# TODO this will eventually inherit from general paynt_task Class


class DtTask:

    def __init__(self, properties, tree_depth):

        paynt.verification.property.Property.initialize(False)
        properties = [paynt.verification.property.construct_property(p, 0) for p in properties]
        specification = paynt.verification.property.Specification(properties)
    
        self.pctl_task = specification
        self.tree_depth = tree_depth
        self.scheduler_to_map = None

    def set_scheduler_to_map(self, scheduler):
        self.scheduler_to_map = scheduler

    @property
    def has_scheduler_to_map(self):
        return self.scheduler_to_map is not None