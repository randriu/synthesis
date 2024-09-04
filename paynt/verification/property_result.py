import stormpy

from paynt.verification.property import *


class PropertyResult:
    def __init__(self, prop, result, value):
        self.result = result
        self.value = value
        self.sat = prop.satisfies_threshold(value)
        self.improves_optimum = None if not isinstance(prop,OptimalityProperty) else prop.improves_optimum(value)

    def __str__(self):
        return str(self.value)


class ConstraintsResult:
    '''
    A list of constraint results.
    Note: some results might be None (not evaluated).
    '''
    def __init__(self, results):
        self.results = results
        self.undecided_constraints = [i for i,result in enumerate(results) if result is not None and result.sat is None]
        
        result_sats = [result.sat for result in results if result is not None]
        if False in result_sats:
            self.sat = False
        elif None in result_sats:
            self.sat = None
        else:
            self.sat = True


    def __str__(self):
        return ",".join([str(result) for result in self.results])


class SpecificationResult:
    def __init__(self):
        self.constraints_result = None
        self.optimality_result = None

    def __str__(self):
        return str(self.constraints_result) + " : " + str(self.optimality_result)

    def accepting_dtmc(self, specification):
        """
        :return (1) whether specification is satisfied (dtmc is accepting)
        :return (2) new optimal value associated with the accepting dtmc
            (can be None if no optimality)
        """

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


    def undecided_result(self):
        if self.optimality_result is not None and self.optimality_result.can_improve:
            return self.optimality_result
        return self.constraints_result.results[self.constraints_result.undecided_constraints[0]]

            

class MdpPropertyResult:
    def __init__(self,prop):
        self.prop = prop
        self.primary = None
        self.secondary = None
        self.sat = None
        self.primary_selection = None

    @property
    def minimizing(self):
        return self.prop.minimizing

    def __str__(self):
        prim = str(self.primary)
        seco = str(self.secondary)
        if self.minimizing:
            return "{} - {}".format(prim,seco)
        else:
            return "{} - {}".format(seco,prim)



class MdpOptimalityResult(MdpPropertyResult):
    def __init__(self, prop):
        super().__init__(prop)
        self.improving_assignment = None
        self.improving_value = None
        self.can_improve = None


class MdpSpecificationResult(SpecificationResult):

    def __init__(self):
        pass

    def evaluate(self, family):
        self.improving_assignment = None
        self.improving_value = None
        self.can_improve = None

        cr = self.constraints_result
        opt = self.optimality_result

        if cr.sat is False:
            self.can_improve = False
            return

        if cr.sat is True:
            # all constraints were satisfied
            if opt is None:
                self.improving_assignment = family
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
