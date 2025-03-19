import stormpy
import payntbind
import logging
import graphviz
import json

logger = logging.getLogger(__name__)


class DecisionTree:

    def __init__(self, quotient, variables):
        self.quotient = quotient
        self.variables = variables
        self.reset()

    def reset(self):
        self.root = DecisionTreeNode(None)

    def random_tree(self):
        self.root = DecisionTreeNode(None)
        self.root.action = self.quotient.action_labels.index("__random__")

    def copy(self):
        new_tree = DecisionTree(self.quotient, self.variables)
        new_tree.root = self.root.copy(None)
        return new_tree

    def set_depth(self, depth: int):
        self.reset()
        for level in range(depth):
            for node in self.collect_terminals():
                node.add_children()
        self.root.assign_identifiers()

    def get_depth(self):
        return self.root.get_depth()

    def build_from_tree_helper(self, tree_helper):
        self.reset()
        node_stack = [(0, self.root)]
        var_names = [v.name for v in self.variables]
        var_domains = [v.domain for v in self.variables]
        self.root.set_node_from_helper(tree_helper[0], var_names, var_domains, self.quotient.action_labels)
        while node_stack:
            node_id, node = node_stack.pop()
            if tree_helper[node_id]["leaf"]:
                continue
            node.add_children_from_helper(tree_helper, tree_helper[node_id], var_names, var_domains,
                                          self.quotient.action_labels)
            node_stack.append((tree_helper[node_id]["children"][0], node.child_true))
            node_stack.append((tree_helper[node_id]["children"][1], node.child_false))

        self.root.assign_identifiers()

        # double check if identifiers correspond to the tree helper
        nodes = self.collect_nodes()
        for node_id, node in enumerate(nodes):
            assert node.is_terminal == tree_helper[node.identifier][
                "leaf"], f"node {node_id} is terminal: {node.is_terminal}, expected: {tree_helper[node_id]['leaf']}"
            assert node.identifier == tree_helper[node.identifier][
                "id"], f"node {node_id} has identifier {node.identifier}, expected: {tree_helper[node_id]['id']}"

    def collect_nodes(self, node_condition=None):
        if node_condition is None:
            node_condition = lambda node: True
        node_queue = [self.root]
        output_nodes = []
        while node_queue:
            node = node_queue.pop(0)
            if node_condition(node):
                output_nodes.append(node)
            node_queue += node.child_nodes
        return output_nodes

    def collect_terminals(self):
        return self.collect_nodes(lambda node: node.is_terminal)

    def collect_nonterminals(self):
        return self.collect_nodes(lambda node: not node.is_terminal)

    def to_list(self):
        num_nodes = len(self.collect_nodes())
        node_info = [None for node in range(num_nodes)]
        for node in self.collect_nodes():
            parent = num_nodes if node.parent is None else node.parent.identifier
            child_true = num_nodes if node.is_terminal else node.child_true.identifier
            child_false = num_nodes if node.is_terminal else node.child_false.identifier
            node_info[node.identifier] = (parent, child_true, child_false)
        return node_info

    def simplify(self, state_valuations):
        self.root.simplify(self.variables, state_valuations)

    def to_string(self):
        return self.root.to_string(self.variables, self.quotient.action_labels)

    def to_prism(self, indent_size=2):
        indent = " " * indent_size
        s = ""
        s += "module scheduler\n"
        for terminal in self.collect_terminals():
            action = f"{self.quotient.action_labels[terminal.action]}"
            guard = " & ".join(terminal.path_expression(self.variables))
            if guard == "":
                guard = "true"
            s += f"{indent}[{action}] {guard} -> true;\n"
        # s += indent + f"if {var.name}<={var.domain[self.variable_bound]}:" + "\n"
        # s += self.child_true.to_string(variables,action_labels,indent_level+1)
        # s += indent + f"else:" + "\n"
        # s += self.child_false.to_string(variables,action_labels,indent_level+1)
        s += "endmodule\n"
        return s

    def to_graphviz(self, highlight_nodes=[]):
        logging.getLogger("graphviz").setLevel(logging.WARNING)
        logging.getLogger("graphviz.sources").setLevel(logging.ERROR)
        graphviz_tree = graphviz.Digraph(comment="decision tree")
        self.root.to_graphviz(graphviz_tree, self.variables, self.quotient.action_labels, highlight_nodes)
        return graphviz_tree

    def to_scheduler_json(self, reachable_states=None):
        if reachable_states is None:
            reachable_states = stormpy.BitVector(self.quotient.quotient_mdp.nr_states, True)
        scheduler = payntbind.synthesis.create_scheduler(self.quotient.quotient_mdp.nr_states)
        nci = self.quotient.quotient_mdp.nondeterministic_choice_indices.copy()
        for state in range(self.quotient.quotient_mdp.nr_states):
            if self.quotient.state_is_relevant_bv.get(state) and reachable_states.get(state):
                action_index = self.root.get_action_for_state(self.quotient, state,
                                                              self.quotient.relevant_state_valuations[state], nci)
            else:
                # this should leave undefined in the scheduler and will be filtered below
                payntbind.synthesis.set_dont_care_state_for_scheduler(scheduler, state, 0,
                                                                      False)  # trying to filter out these states through Storm
                continue
            scheduler_choice = stormpy.storage.SchedulerChoice(action_index)
            scheduler.set_choice(scheduler_choice, state)

        json_scheduler_full = json.loads(scheduler.to_json_str(self.quotient.quotient_mdp, skip_dont_care_states=True))
        # json_final = []
        # for entry in json_scheduler_full:
        #     if entry["c"] == "undefined":
        #         # TODO remove this eventually (keeping it for testing), the fix above makes this unnecessary
        #         assert False
        #         continue
        #     json_final.append(entry)

        json_str = json.dumps(json_scheduler_full, indent=4)
        return json_str

    def append_tree_as_subtree(self, new_subtree, subtree_root_node_id, subtree_quotient):
        subtree_root_node = self.collect_nodes(lambda node: node.identifier == subtree_root_node_id)
        assert len(subtree_root_node) == 1, f"subtree root node id {subtree_root_node_id} not found in decision tree"
        subtree_root_node = subtree_root_node[0]

        all_current_nodes = self.collect_nodes()
        new_subtree.root.assign_identifiers(identifier=len(all_current_nodes) + 1)
        new_subtree.root.fix_with_respect_to_quotient(subtree_quotient, self.quotient)

        parent = subtree_root_node.parent
        if parent.child_true.identifier == subtree_root_node.identifier:
            parent.child_true = new_subtree.root
        else:
            parent.child_false = new_subtree.root


class DecisionTreeNode:

    def __init__(self, parent):
        self.parent = parent
        self.child_true = None
        self.child_false = None
        self.identifier = None
        self.holes = None

        self.action = None
        self.variable = None
        self.variable_bound = None

    @property
    def is_terminal(self):
        return self.child_false is None and self.child_true is None

    @property
    def child_nodes(self):
        return [] if self.is_terminal else [self.child_true, self.child_false]

    @property
    def is_true_child(self):
        return self is self.parent.child_true

    def add_children(self):
        assert self.is_terminal
        self.child_true = DecisionTreeNode(self)
        self.child_false = DecisionTreeNode(self)

    def set_node_from_helper(self, tree_helper_node, variable_names, variable_domains, action_labels):
        if tree_helper_node["leaf"]:
            self.action = action_labels.index(tree_helper_node["chosen"][0])
        else:
            self.variable = variable_names.index(tree_helper_node["chosen"][0])
            # dtControl uses values that are not necessarily in the domain, e.g. let's say our domain is [0,2,3]
            # and we want to split [0] and [2,3], dtControl can choose 0,5 or 1,5. We expect it will be 0 in this case.
            while tree_helper_node["chosen"][1] not in variable_domains[self.variable]:
                tree_helper_node["chosen"] = (tree_helper_node["chosen"][0], tree_helper_node["chosen"][1] - 1)
            self.variable_bound = variable_domains[self.variable].index(tree_helper_node["chosen"][1])

    def add_children_from_helper(self, tree_helper, helper_node, variable_names, variable_domains, action_labels):
        assert self.is_terminal
        self.child_true = DecisionTreeNode(self)
        true_child_helper = tree_helper[helper_node["children"][0]]
        self.child_true.set_node_from_helper(true_child_helper, variable_names, variable_domains, action_labels)
        self.child_false = DecisionTreeNode(self)
        false_child_helper = tree_helper[helper_node["children"][1]]
        self.child_false.set_node_from_helper(false_child_helper, variable_names, variable_domains, action_labels)

    def get_depth(self):
        if self.is_terminal:
            return 0
        return 1 + max([child.get_depth() for child in self.child_nodes])

    def get_number_of_descendants(self):
        if self.is_terminal:
            return 0
        return 1 + sum([child.get_number_of_descendants() for child in self.child_nodes])

    def assign_identifiers(self, identifier=0, keep_old=False):
        if keep_old:
            self.old_identifier = self.identifier
        self.identifier = identifier
        if self.is_terminal:
            return self.identifier
        identifier = self.child_true.assign_identifiers(identifier + 1, keep_old=keep_old)
        identifier = self.child_false.assign_identifiers(identifier + 1, keep_old=keep_old)
        return identifier

    def associate_holes(self, node_hole_info):
        self.holes = [hole for hole, _, _ in node_hole_info[self.identifier]]
        if self.is_terminal:
            return
        self.child_true.associate_holes(node_hole_info)
        self.child_false.associate_holes(node_hole_info)

    def associate_assignment(self, assignment):
        hole_assignment = [assignment.hole_options(hole)[0] for hole in self.holes]
        if self.is_terminal:
            self.action = hole_assignment[0]
            return

        self.variable = hole_assignment[0]
        self.variable_bound = hole_assignment[self.variable + 1]

        self.child_true.associate_assignment(assignment)
        self.child_false.associate_assignment(assignment)

    def apply_hint(self, subfamily, tree_hint):
        if self.is_terminal or tree_hint.is_terminal:
            return

        variable_hint = tree_hint.variable
        subfamily.hole_set_options(self.holes[0], [variable_hint])
        subfamily.hole_set_options(self.holes[variable_hint + 1], [tree_hint.variable_bound])
        self.child_true.apply_hint(subfamily, tree_hint.child_true)
        self.child_false.apply_hint(subfamily, tree_hint.child_false)

    def simplify(self, variables, state_valuations):
        if self.is_terminal:
            return

        bound = variables[self.variable].domain[self.variable_bound]
        state_valuations_true = [valuation for valuation in state_valuations if valuation[self.variable] <= bound]
        state_valuations_false = [valuation for valuation in state_valuations if valuation[self.variable] > bound]
        child_skip = None
        if len(state_valuations_true) == 0:
            child_skip = self.child_false
        elif len(state_valuations_false) == 0:
            child_skip = self.child_true
        if child_skip is not None:
            self.variable = child_skip.variable
            self.variable_bound = child_skip.variable_bound
            self.action = child_skip.action
            self.child_true = child_skip.child_true
            self.child_false = child_skip.child_false
            self.simplify(variables, state_valuations)
            return

        self.child_true.simplify(variables, state_valuations_true)
        self.child_false.simplify(variables, state_valuations_false)
        if not self.is_terminal and self.child_true.is_terminal and self.child_false.is_terminal and self.child_true.action == self.child_false.action:
            self.variable = self.variable_bound = None
            self.action = self.child_true.action
            self.child_true = self.child_false = None

    def branch_expression(self, variables, true_branch=True):
        var = variables[self.variable]
        if true_branch:
            return f"{var.name}<={var.domain[self.variable_bound]}"
        else:
            return f"{var.name}>{var.domain[self.variable_bound]}"

    def path_expression(self, variables):
        if self.parent is None:
            return []
        return self.parent.path_expression(variables) + [
            self.parent.branch_expression(variables, true_branch=self.is_true_child)]

    def copy(self, parent):
        node_copy = DecisionTreeNode(parent)
        node_copy.identifier = self.identifier
        node_copy.holes = self.holes
        if self.is_terminal:
            node_copy.action = self.action
        else:
            node_copy.variable = self.variable
            node_copy.variable_bound = self.variable_bound
            node_copy.child_true = self.child_true.copy(node_copy)
            node_copy.child_false = self.child_false.copy(node_copy)
        return node_copy

    def to_string(self, variables, action_labels, indent_level=0, indent_size=2):
        indent = " " * indent_level * indent_size
        if self.is_terminal:
            return indent + f"{action_labels[self.action]}" + "\n"
        s = ""
        s += indent + f"if {self.branch_expression(variables)}:" + "\n"
        s += self.child_true.to_string(variables, action_labels, indent_level + 1)
        s += indent + f"else:" + "\n"
        s += self.child_false.to_string(variables, action_labels, indent_level + 1)
        return s

    @property
    def graphviz_id(self):
        return str(self.identifier)

    def to_graphviz(self, graphviz_tree, variables, action_labels, highlight_nodes=[]):
        if not self.is_terminal:
            for child in self.child_nodes:
                child.to_graphviz(graphviz_tree, variables, action_labels, highlight_nodes)

        if self.is_terminal:
            node_label = action_labels[self.action]
        else:
            var = variables[self.variable]
            node_label = f"{var.name}<={var.domain[self.variable_bound]}"

        if self.identifier in highlight_nodes:
            graphviz_tree.node(self.graphviz_id, label=node_label, shape="box", style="filled", fillcolor="lightgreen",
                               margin="0.05,0.05")
        else:
            graphviz_tree.node(self.graphviz_id, label=node_label, shape="box", style="rounded", margin="0.05,0.05")
        if not self.is_terminal:
            graphviz_tree.edge(self.graphviz_id, self.child_true.graphviz_id, label="T")
            graphviz_tree.edge(self.graphviz_id, self.child_false.graphviz_id, label="F")

    def get_action_for_state(self, quotient, state, state_valuation, nci):
        if self.is_terminal:
            action_index = self.action
            index = 0
            for choice in range(nci[state], nci[state + 1]):
                if quotient.choice_to_action[choice] == action_index:
                    return index
                index += 1
            else:
                # TODO as far as I know this happens only because of unreachable states not being included in the tree
                # for now we will treat this by using the __random__ action but it can lead to strange behaviour
                index = 0
                for choice in range(nci[state], nci[state + 1]):
                    if quotient.action_labels[quotient.choice_to_action[choice]] == "__random__":
                        return index
                    index += 1
                assert False
        var = quotient.variables[self.variable]
        bound = var.domain[self.variable_bound]
        if state_valuation[self.variable] <= bound:
            return self.child_true.get_action_for_state(quotient, state, state_valuation, nci)
        else:
            return self.child_false.get_action_for_state(quotient, state, state_valuation, nci)

    # after subtree synthesis the tree nodes contain identifiers to objects from subtree_quotient
    # this needs to be fixed to match the objects in the original quotient
    def fix_with_respect_to_quotient(self, quotient, new_quotient):
        if self.is_terminal:
            old_index = self.action
            self.action = new_quotient.action_labels.index(quotient.action_labels[old_index])
            return

        var = quotient.variables[self.variable]
        var_name = var.name
        var_bound = var.domain[self.variable_bound]
        for var_id, new_var in enumerate(new_quotient.variables):
            if new_var.name == var_name:
                break
        bound_id = new_var.domain.index(var_bound)
        self.variable = var_id
        self.variable_bound = bound_id

        self.child_true.fix_with_respect_to_quotient(quotient, new_quotient)
        self.child_false.fix_with_respect_to_quotient(quotient, new_quotient)