import paynt.quotient.quotient

import stormpy
import payntbind
import json

import logging
logger = logging.getLogger(__name__)


class Variable:

    def __init__(self, name, model):
        self.name = name

        assert model.has_state_valuations(), "model has no state valuations"
        domain = set()
        for state in range(model.nr_states):
            valuation = json.loads(str(model.state_valuations.get_json(state)))
            value = valuation[name]
            domain.add(value)
        domain = list(domain)
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

    @classmethod
    def from_model(cls, model):
        assert model.has_state_valuations(), "model has no state valuations"
        valuation = json.loads(str(model.state_valuations.get_json(0)))
        variables = [Variable(var,model) for var in valuation]
        variables = [v for v in variables if len(v.domain) > 1]
        return variables



class DecisionTreeNode:

    def __init__(self, parent):
        self.parent = parent
        self.variable_index = None
        self.child_false = None
        self.child_true = None
        self.hole = None
        self.identifier = None

    @property
    def is_terminal(self):
        return self.variable_index is None

    @property
    def child_nodes(self):
        return [] if self.is_terminal else [self.child_true,self.child_false]

    @property
    def is_true_child(self):
        return self is self.parent.child_true

    def set_variable(self, variable_index:int):
        '''
        Associate (an index of) a variable with the node.
        '''
        if self.is_terminal:
            self.child_false = DecisionTreeNode(self)
            self.child_true = DecisionTreeNode(self)
        self.variable_index = variable_index

    def set_variable_by_name(self, variable_name:str, decision_tree):
        variable_index = [variable.name for variable in decision_tree.variables].index(variable_name)
        self.set_variable(variable_index)

    def create_hole(self, family, action_labels, variables):
        '''
        Create a unique hole associated with this node. Terminal nodes are associated with actions selection, where
        additional "don't care" action is added.
        '''
        # create a unique hole index based on the current number of holes
        self.hole = family.num_holes
        if self.is_terminal:
            prefix = "A"
            option_labels = action_labels
        else:
            prefix = variables[self.variable_index].name
            option_labels = variables[self.variable_index].hole_domain
        hole_name = f"{prefix}_{self.hole}"
        family.add_hole(hole_name, option_labels)

    def collect_bounds(self):
        lower_bounds = []
        upper_bounds = []
        node = self
        while node.parent is not None:
            if node.is_true_child:
                bounds = upper_bounds
            else:
                bounds = lower_bounds
            bounds.append(node.parent.hole)
            node = node.parent
        return lower_bounds,upper_bounds

    def assign_identifiers(self, identifier):
        self.identifier = identifier
        if self.is_terminal:
            return self.identifier
        identifier = self.child_true.assign_identifiers(identifier+1)
        identifier = self.child_false.assign_identifiers(identifier+1)
        return identifier


class DecisionTree:

    def __init__(self, model):
        self.variables = Variable.from_model(model)
        logger.debug(f"found the following variables: {[str(v) for v in self.variables]}")
        self.reset()

    def reset(self):
        self.root = DecisionTreeNode(None)

    def set_depth(self, depth:int):
        self.reset()
        for level in range(depth):
            for node in self.collect_terminals():
                node.set_variable(0)

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
        node_condition = lambda node : node.is_terminal
        return self.collect_nodes(node_condition)

    def collect_nonterminals(self):
        node_condition = lambda node : not node.is_terminal
        return self.collect_nodes(node_condition)

    def create_family(self, action_labels):
        family = paynt.family.family.Family()
        for node in self.collect_nodes():
            node.create_hole(family, action_labels, self.variables)
        return family

    def to_list(self):
        self.root.assign_identifiers(0)
        num_nodes = len(self.collect_nodes())
        node_info = [ None for node in range(num_nodes) ]
        for node in self.collect_nodes():
            parent = num_nodes if node.parent is None else node.parent.identifier
            child_true = num_nodes if node.is_terminal else node.child_true.identifier
            child_false = num_nodes if node.is_terminal else node.child_false.identifier
            node_info[node.identifier] = (parent,child_true,child_false)
        return node_info



class MdpQuotient(paynt.quotient.quotient.Quotient):

    def __init__(self, mdp, specification):
        super().__init__(specification=specification)
        updated = payntbind.synthesis.restoreActionsInAbsorbingStates(mdp)
        if updated is not None: mdp = updated
        self.quotient_mdp = mdp
        self.choice_destinations = payntbind.synthesis.computeChoiceDestinations(mdp)
        self.action_labels,self.choice_to_action = payntbind.synthesis.extractActionLabels(mdp)
        self.decision_tree = DecisionTree(mdp)

        self.coloring = None
        self.design_space = None

        self.is_action_hole = None

    def decide(self, node, var_name):
        node.set_variable_by_name(var_name,self.decision_tree)

    '''
    Build the design space and coloring corresponding to the current decision tree.
    '''
    def build_coloring(self):
        family = self.decision_tree.create_family(self.action_labels)
        # print("family = ", family)

        hole_bounds = [None for hole in range(family.num_holes)]
        for node in self.decision_tree.collect_nodes():
            hole_bounds[node.hole] = node.collect_bounds()
        # print("hole bounds = ", hole_bounds)

        hole_variable = ["" for _ in range(family.num_holes)]
        hole_domain = [[] for h in range(family.num_holes)]
        for node in self.decision_tree.collect_nonterminals():
            hole_variable[node.hole] = self.decision_tree.variables[node.variable_index].name
            hole_domain[node.hole] = family.hole_to_option_labels[node.hole]
        # print("hole variables = ", hole_variable)
        # print("hole domain = ", hole_domain)

        self.is_action_hole = [var == "" for var in hole_variable]
        self.coloring = payntbind.synthesis.ColoringSmt(
            self.quotient_mdp.nondeterministic_choice_indices, self.choice_to_action,
            self.quotient_mdp.state_valuations,
            hole_variable, hole_bounds, hole_domain
        )
        self.design_space = paynt.family.family.DesignSpace(family)

    def build_coloring_full(self):

        variables = self.decision_tree.variables
        variable_name = [v.name for v in variables]
        variable_domain = [v.domain for v in variables]
        tree_list = self.decision_tree.to_list()
        self.coloring = payntbind.synthesis.ColoringSmtFull(
            self.quotient_mdp.nondeterministic_choice_indices, self.choice_to_action, 
            self.quotient_mdp.state_valuations,
            variable_name, variable_domain, tree_list
        )
        # reconstruct the family
        family = paynt.family.family.Family()
        for hole_name,hole_type in self.coloring.getFamilyInfo():
            if hole_type == "__action__":
                option_labels = self.action_labels
            elif hole_type == "__decision__":
                option_labels = variable_name
            else:
                variable = variable_name.index(hole_type)
                option_labels = variables[variable].hole_domain
            family.add_hole(hole_name, option_labels)
        self.design_space = paynt.family.family.DesignSpace(family)

    def build_unsat_result(self):
        constraints_result = paynt.verification.property_result.ConstraintsResult([])
        optimality_result = paynt.verification.property_result.MdpOptimalityResult(None)
        optimality_result.can_improve = False
        analysis_result = paynt.verification.property_result.MdpSpecificationResult(constraints_result,optimality_result)
        return analysis_result

    def build(self, family):
        # family.parent_info = None
        if family.parent_info is None:
            choices = self.coloring.selectCompatibleChoices(family.family)
        else:
            choices = self.coloring.selectCompatibleChoices(family.family, family.parent_info.selected_choices)
        if choices.number_of_set_bits() == 0:
            family.mdp = None
            family.analysis_result = self.build_unsat_result()
            return

        # proceed as before
        family.selected_choices = choices
        family.mdp = self.build_from_choice_mask(choices)
        # assert family.mdp.model.nr_choices == self.quotient_mdp.nr_choices
        family.mdp.design_space = family


    def areChoicesConsistent(self, choices, mdp):
        return self.coloring.areChoicesConsistent(choices, mdp.design_space.family)

    def scheduler_is_consistent(self, mdp, prop, result):
        ''' Get hole options involved in the scheduler selection. '''

        scheduler = result.scheduler
        assert scheduler.memoryless and scheduler.deterministic
        state_to_choice = self.scheduler_to_state_to_choice(mdp, scheduler)
        choices = self.state_to_choice_to_choices(state_to_choice)
        consistent,hole_selection = self.areChoicesConsistent(choices, mdp)
        # print(consistent,hole_selection)

        # convert selection to actual hole options
        # for hole,values in enumerate(hole_selection):
        #     if self.is_action_hole[hole]:
        #         continue
        #     hole_selection[hole] = [self.design_space.hole_to_option_labels[hole].index(value) for value in values]
        for hole,options in enumerate(hole_selection):
            for option in options:
                assert option in mdp.design_space.hole_options(hole), \
                f"option {option} for hole {hole} ({mdp.design_space.hole_name(hole)}) is not in the family"

        return hole_selection, consistent


    def scheduler_get_quantitative_values(self, mdp, prop, result, selection):
        '''
        :return choice values
        :return expected visits
        :return hole scores
        '''

        inconsistent_assignments = {hole:options for hole,options in enumerate(selection) if len(options) > 0 }
        inconsistent_action_holes = [(hole,options) for hole,options in inconsistent_assignments.items() if self.is_action_hole[hole]]
        inconsistent_variable_holes = [(hole,options) for hole,options in inconsistent_assignments.items() if not self.is_action_hole[hole]]

        # choose splitter and force its score
        splitter = None

        # try action holes first
        for hole,options in inconsistent_action_holes:
            if len(options) > 1:
                splitter = hole
                break
        else:
            for hole,values in inconsistent_variable_holes:
                # pick an arbitrary value and find the corresponding hole option
                value = values[0]
                for option in mdp.design_space.hole_options(hole):
                    if mdp.design_space.hole_to_option_labels[hole][option] == value:
                        splitter = hole
                        selection[splitter] = [option]
                        # TODO make sure this selection will split this hole in half
                        break
                else:
                    assert False, "this should not occur..."
        assert splitter is not None, "inconsistent action hole with exactly 1 option?"

        inconsistent_differences = {splitter:10}
        return None, None, inconsistent_differences

    def split(self, family):

        mdp = family.mdp
        assert not mdp.is_deterministic

        # split family wrt last undecided result
        result = family.analysis_result.undecided_result()
        hole_assignments = result.primary_selection
        scores = result.primary_scores

        splitters = self.holes_with_max_score(scores)
        splitter = splitters[0]
        if self.is_action_hole[splitter]:
            assert len(hole_assignments[splitter]) > 1
            core_suboptions,other_suboptions = self.suboptions_enumerate(mdp, splitter, hole_assignments[splitter])
        else:
            assert len(hole_assignments[splitter]) == 1
            splitter_option = hole_assignments[splitter][0]
            subfamily_options = family.hole_options(splitter)
            index = subfamily_options.index(splitter_option)
            if index == 0:
                core_suboptions = [subfamily_options[:1], subfamily_options[1:]]
            else:
                core_suboptions = [subfamily_options[:index], subfamily_options[index:]]
            for options in core_suboptions: assert len(options) > 0
            other_suboptions = []

        new_design_space = mdp.design_space.copy()
        if len(other_suboptions) == 0:
            suboptions = core_suboptions
        else:
            suboptions = [other_suboptions] + core_suboptions  # DFS solves core first

        # construct corresponding design subspaces
        design_subspaces = []
        family.splitter = splitter
        parent_info = family.collect_parent_info(self.specification)
        for suboption in suboptions:
            subholes = new_design_space.subholes(splitter, suboption)
            design_subspace = paynt.family.family.DesignSpace(subholes, parent_info)
            design_subspace.hole_set_options(splitter, suboption)
            design_subspaces.append(design_subspace)

        return design_subspaces
