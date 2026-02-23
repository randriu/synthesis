

# TODO this will inherit from general result class eventually

from .decision_tree import DecisionTree

import logging
logger = logging.getLogger(__name__)

class DtResult:

    def __init__(self, success : bool, value : float | None, tree : DecisionTree | None):
        
        self.success = success
        self.value = value
        self.tree = tree