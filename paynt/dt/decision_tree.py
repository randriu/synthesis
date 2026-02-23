from collections.abc import Callable
from typing import Optional

import graphviz

import logging
logger = logging.getLogger(__name__)

class DtVariable:

    def __init__(self, name : str, domain : set[int]):
        self.name = name
        # conversion of boolean variables to integers
        domain_new = []
        for value in domain:
            if value is True:
                value = 1
            elif value is False:
                value = 0
            domain_new.append(value)
        domain = domain_new
        domain = sorted(domain)
        self.domain = domain

    @property
    def domain_min(self) -> int:
        return self.domain[0]

    @property
    def domain_max(self) -> int:
        return self.domain[-1]

    @property
    def parameter_domain(self) -> list[int]:
        '''
        Parameter domain does not include the maximum value.
        '''
        return self.domain[:-1]

    def __str__(self) -> str:
        domain = f"[{self.domain_min}..{self.domain_max}]"
        return f"{self.name}:{domain}"




class DecisionTreeNode:

    def __init__(self, parent : Optional["DecisionTreeNode"]):
        self.parent = parent
        self.child_true = None
        self.child_false = None
        self.identifier = None
        self.parameters = None

        self.action = None
        self.variable = None
        self.variable_bound = None

    @property
    def is_terminal(self) -> bool:
        return self.child_false is None and self.child_true is None

    @property
    def child_nodes(self) -> list["DecisionTreeNode"]:
        return [] if self.is_terminal else [self.child_true,self.child_false]

    @property
    def is_true_child(self) -> bool:
        return self is self.parent.child_true

    def add_children(self):
        assert self.is_terminal
        self.child_true = DecisionTreeNode(self)
        self.child_false = DecisionTreeNode(self)

    def get_depth(self) -> int:
        if self.is_terminal:
            return 0
        return 1 + max([child.get_depth() for child in self.child_nodes])

    def assign_identifiers(self, identifier : int = 0) -> int:
        '''
        Recursively assigns unique identifiers to each child node with pre-order traversal.
        '''
        self.identifier = identifier
        if self.is_terminal:
            return self.identifier
        identifier = self.child_true.assign_identifiers(identifier+1)
        identifier = self.child_false.assign_identifiers(identifier+1)
        return identifier

    def associate_parameters(self, node_parameter_info : list[tuple[int,str,str]]):
        self.parameters = [parameter for parameter,_,_ in node_parameter_info[self.identifier]]
        if self.is_terminal:
            return
        self.child_true.associate_parameters(node_parameter_info)
        self.child_false.associate_parameters(node_parameter_info)

    def associate_assignment(self, assignment): # TODO type of assignment
        parameter_assignment = [assignment.hole_options(parameter)[0] for parameter in self.parameters]
        if self.is_terminal:
            self.action = parameter_assignment[0]
            return

        self.variable = parameter_assignment[0]
        self.variable_bound = parameter_assignment[self.variable+1]

        self.child_true.associate_assignment(assignment)
        self.child_false.associate_assignment(assignment)

    def apply_hint(self, subfamily, tree_hint):
        if self.is_terminal or tree_hint.is_terminal:
            return

        variable_hint = tree_hint.variable
        subfamily.hole_set_options(self.parameters[0],[variable_hint]) # TODO refactor, rename holes to parameters
        subfamily.hole_set_options(self.parameters[variable_hint+1],[tree_hint.variable_bound])
        self.child_true.apply_hint(subfamily,tree_hint.child_true)
        self.child_false.apply_hint(subfamily,tree_hint.child_false)

    def simplify(self, variables : list["DtVariable"], state_valuations : list[list[int]]):
        '''
        Recursively simplifies the decision tree by removing nodes that have only one child due to the given state valuations, and by merging terminal nodes with the same action.
        '''
        if self.is_terminal:
            return

        bound = variables[self.variable].domain[self.variable_bound]
        state_valuations_true =  [valuation for valuation in state_valuations if valuation[self.variable] <= bound]
        state_valuations_false = [valuation for valuation in state_valuations if valuation[self.variable]  > bound]
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
            self.simplify(variables,state_valuations)
            return

        self.child_true.simplify(variables, state_valuations_true)
        self.child_false.simplify(variables, state_valuations_false)
        if not self.is_terminal and self.child_true.is_terminal and self.child_false.is_terminal and self.child_true.action == self.child_false.action:
            self.variable = self.variable_bound = None
            self.action = self.child_true.action
            self.child_true = self.child_false = None

    def branch_expression(self, variables : list["DtVariable"], true_branch : bool = True) -> str:
        var = variables[self.variable]
        if true_branch:
            return f"{var.name}<={var.domain[self.variable_bound]}"
        else:
            return f"{var.name}>{var.domain[self.variable_bound]}"

    def path_expression(self, variables : list["DtVariable"]) -> list[str]:
        if self.parent is None:
            return []
        return self.parent.path_expression(variables) + [self.parent.branch_expression(variables,true_branch=self.is_true_child)]

    def to_string(self, variables : list["DtVariable"], action_labels : list[str], indent_level : int = 0, indent_size : int = 2) -> str:
        indent = " "*indent_level*indent_size
        if self.is_terminal:
            return indent + f"{action_labels[self.action]}" + "\n"
        s = ""
        s += indent + f"if {self.branch_expression(variables)}:" + "\n"
        s += self.child_true.to_string(variables,action_labels,indent_level+1)
        s += indent + f"else:" + "\n"
        s += self.child_false.to_string(variables,action_labels,indent_level+1)
        return s

    @property
    def graphviz_id(self) -> str:
        return str(self.identifier)

    def to_graphviz(self, graphviz_tree : graphviz.Digraph, variables : list["DtVariable"], action_labels : list[str]):
        if not self.is_terminal:
            for child in self.child_nodes:
                child.to_graphviz(graphviz_tree,variables,action_labels)

        if self.is_terminal:
            node_label = action_labels[self.action]
        else:
            var = variables[self.variable]
            node_label = f"{var.name}<={var.domain[self.variable_bound]}"

        graphviz_tree.node(self.graphviz_id, label=node_label, shape="box", style="rounded", margin="0.05,0.05")
        if not self.is_terminal:
            graphviz_tree.edge(self.graphviz_id,self.child_true.graphviz_id,label="T")
            graphviz_tree.edge(self.graphviz_id,self.child_false.graphviz_id,label="F")



class DecisionTree:

    def __init__(self, action_labels : list[str], variables : list["DtVariable"]):
        self.action_labels = action_labels
        self.variables = variables
        self.reset()

    def reset(self):
        self.root = DecisionTreeNode(None)

    def set_depth(self, depth : int):
        self.reset()
        for level in range(depth):
            for node in self.collect_terminals():
                node.add_children()
        self.root.assign_identifiers()

    def get_depth(self) -> int:
        return self.root.get_depth()

    def collect_nodes(self, node_condition : Callable[[DecisionTreeNode], bool] | None = None) -> list[DecisionTreeNode]:
        '''
        Returns a list of nodes in the tree that satisfy the given node_condition. If node_condition is None, returns all nodes in the tree.
        '''
        if node_condition is None:
            node_condition = lambda node : True
        node_queue = [self.root]
        output_nodes = []
        while node_queue:
            node = node_queue.pop(0)
            if node_condition(node):
                output_nodes.append(node)
            node_queue += node.child_nodes
        return output_nodes

    def collect_terminals(self) -> list[DecisionTreeNode]:
        return self.collect_nodes(lambda node : node.is_terminal)

    def collect_nonterminals(self) -> list[DecisionTreeNode]:
        return self.collect_nodes(lambda node : not node.is_terminal)

    def to_list(self) -> list[tuple[int,int,int]]:
        num_nodes = len(self.collect_nodes())
        node_info = [ None for node in range(num_nodes) ]
        for node in self.collect_nodes():
            parent = num_nodes if node.parent is None else node.parent.identifier
            child_true = num_nodes if node.is_terminal else node.child_true.identifier
            child_false = num_nodes if node.is_terminal else node.child_false.identifier
            node_info[node.identifier] = (parent,child_true,child_false)
        return node_info

    def simplify(self, state_valuations : list[list[int]]):
        self.root.simplify(self.variables, state_valuations)

    def to_string(self) -> str:
        return self.root.to_string(self.variables,self.action_labels)

    def to_prism(self, indent_size : int = 2):
        indent = " "*indent_size
        s = ""
        s += "module scheduler\n"
        for terminal in self.collect_terminals():
            action = f"{self.action_labels[terminal.action]}"
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

    def to_graphviz(self) -> graphviz.Digraph:
        logging.getLogger("graphviz").setLevel(logging.WARNING)
        logging.getLogger("graphviz.sources").setLevel(logging.ERROR)
        graphviz_tree = graphviz.Digraph(comment="decision tree")
        self.root.to_graphviz(graphviz_tree,self.variables,self.action_labels)
        return graphviz_tree