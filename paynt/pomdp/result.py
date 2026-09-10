from __future__ import annotations

from typing import Any

import paynt.result
import paynt.pomdp.fsc


class PomdpResult(paynt.result.Result):

    def __init__(self, success : bool, value : float | None = None, assignment : Any = None, fsc : paynt.pomdp.fsc.FscFactored | None = None):
        super().__init__(success, value, assignment)
        # the synthesized FSC (paynt.pomdp.fsc.FscFactored), or None if no assignment was found
        self.fsc = fsc
