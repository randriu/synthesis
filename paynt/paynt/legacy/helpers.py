import operator

import stormpy

from ..jani.jani_quotient_builder import JaniQuotientBuilder

# Zero approximation to avoid zero division etc.
APPROX_ZERO = 0.000001


def safe_division(dividend, divisor):
    """Safe division of dividend by operand
    :param number dividend: upper operand of the division
    :param number divisor: lower operand of the division, may be zero
    :return: safe value after division of approximated zero
    """
    try:
        return dividend / divisor
    except (ZeroDivisionError, ValueError):
        return dividend / APPROX_ZERO

def check_dtmc(dtmc, formula, quantitative=False):
    """Model check a DTMC against a (quantitative) property."""
    if quantitative:
        formula = formula.clone()
        formula.remove_bound()

    result = stormpy.model_checking(dtmc, formula)
    at_init = result.at(dtmc.initial_states[0])
    satisfied = at_init if not quantitative else is_satisfied(formula, at_init)
    return satisfied, result


def readable_assignment(assignment):
    assignment = {} if assignment is None else assignment
    read_assignment = {}
    for (name, values) in assignment.items():
        read_assignment[name] = \
            [JaniQuotientBuilder.convert_expr_to_num(assignment[name][idx]) for idx, value in enumerate(values)]
    return ",".join([f"{k}={v if len(v) > 1 else v[0]}" for k, v in read_assignment.items()])
