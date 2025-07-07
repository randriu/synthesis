"""Reach goal with prob>0 or prob=1."""

import z3
import math
from stormpy import model_checking

import logging
logger = logging.getLogger(__name__)

class ProbGoalConstraint():
    def __init__(self, prob: int = 0):
        assert prob in [0, 1], "ProbGoal requires prob to be either 0 or 1."
        self.prob0 = (prob == 0)

    def build_constraint(
        self,
        variables,
        quotient
    ) -> z3.ExprRef:

        # We build the quotient here
        quotient.build(quotient.family)

        transition_matrix = quotient.family.mdp.model.transition_matrix

        choice_to_assignment = quotient.coloring.getChoiceToAssignment()

        target_states = model_checking(quotient.family.mdp.model, quotient.specification.all_properties()[0].formula.subformula.subformula).get_truth_values()

        assertions = []

        reachability_vars = []
        for state in range(transition_matrix.nr_columns):
            reach_var = z3.Bool(f"reach_{state}")
            reachability_vars.append(reach_var)

        if not self.prob0:
            min_step_vars = []
            for state in range(transition_matrix.nr_columns):
                min_step_var = z3.Int(f"min_step_{state}")
                min_step_vars.append(min_step_var)
                assertions.append(min_step_var >= 0)

            for state in range(transition_matrix.nr_columns):
                if target_states.get(state):
                    assertions.append(reachability_vars[state])
                    assertions.append(min_step_vars[state] == 0)
                    continue
                
                statement_for_state = []
                
                rows = transition_matrix.get_rows_for_group(state)
                for row in rows:
                    assignment = choice_to_assignment[row]
                    assignment_as_z3 = z3.And([
                        variables[var] == z3.IntVal(x)
                        for var, x in assignment
                    ])

                    reachability_vars_of_row = []
                    min_step_vars_of_row = []

                    for entry in transition_matrix.get_row(row):
                        value = entry.value()
                        if value == 0:
                            continue
                        assert value > 0, "Transition probabilities must be positive."
                        to_state = entry.column
                        if to_state == state:
                            continue
                        reachability_vars_of_row.append(reachability_vars[to_state])
                        min_step_vars_of_row.append(min_step_vars[to_state])
                    statement_for_state.append(z3.Implies(assignment_as_z3, z3.And(reachability_vars_of_row)))
                    assertions.append(
                        z3.Implies(
                            z3.And(reachability_vars[state], assignment_as_z3),
                            z3.And(
                                z3.Or([min_step_vars[state] == x + 1 for x in min_step_vars_of_row]),
                                z3.And([min_step_vars[state] <= x + 1 for x in min_step_vars_of_row])
                            )
                        )
                    )
                assertions.append(z3.Implies(reachability_vars[state], z3.And(statement_for_state)))
        else:
            assert False, "prob0 not implemented."


                # else:
                #     assertions.append(
                #         z3.Implies(
                #             z3.And(reachability_vars[to_state], assignment_as_z3),
                #             z3.And(reachability_vars[state])
                #         )
                #     )
                #     max_step_vars_of_row.append(max_step_vars[to_state])

                # if not self.prob0:
                #     assertions.append(
                #         z3.Implies(
                #             reachability_vars[state],
                #             z3.Or([max_step_vars[state] > x for x in max_step_vars_of_row])
                #         )
                #     )

        initial_state = quotient.family.mdp.model.initial_states[0]
        assert len(quotient.family.mdp.model.initial_states) == 1, "ProbGoal only supports single initial states."

        assertions.append(reachability_vars[initial_state])
        logger.info("Done building assertions for ProbGoal.")
        return assertions

    # def show_result(self, model, solver, **args):
    #     print([(x, model[x]) for x in model if x.name().startswith("reach_")])
