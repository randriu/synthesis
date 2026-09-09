import paynt.result


class PomdpResult(paynt.result.Result):

    def __init__(self, success, value=None, assignment=None, fsc=None):
        super().__init__(success, value, assignment)
        # the synthesized FSC (paynt.pomdp.fsc.FscFactored), or None if no assignment was found
        self.fsc = fsc
