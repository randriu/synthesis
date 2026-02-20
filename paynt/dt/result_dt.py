

# TODO this will inherit from general result class eventually


class ResultDT:

    def __init__(self, success, value, tree):
        
        self.success = success
        self.value = value
        self.tree = tree