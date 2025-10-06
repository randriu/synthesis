import paynt.quotient.quotient

import stormpy
import payntbind
import json
import graphviz

import logging
logger = logging.getLogger(__name__)

class Variable:

    def __init__(self, variable, name, domain):
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
    def domain_min(self):
        return self.domain[0]

    @property
    def domain_max(self):
        return self.domain[-1]

    @property
    def hole_domain(self):
        '''
        Hole domain does not include the maximum value.
        '''
        return self.domain[:-1]

    def __str__(self):
        # domain = "bool" if self.has_boolean_type else f"[{self.domain_min}..{self.domain_max}]"
        domain = f"[{self.domain_min}..{self.domain_max}]"
        return f"{self.name}:{domain}"




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
        return [] if self.is_terminal else [self.child_true,self.child_false]

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
            # and we want to split [0] and [2,3], dtControl can choose 0.5 or 1.5. We expect it will be 0 in this case.
            # Note that dtControl bound decisions are floored when creating the tree helper i.e. 1.5 becomes 1
            while tree_helper_node["chosen"][1] not in variable_domains[self.variable]:
                tree_helper_node["chosen"] = (tree_helper_node["chosen"][0], tree_helper_node["chosen"][1]-1)
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

    # keep_old is used in dtNest, because the node queue is created based on the original node identifiers
    def assign_identifiers(self, identifier=0, keep_old=False):
        if keep_old:
            self.old_identifier = self.identifier
        self.identifier = identifier
        if self.is_terminal:
            return self.identifier
        identifier = self.child_true.assign_identifiers(identifier+1, keep_old=keep_old)
        identifier = self.child_false.assign_identifiers(identifier+1, keep_old=keep_old)
        return identifier

    def associate_holes(self, node_hole_info):
        self.holes = [hole for hole,_,_ in node_hole_info[self.identifier]]
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
        self.variable_bound = hole_assignment[self.variable+1]

        self.child_true.associate_assignment(assignment)
        self.child_false.associate_assignment(assignment)

    def apply_hint(self, subfamily, tree_hint):
        if self.is_terminal or tree_hint.is_terminal:
            return

        variable_hint = tree_hint.variable
        subfamily.hole_set_options(self.holes[0],[variable_hint])
        subfamily.hole_set_options(self.holes[variable_hint+1],[tree_hint.variable_bound])
        self.child_true.apply_hint(subfamily,tree_hint.child_true)
        self.child_false.apply_hint(subfamily,tree_hint.child_false)

    def simplify(self, variables, state_valuations):
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

    def branch_expression(self, variables, true_branch=True):
        var = variables[self.variable]
        if true_branch:
            return f"{var.name}<={var.domain[self.variable_bound]}"
        else:
            return f"{var.name}>{var.domain[self.variable_bound]}"

    def path_expression(self, variables):
        if self.parent is None:
            return []
        return self.parent.path_expression(variables) + [self.parent.branch_expression(variables,true_branch=self.is_true_child)]
    
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
    def graphviz_id(self):
        return str(self.identifier)

    def to_graphviz(self, graphviz_tree, variables, action_labels, highlight_nodes=[]):
        if not self.is_terminal:
            for child in self.child_nodes:
                child.to_graphviz(graphviz_tree,variables,action_labels,highlight_nodes)

        if self.is_terminal:
            node_label = action_labels[self.action]
        else:
            var = variables[self.variable]
            node_label = f"{var.name}<={var.domain[self.variable_bound]}"
        
        if self.identifier in highlight_nodes:
            graphviz_tree.node(self.graphviz_id, label=node_label, shape="box", style="filled", fillcolor="lightgreen", margin="0.05,0.05")
        else:
            graphviz_tree.node(self.graphviz_id, label=node_label, shape="box", style="rounded", margin="0.05,0.05")
        if not self.is_terminal:
            graphviz_tree.edge(self.graphviz_id,self.child_true.graphviz_id,label="T")
            graphviz_tree.edge(self.graphviz_id,self.child_false.graphviz_id,label="F")

    def get_action_for_state(self, quotient, state, state_valuation, nci):
        if self.is_terminal:
            action_index = self.action
            index = 0
            for choice in range(nci[state],nci[state+1]):
                if quotient.choice_to_action[choice] == action_index:
                    return index
                index += 1
            else:
                # TODO as far as I know this happens only because of unreachable states not being included in the tree
                # for now we will treat this by using the __random__ action but it can lead to strange behaviour
                index = 0
                for choice in range(nci[state],nci[state+1]):
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
        
    # in dtNest the tree nodes contain reference indeces to objects from subtree_quotient
    # this needs to be fixed to match the references in the original quotient
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

    def set_depth(self, depth:int):
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
            node.add_children_from_helper(tree_helper, tree_helper[node_id], var_names, var_domains, self.quotient.action_labels)
            node_stack.append((tree_helper[node_id]["children"][0], node.child_true))
            node_stack.append((tree_helper[node_id]["children"][1], node.child_false))

        self.root.assign_identifiers()

        # double check if identifiers correspond to the tree helper
        nodes = self.collect_nodes()
        for node_id, node in enumerate(nodes):
            assert node.is_terminal == tree_helper[node.identifier]["leaf"], f"node {node_id} is terminal: {node.is_terminal}, expected: {tree_helper[node_id]['leaf']}"
            assert node.identifier == tree_helper[node.identifier]["id"], f"node {node_id} has identifier {node.identifier}, expected: {tree_helper[node_id]['id']}"
        

    def collect_nodes(self, node_condition=None):
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

    def collect_terminals(self):
        return self.collect_nodes(lambda node : node.is_terminal)

    def collect_nonterminals(self):
        return self.collect_nodes(lambda node : not node.is_terminal)

    def to_list(self):
        num_nodes = len(self.collect_nodes())
        node_info = [ None for node in range(num_nodes) ]
        for node in self.collect_nodes():
            parent = num_nodes if node.parent is None else node.parent.identifier
            child_true = num_nodes if node.is_terminal else node.child_true.identifier
            child_false = num_nodes if node.is_terminal else node.child_false.identifier
            node_info[node.identifier] = (parent,child_true,child_false)
        return node_info

    def simplify(self, state_valuations):
        self.root.simplify(self.variables, state_valuations)

    def to_string(self):
        return self.root.to_string(self.variables,self.quotient.action_labels)

    def to_prism(self, indent_size=2):
        indent = " "*indent_size
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
        self.root.to_graphviz(graphviz_tree,self.variables,self.quotient.action_labels,highlight_nodes)
        return graphviz_tree
    
    def to_scheduler_json(self, reachable_states=None):
        if reachable_states is None:
            reachable_states = stormpy.BitVector(self.quotient.quotient_mdp.nr_states, True)
        scheduler = payntbind.synthesis.create_scheduler(self.quotient.quotient_mdp.nr_states)
        nci = self.quotient.quotient_mdp.nondeterministic_choice_indices.copy()
        for state in range(self.quotient.quotient_mdp.nr_states):
            if self.quotient.state_is_relevant_bv.get(state) and reachable_states.get(state):
                action_index = self.root.get_action_for_state(self.quotient, state, self.quotient.relevant_state_valuations[state], nci)
            else:
                # this should leave undefined in the scheduler and will be filtered below
                payntbind.synthesis.set_dont_care_state_for_scheduler(scheduler, state, 0, False) # trying to filter out these states through Storm
                continue
            scheduler_choice = stormpy.storage.SchedulerChoice(action_index)
            scheduler.set_choice(scheduler_choice, state)
            
        json_scheduler_full = json.loads(scheduler.to_json_str(self.quotient.quotient_mdp, skip_dont_care_states=True))

        json_str = json.dumps(json_scheduler_full, indent=4)
        return json_str

    
    def append_tree_as_subtree(self, new_subtree, subtree_root_node_id, subtree_quotient):
        subtree_root_node = self.collect_nodes(lambda node : node.identifier == subtree_root_node_id)
        assert len(subtree_root_node) == 1, f"subtree root node id {subtree_root_node_id} not found in decision tree"
        subtree_root_node = subtree_root_node[0]

        all_current_nodes = self.collect_nodes()
        new_subtree.root.assign_identifiers(identifier=len(all_current_nodes)+1)
        new_subtree.root.fix_with_respect_to_quotient(subtree_quotient, self.quotient)

        parent = subtree_root_node.parent
        if parent.child_true.identifier == subtree_root_node.identifier:
            parent.child_true = new_subtree.root
        else:
            parent.child_false = new_subtree.root



class MdpQuotient(paynt.quotient.quotient.Quotient):

    # label for action executing a random action selection
    DONT_CARE_ACTION_LABEL = "__random__"
    # if true, an explicit action executing a random choice of an available action will be added to each state
    add_dont_care_action = False
    # if true, irrelevant states will not be considered for tree mapping
    filter_deterministic_states = True

    @classmethod
    # TODO only get this for relevant states for dtnest if possible
    def get_state_valuations(cls, model):
        ''' Identify variable names and extract state valuation in the same order. '''
        assert model.has_state_valuations(), "model has no state valuations"
        # get name
        sv = model.state_valuations
        variable_name = None
        state_valuations = []
        for state in range(model.nr_states):
            valuation = json.loads(str(sv.get_json(state)))
            if variable_name is None:
                variable_name = list(valuation.keys())
            valuation = [valuation[var_name] for var_name in variable_name]
            state_valuations.append(valuation)
        return variable_name,state_valuations

    def __init__(self, mdp, specification):
        super().__init__(specification=specification)

        # mask of relevant states: non-absorbing states with more than one action
        self.state_is_relevant = None
        # bitvector of relevant states
        self.state_is_relevant_bv = None

        # list of relevant variables: variables having at least two different options on relevant states
        self.variables = None
        # for every state, a valuation of relevant variables
        self.relevant_state_valuations = None
        # decision tree obtained after reset_tree
        self.decision_tree = None

        # deprecated
        # updated = payntbind.synthesis.restoreActionsInAbsorbingStates(mdp)
        # if updated is not None: mdp = updated

        # identify relevant states
        self.state_is_relevant = [True for state in range(mdp.nr_states)]
        state_is_absorbing = self.identify_absorbing_states(mdp)
        self.state_is_relevant = [relevant and not state_is_absorbing[state] for state,relevant in enumerate(self.state_is_relevant)]

        if MdpQuotient.filter_deterministic_states:
            state_has_actions = self.identify_states_with_actions(mdp)
            self.state_is_relevant = [relevant and state_has_actions[state] for state,relevant in enumerate(self.state_is_relevant)]
        self.state_is_relevant_bv = stormpy.BitVector(mdp.nr_states)
        [self.state_is_relevant_bv.set(state,value) for state,value in enumerate(self.state_is_relevant)]
        logger.debug(f"MDP has {self.state_is_relevant_bv.number_of_set_bits()}/{self.state_is_relevant_bv.size()} relevant states")

        action_labels,_ = payntbind.synthesis.extractActionLabels(mdp)
        if MdpQuotient.DONT_CARE_ACTION_LABEL not in action_labels and MdpQuotient.add_dont_care_action:
            logger.debug("adding explicit don't-care action to relevant states...")
            mdp = payntbind.synthesis.addDontCareAction(mdp,self.state_is_relevant_bv)

        self.quotient_mdp = mdp
        self.choice_destinations = payntbind.synthesis.computeChoiceDestinations(mdp)
        self.action_labels,self.choice_to_action = payntbind.synthesis.extractActionLabels(mdp)
        logger.info(f"MDP has {len(self.action_labels)} actions")
        # TODO filter irrelevant actions?

        # get variable domains on relevant states
        variable_name,state_valuations = self.get_state_valuations(mdp)
        num_variables = len(variable_name)
        variable_domain = [set() for variable in range(num_variables)]
        for state in self.state_is_relevant_bv:
            valuation = state_valuations[state]
            for variable in range(num_variables):
                variable_domain[variable].add(valuation[variable])
        variable_domain = [sorted(domain) for domain in variable_domain]

        # filter variables having only one option
        variable_mask = [len(domain) > 1 for domain in variable_domain]
        variable_name = [value for variable,value in enumerate(variable_name) if variable_mask[variable]]
        variable_domain = [value for variable,value in enumerate(variable_domain) if variable_mask[variable]]
        # we filter unused variables from state valuations: this means that multiple states can now have the same "valuation"
        state_valuations = [
            [value for variable,value in enumerate(valuations) if variable_mask[variable]]
            for valuations in state_valuations
        ]

        self.variables = [Variable(variable,name,variable_domain[variable]) for variable,name in enumerate(variable_name)]
        self.relevant_state_valuations = state_valuations
        logger.debug(f"found the following {len(self.variables)} variables: {[str(v) for v in self.variables]}")


    def get_variable_id(self, var):
        for id, variable in enumerate(self.variables):
            if variable.name == var:
                break
        return id
    
    def get_states_satisfying_predicate(self, node, current_states, leq=True):
        bound = self.variables[node.variable].domain[node.variable_bound]
        for state,state_valuation in enumerate(self.relevant_state_valuations):
            if not current_states.get(state):
                continue
            if leq and state_valuation[node.variable] > bound:
                current_states.set(state, False)
            elif not leq and state_valuation[node.variable] <= bound:
                current_states.set(state, False)
        return current_states
    
    def get_state_space_for_tree_helper_node(self, node_id):
        node = self.tree_helper_tree.collect_nodes(lambda node : node.identifier == node_id)[0]
        current_node = node
        states = stormpy.storage.BitVector(self.quotient_mdp.nr_states, True)
        while current_node.parent is not None:
            parent_node = current_node.parent
            if parent_node.child_true.identifier == current_node.identifier:
                states = self.get_states_satisfying_predicate(parent_node, states, leq=True)
            else:
                states = self.get_states_satisfying_predicate(parent_node, states, leq=False)
            current_node = parent_node
        return states
    
    def get_chosen_action_for_state_from_tree_helper(self, state):
        state_valuation = self.relevant_state_valuations[state]
        current_node = self.tree_helper_tree.root
        while not current_node.is_terminal:
            bound = self.variables[current_node.variable].domain[current_node.variable_bound]
            if state_valuation[current_node.variable] <= bound:
                current_node = current_node.child_true
            else:
                current_node = current_node.child_false
        return self.action_labels[current_node.action]
    
    def get_selected_choices_from_tree_helper(self, state_to_exclude):
        selected_choices = stormpy.storage.BitVector(self.quotient_mdp.nr_choices, False)
        mdp_nci = self.quotient_mdp.nondeterministic_choice_indices.copy()
        for state in range(self.quotient_mdp.nr_states):
            if state_to_exclude.get(state) or self.state_is_relevant_bv.get(state) == False:
                for choice in range(mdp_nci[state],mdp_nci[state+1]):
                    selected_choices.set(choice, True)
                continue
            chosen_action_label = self.get_chosen_action_for_state_from_tree_helper(state)
            action_index = self.action_labels.index(chosen_action_label)
            for choice in range(mdp_nci[state],mdp_nci[state+1]):
                if self.choice_to_action[choice] == action_index:
                    selected_choices.set(choice, True)
                    break
            else:
                # TODO as far as I know this happens only because of unreachable states not being included in the tree
                # for now we will treat this by using the __random__ action but it can lead to strange behaviour
                for choice in range(mdp_nci[state],mdp_nci[state+1]):
                    if self.action_labels[self.choice_to_action[choice]] == "__random__":
                        selected_choices.set(choice, True)
                        break
                continue
                assert False, f"no choice for state {state} even though action {chosen_action_label} was chosen"

        return selected_choices


    def scheduler_json_to_choices(self, scheduler_json, discard_unreachable_states=False):
        variable_name,state_valuations = self.get_state_valuations(self.quotient_mdp)
        nci = self.quotient_mdp.nondeterministic_choice_indices.copy()
        assert self.quotient_mdp.nr_states == len(scheduler_json)
        state_to_choice = self.empty_scheduler()
        for state_decision in scheduler_json:
            valuation = [state_decision["s"][name] for name in variable_name]
            for state,state_valuation in enumerate(state_valuations):
                if valuation == state_valuation:
                    break
            else:
                assert False, "state valuation not found"

            actions = state_decision["c"]
            assert len(actions) == 1
            action_labels = actions[0]["labels"]
            assert len(action_labels) <= 1
            if len(action_labels) == 0:
                state_to_choice[state] = nci[state]
                continue
            action = self.action_labels.index(action_labels[0])
            # find a choice that executes this action
            for choice in range(nci[state],nci[state+1]):
                if self.choice_to_action[choice] == action:
                    state_to_choice[state] = choice
                    break
            else:
                assert False, "action is not available in the state"
        # enable implicit actions
        for state,choice in enumerate(state_to_choice):
            if choice is None:
                logger.warning(f"WARNING: scheduler has no action for state {state}")
                state_to_choice[state] = nci[state]

        if discard_unreachable_states:
            state_to_choice = self.discard_unreachable_choices(state_to_choice)
        # keep only relevant states
        state_to_choice = [choice if self.state_is_relevant[state] else None for state,choice in enumerate(state_to_choice)]
        choices = self.state_to_choice_to_choices(state_to_choice)

        scheduler_json_relevant = []
        for state_decision in scheduler_json:
            valuation = [state_decision["s"][name] for name in variable_name]
            for state,state_valuation in enumerate(state_valuations):
                if valuation == state_valuation:
                    break
            if state_to_choice[state] is None:
                continue
            scheduler_json_relevant.append(state_decision)

        return choices,scheduler_json_relevant
    
    # gets all choices that represent random action, used to compute the value of uniformly random scheduler
    def get_random_choices(self):
        nci = self.quotient_mdp.nondeterministic_choice_indices.copy()
        state_to_choice = self.empty_scheduler()
        random_action = self.action_labels.index(MdpQuotient.DONT_CARE_ACTION_LABEL)
        for state in range(self.quotient_mdp.nr_states):
            # find a choice that executes this action
            for choice in range(nci[state],nci[state+1]):
                if self.choice_to_action[choice] == random_action:
                    state_to_choice[state] = choice
                    break
        for state,choice in enumerate(state_to_choice):
            if choice is None:
                state_to_choice[state] = nci[state]

        choices = self.state_to_choice_to_choices(state_to_choice)

        return choices
    
    def build_tree_helper_tree(self, tree_helper=None):
        if tree_helper is None:
            tree_helper = self.tree_helper
        helper_tree = DecisionTree(self,self.variables)
        helper_tree.build_from_tree_helper(tree_helper)
        return helper_tree
    
    # unfixed_states is a bitvector of states that should be left unfixed in the submdp
    def get_submdp_from_unfixed_states(self, unfixed_states=None):
        if unfixed_states is None:
            unfixed_states = stormpy.storage.BitVector(self.quotient_mdp.nr_states, False)
        selected_choices = self.get_selected_choices_from_tree_helper(unfixed_states)
        submdp = self.build_from_choice_mask(selected_choices)
        return submdp
    
    # in dtNest, there might be an MDP for a subtree with no relevant states, in that case we want to replace this subtree with a random action
    def create_uniform_random_tree(self):
        decision_tree = DecisionTree(self,self.variables)
        decision_tree.random_tree()
        return decision_tree


    def reset_tree(self, depth, enable_harmonization=True):
        '''
        Rebuild the decision tree template, the design space and the coloring.
        '''
        logger.debug(f"building tree of depth {depth}")

        num_actions = len(self.action_labels)
        dont_care_action = num_actions
        if MdpQuotient.DONT_CARE_ACTION_LABEL in self.action_labels:
            dont_care_action = self.action_labels.index(MdpQuotient.DONT_CARE_ACTION_LABEL)

        self.decision_tree = DecisionTree(self,self.variables)
        self.decision_tree.set_depth(depth)

        variables = self.decision_tree.variables
        variable_name = [v.name for v in variables]
        variable_domain = [v.domain for v in variables]
        tree_list = self.decision_tree.to_list()
        self.coloring = payntbind.synthesis.ColoringSmt(
            self.quotient_mdp.nondeterministic_choice_indices, self.choice_to_action,
            num_actions, dont_care_action,
            self.quotient_mdp.state_valuations, self.state_is_relevant_bv,
            variable_name, variable_domain, tree_list, enable_harmonization
        )
        # return
        self.coloring.enableStateExploration(self.quotient_mdp)

        # reconstruct the family
        hole_info = self.coloring.getFamilyInfo()
        self.family = paynt.family.family.Family()
        self.is_action_hole = [False for hole in hole_info]
        self.is_decision_hole = [False for hole in hole_info]
        self.is_variable_hole = [False for hole in hole_info]
        domain_max = max([len(domain) for domain in variable_domain])
        bound_domain = list(range(domain_max))
        node_hole_info = [[] for node in self.decision_tree.collect_nodes()]
        for hole,info in enumerate(hole_info):
            node,hole_name,hole_type = info
            node_hole_info[node].append( (hole,hole_name,hole_type) )
            if hole_type == "__action__":
                self.is_action_hole[hole] = True
                option_labels = self.action_labels
            elif hole_type == "__decision__":
                self.is_decision_hole[hole] = True
                option_labels = variable_name
            else:
                self.is_variable_hole[hole] = True
                variable = variable_name.index(hole_type)
                option_labels = variables[variable].hole_domain
            self.family.add_hole(hole_name, option_labels)
        self.decision_tree.root.associate_holes(node_hole_info)

    def build_unsat_result(self):
        spec_result = paynt.verification.property_result.MdpSpecificationResult()
        spec_result.constraints_result = paynt.verification.property_result.ConstraintsResult([])
        spec_result.optimality_result = paynt.verification.property_result.MdpOptimalityResult(None)
        spec_result.evaluate(None)
        spec_result.can_improve = False
        return spec_result

    def build(self, family):
        if family.parent_info is None:
            choices = self.coloring.selectCompatibleChoices(family.family)
        else:
            choices = self.coloring.selectCompatibleChoices(family.family, family.parent_info.selected_choices)
        assert choices.number_of_set_bits() > 0

        # proceed as before
        family.selected_choices = choices
        family.mdp = self.build_from_choice_mask(choices)
        family.mdp.family = family


    def are_choices_consistent(self, choices, family):
        ''' Separate method for profiling purposes. '''
        consistent,hole_selection = self.coloring.areChoicesConsistent(choices, family.family)
        for hole,options in enumerate(hole_selection):
            assert len(options) == len(set(options)), str(hole_selection)
            for option in options:
                assert option in family.hole_options(hole), \
                f"option {option} for hole {hole} ({mdp.family.hole_name(hole)}) is not in the family"
        return consistent,hole_selection


    def scheduler_is_consistent(self, mdp, prop, result):
        ''' Get hole options involved in the scheduler selection. '''
        scheduler = result.scheduler
        assert scheduler.memoryless and scheduler.deterministic
        state_to_choice = self.scheduler_to_state_to_choice(mdp, scheduler)
        choices = self.state_to_choice_to_choices(state_to_choice)
        if self.specification.is_single_property:
            mdp.family.scheduler_choices = choices
        consistent,hole_selection = self.are_choices_consistent(choices, mdp.family)
        return hole_selection, consistent


    def scheduler_scores(self, mdp, prop, result, selection):
        inconsistent_assignments = {hole:options for hole,options in enumerate(selection) if len(options) > 1 }
        assert len(inconsistent_assignments) > 0, f"obtained selection with no inconsistencies: {selection}"
        inconsistent_action_holes = [(hole,options) for hole,options in inconsistent_assignments.items() if self.is_action_hole[hole]]
        inconsistent_decision_holes = [(hole,options) for hole,options in inconsistent_assignments.items() if self.is_decision_hole[hole]]
        inconsistent_variable_holes = [(hole,options) for hole,options in inconsistent_assignments.items() if self.is_variable_hole[hole]]

        # choose one splitter
        splitter = None
        # try action or decision holes first
        if len(inconsistent_action_holes) > 0:
            splitter = inconsistent_action_holes[0][0]
        elif len(inconsistent_decision_holes) > 0:
            splitter = inconsistent_decision_holes[0][0]
        else:
            splitter = inconsistent_variable_holes[0][0]
        assert splitter is not None, "splitter not set"
        # force the score of the selected splitter
        return {splitter:10}


    def split(self, family):

        mdp = family.mdp
        assert not mdp.is_deterministic

        # split family wrt last undecided result
        result = family.analysis_result.undecided_result()
        hole_assignments = result.primary_selection
        scores = self.scheduler_scores(mdp, result.prop, result.primary.result, result.primary_selection)

        splitters = self.holes_with_max_score(scores)
        splitter = splitters[0]
        if self.is_action_hole[splitter] or self.is_decision_hole[splitter]:
            assert len(hole_assignments[splitter]) > 1
            core_suboptions,other_suboptions = self.suboptions_enumerate(mdp, splitter, hole_assignments[splitter])
        else:
            subfamily_options = family.hole_options(splitter)

            # split in half
            index_split = len(subfamily_options)//2

            # split by inconsistent options
            option_1 = hole_assignments[splitter][0]; index_1 = subfamily_options.index(option_1)
            option_2 = hole_assignments[splitter][1]; index_2 = subfamily_options.index(option_2)
            index_split = index_2

            core_suboptions = [subfamily_options[:index_split], subfamily_options[index_split:]]

            for options in core_suboptions: assert len(options) > 0
            other_suboptions = []

        if len(other_suboptions) == 0:
            suboptions = core_suboptions
        else:
            suboptions = [other_suboptions] + core_suboptions  # DFS solves core first

        # construct corresponding subfamilies
        parent_info = family.collect_parent_info(self.specification)
        parent_info.analysis_result = family.analysis_result
        parent_info.scheduler_choices = family.scheduler_choices
        # parent_info.unsat_core_hint = self.coloring.unsat_core.copy()
        subfamilies = family.split(splitter,suboptions)
        assert family.size == sum([family.size for family in subfamilies])
        for subfamily in subfamilies:
            subfamily.add_parent_info(parent_info)
        return subfamilies
