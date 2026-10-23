"""Random formulas for the tests of colorings: z3py formulas in the language of ColoringBuilder, each built with the Python function that evaluates it."""

from __future__ import annotations

import operator

import z3

import paynt.utils.coloring_builder


class FormulaGenerator:
    """Random formulas over three parameters (value = option index), one data column and a bit mask, built together with the Python function that evaluates
    them: the reference the builder's formula language is held to."""

    COMPARISONS = [operator.eq, operator.ne, operator.lt, operator.le, operator.gt, operator.ge]

    def __init__(self, rng, parameters, column, mask):
        self.rng = rng
        self.parameters = parameters
        self.column = column
        self.mask = mask

    def term(self, depth):
        rng = self.rng
        kind = rng.choice(["parameter", "literal", "column"] if depth == 0 else ["parameter", "literal", "column", "add", "sub", "mul", "neg", "if"])
        if kind == "parameter":
            index = rng.randrange(len(self.parameters))
            return self.parameters[index], lambda values, data, index=index: values[index]
        if kind == "literal":
            literal = rng.randint(-1, 3)
            return z3.IntVal(literal), lambda values, data, literal=literal: literal
        if kind == "column":
            return self.column, lambda values, data: data["column"]
        if kind == "neg":
            expression, function = self.term(depth - 1)
            return -expression, lambda values, data: -function(values, data)
        if kind == "if":
            condition, test = self.boolean(depth - 1)
            (then_expression, then_function), (else_expression, else_function) = self.term(depth - 1), self.term(depth - 1)
            return (
                z3.If(condition, then_expression, else_expression),
                lambda values, data: then_function(values, data) if test(values, data) else else_function(values, data),
            )
        (left, left_function), (right, right_function) = self.term(depth - 1), self.term(depth - 1)
        combine = {"add": operator.add, "sub": operator.sub, "mul": operator.mul}[kind]
        return combine(left, right), lambda values, data: combine(left_function(values, data), right_function(values, data))

    def boolean(self, depth):
        rng = self.rng
        kind = rng.choice(["compare", "options", "bits"] if depth == 0 else ["compare", "options", "bits", "not", "and", "or", "implies", "if"])
        if kind == "compare":
            compare = rng.choice(self.COMPARISONS)
            (left, left_function), (right, right_function) = self.term(max(depth - 1, 0)), self.term(max(depth - 1, 0))
            return compare(left, right), lambda values, data: compare(left_function(values, data), right_function(values, data))
        if kind == "options":
            index = rng.randrange(len(self.parameters))
            options = rng.sample([0, 1, 2], rng.randint(1, 3))
            return z3.Or([self.parameters[index] == option for option in options]), lambda values, data: values[index] in options
        if kind == "bits":
            index = rng.randrange(len(self.parameters))
            return paynt.utils.coloring_builder.ColoringBuilder.in_bits(self.parameters[index], self.mask), lambda values, data: bool(
                (data["mask"] >> values[index]) & 1
            )
        if kind == "not":
            expression, function = self.boolean(depth - 1)
            return z3.Not(expression), lambda values, data: not function(values, data)
        if kind == "if":
            (condition, test), (then_expression, then_function), (else_expression, else_function) = (
                self.boolean(depth - 1),
                self.boolean(depth - 1),
                self.boolean(depth - 1),
            )
            return (
                z3.If(condition, then_expression, else_expression),
                lambda values, data: then_function(values, data) if test(values, data) else else_function(values, data),
            )
        operands = [self.boolean(depth - 1) for _ in range(rng.randint(2, 3))]
        expressions = [expression for expression, _ in operands]
        functions = [function for _, function in operands]
        if kind == "and":
            return z3.And(expressions), lambda values, data: all(function(values, data) for function in functions)
        if kind == "or":
            return z3.Or(expressions), lambda values, data: any(function(values, data) for function in functions)
        return z3.Implies(expressions[0], expressions[1]), lambda values, data: (not functions[0](values, data)) or functions[1](values, data)
