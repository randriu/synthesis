from __future__ import annotations

from typing import Any

import stormpy

from paynt.specification.property import *


class PropertyResult:
    def __init__(self, prop : Property, result : Any, value : Any):
        self.result = result
        self.value = value
        self.sat = prop.satisfies_threshold(value)
        self.improves_optimum : bool | None = None if not isinstance(prop,OptimalityProperty) else prop.improves_optimum(value)

    def __str__(self) -> str:
        return str(self.value)


class ConstraintsResult:
    '''
    A list of constraint results.
    Note: some results might be None (not evaluated).
    '''
    def __init__(self, results : list["PropertyResult | None"]):
        self.results = results
        self.undecided_constraints = [i for i,result in enumerate(results) if result is not None and result.sat is None]

        result_sats = [result.sat for result in results if result is not None]
        if False in result_sats:
            self.sat : bool | None = False
        elif None in result_sats:
            self.sat = None
        else:
            self.sat = True


    def __str__(self) -> str:
        return ",".join([str(result) for result in self.results])


class SpecificationResult:
    def __init__(self):
        self.constraints_result : ConstraintsResult | None = None
        # PropertyResult for a plain specification, MdpOptimalityResult for an MdpSpecificationResult -- kept
        # as Any rather than a Union since the two concrete flows never mix on the same instance
        self.optimality_result : Any = None

    def __str__(self) -> str:
        return str(self.constraints_result) + " : " + str(self.optimality_result)

    def accepting_dtmc(self, specification : Specification) -> tuple[bool, Any | None]:
        """
        :return (1) whether specification is satisfied (dtmc is accepting)
        :return (2) new optimal value associated with the accepting dtmc
            (can be None if no optimality)
        """

        assert self.constraints_result is not None
        if not self.constraints_result.sat:
            # constraints not sat
            return False, None

        if self.optimality_result is None:
            # constraints sat and no optimality
            return True, None
        
        if not self.optimality_result.improves_optimum:
            # constraints sat and optimality not sat
            return False, None
        
        # constraints sat and optimality sat
        return True, self.optimality_result.value


    def undecided_result(self) -> Any:
        if self.optimality_result is not None and self.optimality_result.can_improve:
            return self.optimality_result
        assert self.constraints_result is not None
        return self.constraints_result.results[self.constraints_result.undecided_constraints[0]]



class MdpPropertyResult:
    def __init__(self, prop : Property):
        self.prop = prop
        self.primary : Any = None
        self.secondary : Any = None
        self.sat : bool | None = None
        self.primary_selection : list[list[int]] | None = None

    @property
    def minimizing(self) -> bool:
        return self.prop.minimizing

    def __str__(self) -> str:
        prim = str(self.primary)
        seco = str(self.secondary)
        if self.minimizing:
            return "{} - {}".format(prim,seco)
        else:
            return "{} - {}".format(seco,prim)



class MdpOptimalityResult(MdpPropertyResult):
    def __init__(self, prop : Property):
        super().__init__(prop)
        self.improving_assignment : Any = None
        self.improving_value : Any = None
        self.can_improve : bool | None = None


class MdpSpecificationResult(SpecificationResult):

    def __init__(self):
        super().__init__()
        self.improving_assignment : Any = None
        self.improving_value : Any = None
        self.can_improve : bool | None = None

    def evaluate(self, parameter_space : Any = None, admissible_assignment : Any = None) -> None:
        self.improving_assignment = None
        self.improving_value = None
        self.can_improve = None

        cr = self.constraints_result
        opt = self.optimality_result
        assert cr is not None

        if cr.sat is False:
            self.can_improve = False
            return

        if cr.sat is True:
            # all constraints were satisfied
            if opt is None:
                if admissible_assignment is not None:
                    self.improving_assignment = admissible_assignment
                else:
                    self.improving_assignment = parameter_space
                self.can_improve = False
            else:
                self.improving_assignment = opt.improving_assignment
                self.improving_value = opt.improving_value
                self.can_improve = opt.can_improve
            return

        # constraints undecided
        if opt is None: 
            self.can_improve = True
        else:
            self.improving_assignment = opt.improving_assignment
            self.improving_value = opt.improving_value
            self.can_improve = opt.improving_value is None and opt.can_improve
