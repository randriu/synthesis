'''
The final result of a completed synthesis run for a Task. Feature-specific results subclass this to add
their own fields -- e.g. paynt.dt.result.DtResult adds the synthesized tree.
'''


class Result:

    def __init__(self, success, value=None, assignment=None):
        self.success = success
        # the achieved optimum, or None if the specification has no optimality objective
        self.value = value
        # the winning parameter assignment, or None if none was found
        # (some feature results -- e.g. paynt.family.policy_tree_synthesizer's policy-tree result -- have no
        # single assignment/value at all, since they represent a set of region-specific policies rather than
        # one answer; those leave both fields None, which the caller should read as "not applicable", not
        # "not found")
        self.assignment = assignment
