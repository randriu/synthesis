import payntbind

import stormpy
import paynt.family.family
import paynt.quotient.quotient
import paynt.models.models
import paynt.quotient.utils.variable
import paynt.quotient.utils.decision_tree

import json

import logging
logger = logging.getLogger(__name__)


class MdpFamilyQuotient(paynt.quotient.quotient.Quotient):

    # label for action executing a random action selection
    DONT_CARE_ACTION_LABEL = "__random__"

    # if true, irrelevant states will not be considered for tree mapping
    filter_deterministic_states = True # TODO: change to false

    # default value for DTNest (UAI25) - origin in mdp.py
    tree_helper = None

    @staticmethod
    def map_state_action_to_choices(mdp, num_actions, choice_to_action):
        state_action_choices = []
        for state in range(mdp.nr_states):
            action_choices = [[] for action in range(num_actions)]
            for choice in mdp.transition_matrix.get_rows_for_group(state):
                action = choice_to_action[choice]
                action_choices[action].append(choice)
            state_action_choices.append(action_choices)
        return state_action_choices

    @staticmethod
    def map_state_to_available_actions(state_action_choices):
        state_to_actions = []
        for state,action_choices in enumerate(state_action_choices):
            available_actions = []
            for action,choices in enumerate(action_choices):
                if choices:
                    available_actions.append(action)
            state_to_actions.append(available_actions)
        return state_to_actions

    
    def __init__(self, quotient_mdp, family, coloring, specification, specification_alt, tree_helper_path=None):
        super().__init__(quotient_mdp = quotient_mdp, family = family, coloring = coloring, specification = specification)
        self.specification_alt = specification_alt

        # number of distinct actions in the quotient
        self.num_actions = None
        # a list of action labels
        self.action_labels = None
        # for each choice of the quotient, the executed action
        self.choice_to_action = None
        # for each state of the quotient and for each action, a list of choices that execute this action
        self.state_action_choices = None
        # for each state of the quotient, a list of available actions
        self.state_to_actions = None
        # dict of irrelevant variables, filled by extract_policies call with their defaults
        self.irrelevant_variables = None
        # path to the tree helper for DTNest
        self.tree_helper_path = tree_helper_path

        # identify relevant states
        self.state_is_relevant = [True for state in range(quotient_mdp.nr_states)]
        state_is_absorbing = self.identify_absorbing_states(quotient_mdp)
        self.state_is_relevant = [relevant and not state_is_absorbing[state] for state,relevant in enumerate(self.state_is_relevant)]

        if MdpFamilyQuotient.filter_deterministic_states:
            state_has_actions = self.identify_states_with_actions(quotient_mdp)
            self.state_is_relevant = [relevant and state_has_actions[state] for state,relevant in enumerate(self.state_is_relevant)]
        self.state_is_relevant_bv = stormpy.BitVector(quotient_mdp.nr_states)
        [self.state_is_relevant_bv.set(state,value) for state,value in enumerate(self.state_is_relevant)]
        logger.debug(f"MDP has {self.state_is_relevant_bv.number_of_set_bits()}/{self.state_is_relevant_bv.size()} relevant states")

        action_labels,_ = payntbind.synthesis.extractActionLabels(quotient_mdp)
        # if MdpFamilyQuotient.DONT_CARE_ACTION_LABEL not in action_labels and MdpFamilyQuotient.add_dont_care_action:
        # LADA TODO: adding don't care must come later to single mdp
        #     logger.debug("adding explicit don't-care action to relevant states...")
        #     quotient_mdp = payntbind.synthesis.addDontCareAction(quotient_mdp,self.state_is_relevant_bv)

        self.quotient_mdp = quotient_mdp

        self.action_labels,self.choice_to_action = payntbind.synthesis.extractActionLabels(quotient_mdp)
        self.num_actions = len(self.action_labels)
        self.state_action_choices = MdpFamilyQuotient.map_state_action_to_choices(
            self.quotient_mdp, self.num_actions, self.choice_to_action)
        self.state_to_actions = MdpFamilyQuotient.map_state_to_available_actions(self.state_action_choices)

        # Copy from MdpQuotient class, also variable class
        assert quotient_mdp.has_state_valuations(), "model has no state valuations"
        sv = quotient_mdp.state_valuations
        valuation = json.loads(str(sv.get_json(0)))
        variable_name = [var_name for var_name in valuation]
        state_valuations = []
        for state in range(quotient_mdp.nr_states):
            valuation = json.loads(str(sv.get_json(state)))
            valuation = [valuation[var_name] for var_name in variable_name]
            state_valuations.append(valuation)

        vars_domains = []
        for variable_index in range(len(state_valuations[0])):
            single_var_domain = set()
            for state,valuation in enumerate(state_valuations):
                value = valuation[variable_index]
                single_var_domain.add(value)
            vars_domains.append(list(single_var_domain))

        variables = [paynt.quotient.utils.variable.Variable.create_variable(variable, name, vars_domains[variable]) for variable, name in enumerate(variable_name)]
        variable_mask = [len(v.domain) > 1 for v in variables]
        variables = [v for index, v in enumerate(variables) if variable_mask[index]]
        for state, valuation in enumerate(state_valuations):
            state_valuations[state] = [value for index, value in enumerate(valuation) if variable_mask[index]]
        self.variables = variables
        self.state_valuations = state_valuations
        self.relevant_state_valuations = state_valuations
        self.state_is_relevant_bv_backup = self.copy_bitvector(self.state_is_relevant_bv)
        
        # used to set coloring according to new mdp_quotient ( due to DONT_CARE_ACTION_LABEL )
        # self.reset_tree(0)
        #        payntbind.synthesis.Coloring(family.family, quotient_mdp.nondeterministic_choice_indices,
        #                                     jani_unfolder.choice_to_hole_options)
        
    # gets all choices that represent random action, used to compute the value of uniformly random scheduler
    def get_random_choices(self):
        nci = self.quotient_mdp.nondeterministic_choice_indices.copy()
        state_to_choice = self.empty_scheduler()
        random_action = self.action_labels.index(MdpFamilyQuotient.DONT_CARE_ACTION_LABEL)
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

    @staticmethod
    def copy_bitvector(bitvector):
        """Create a copy of the given BitVector object."""
        new_bitvector = stormpy.BitVector(bitvector.size())
        for i in range(bitvector.size()):
            new_bitvector.set(i, bitvector.get(i))
        return new_bitvector

    def empty_policy(self):
        return self.empty_scheduler()

    def scheduler_to_policy(self, scheduler, mdp):
        state_to_choice = self.scheduler_to_state_to_choice(mdp,scheduler)
        policy = self.empty_policy()
        for state in range(self.quotient_mdp.nr_states):
            choice = state_to_choice[state]
            if choice is not None:
                policy[state] = self.choice_to_action[choice]
        return policy

    def state_valuation_to_state(self, valuation):
        valuation = [valuation[v.name] for v in self.variables]
        for state,state_valuation in enumerate(self.state_valuations):
            if valuation == state_valuation:
                return state
        else:
            assert False, "state valuation not found"

    def policy_to_policy_vector(self, policy):
        # assert self.quotient_mdp.nr_states == len(policy), "policy length does not match the number of states"
        choices = self.state_to_choice_to_choices(policy)
        return choices


    def reset_tree(self, depth, enable_harmonization=True):
        '''
        Rebuild the decision tree template, the design space and the coloring.
        '''
        logger.debug(f"building tree of depth {depth}")

        num_actions = len(self.action_labels)
        dont_care_action = num_actions
        if MdpFamilyQuotient.DONT_CARE_ACTION_LABEL in self.action_labels:
            dont_care_action = self.action_labels.index(MdpFamilyQuotient.DONT_CARE_ACTION_LABEL)

        self.decision_tree = paynt.quotient.utils.decision_tree.DecisionTree(self,self.variables)
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
        self.splitter_count = [0] * self.family.num_holes
        self.decision_tree.root.associate_holes(node_hole_info)

    def build_unsat_result(self):
        spec_result = paynt.verification.property_result.MdpSpecificationResult()
        spec_result.constraints_result = paynt.verification.property_result.ConstraintsResult([])
        spec_result.optimality_result = paynt.verification.property_result.MdpOptimalityResult(None)
        spec_result.evaluate(None)
        spec_result.can_improve = False
        return spec_result

    def are_choices_consistent(self, choices, family):
        ''' Separate method for profiling purposes. '''
        return self.coloring.areChoicesConsistent(choices, family.family)

    def policy_to_state_valuation_actions(self, policy, family = None):
        '''
        Create a representation for a policy that associated action labels with state valuations. States with only
        one available action are omitted.
        '''
        policy,_ = policy
        sv = self.quotient_mdp.state_valuations
        state_valuation_to_action = []
        for state,action in enumerate(policy):
            if action is None:
                continue
            if len(self.state_to_actions[state])==1:
                continue
            # get action label
            action = self.action_labels[action]
            if action == "empty_label":
                continue

            # get state valuation
            valuation_jani = json.loads(str(sv.get_json(state)))
            valuation = {}
            for variable,value in valuation_jani.items():
                if "_loc_prism2jani_" in variable:
                    continue
                valuation[variable] = value
            state_valuation_to_action.append( (valuation,action) )

        # omit variables that are assigned to the same value
        default_valuation,_ = state_valuation_to_action[0]
        irrelevant_variables = set(default_valuation)
        for valuation,_ in state_valuation_to_action[1:]:
            for variable in list(irrelevant_variables):
                if valuation[variable] != default_valuation[variable]:
                    irrelevant_variables.remove(variable)

        self.irrelevant_variables = {variable: default_valuation[variable] for variable in irrelevant_variables}

        # add family to state valuation
        if family:
            hole_names = family.hole_to_name
            # get first option for each hole
            hole_options = [h[0] for h in family.holes_options]

            for valuation, action in state_valuation_to_action:
                for hole, val in zip(hole_names, hole_options):
                    valuation[hole] = val

        # remove irrelevant variables - DTcontrol needs homogeneous states
        if not family:
            state_valuation_to_action = [
                ({variable:value for variable,value in valuation.items() if variable not in irrelevant_variables},action)
                for valuation, action in state_valuation_to_action
            ]
        return state_valuation_to_action

    def policy_to_json(self, state_valuation_to_action, dt_control=False):
        '''
        :param state_valuation_to_action: a list of tuples (valuation,action) where valuation is a dictionary of variable
        :param dt_control: if True, outputs JSON in the format expected by the DT control tool,
                otherwise simpler format is used
        '''
        json_whole = []
        for index, valuation_action in enumerate(state_valuation_to_action):
            if dt_control:
                json_unit = {}
                valuation, action = valuation_action
                json_unit["c"] = [{"origin": {"action-label": action}}]
                json_unit["s"] = valuation
                json_whole.append(json_unit)
            else:
                json_whole.append(valuation_action)

        return json_whole

    
    def fix_and_apply_policy_to_family(self, family, policy):
        '''
        Apply policy to the quotient MDP for the given family. Every undefined action in a policy is set to an arbitrary
        one. Upon constructing the MDP, reset unused actions in a policy to None.
        :returns fixed policy
        :returns the resulting MDP
        '''
        policy = [action if action is not None else self.state_to_actions[state][0] for state,action in enumerate(policy)]
        policy_choices = []
        for state,action in enumerate(policy):
            policy_choices += self.state_action_choices[state][action]
        choices = payntbind.synthesis.policyToChoicesForFamily(policy_choices, family.selected_choices)

        # build MDP and keep only reachable states in policy
        mdp = self.build_from_choice_mask(choices)
        policy_fixed = self.empty_policy()
        for state in mdp.quotient_state_map:
            policy_fixed[state] = policy[state]

        mask = [state for state,action in enumerate(policy_fixed) if action is not None]
        policy_fixed = (policy_fixed,mask)
        return policy_fixed,mdp
    

    def apply_policy_to_family(self, family, policy):
        policy_choices = []
        for state,action in enumerate(policy):
            if action is None:
                for choice in self.state_action_choices[state]:
                    policy_choices += choice
            else:
                policy_choices += self.state_action_choices[state][action]
        choices = payntbind.synthesis.policyToChoicesForFamily(policy_choices, family.selected_choices)

        mdp = self.build_from_choice_mask(choices)

        return mdp

    
    def assert_mdp_is_deterministic(self, mdp, family):
        if mdp.is_deterministic:
            return
        
        logger.error(f"applied policy to a singleton family {family} and obtained MDP with nondeterminism")
        for state in range(mdp.model.nr_states):

            choices = mdp.model.transition_matrix.get_rows_for_group(state)
            if len(choices)>1:
                quotient_state = mdp.quotient_state_map[state]
                quotient_choices = [mdp.quotient_choice_map[choice] for choice in choices]
                state_str = self.quotient_mdp.state_valuations.get_string(quotient_state)
                state_str = state_str.replace(" ","")
                state_str = state_str.replace("\t","")
                actions_str = [self.action_labels[self.choice_to_action[choice]] for choice in quotient_choices]
                logger.error(f"the following state {state_str} has multiple actions {actions_str}")
        logger.error("aborting...")
        exit(1)
        

    def build_game_abstraction_solver(self, prop):
        target_label = prop.get_target_label()
        precision = paynt.verification.property.Property.model_checking_precision
        solver = payntbind.synthesis.GameAbstractionSolver(
            self.quotient_mdp, len(self.action_labels), self.choice_to_action, prop.formula, prop.maximizing, target_label, precision
        )
        return solver

    def build_assignment(self, family):
        assert family.size == 1, "expecting family of size 1"
        choices = self.coloring.selectCompatibleChoices(family.family)
        model,state_map,choice_map = self.restrict_quotient(choices)
        model = MdpFamilyQuotient.mdp_to_dtmc(model)
        return paynt.models.models.SubMdp(model,state_map,choice_map)

    def mark_irrelevant_states(self, irrelevant_variables: dict):
        """mark state irrelevant wrt variable if not default for given domain"""
        for j in range(len(self.state_valuations)):
            if not self.state_is_relevant_bv[j]:
                continue
            relevant = True
            for variable, default in irrelevant_variables.items():
                for index,var in enumerate(self.variables):
                    if var.name == variable:
                        if self.state_valuations[j][index] != default:
                            relevant = False
                            break
                if not relevant:
                    break
            if not relevant:
                self.state_is_relevant_bv.set(j,False)
        return True
    
    def build_tree_helper_tree(self, tree_helper=None):
        if tree_helper is None:
            tree_helper = self.tree_helper
        helper_tree = paynt.quotient.utils.decision_tree.DecisionTree(self, self.variables)
        helper_tree.build_from_tree_helper(tree_helper)
        return helper_tree
    
    def get_submdp_from_unfixed_states(self, unfixed_states=None):
        if unfixed_states is None:
            unfixed_states = stormpy.storage.BitVector(self.quotient_mdp.nr_states, True)
        selected_choices = self.get_selected_choices_from_tree_helper(unfixed_states)
        submdp = self.build_from_choice_mask(selected_choices)
        return submdp
    
    def get_selected_choices_from_tree_helper(self, state_to_exclude):
        # LADA TODO: emror here- returns None
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

        return selected_choices

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

    def return_copy(self):
        return MdpFamilyQuotient(
            self.quotient_mdp,
            self.family,
            self.coloring,
            self.specification,
            self.specification_alt,
            tree_helper_path=self.tree_helper_path
        )