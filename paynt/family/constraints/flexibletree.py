"""A classic decision tree."""

import z3
from itertools import product, chain
import os


def piecewise_select(array, z3_int):
    """Select an element of an array based on a z3 integer."""
    return z3.Sum([z3.If(z3_int == i, array[i], 0) for i in range(len(array))])


def get_property_names(variable_name):
    return [
        x.strip().split("=")[0].replace("!", "")
        for x in variable_name[
            variable_name.find("[") + 1 : variable_name.find("]")
        ].split("&")
    ]


def get_property_values(variable_name):
    return [
        int(x.strip().split("=")[1]) if "=" in x else (0 if x.strip()[0] == "!" else 1)
        for x in variable_name[
            variable_name.find("[") + 1 : variable_name.find("]")
        ].split("&")
    ]


class DecisionTreeConstraint():

    tree_nodes: int | None

    def __init__(self):
        self.policy_vars = None
        self.labels = None
        self.label_to_index = None
        self.left_child_ranges = None
        self.right_child_ranges = None


    def build_constraint(self, variables, quotient):
        self.variables = variables
        num_nodes = self.tree_nodes

        policy_indices = list(range(len(variables)))
        policy_vars = [variables[i] for i in policy_indices]
        self.policy_vars = policy_vars

        # Collect all action labels and put them into an order
        labels = list(
            dict.fromkeys(
                chain(
                    *[quotient.family.hole_to_option_labels[i] for i in policy_indices]
                )
            )
        )
        print(labels)
        label_to_index = {label: i for i, label in enumerate(labels)}
        self.labels = labels
        self.label_to_index = label_to_index
        hole_to_label_indices = []
        # assert 2**num_bits > len(labels)

        # Check that the available action labels of policy vars are consistent
        for i in policy_indices:
            hole_to_label_indices.append(
                [
                    label_to_index[label]
                    for label in quotient.family.hole_to_option_labels[i]
                ]
            )

        # variables have names of the form
        # A([picked0=1       & picked1=0     & picked2=1     & picked3=1     & picked4=0     & picked5=1     & picked6=1     & x=3   & y=2],0
        first_variable_name = str(policy_vars[0])
        if "A([" not in first_variable_name:
            raise ValueError(
                "Variables must have properties (e.g., generated from POMDPs.)."
            )
        property_names = get_property_names(first_variable_name)
        num_properties = len(property_names)

        property_ranges = [(1e6, -1e6) for _ in range(num_properties)]
        for variable in policy_vars:
            property_values = get_property_values(str(variable))
            for i in range(num_properties):
                property_ranges[i] = (
                    min(property_ranges[i][0], property_values[i]),
                    max(property_ranges[i][1], property_values[i]),
                )

        constraints = []

        # create a function for each node
        decision_functions = []
        for i in range(num_nodes):
            decision_functions.append(
                z3.Function(
                    f"decision_{i}",
                    *[z3.IntSort()] * num_properties,
                    z3.IntSort(),
                )
            )

        # Left child is in range even([i+1, min(2i, num_nodes-1)])
        # Right child is in range odd([i+2, min(2i+1, num_nodes)])
        self.left_child_ranges = [
            [j for j in range(i + 1, min(2 * (i + 1), num_nodes)) if j % 2 == 1]
            for i in range(num_nodes)
        ]
        self.right_child_ranges = [
            [j for j in range(i + 2, min(2 * (i + 1) + 1, num_nodes)) if j % 2 == 0]
            for i in range(num_nodes)
        ]

        # make weight nodes for constraints
        node_constants = []
        property_indices = []
        node_is_leaf = []
        left_children = []
        right_children = []

        for i in range(num_nodes):
            # Is this node a leaf?
            is_leaf = z3.Bool(f"leaf_{i}")
            node_is_leaf.append(is_leaf)

            # The constant of a node
            constant_var = z3.Int(f"const_{i}")
            node_constants.append(constant_var)

            # The property index of a node
            prop_index = z3.Int(f"prop_index_{i}")
            # Must be in range
            constraints.append(prop_index >= 0)
            # print(num_properties)
            constraints.append(prop_index < num_properties)
            property_indices.append(prop_index)

            constraints.append(constant_var >= 0)
            constraints.append(
                z3.If(
                    is_leaf,
                    constant_var < len(labels),
                    constant_var <= piecewise_select(
                        [z3.IntVal(x[1]) for x in property_ranges],
                        prop_index,
                    ),
                )
            )

            left_child = z3.Int(f"left_{i}")
            left_children.append(left_child)
            right_child = z3.Int(f"right_{i}")
            right_children.append(right_child)
            # If this node is a leaf, the left and right children must be 0

            constraints.append(
                z3.If(
                    is_leaf,
                    left_child == 0,
                    left_child <= len(self.left_child_ranges[i]),
                )
            )
            constraints.append(
                z3.If(
                    is_leaf,
                    right_child == 0,
                    right_child <= len(self.right_child_ranges[i]),
                )
            )
            constraints.append(z3.Implies(is_leaf, prop_index == 0))

            all_property_values = [
                get_property_values(str(variable))
                for variable in enumerate(policy_vars)
            ]

            for values in all_property_values:
                prop_vals = [z3.IntVal(v) for v in values]
                constraints.append(
                    z3.If(
                        is_leaf,
                        decision_functions[i](*prop_vals) == constant_var,
                        z3.If(
                            piecewise_select(prop_vals, prop_index) >= constant_var,
                            z3.Or(
                                *[
                                    z3.And(
                                        left_child == j,
                                        decision_functions[i](*prop_vals)
                                        == decision_functions[
                                            self.left_child_ranges[i][j]
                                        ](*prop_vals),
                                    )
                                    for j in range(len(self.left_child_ranges[i]))
                                ]
                            ),
                            z3.Or(
                                *[
                                    z3.And(
                                        right_child == j,
                                        decision_functions[i](*prop_vals)
                                        == decision_functions[
                                            self.right_child_ranges[i][j]
                                        ](*prop_vals),
                                    )
                                    for j in range(len(self.right_child_ranges[i]))
                                ]
                            ),
                        ),
                    )
                )

        # each tree has (num_nodes+1) / 2 leaves
        constraints.append(z3.Sum(node_is_leaf) == (num_nodes + 1) // 2)
        # each node, except 0, must have a parent, that is before it

        for i in range(1, num_nodes):
            # identify the nodes that have i in left_child_ranges or right_child_ranges
            left_children_ranges = [
                j for j in range(num_nodes) if i in self.left_child_ranges[j]
            ]
            right_children_ranges = [
                j for j in range(num_nodes) if i in self.right_child_ranges[j]
            ]
            # i is left_child of one of the left_children or right_child of one of the right_children
            parent_constraint = z3.Or(
                *[
                    z3.And(
                        left_children[x] == self.left_child_ranges[x].index(i),
                        z3.Not(node_is_leaf[x]),
                    )
                    for x in left_children_ranges
                    if i in self.left_child_ranges[x]
                ]
                + [
                    z3.And(
                        right_children[x] == self.right_child_ranges[x].index(i),
                        z3.Not(node_is_leaf[x]),
                    )
                    for x in right_children_ranges
                    if i in self.right_child_ranges[x]
                ]
            )
            constraints.append(parent_constraint)

        for i, variable in enumerate(policy_vars):
            label_range = quotient.family.hole_to_option_labels[policy_indices[i]]
            if label_range == labels:
                # The semantics of the variable is the same as the decision tree's
                property_values = get_property_values(str(variable))
                constraints.append(variable == decision_functions[0](*property_values))
            else:
                # We need to map the decision tree's value to the label index
                label_indices = [label_to_index[label] for label in label_range]
                property_values = get_property_values(str(variable))
                x = decision_functions[0](*property_values)
                for index, label_index in enumerate(label_indices):
                    constraints.append((variable == index) == (x == label_index))

        return constraints
