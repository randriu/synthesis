import paynt.quotient.quotient

import stormpy
import payntbind
import json

import logging
logger = logging.getLogger(__name__)

class Variable:

    def __init__(self, variable, name, state_valuations):
        self.name = name
        domain = set()
        for state,valuation in enumerate(state_valuations):
            value = valuation[variable]
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
        sv = model.state_valuations
        valuation = json.loads(str(sv.get_json(0)))
        variable_name = [var_name for var_name in valuation]
        state_valuations = []
        for state in range(model.nr_states):
            valuation = json.loads(str(sv.get_json(state)))
            valuation = [valuation[var_name] for var_name in variable_name]
            state_valuations.append(valuation)
        variables = [Variable(var,var_name,state_valuations) for var,var_name in enumerate(variable_name)]
        variables = [v for v in variables if len(v.domain) > 1]
        return variables



class DecisionTreeNode:

    def __init__(self, parent):
        self.parent = parent
        self.variable_index = None
        self.child_true = None
        self.child_false = None
        self.identifier = None
        self.holes = None
        self.hole_assignment = None

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

    def assign_identifiers(self, identifier=0):
        self.identifier = identifier
        if self.is_terminal:
            return self.identifier
        identifier = self.child_true.assign_identifiers(identifier+1)
        identifier = self.child_false.assign_identifiers(identifier+1)
        return identifier

    def associate_holes(self, node_hole_info):
        self.holes = [hole for hole,_,_ in node_hole_info[self.identifier]]
        if self.is_terminal:
            return
        self.child_true.associate_holes(node_hole_info)
        self.child_false.associate_holes(node_hole_info)

    def associate_assignment(self, assignment):
        self.hole_assignment = [assignment.hole_options(hole)[0] for hole in self.holes]
        if self.is_terminal:
            return
        self.child_true.associate_assignment(assignment)
        self.child_false.associate_assignment(assignment)

    def apply_hint(self, subfamily, tree_hint):
        if self.is_terminal or tree_hint.is_terminal:
            return
        for hole_index,option in enumerate(tree_hint.hole_assignment):
            hole = self.holes[hole_index]
            subfamily.hole_set_options(hole,[option])
        self.child_true.apply_hint(subfamily,tree_hint.child_true)
        self.child_false.apply_hint(subfamily,tree_hint.child_false)


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
                node.add_children()
        self.root.assign_identifiers()

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


class MdpQuotient(paynt.quotient.quotient.Quotient):

    # if set, an explicit action simulating a random action selection will be added to each state
    add_dont_care_action = False

    def __init__(self, mdp, specification):
        super().__init__(specification=specification)
        updated = payntbind.synthesis.restoreActionsInAbsorbingStates(mdp)
        if updated is not None: mdp = updated
        if MdpQuotient.add_dont_care_action:
            mdp = payntbind.synthesis.addDontCareAction(mdp)

        self.quotient_mdp = mdp
        self.choice_destinations = payntbind.synthesis.computeChoiceDestinations(mdp)
        self.action_labels,self.choice_to_action = payntbind.synthesis.extractActionLabels(mdp)
        self.decision_tree = DecisionTree(mdp)

        self.coloring = None
        self.family = None
        self.splitter_count = None

    def decide(self, node, var_name):
        node.set_variable_by_name(var_name,self.decision_tree)

    '''
    Build the design space and coloring corresponding to the current decision tree.
    '''
    def set_depth(self, depth):
        logger.debug(f"synthesizing tree of depth {depth}")
        self.decision_tree.set_depth(depth)

        # logger.debug("building coloring...")
        variables = self.decision_tree.variables
        variable_name = [v.name for v in variables]
        variable_domain = [v.domain for v in variables]
        tree_list = self.decision_tree.to_list()
        self.coloring = payntbind.synthesis.ColoringSmt(self.quotient_mdp, variable_name, variable_domain, tree_list, False)

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
        self.splitter_count = [0] * self.family.num_holes
        self.decision_tree.root.associate_holes(node_hole_info)


    def build_unsat_result(self):
        spec_result = paynt.verification.property_result.MdpSpecificationResult()
        spec_result.constraints_result = paynt.verification.property_result.ConstraintsResult([])
        spec_result.optimality_result = paynt.verification.property_result.MdpOptimalityResult(None)
        spec_result.evaluate(None)
        spec_result.can_improve = False
        return spec_result

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
        family.mdp.family = family


    def are_choices_consistent(self, choices, family):
        ''' Separate method for profiling purposes. '''
        return self.coloring.areChoicesConsistent(choices, family.family)
        # if family.parent_info is None:
        #     return self.coloring.areChoicesConsistent(choices, family.family)
        # else:
        #     return self.coloring.areChoicesConsistentUseHint(choices, family.family, family.parent_info.unsat_core_hint)

    def scheduler_is_consistent(self, mdp, prop, result):
        ''' Get hole options involved in the scheduler selection. '''

        scheduler = result.scheduler
        assert scheduler.memoryless and scheduler.deterministic
        state_to_choice = self.scheduler_to_state_to_choice(mdp, scheduler)
        choices = self.state_to_choice_to_choices(state_to_choice)
        if self.specification.is_single_property:
            mdp.family.scheduler_choices = choices
        consistent,hole_selection = self.are_choices_consistent(choices, mdp.family)

        for hole,options in enumerate(hole_selection):
            for option in options:
                assert option in mdp.family.hole_options(hole), \
                f"option {option} for hole {hole} ({mdp.family.hole_name(hole)}) is not in the family"

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
        self.splitter_count[splitter] += 1
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

        new_family = mdp.family.copy()
        if len(other_suboptions) == 0:
            suboptions = core_suboptions
        else:
            suboptions = [other_suboptions] + core_suboptions  # DFS solves core first

        # construct corresponding subfamilies
        subfamilies = []
        family.splitter = splitter
        parent_info = family.collect_parent_info(self.specification)
        parent_info.analysis_result = family.analysis_result
        parent_info.scheduler_choices = family.scheduler_choices
        parent_info.unsat_core_hint = self.coloring.unsat_core.copy()
        for suboption in suboptions:
            subfamily = new_family.subholes(splitter, suboption)
            subfamily.add_parent_info(parent_info)
            subfamily.hole_set_options(splitter, suboption)
            subfamilies.append(subfamily)

        return subfamilies
