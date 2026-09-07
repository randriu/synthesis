import paynt.parameter_space.parameter_space
import paynt.underlying_model.underlying_model
from paynt.dt.colored_mdp import DtColoredMdp

from paynt.parser._utils import make_rewards_action_based

import stormpy
import payntbind

from .decision_tree import DecisionTree, DtVariable
from ._utils import get_state_valuations

import logging
logger = logging.getLogger(__name__)


class DtColoredMdpFactory:
    '''
    Constructs a DtColoredMdp for a given decision-tree depth. Unlike the FSC-unfolding factories
    (POSMG/Dec-POMDP/POMDP), a fresh tree/coloring must be rebuilt for every depth tried during search
    (DtSynthesizer.synthesize_tree_sequence tries several), not just when memory needs to grow -- so
    reset_tree is the main entry point, called far more often than __init__ itself.

    task is optional (unlike the other factories) to support constructing a DtColoredMdpFactory purely from
    an MDP before the specification/tree-depth/timeout are known, then attaching the real Task once it is
    (see paynt.dt.api.get_synthesizer) -- this is a real, exercised library usage pattern, not a hypothetical.
    '''

    # label for action executing a random action selection
    DONT_CARE_ACTION_LABEL = DtColoredMdp.DONT_CARE_ACTION_LABEL
    # if true, irrelevant states will not be considered for tree mapping
    filter_deterministic_states = True

    def __init__(self, mdp, task=None, use_exact=False):
        self.task = task
        self.use_exact = use_exact
        # task is optional here (see class docstring), and even when present may be a plain Task rather than
        # a DtTask (e.g. dtnest's per-subtree re-synthesis constructs one via Task.from_specification, which
        # has no add_dont_care_action field at all) -- getattr falls back to DtTask's own default in both cases
        add_dont_care_action = getattr(task, 'add_dont_care_action', True)

        make_rewards_action_based(mdp) # needed for initialization

        # identify relevant states: non-absorbing states with more than one action
        state_is_relevant = [True for state in range(mdp.nr_states)]
        state_is_absorbing = paynt.underlying_model.underlying_model.ModelIndex.identify_absorbing_states(mdp)
        state_is_relevant = [relevant and not state_is_absorbing[state] for state,relevant in enumerate(state_is_relevant)]

        if DtColoredMdpFactory.filter_deterministic_states:
            state_has_actions = paynt.underlying_model.underlying_model.ModelIndex.identify_states_with_actions(mdp)
            state_is_relevant = [relevant and state_has_actions[state] for state,relevant in enumerate(state_is_relevant)]
        state_is_relevant_bv = stormpy.BitVector(mdp.nr_states)
        [state_is_relevant_bv.set(state,value) for state,value in enumerate(state_is_relevant)]
        logger.debug(f"MDP has {state_is_relevant_bv.number_of_set_bits()}/{state_is_relevant_bv.size()} relevant states")
        self.state_is_relevant = state_is_relevant
        self.state_is_relevant_bv = state_is_relevant_bv

        action_labels,_ = payntbind.synthesis.extractActionLabels(mdp)
        if DtColoredMdpFactory.DONT_CARE_ACTION_LABEL not in action_labels and add_dont_care_action:
            logger.debug("adding explicit don't-care action to relevant states...")
            mdp = payntbind.synthesis.addDontCareAction(mdp,self.state_is_relevant_bv)

        self.underlying_mdp = mdp
        self.choice_destinations = payntbind.synthesis.computeChoiceDestinations(mdp)
        self.action_labels,self.choice_to_action = payntbind.synthesis.extractActionLabels(mdp)
        logger.info(f"MDP has {len(self.action_labels)} actions")
        # TODO filter irrelevant actions?

        # get variable domains on relevant states
        variable_name,state_valuations = get_state_valuations(mdp)
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

        self.variables = [DtVariable(name,variable_domain[variable]) for variable,name in enumerate(variable_name)]
        self.relevant_state_valuations = state_valuations
        logger.debug(f"found the following {len(self.variables)} variables: {[str(v) for v in self.variables]}")

        # build an initial (depth-0) tree so this factory always produces a usable colored_mdp, matching
        # every other colored-MDP factory -- 0 is also the CLI's own default --tree-depth
        self.colored_mdp = self.reset_tree(0)

    def reset_tree(self, depth : int, enable_harmonization : bool = True):
        '''
        Rebuild the decision tree template, the parameter space and the coloring, producing a fresh
        DtColoredMdp -- callers reassign their reference (e.g. self.colored_mdp = factory.reset_tree(k)) rather
        than relying on in-place mutation.
        '''
        logger.debug(f"building tree of depth {depth}")

        num_actions = len(self.action_labels)
        dont_care_action = num_actions
        if DtColoredMdpFactory.DONT_CARE_ACTION_LABEL in self.action_labels:
            dont_care_action = self.action_labels.index(DtColoredMdpFactory.DONT_CARE_ACTION_LABEL)

        decision_tree = DecisionTree(self.action_labels,self.variables)
        decision_tree.set_depth(depth)

        variables = decision_tree.variables
        variable_name = [v.name for v in variables]
        variable_domain = [v.domain for v in variables]
        tree_list = decision_tree.to_list()
        coloring = payntbind.synthesis.ColoringSmt(
            self.underlying_mdp.nondeterministic_choice_indices, self.choice_to_action,
            num_actions, dont_care_action,
            self.underlying_mdp.state_valuations, self.state_is_relevant_bv,
            variable_name, variable_domain, tree_list, enable_harmonization
        )
        coloring.enableStateExploration(self.underlying_mdp)

        # reconstruct the parameter space
        parameter_info = coloring.getFamilyInfo()
        parameter_space = paynt.parameter_space.parameter_space.ParameterSpace()
        is_action_parameter = [False for _ in parameter_info]
        is_decision_parameter = [False for _ in parameter_info]
        is_variable_parameter = [False for _ in parameter_info]
        node_parameter_info = [[] for _ in decision_tree.collect_nodes()]
        for parameter_id,info in enumerate(parameter_info):
            node,parameter_name,parameter_type = info
            node_parameter_info[node].append( (parameter_id,parameter_name,parameter_type) )
            if parameter_type == "__action__":
                is_action_parameter[parameter_id] = True
                option_labels = self.action_labels
            elif parameter_type == "__decision__":
                is_decision_parameter[parameter_id] = True
                option_labels = variable_name
            else:
                is_variable_parameter[parameter_id] = True
                variable = variable_name.index(parameter_type)
                option_labels = variables[variable].parameter_domain
            parameter_space.add_parameter(parameter_name, option_labels)
        decision_tree.root.associate_parameters(node_parameter_info)

        colored_mdp = DtColoredMdp(
            self.underlying_mdp, parameter_space, coloring, self.use_exact,
            self.action_labels, self.choice_to_action, self.state_is_relevant, self.state_is_relevant_bv,
            self.variables, self.relevant_state_valuations, decision_tree,
            is_action_parameter, is_decision_parameter, is_variable_parameter)
        self.colored_mdp = colored_mdp
        return colored_mdp
