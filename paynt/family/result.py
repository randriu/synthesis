import paynt.result


class PolicyTreeResult(paynt.result.Result):

    def __init__(self, success, policy_tree=None):
        # value/assignment are always None here: a policy tree is a set of region-specific policies covering
        # the whole family, not a single answer the way a normal synthesizer result is -- see
        # paynt.result.Result's own docstring for this convention. A future family-wide synthesizer
        # (searching for one policy that works across every family member) would return a plain Result
        # with a real value/assignment instead, once built.
        super().__init__(success, value=None, assignment=None)
        self.policy_tree = policy_tree
