
from paynt.family.constraints.flexibletree import DecisionTreeConstraint
from paynt.family.constraints.prob_goal import ProbGoalConstraint
from paynt.family.constraints.costs import CostsConstraint

class Constraints:

    @staticmethod
    def create_constraint(constraint_type):
        if constraint_type == "prob1":
            return ProbGoalConstraint(prob=1)
        elif constraint_type == "prob0":
            return ProbGoalConstraint(prob=0)
        elif constraint_type == "tree":
            return DecisionTreeConstraint()
        elif constraint_type == "costs":
            return CostsConstraint()
        else:            
            raise ValueError(f"Unknown constraint type: {constraint_type}")
