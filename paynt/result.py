'''
The final result of a completed synthesis run for a Task. Feature-specific results subclass this to add
their own fields -- e.g. paynt.dt.result.DtResult adds the synthesized tree.
'''


class Result:

    def __init__(self, success, value=None):
        self.success = success
        self.value = value
