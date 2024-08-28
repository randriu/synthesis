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
        logger.debug(f"found the following {len(self.variables)} variables: {[str(v) for v in self.variables]}")
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

    def collect_variables(self):
        node_to_variable = None
        nodes = self.collect_nodes()
        node_to_variable = [len(self.variables) for node in range(len(nodes))]
        for node in nodes:
            if node.variable_index is not None:
                node_to_variable[node.identifier] = node.variable_index
        return node_to_variable


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
    def build_coloring(self, use_generic_template=True):
        # logger.debug("building coloring...")
        variables = self.decision_tree.variables
        variable_name = [v.name for v in variables]
        variable_domain = [v.domain for v in variables]
        tree_list = self.decision_tree.to_list()

        node_to_variable = []
        if not use_generic_template:
            node_to_variable = self.decision_tree.collect_variables()
        self.coloring = payntbind.synthesis.ColoringSmt(
            self.quotient_mdp, variable_name, variable_domain, tree_list, node_to_variable
        )

        # reconstruct the family
        hole_info = self.coloring.getFamilyInfo()
        family = paynt.family.family.Family()
        self.is_action_hole = [False for hole in hole_info]
        self.is_decision_hole = [False for hole in hole_info]
        self.is_bound_hole = [False for hole in hole_info]
        self.is_variable_hole = [False for hole in hole_info]
        domain_max = max([len(domain) for domain in variable_domain])
        bound_domain = list(range(domain_max))
        for hole,info in enumerate(hole_info):
            hole_name,hole_type = info
            if hole_type == "__action__":
                self.is_action_hole[hole] = True
                option_labels = self.action_labels
            elif hole_type == "__decision__":
                self.is_decision_hole[hole] = True
                option_labels = variable_name
            elif hole_type == "__bound__":
                self.is_bound_hole[hole] = True
                option_labels = bound_domain
            else:
                self.is_variable_hole[hole] = True
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
        # logger.debug("building sub-MDP...")
        # print("\nfamily = ", family, flush=True)
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
        family.mdp.design_space = family


    def scheduler_is_consistent(self, mdp, prop, result):
        ''' Get hole options involved in the scheduler selection. '''

        scheduler = result.scheduler
        assert scheduler.memoryless and scheduler.deterministic
        state_to_choice = self.scheduler_to_state_to_choice(mdp, scheduler)
        choices = self.state_to_choice_to_choices(state_to_choice)
        consistent,hole_selection = self.coloring.areChoicesConsistent(choices, mdp.design_space.family)
        # print(consistent,hole_selection)

        # threshold hack
        # import math
        # choice_values = self.choice_values(mdp.model, self.get_property(), result.get_values())
        # ndi = mdp.model.nondeterministic_choice_indices
        # state_relevant = [False] * self.quotient_mdp.nr_states
        # state_diff = []
        # for state in range(mdp.model.nr_states):
        #     state_min = state_max = choice_values[ndi[state]]
        #     for choice in range(ndi[state]+1,ndi[state+1]):
        #         if choice_values[choice] < state_min:
        #             state_min = choice_values[choice]
        #         if choice_values[choice] > state_max:
        #             state_max = choice_values[choice]
        #     divisor = None
        #     max_diff = state_max-state_min
        #     if math.fabs(state_min) > 0.001:
        #         state_diff = math.fabs(max_diff/state_min)
        #     elif math.fabs(state_max) > 0.001:
        #         state_diff = math.fabs(max_diff/state_max)
        #     else:
        #         state_diff = 0
        #     if state_diff > 0:
        #         state_relevant[mdp.quotient_state_map[state]] = True
        # consistent,hole_selection = self.coloring.areChoicesConsistentRelevant(choices, mdp.design_space.family, state_relevant)

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
        # return None,None,None

        inconsistent_assignments = {hole:options for hole,options in enumerate(selection) if len(options) > 1 }
        if len(inconsistent_assignments) == 0:
            assert False, f"obtained selection with no inconsistencies: {selection}"
            inconsistent_assignments = {hole:options for hole,options in enumerate(selection) if len(options) > 0 }
        inconsistent_action_holes = [(hole,options) for hole,options in inconsistent_assignments.items() if self.is_action_hole[hole]]
        inconsistent_decision_holes = [(hole,options) for hole,options in inconsistent_assignments.items() if self.is_decision_hole[hole]]
        inconsistent_bound_holes = [(hole,options) for hole,options in inconsistent_assignments.items() if self.is_bound_hole[hole]]
        inconsistent_variable_holes = [(hole,options) for hole,options in inconsistent_assignments.items() if self.is_variable_hole[hole]]

        # choose one splitter and force its score
        splitter = None

        # try action or decision holes first
        if len(inconsistent_action_holes) > 0:
            splitter = inconsistent_action_holes[0][0]
        elif len(inconsistent_decision_holes) > 0:
            splitter = inconsistent_decision_holes[0][0]
        elif len(inconsistent_bound_holes) > 0:
            splitter = inconsistent_bound_holes[0][0]
        else:
            splitter,options = inconsistent_variable_holes[0]
            # selection[splitter] = [options[0]]
        assert splitter is not None, "splitter not set"

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
        if self.is_action_hole[splitter] or self.is_decision_hole[splitter]:
            assert len(hole_assignments[splitter]) > 1
            core_suboptions,other_suboptions = self.suboptions_enumerate(mdp, splitter, hole_assignments[splitter])
        else:
            # split in half
            subfamily_options = family.hole_options(splitter)
            index_half = len(subfamily_options)//2
            core_suboptions = [subfamily_options[:index_half], subfamily_options[index_half:]]
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
