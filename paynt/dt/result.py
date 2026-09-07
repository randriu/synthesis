import paynt.result

from .decision_tree import DecisionTree

import logging
logger = logging.getLogger(__name__)

class DtResult(paynt.result.Result):

    def __init__(self, success : bool, value : float | None, tree : DecisionTree | None):
        super().__init__(success, value)
        self.tree = tree
