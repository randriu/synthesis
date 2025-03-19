import paynt.quotient.quotient

import stormpy
import payntbind
import json
import paynt.quotient.utils.variable
import paynt.quotient.utils.decision_tree

import logging

logger = logging.getLogger(__name__)

class MdpQuotient(paynt.quotient.quotient.Quotient):
    # label for action executing a random action selection
    DONT_CARE_ACTION_LABEL = "__random__"

    # if true, irrelevant states will not be considered for tree mapping
    filter_deterministic_states = True

    @classmethod
    # TODO only get this for relevant states for the integration if possible
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
        return variable_name, state_valuations

    def __init__(self, mdp, specification, tree_helper=None):
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
        self.state_is_relevant = [relevant and not state_is_absorbing[state] for state, relevant in
                                  enumerate(self.state_is_relevant)]

        if MdpQuotient.filter_deterministic_states:
            state_has_actions = self.identify_states_with_actions(mdp)
            self.state_is_relevant = [relevant and state_has_actions[state] for state, relevant in
                                      enumerate(self.state_is_relevant)]
        self.state_is_relevant_bv = stormpy.BitVector(mdp.nr_states)
        [self.state_is_relevant_bv.set(state, value) for state, value in enumerate(self.state_is_relevant)]
        logger.debug(
            f"MDP has {self.state_is_relevant_bv.number_of_set_bits()}/{self.state_is_relevant_bv.size()} relevant states")

        action_labels, _ = payntbind.synthesis.extractActionLabels(mdp)
        if MdpQuotient.DONT_CARE_ACTION_LABEL not in action_labels and MdpQuotient.add_dont_care_action:
            logger.debug("adding explicit don't-care action to relevant states...")
            mdp = payntbind.synthesis.addDontCareAction(mdp, self.state_is_relevant_bv)

        self.quotient_mdp = mdp
        self.choice_destinations = payntbind.synthesis.computeChoiceDestinations(mdp)
        self.action_labels, self.choice_to_action = payntbind.synthesis.extractActionLabels(mdp)
        logger.info(f"MDP has {len(self.action_labels)} actions")
        # TODO filter irrelevant actions?

        # get variable domains on relevant states
        variable_name, state_valuations = self.get_state_valuations(mdp)
        num_variables = len(variable_name)
        variable_domain = [set() for variable in range(num_variables)]
        for state in self.state_is_relevant_bv:
            valuation = state_valuations[state]
            for variable in range(num_variables):
                variable_domain[variable].add(valuation[variable])
        variable_domain = [sorted(domain) for domain in variable_domain]

        # filter variables having only one option
        variable_mask = [len(domain) > 1 for domain in variable_domain]
        variable_name = [value for variable, value in enumerate(variable_name) if variable_mask[variable]]
        variable_domain = [value for variable, value in enumerate(variable_domain) if variable_mask[variable]]
        # we filter unused variables from state valuations: this means that multiple states can now have the same "valuation"
        state_valuations = [
            [value for variable, value in enumerate(valuations) if variable_mask[variable]]
            for valuations in state_valuations
        ]

        self.variables = [paynt.quotient.utils.variable.Variable.create_variable(variable, name, variable_domain[variable]) for variable, name in enumerate(variable_name)]
        self.relevant_state_valuations = state_valuations
        logger.debug(f"found the following {len(self.variables)} variables: {[str(v) for v in self.variables]}")
        
        self.decision_tree = None
        self.coloring = None
        self.family = None
        self.splitter_count = None

        self.tree_helper = tree_helper

    def get_variable_id(self, var):
        for id, variable in enumerate(self.variables):
            if variable.name == var:
                break
        return id

    def get_states_satisfying_predicate_old_old(self, variable, bound, leq=True):
        states = []
        for state, state_valuation in enumerate(self.relevant_state_valuations):
            for id, var in enumerate(self.variables):
                if var.name == variable:
                    break
            if leq and state_valuation[id] <= bound:
                states.append(state)
            elif not leq and state_valuation[id] > bound:
                states.append(state)
        return states

    def get_states_satisfying_predicate_old(self, node, current_states, leq=True):
        states = set()
        bound = self.variables[node.variable].domain[node.variable_bound]
        for state, state_valuation in enumerate(self.relevant_state_valuations):
            if state not in current_states:
                continue
            if leq and state_valuation[node.variable] <= bound:
                states.add(state)
            elif not leq and state_valuation[node.variable] > bound:
                states.add(state)
        return states

    def get_states_satisfying_predicate(self, node, current_states, leq=True):
        bound = self.variables[node.variable].domain[node.variable_bound]
        for state, state_valuation in enumerate(self.relevant_state_valuations):
            if not current_states.get(state):
                continue
            if leq and state_valuation[node.variable] > bound:
                current_states.set(state, False)
            elif not leq and state_valuation[node.variable] <= bound:
                current_states.set(state, False)
        return current_states

    def get_state_space_for_tree_helper_node_old_old(self, node_id):
        node = self.tree_helper[node_id]
        current_node = node
        states = list(range(self.quotient_mdp.nr_states))
        while current_node['parent'] is not None:
            parent_node = self.tree_helper[current_node['parent']]
            if parent_node["children"].index(self.tree_helper.index(current_node)) == 0:
                node_states = self.get_states_satisfying_predicate_old(parent_node["chosen"][0],
                                                                       parent_node["chosen"][1], leq=True)
            else:
                node_states = self.get_states_satisfying_predicate_old(parent_node["chosen"][0],
                                                                       parent_node["chosen"][1], leq=False)
            states = list(set(states) & set(node_states))
            current_node = parent_node
        return states

    def get_state_space_for_tree_helper_node_old(self, node_id):
        node = self.tree_helper_tree.collect_nodes(lambda node: node.identifier == node_id)[0]
        current_node = node
        states = set(range(self.quotient_mdp.nr_states))
        while current_node.parent is not None:
            parent_node = current_node.parent
            if parent_node.child_true.identifier == current_node.identifier:
                states = self.get_states_satisfying_predicate(parent_node, states, leq=True)
            else:
                states = self.get_states_satisfying_predicate(parent_node, states, leq=False)
            current_node = parent_node
        return list(states)

    def get_state_space_for_tree_helper_node(self, node_id):
        node = self.tree_helper_tree.collect_nodes(lambda node: node.identifier == node_id)[0]
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

    # TODO remove this
    def get_open_variables_and_domains_for_tree_helper_node(self, node_id):
        node = self.tree_helper[node_id]
        current_node = node
        open_variables = self.variables
        variable_name = [v.name for v in open_variables]
        variable_domains = [list(v.domain) for v in open_variables]
        while current_node['parent'] is not None:
            parent_node = self.tree_helper[current_node['parent']]
            chosen_variable_index = variable_name.index(parent_node["chosen"][0])
            # print(f'{parent_node["chosen"]}')
            if parent_node["children"].index(self.tree_helper.index(current_node)) == 0:
                variable_domains[chosen_variable_index] = [value for value in variable_domains[chosen_variable_index] if
                                                           value <= parent_node["chosen"][1]]
            else:
                variable_domains[chosen_variable_index] = [value for value in variable_domains[chosen_variable_index] if
                                                           value > parent_node["chosen"][1]]
            current_node = parent_node

        open_variables = [Variable(variable_name[i], variable_domains[i]) for i in range(len(variable_name)) if
                          len(variable_domains[i]) > 1]
        return open_variables

    def get_chosen_action_for_state_from_tree_helper_old(self, state):
        state_valuation = self.relevant_state_valuations[state]
        current_node = self.tree_helper[0]
        while not current_node['leaf']:
            var_id = self.get_variable_id(current_node["chosen"][0])
            if state_valuation[var_id] <= current_node['chosen'][1]:
                current_node = self.tree_helper[current_node['children'][0]]
            else:
                current_node = self.tree_helper[current_node['children'][1]]
        return current_node['chosen'][0]

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
                for choice in range(mdp_nci[state], mdp_nci[state + 1]):
                    selected_choices.set(choice, True)
                continue
            chosen_action_label = self.get_chosen_action_for_state_from_tree_helper(state)
            action_index = self.action_labels.index(chosen_action_label)
            for choice in range(mdp_nci[state], mdp_nci[state + 1]):
                if self.choice_to_action[choice] == action_index:
                    selected_choices.set(choice, True)
                    break
            else:
                # TODO as far as I know this happens only because of unreachable states not being included in the tree
                # for now we will treat this by using the __random__ action but it can lead to strange behaviour
                for choice in range(mdp_nci[state], mdp_nci[state + 1]):
                    if self.action_labels[self.choice_to_action[choice]] == "__random__":
                        selected_choices.set(choice, True)
                        break
                continue
                assert False, f"no choice for state {state} even though action {chosen_action_label} was chosen"

        # TODO another implementation, both suck!
        # selected_choices = stormpy.storage.BitVector(self.quotient_mdp.nr_choices, True)
        # mdp_nci = self.quotient_mdp.nondeterministic_choice_indices.copy()
        # for state in range(self.quotient_mdp.nr_states):
        #     if self.state_is_relevant_bv.get(state) and state not in state_to_exclude:
        #         chosen_action_label = self.get_chosen_action_for_state_from_tree_helper(state)
        #         action_index = self.action_labels.index(chosen_action_label)
        #         one_choice_set = False
        #         for choice in range(mdp_nci[state],mdp_nci[state+1]):
        #             if self.choice_to_action[choice] != action_index:
        #                 selected_choices.set(choice, False)
        #             else:
        #                 assert not one_choice_set, f"multiple choices for state {state}"
        #                 one_choice_set = True
        #         if not one_choice_set:
        #             for choice in reversed(range(mdp_nci[state],mdp_nci[state+1])):
        #                 if self.action_labels[self.choice_to_action[choice]] == "__random__":
        #                     selected_choices.set(choice, True)
        #                     break
        #             continue
        #             assert False, f"no choice for state {state} even though action {chosen_action_label} was chosen"

        return selected_choices

    def scheduler_json_to_choices(self, scheduler_json, discard_unreachable_states=False):
        variable_name, state_valuations = self.get_state_valuations(self.quotient_mdp)
        nci = self.quotient_mdp.nondeterministic_choice_indices.copy()
        assert self.quotient_mdp.nr_states == len(scheduler_json)
        state_to_choice = self.empty_scheduler()
        for state_decision in scheduler_json:
            valuation = [state_decision["s"][name] for name in variable_name]
            for state, state_valuation in enumerate(state_valuations):
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
            for choice in range(nci[state], nci[state + 1]):
                if self.choice_to_action[choice] == action:
                    state_to_choice[state] = choice
                    break
            else:
                assert False, "action is not available in the state"
        # enable implicit actions
        for state, choice in enumerate(state_to_choice):
            if choice is None:
                logger.warning(f"WARNING: scheduler has no action for state {state}")
                state_to_choice[state] = nci[state]

        if discard_unreachable_states:
            state_to_choice = self.discard_unreachable_choices(state_to_choice)
        # keep only relevant states
        state_to_choice = [choice if self.state_is_relevant[state] else None for state, choice in
                           enumerate(state_to_choice)]
        choices = self.state_to_choice_to_choices(state_to_choice)

        scheduler_json_relevant = []
        for state_decision in scheduler_json:
            valuation = [state_decision["s"][name] for name in variable_name]
            for state, state_valuation in enumerate(state_valuations):
                if valuation == state_valuation:
                    break
            if state_to_choice[state] is None:
                continue
            scheduler_json_relevant.append(state_decision)

        return choices, scheduler_json_relevant

    # gets all choices that represent random action, used to compute the value of uniformly random scheduler
    def get_random_choices(self):
        nci = self.quotient_mdp.nondeterministic_choice_indices.copy()
        state_to_choice = self.empty_scheduler()
        random_action = self.action_labels.index(MdpQuotient.DONT_CARE_ACTION_LABEL)
        for state in range(self.quotient_mdp.nr_states):
            # find a choice that executes this action
            for choice in range(nci[state], nci[state + 1]):
                if self.choice_to_action[choice] == random_action:
                    state_to_choice[state] = choice
                    break
        for state, choice in enumerate(state_to_choice):
            if choice is None:
                state_to_choice[state] = nci[state]

        choices = self.state_to_choice_to_choices(state_to_choice)

        return choices

    def build_tree_helper_tree(self, tree_helper=None):
        if tree_helper is None:
            tree_helper = self.tree_helper
        helper_tree = paynt.quotient.utils.decision_tree.DecisionTree(self, self.variables)
        helper_tree.build_from_tree_helper(tree_helper)
        return helper_tree

    # TODO remove this
    def get_helper_choice_for_state(self, state):
        state_valuations = self.state_valuations[state]
        current_node = self.tree_helper[0]
        while current_node["leaf"] != True:
            (node_var, node_threshold) = current_node["chosen"]
            var_id = self.get_variable_id(node_var)
            if state_valuations[var_id] <= node_threshold:
                current_node = self.tree_helper[current_node["children"][0]]
            else:
                current_node = self.tree_helper[current_node["children"][1]]

                # unfixed_states is a bitvector of states that should be left unfixed in the submdp

    def get_submdp_from_unfixed_states(self, unfixed_states=None):
        if unfixed_states is None:
            unfixed_states = stormpy.storage.BitVector(self.quotient_mdp.nr_states, False)
        selected_choices = self.get_selected_choices_from_tree_helper(unfixed_states)
        submdp = self.build_from_choice_mask(selected_choices)
        # print(dir(submdp))
        # res = submdp.check_specification(self.specification)
        # print(res)
        # exit()
        return submdp

    def create_uniform_random_tree(self):
        decision_tree = DecisionTree(self, self.variables)
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

        self.decision_tree = paynt.quotient.utils.decision_tree.DecisionTree(self, self.variables)
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
        for hole, info in enumerate(hole_info):
            node, hole_name, hole_type = info
            node_hole_info[node].append((hole, hole_name, hole_type))
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

    # TODO: remove this method
    def get_subtree_family(self, node_id, variables):
        subtree_family = self.family.copy()

        variable_names = [v.name for v in variables]
        variable_domains = [v.domain for v in variables]

        for hole in range(subtree_family.num_holes):
            hole_option_labels = subtree_family.hole_to_option_labels[hole]
            if subtree_family.hole_name(hole).startswith('V_'):
                chosen_options = []
                for option in subtree_family.hole_options(hole):
                    if hole_option_labels[option] in variable_names:
                        chosen_options.append(option)
                subtree_family.hole_set_options(hole, chosen_options)
            else:
                for id, variable_name in enumerate(variable_names):
                    if subtree_family.hole_name(hole).startswith(variable_name + "_"):
                        chosen_options = [option for option in subtree_family.hole_options(hole) if
                                          hole_option_labels[option] in variable_domains[id]]
                        subtree_family.hole_set_options(hole, chosen_options)
                        break
                else:
                    if subtree_family.hole_name(hole).startswith('A_'):
                        continue
                    else:
                        subtree_family.hole_set_options(hole, [subtree_family.hole_options(hole)[0]])

        return subtree_family

    # TODO: remove this method
    def get_subfamily_from_used_predicates(self, family):
        used_predicates_dict = {}
        for helper_node in self.tree_helper:
            if helper_node['leaf']:
                continue
            if helper_node['chosen'][0] not in used_predicates_dict.keys():
                used_predicates_dict[helper_node['chosen'][0]] = [helper_node['chosen'][1]]
            elif helper_node['chosen'][1] not in used_predicates_dict[helper_node['chosen'][0]]:
                used_predicates_dict[helper_node['chosen'][0]].append(helper_node['chosen'][1])

        used_predicates_family = family.copy()
        for hole in range(used_predicates_family.num_holes):
            hole_option_labels = used_predicates_family.hole_to_option_labels[hole]
            if used_predicates_family.hole_name(hole).startswith('V_'):
                chosen_options = []
                for option in used_predicates_family.hole_options(hole):
                    if hole_option_labels[option] in used_predicates_dict.keys():
                        chosen_options.append(option)
                used_predicates_family.hole_set_options(hole, chosen_options)
            else:
                for variable_name in used_predicates_dict.keys():
                    if used_predicates_family.hole_name(hole).startswith(variable_name + "_"):
                        chosen_options = [option for option in used_predicates_family.hole_options(hole) if
                                          hole_option_labels[option] in used_predicates_dict[variable_name]]
                        used_predicates_family.hole_set_options(hole, chosen_options)

        logger.info(
            f"used tree helper to get subfamily from used predicates. Family size reduced from {family.size_or_order} to {used_predicates_family.size_or_order}")
        # exit()

        print()
        print(family)
        print("--------")
        print(used_predicates_family)
        print()
        exit()

        return used_predicates_family

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
        assert choices.number_of_set_bits() > 0

        # proceed as before
        family.selected_choices = choices
        family.mdp = self.build_from_choice_mask(choices)
        family.mdp.family = family

    def are_choices_consistent(self, choices, family):
        ''' Separate method for profiling purposes. '''
        # relevant_choices = stormpy.BitVector(choices)
        # # TODO add more ways to determine relevant choices
        # nci = self.quotient_mdp.nondeterministic_choice_indices.copy()
        # for state in range(self.quotient_mdp.nr_states):
        #     if self.quotient_mdp.get_nr_available_actions(state) <= 1:
        #         for choice in range(nci[state],nci[state+1]):
        #             relevant_choices.set(choice, False)
        return self.coloring.areChoicesConsistent(choices, family.family)

    def scheduler_is_consistent(self, mdp, prop, result):
        ''' Get hole options involved in the scheduler selection. '''

        scheduler = result.scheduler
        assert scheduler.memoryless and scheduler.deterministic
        state_to_choice = self.scheduler_to_state_to_choice(mdp, scheduler)
        choices = self.state_to_choice_to_choices(state_to_choice)
        if self.specification.is_single_property:
            mdp.family.scheduler_choices = choices
        consistent, hole_selection = self.are_choices_consistent(choices, mdp.family)

        for hole, options in enumerate(hole_selection):
            for option in options:
                assert option in mdp.family.hole_options(hole), \
                    f"option {option} for hole {hole} ({mdp.family.hole_name(hole)}) is not in the family"

        return hole_selection, consistent

    def scheduler_scores(self, mdp, prop, result, selection):
        inconsistent_assignments = {hole: options for hole, options in enumerate(selection) if len(options) > 1}
        assert len(inconsistent_assignments) > 0, f"obtained selection with no inconsistencies: {selection}"
        inconsistent_action_holes = [(hole, options) for hole, options in inconsistent_assignments.items() if
                                     self.is_action_hole[hole]]
        inconsistent_decision_holes = [(hole, options) for hole, options in inconsistent_assignments.items() if
                                       self.is_decision_hole[hole]]
        inconsistent_variable_holes = [(hole, options) for hole, options in inconsistent_assignments.items() if
                                       self.is_variable_hole[hole]]

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
        return {splitter: 10}

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
            core_suboptions, other_suboptions = self.suboptions_enumerate(mdp, splitter, hole_assignments[splitter])
        else:
            subfamily_options = family.hole_options(splitter)

            # split in half
            index_split = len(subfamily_options) // 2

            # split by inconsistent options
            option_1 = hole_assignments[splitter][0];
            index_1 = subfamily_options.index(option_1)
            option_2 = hole_assignments[splitter][1];
            index_2 = subfamily_options.index(option_2)
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
        subfamilies = family.split(splitter, suboptions)
        for subfamily in subfamilies:
            subfamily.add_parent_info(parent_info)
        return subfamilies
