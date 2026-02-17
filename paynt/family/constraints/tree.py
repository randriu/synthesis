"""A classic decision tree."""

import z3


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


class DecisionTreeConstraintOld():

    tree_depth: int

    tree_nodes: int | None

    def __init__(self):
        pass

    def build_constraint(self, variables, quotient):
        tree_depth = self.tree_depth
        self.variables = variables
        num_enabled_nodes = self.tree_nodes

        # variables have names of the form
        # A([picked0=1       & picked1=0     & picked2=1     & picked3=1     & picked4=0     & picked5=1     & picked6=1     & x=3   & y=2],0
        first_variable_name = str(variables[0])
        if "A([" not in first_variable_name:
            raise ValueError(
                "Variables must have properties (e.g., generated from POMDPs.)."
            )
        property_names = get_property_names(first_variable_name)
        num_properties = len(property_names)

        property_ranges = [(1e6, -1e6) for _ in range(num_properties)]
        for variable in variables:
            property_values = get_property_values(str(variable))
            for i in range(num_properties):
                property_ranges[i] = (
                    min(property_ranges[i][0], property_values[i]),
                    max(property_ranges[i][1], property_values[i]),
                )

        # create a function
        max_action_size = max([len(quotient.family.hole_options(hole)) for hole in range(len(variables))])
        decision_func = z3.Function(
            "decision", *[z3.IntSort()] * num_properties, z3.IntSort()
        )

        # decision_func_int = z3.Function(
        #     "decision", *[z3.IntSort()] * num_properties, z3.IntSort()
        # )

        constraints = []

        # tree is structured as follows
        # 0
        # 1 2
        # 3 4 5 6
        # 7 8 9 10 11 12 13 14

        num_nodes = 2**tree_depth - 1
        leaf_values = [
            z3.Int(f"leaf_{i}") for i in range(num_nodes + 1)
        ]

        # make weight nodes for constraints
        node_property = []
        node_constants = []
        for i in range(num_nodes):
            # weight per variable
            prop_index = z3.Int(f"node_{i}")

            # prop index must be in range
            constraints.append(prop_index >= 0)
            constraints.append(prop_index < num_properties)

            node_property.append(prop_index)
            constant_var = z3.Int(f"const_{i}")
            node_constants.append(constant_var)
            constraints.append(constant_var >= 0)

            # if the constant of this node is > 0, this is also true for the parent
            # this breaks symmetry for disabled nodes
            if i > 0:
                constraints.append(
                    z3.Implies(node_constants[i] > 0, node_constants[(i - 1) // 2] > 0)
                )
            # if the constant is 0, the property must be 0
            constraints.append(
                z3.Implies(node_constants[i] == 0, node_property[i] == 0)
            )

        # only num_enabled_nodes nodes can have constant > 0
        if num_enabled_nodes is not None:
            constraints.append(
                z3.Sum([z3.If(node_constants[i] > 0, 1, 0) for i in range(num_nodes)])
                == num_enabled_nodes
            )

        def decision_at_node(node: int, properties):
            return z3.Or(
                node_constants[node] == 0,
                z3.Sum(
                    [
                        z3.If(node_property[node] == i, properties[i], 0)
                        for i in range(num_properties)
                    ]
                )
                >= node_constants[node],
            )

        def traverse_tree(node: int, properties: list[z3.Int]):
            if node >= num_nodes:
                return leaf_values[node - num_nodes]
            else:
                left = traverse_tree(2 * node + 1, properties)
                right = traverse_tree(2 * node + 2, properties)
                return z3.If(decision_at_node(node, properties), left, right)

        decision_variables = [z3.Int(f"decision_{i}") for i in range(num_properties)]
        constraints.append(
            z3.ForAll(
                decision_variables,
                traverse_tree(0, decision_variables)
                == decision_func(*decision_variables),
            )
        )

        for variable in variables:
            property_values = get_property_values(str(variable))
            constraints.append(variable == decision_func(*property_values))
        return constraints

