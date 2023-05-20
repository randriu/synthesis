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
    A list of property results.
    Note: some results might be None (not evaluated).
    '''
    def __init__(self, results):
        self.results = results

    def __str__(self):
        return ",".join([str(result) for result in self.results])

    @property
    def all_sat(self):
        for result in self.results:
            if result is not None and not result.sat:
                return False
        return True


class SpecificationResult:
    def __init__(self, constraints_result, optimality_result):
        self.constraints_result = constraints_result
        self.optimality_result = optimality_result

    def __str__(self):
        return str(self.constraints_result) + " : " + str(self.optimality_result)

    def accepting_dtmc(self, specification):
        """
        :return (1) whether specification is satisfied (dtmc is accepting)
        :return (2) new optimal value associated with the accepting dtmc
            (can be None if no optimality)
        """

        if not self.constraints_result.all_sat:
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
    def __init__(self,
        prop, primary, secondary, feasibility,
        primary_selection, primary_choice_values, primary_expected_visits,
        primary_scores
    ):
        self.minimizing = prop.minimizing
        self.primary = primary
        self.secondary = secondary
        self.feasibility = feasibility

        self.primary_selection = primary_selection
        self.primary_choice_values = primary_choice_values
        self.primary_expected_visits = primary_expected_visits
        self.primary_scores = primary_scores

    def __str__(self):
        prim = str(self.primary)
        seco = str(self.secondary)
        if self.minimizing:
            return "{} - {}".format(prim,seco)
        else:
            return "{} - {}".format(seco,prim)
            

class MdpConstraintsResult:
    def __init__(self, results):
        self.results = results
        self.undecided_constraints = [index for index,result in enumerate(results) if result is not None and result.feasibility is None]

        self.feasibility = True
        for result in results:
            if result is None:
                continue
            if result.feasibility == False:
                self.feasibility = False
                break
            if result.feasibility == None:
                self.feasibility = None

    def __str__(self):
        return ",".join([str(result) for result in self.results])


class MdpOptimalityResult(MdpPropertyResult):
    def __init__(self,
        prop, primary, secondary,
        improving_assignment, improving_value, can_improve,
        primary_selection, primary_choice_values, primary_expected_visits,
        primary_scores
    ):
        super().__init__(
            prop, primary, secondary, None,
            primary_selection, primary_choice_values, primary_expected_visits,
            primary_scores)
        self.improving_assignment = improving_assignment
        self.improving_value = improving_value
        self.can_improve = can_improve

class MdpSpecificationResult(SpecificationResult):

    def __init__(self, constraints_result, optimality_result):
        super().__init__(constraints_result,optimality_result)
        self.evaluate()

    
    def evaluate(self):
        self.improving_assignment = None
        self.improving_value = None
        self.can_improve = None

        cr = self.constraints_result
        opt = self.optimality_result

        if cr.feasibility == True:
            # either no constraints or constraints were satisfied
            if opt is not None:
                self.improving_assignment = opt.improving_assignment
                self.improving_value = opt.improving_value
                self.can_improve = opt.can_improve
            else:
                self.improving_assignment = family.pick_any()
                self.can_improve = False
            return

        if cr.feasibility == False:
            self.can_improve = False
            return

        # constraints undecided: try to push optimality assignment
        if opt is not None: 
            self.improving_assignment = opt.improving_assignment
            self.improving_value = opt.improving_value
            self.can_improve = opt.improving_value is None and opt.can_improve
        else:
            self.can_improve = True


