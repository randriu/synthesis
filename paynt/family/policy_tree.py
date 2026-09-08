import paynt.synthesizer.synthesizer
import paynt.synthesizer.search_node
import paynt.underlying_model.underlying_model
from paynt.specification.property import Property
import paynt.utils.timer
import paynt.utils.scoring

import logging
logger = logging.getLogger(__name__)

# disable logging when importing graphviz to suppress warnings
logging.disable(logging.CRITICAL)
import graphviz
logging.disable(logging.NOTSET)


def policies_are_compatible(policy1, policy2):
    policy1,policy1_mask = policy1
    policy2,_ = policy2
    for state in policy1_mask:
        a1 = policy1[state]
        a2 = policy2[state]
        if a2 is not None and a1 != a2:
            return False
    return True

def merge_policies(policy1, policy2):
    '''
    Attempt to merge multiple policies into one.
    :returns one policy or None if some policies were incompatible
    '''
    if not policies_are_compatible(policy1,policy2):
        return None
    policy1,_ = policy1
    policy2,_ = policy2
    policy = [a1 or policy2[state] for state,a1 in enumerate(policy1)]
    mask = [state for state,action in enumerate(policy) if action is not None]
    return (policy,mask)

def merge_policies_exclusively(policy1, policy2):
    policy1,_ = policy1
    policy2,_ = policy2
    policy12 = policy1.copy()
    policy21 = policy2.copy()
    for state,a1 in enumerate(policy1):
        a2 = policy2[state]
        if a1 is None:
            policy12[state] = a2
        if a2 is None:
            policy21[state] = a1
    return policy12,policy21


class PolicyTreeNode(paynt.synthesizer.search_node.SearchNode):

    def __init__(self, parameter_space, parent_info=None):
        super().__init__(parameter_space, parent_info)

        # a previously-computed game-abstraction policy supplied by the parent split, tried before solving a
        # fresh game abstraction for this node (see PolicyTreeSynthesizer.verify_parameter_space)
        self.candidate_policy = None

        self.splitter = None
        self.suboptions = []
        self.child_nodes = []

        self.sat = None
        self.policy_index = None

    @property
    def is_leaf(self):
        return self.sat is not None

    def num_nodes(self):
        num = 1
        for child in self.child_nodes:
            num += child.num_nodes()
        return num

    def num_leaves(self):
        num = 1 if self.is_leaf else 0
        for child in self.child_nodes:
            num += child.num_leaves()
        return num

    def attach_children(self, splitter, suboptions, parameter_subspaces, candidate_policies=None):
        '''
        Wrap each of parameter_subspaces (already-split ParameterSpace values) as a child PolicyTreeNode.
        Named distinctly from the inherited SearchNode.split (which computes the parameter_space split
        itself and hands back nodes carrying ParentInfo) since this method has a different signature and
        role: it just attaches pre-computed subspaces as tree children, matching this class's simple flat
        parent/child_nodes bookkeeping rather than SearchNode's generic ParentInfo handoff, which policy-tree
        synthesis doesn't use.
        '''
        self.splitter = splitter
        self.suboptions = suboptions
        self.child_nodes = []
        if candidate_policies is None:
            candidate_policies = [None for _ in parameter_subspaces]
        for parameter_subspace,candidate_policy in zip(parameter_subspaces,candidate_policies):
            child_node = PolicyTreeNode(parameter_subspace)
            child_node.candidate_policy = candidate_policy
            self.child_nodes.append(child_node)

    def double_check(self, colored_mdp, prop, policies):
        assert self.sat is not None
        self.mdp, self.selected_choices = colored_mdp.build(self.parameter_space)
        if self.sat is False:
            result = self.mdp.model_check_property(prop)
            assert not result.sat
        else:
            PolicyTreeSynthesizer.double_check_policy(colored_mdp, self, prop, policies[self.policy_index][0])


    def merge_children_indices(self, indices):
        if len(indices) <= 1:
            return
        target = indices[0]
        for j in reversed(indices[1:]):
            self.suboptions[target] += self.suboptions[j]
            self.child_nodes[target].parameter_space.parameter_set_options(self.splitter,self.suboptions[target])
            self.suboptions.pop(j)
            self.child_nodes.pop(j)

        if len(self.child_nodes) > 1:
            return
        # a single child remains, can be merged into parent
        child_node = self.child_nodes[0]
        self.sat = child_node.sat
        self.policy_index = child_node.policy_index
        self.splitter = None
        self.suboptions = []
        self.child_nodes = []

    def merge_children_sat(self):
        indices = [i for i,child in enumerate(self.child_nodes) if child.sat is True]
        self.merge_children_indices(indices)

    def merge_children_having_same_solution(self):
        if self.is_leaf:
            return

        # merge UNSAT children
        indices = [i for i,child in enumerate(self.child_nodes) if child.sat is False]
        self.merge_children_indices(indices)

        # merge children having the same policy
        i = 0
        while i < len(self.child_nodes):
            child1 = self.child_nodes[i]
            if child1.sat is not True:
                i += 1
                continue

            join_to_i = [i]
            # collect other children to merge to i
            for j in range(i+1,len(self.child_nodes)):
                child2 = self.child_nodes[j]
                if child2.policy_index == child1.policy_index:
                    join_to_i.append(j)
            self.merge_children_indices(join_to_i)
            i += 1

    def make_policies_compatible(colored_mdp, prop, node1, node2, policies):
        policy1 = policies[node1.policy_index]
        policy2 = policies[node2.policy_index]
        policy = merge_policies(policy1,policy2)
        if policy is not None:
            return policy

        policy12,policy21 = merge_policies_exclusively(policy1,policy2)

        # try policy1 for node2's parameter space
        policy,mdp = colored_mdp.fix_and_apply_policy_to_parameter_space(node2.selected_choices, policy12)
        policy_result = mdp.model_check_property(prop, alt=True)
        PolicyTreeNode.mdps_model_checked += 1
        if policy_result.sat:
            return policy

        # try policy2 for node1's parameter space
        policy,mdp = colored_mdp.fix_and_apply_policy_to_parameter_space(node1.selected_choices, policy21)
        policy_result = mdp.model_check_property(prop, alt=True)
        PolicyTreeNode.mdps_model_checked += 2
        if policy_result.sat:
            return policy

        # neither fits
        return None

    def merge_children_having_compatible_policies(self, colored_mdp, prop, policies):
        if self.is_leaf:
            return
        i = 0
        while i < len(self.child_nodes):
            child1 = self.child_nodes[i]
            if child1.sat is not True:
                i += 1
                continue

            join_to_i = [i]
            # collect other children to merge to i
            for j in range(i+1,len(self.child_nodes)):
                child2 = self.child_nodes[j]
                if child2.sat is not True:
                    continue
                policy = PolicyTreeNode.make_policies_compatible(colored_mdp,prop,child1,child2,policies)
                if policy is None:
                    continue
                # nodes can be merged
                policies[child1.policy_index] = policy
                policies[child2.policy_index] = None
                join_to_i.append(j)

            self.merge_children_indices(join_to_i)
            i += 1

    def skip_redundant_children(self):
        ''' Adopt grandchildren of each child that uses the same splitter as self. '''
        if self.splitter is None:
            return
        suboptions = []
        child_nodes = []
        for child_index,child in enumerate(self.child_nodes):
            if child.splitter != self.splitter:
                suboptions.append(self.suboptions[child_index])
                child_nodes.append(self.child_nodes[child_index])
            else:
                for grandchild_index,grandchild in enumerate(child.child_nodes):
                    suboptions.append(child.suboptions[grandchild_index])
                    child_nodes.append(grandchild)
        self.suboptions = suboptions
        self.child_nodes = child_nodes



    @property
    def node_id(self):
        return str(self.parameter_space).replace(' ','').replace(':','=')

    def add_nodes_to_graphviz_tree(self, graphviz_tree):
        node_label = ""
        if self.sat is False:
            node_label = "∅"
            # node_label = "X"
        elif self.sat is True:
            # node_label = "✓"
            node_label = f"p{self.policy_index}"
        graphviz_tree.node(self.node_id, label=node_label, shape="ellipse", width="0.15", height="0.15")
        # enumerating in reverse to print policies in ascending order, from left to right
        for child in reversed(self.child_nodes):
            child.add_nodes_to_graphviz_tree(graphviz_tree)

    def add_edges_to_graphviz_tree(self, graphviz_tree):
        if self.splitter is None:
            return
        splitter_name = self.parameter_space.parameter_name(self.splitter)
        for index,child in enumerate(self.child_nodes):
            edge_label = self.parameter_space.parameter_options_to_string(self.splitter,self.suboptions[index])
            graphviz_tree.edge(self.node_id,child.node_id,label=edge_label)
            child.add_edges_to_graphviz_tree(graphviz_tree)



class PolicyTree:

    def __init__(self, parameter_space):
        self.root = PolicyTreeNode(parameter_space)
        self.policies = []

    def new_policy(self, policy):
        policy_index = len(self.policies)
        mask = [state for state,action in enumerate(policy) if action is not None]
        self.policies.append( (policy,mask) )
        return policy_index

    def collect_all(self):
        node_queue = [self.root]
        all_nodes = []
        while node_queue:
            node = node_queue.pop(0)
            all_nodes.append(node)
            node_queue += node.child_nodes
        return all_nodes

    def collect_leaves(self):
        node_queue = [self.root]
        leaves = []
        while node_queue:
            node = node_queue.pop(0)
            if node.is_leaf:
                leaves.append(node)
            else:
                node_queue = node_queue + node.child_nodes
        return leaves

    def collect_nonleaves(self):
        node_queue = [self.root]
        nonleaves = []
        while node_queue:
            node = node_queue.pop(0)
            if not node.is_leaf:
                nonleaves.append(node)
                node_queue = node_queue + node.child_nodes
        return nonleaves

    def collect_sat(self):
        node_queue = [self.root]
        sat = []
        while node_queue:
            node = node_queue.pop(0)
            if node.sat:
                sat.append(node)
            else:
                node_queue += node.child_nodes
        return sat


    def double_check(self, colored_mdp, prop):
        leaves = self.collect_leaves()
        logger.info("double-checking {} parameter spaces...".format(len(leaves)))
        for leaf in leaves:
            leaf.double_check(colored_mdp,prop,self.policies)
        logger.info("all solutions are OK")


    def count_diversity(self):
        from collections import defaultdict
        children_stats = defaultdict(int)
        for node in self.collect_all():
            if node.is_leaf:
                continue
            with_policy = len([node for node in node.child_nodes if node.sat])
            with_none = len([node for node in node.child_nodes if node.policy is None])
            with_false = len([node for node in node.child_nodes if node.policy==False])
            children_stats[(with_policy,with_none,with_false)] += 1
        return children_stats


    def print_stats(self):
        members_total = self.root.parameter_space.size
        num_policies = len(self.policies)

        members_satisfied = 0
        num_leaves_singleton = 0
        leaves = self.collect_leaves()
        for node in leaves:
            if node.parameter_space.size==1:
                num_leaves_singleton += 1
            if node.sat:
                members_satisfied += node.parameter_space.size
        satisfied_percentage = round(members_satisfied/members_total*100,0)
        members_unsatisfied = members_total-members_satisfied

        num_nodes = len(self.collect_all())
        num_leaves = len(leaves)
        num_leaves_solvable = len(self.collect_sat())
        num_leaves_unsolvable = num_leaves-num_leaves_solvable
        if num_leaves_solvable > 0:
            leaf_solvable_avg = round(members_satisfied / num_leaves_solvable,1)
        else:
            leaf_solvable_avg = "NA"

        if num_leaves_unsolvable > 0:
            leaf_unsolvable_avg = round(members_unsatisfied / num_leaves_unsolvable,1)
        else:
            leaf_unsolvable_avg = "NA"

        logger.info("--------------------")
        logger.info("Policy tree summary:")
        logger.info("found {} satisfying {} for {}/{} family members ({}%)".format(
            num_policies, "policy" if num_policies==1 else "policies", members_satisfied,members_total,satisfied_percentage))
        logger.info("policy tree has {} nodes, {} of them are leaves:".format(num_nodes, num_leaves))
        logger.info("\t  solvable leaves: {} (avg.size: {})".format(num_leaves_solvable,leaf_solvable_avg))
        logger.info("\tunsolvable leaves: {} (avg.size: {})".format(num_leaves_unsolvable,leaf_unsolvable_avg))
        logger.info("\t singleton leaves: {}".format(num_leaves_singleton))

        logger.info("--------------------")

    def discard_unused_policies(self):
        policy_old_to_new  = [None for _ in self.policies]
        num_policies = 0
        for policy_index,policy in enumerate(self.policies):
            if policy is not None:
                policy_old_to_new[policy_index] = num_policies
                num_policies += 1
        self.policies = [policy for policy in self.policies if policy is not None]
        assert num_policies == len(self.policies)
        for leaf in self.collect_sat():
            leaf.policy_index = policy_old_to_new[leaf.policy_index]
            assert leaf.policy_index is not None

    def merge_compatible_policies(self, policy_indices):
        policy_old_to_new_map = [policy_index for policy_index,_ in enumerate(self.policies)]

        for policy1_index_index,policy1_index in enumerate(policy_indices):
            policy1 = self.policies[policy1_index]
            if policy1 is None:
                continue
            for policy2_index in policy_indices[policy1_index_index+1:]:
                policy2 = self.policies[policy2_index]
                if policy2 is None:
                    continue
                policy = merge_policies(policy1,policy2)
                if policy is None:
                    continue
                # store updated policy
                self.policies[policy1_index] = policy
                policy1 = policy
                # discard irrelevant policy
                policy_old_to_new_map[policy2_index] = policy1_index
                self.policies[policy2_index] = None

        return policy_old_to_new_map

    def postprocess(self, colored_mdp, prop):

        postprocessing_timer = paynt.utils.timer.Timer()
        postprocessing_timer.start()
        logger.info("post-processing the policy tree...")

        logger.info("merging SAT siblings solved by non-exclusively compatible policies...")
        PolicyTreeNode.mdps_model_checked = 0
        nodes_before = self.root.num_nodes()
        for node in reversed(self.collect_all()):
            node.merge_children_having_compatible_policies(colored_mdp, prop, self.policies)
        self.discard_unused_policies()
        nodes_removed = nodes_before - self.root.num_nodes()
        logger.info("additional {} MDPs were model checked".format(PolicyTreeNode.mdps_model_checked))
        logger.info("removed {} nodes".format(nodes_removed))

        logger.info("merging all exclusively compatible policies...")
        policies_before = len(self.policies)
        policy_indices = [index for index,_ in enumerate(self.policies)]
        policy_old_to_new_map = self.merge_compatible_policies(policy_indices)
        for leaf in self.collect_sat():
            leaf.policy_index = policy_old_to_new_map[leaf.policy_index]
        self.discard_unused_policies()
        policies_removed = policies_before - len(self.policies)
        logger.info("removed {} policies".format(policies_removed))

        logger.info("reducing tree height...")
        nodes_before = self.root.num_nodes()
        for node in reversed(self.collect_nonleaves()):
            node.skip_redundant_children()
        nodes_removed = nodes_before - self.root.num_nodes()
        logger.info("removed {} nodes".format(nodes_removed))

        logger.info("merging siblings that have the same solution...")
        nodes_before = self.root.num_nodes()
        for node in reversed(self.collect_nonleaves()):
            node.merge_children_having_same_solution()
        nodes_removed = nodes_before - self.root.num_nodes()
        logger.info("removed {} nodes".format(nodes_removed))

        postprocessing_timer.stop()
        time = int(postprocessing_timer.read())
        logger.debug(f"postprocessing took {time} s")
        return time


    def extract_policies(self, colored_mdp):
        return {
            f"p{policy_index}" : colored_mdp.policy_to_state_valuation_actions(policy)
            for policy_index,policy in enumerate(self.policies)
        }

    def extract_policy_tree(self, colored_mdp):
        logging.getLogger("graphviz").setLevel(logging.WARNING)
        logging.getLogger("graphviz.sources").setLevel(logging.ERROR)
        graphviz_tree = graphviz.Digraph(comment="policy_tree")
        self.root.add_nodes_to_graphviz_tree(graphviz_tree)
        self.root.add_edges_to_graphviz_tree(graphviz_tree)
        return graphviz_tree



class MdpFamilyResult:
    def __init__(self):
        # if None, then family is undediced
        # if False, then all family members are UNSAT
        # otherwise, contains a satisfying policy for all MDPs in the family
        self.policy = None

        self.game_policy = None
        self.parameter_selection = None
        self.splitter = None

class PolicyTreeSynthesizer(paynt.synthesizer.synthesizer.Synthesizer):

    # if True, tree leaves will be double-checked after synthesis
    double_check_policy_tree_leaves = False

    @property
    def method_name(self):
        return "AR (policy tree)"

    @staticmethod
    def double_check_policy(colored_mdp, node, prop, policy):
        _,mdp = colored_mdp.fix_and_apply_policy_to_parameter_space(node.selected_choices, policy)
        if node.parameter_space.size == 1:
            colored_mdp.assert_mdp_is_deterministic(mdp, node.parameter_space)
        DOUBLE_CHECK_PRECISION = 1e-6
        default_precision = Property.model_checking_precision
        Property.set_model_checking_precision(DOUBLE_CHECK_PRECISION)
        policy_result = mdp.model_check_property(prop, alt=True)
        Property.set_model_checking_precision(default_precision)
        if not policy_result.sat:
            logger.warning("policy should be SAT but (most likely due to model checking precision) has value {}".format(policy_result.value))
        return


    def verify_policy(self, selected_choices, prop, policy):
        '''
        :param selected_choices the compatible-choices bitmask to verify against -- callers outside this
            class have no PolicyTreeNode to read it from, so it must be supplied explicitly (see
            ParameterSpaceEvaluation.selected_choices, captured at decision time)
        '''
        _,mdp = self.colored_mdp.fix_and_apply_policy_to_parameter_space(selected_choices, policy)
        policy_result = mdp.model_check_property(prop, alt=True)
        self.stat.iteration(mdp)
        return policy_result.sat


    def solve_singleton(self, node, prop):
        result = node.mdp.model_check_property(prop)
        self.stat.iteration(node.mdp)
        if not result.sat:
            return False
        policy = self.colored_mdp.scheduler_to_policy(result.result.scheduler, node.mdp)

        # uncomment below to preemptively double-check the policy
        # PolicyTreeSynthesizer.double_check_policy(self.colored_mdp, node, prop, policy)
        return policy


    def solve_game_abstraction(self, node, prop, game_solver):
        # construct and solve the game abstraction
        # logger.debug("solving game abstraction...")

        game_solver.solve_sg(node.selected_choices)
        # game_solver.solve_smg(node.selected_choices)

        game_value = game_solver.solution_value
        self.stat.iteration_game(node.mdp.states)
        game_sat = prop.satisfies_threshold_within_precision(game_value)
        # logger.debug("game solved, value is {}".format(game_value))
        game_policy = game_solver.solution_state_to_player1_action
        # fix irrelevant choices
        game_policy_fixed = self.colored_mdp.empty_policy()
        for state,action in enumerate(game_policy):
            if action < self.colored_mdp.num_actions:
                game_policy_fixed[state] = action
        game_policy = game_policy_fixed
        return game_policy,game_sat

    def state_to_choice_to_parameter_selection(self, state_to_choice):
        if self.task.discard_unreachable_choices:
            state_to_choice = paynt.underlying_model.underlying_model.ModelIndex.discard_unreachable_choices(
                self.colored_mdp.underlying_mdp, self.colored_mdp.choice_destinations, state_to_choice)
        scheduler_choices = paynt.underlying_model.underlying_model.ModelIndex.state_to_choice_to_choices(
            self.colored_mdp.underlying_mdp, state_to_choice)
        parameter_selection = self.colored_mdp.coloring.collectHoleOptions(scheduler_choices)
        return scheduler_choices,parameter_selection

    def parse_game_scheduler(self, game_solver):
        state_to_choice = game_solver.solution_state_to_quotient_choice.copy()
        scheduler_choices,parameter_selection = self.state_to_choice_to_parameter_selection(state_to_choice)
        state_values = game_solver.solution_state_values
        return scheduler_choices,parameter_selection,state_values

    def verify_parameter_space(self, node, game_solver, prop):
        # logger.info("investigating parameter space of size {}".format(node.parameter_space.size))
        node.mdp, node.selected_choices = self.colored_mdp.build(node.parameter_space)
        mdp_family_result = MdpFamilyResult()

        if node.parameter_space.size == 1:
            mdp_family_result.policy = self.solve_singleton(node,prop)
            return mdp_family_result

        if node.candidate_policy is None:
            game_policy,game_sat = self.solve_game_abstraction(node,prop,game_solver)
        else:
            game_policy = node.candidate_policy
            game_sat = False

        mdp_family_result.game_policy = game_policy
        if game_sat:
            mdp_family_result.policy = game_policy
            return mdp_family_result

        # solve primary direction for the MDP abstraction
        mdp_result = node.mdp.model_check_property(prop)
        mdp_value = mdp_result.value
        self.stat.iteration(node.mdp)
        # logger.debug("primary-primary direction solved, value is {}".format(mdp_value))
        if not mdp_result.sat:
            mdp_family_result.policy = False
            return mdp_family_result

        # undecided: choose scheduler choices to be used for splitting
        scheduler_choices,parameter_selection,state_values = self.parse_game_scheduler(game_solver)

        splitter = self.choose_splitter(node.parameter_space,prop,scheduler_choices,state_values,parameter_selection)
        mdp_family_result.splitter = splitter
        mdp_family_result.parameter_selection = parameter_selection
        return mdp_family_result

    def choose_splitter(self, parameter_space, prop, scheduler_choices, state_values, parameter_selection):
        inconsistent_assignments = {parameter:options for parameter,options in enumerate(parameter_selection) if len(options) > 1}
        if len(inconsistent_assignments)==0:
            # pick any parameter with multiple options involved in the parameter selection
            for parameter,options in enumerate(parameter_selection):
                if parameter_space.parameter_num_options(parameter) > 1 and len(options) > 0:
                    return parameter
            # pick any parameter with multiple options
            # logger.debug("picking an arbitrary parameter...")
            for parameter in range(parameter_space.num_parameters):
                if parameter_space.parameter_num_options(parameter) > 1:
                    return parameter
        if len(inconsistent_assignments)==1:
            for parameter in inconsistent_assignments.keys():
                return parameter

        # compute scores for inconsistent parameters
        scores = self.compute_scores(prop, scheduler_choices, state_values, inconsistent_assignments)
        splitters = paynt.utils.scoring.parameters_with_max_score(scores)
        splitter = splitters[0]
        return splitter

    def compute_scores(self, prop, scheduler_choices, state_values, inconsistent_assignments):
        mdp = self.colored_mdp.underlying_mdp
        choice_values = paynt.underlying_model.underlying_model.ModelIndex.choice_values(mdp, prop, state_values)
        expected_visits = paynt.underlying_model.underlying_model.ModelIndex.compute_expected_visits(
            mdp, prop, scheduler_choices, disable_expected_visits=self.task.disable_expected_visits)
        underlying_mdp_choice_map = [choice for choice in range(self.colored_mdp.underlying_mdp.nr_choices)]
        scores = paynt.utils.scoring.estimate_scheduler_difference(
            self.colored_mdp, self.colored_mdp.underlying_mdp, underlying_mdp_choice_map, inconsistent_assignments, choice_values, expected_visits)
        return scores

    def assign_candidate_policy(self, parameter_subspaces, candidate_policies, parameter_selection, splitter, policy):
        ''' Fill in candidate_policies[i] = policy for whichever parameter_subspaces[i] contains the parameter
        selection, in place -- parameter_subspaces are plain ParameterSpace values here (not yet wrapped as
        PolicyTreeNode children), so the candidate policy can't be attached directly until attach_children
        wraps them (see evaluate_all). '''
        policy_consistent = all([len(options) <= 1 for options in parameter_selection])
        if not policy_consistent:
            return
        # associate the branch of the split that contains the parameter selection with the policy
        used_options = parameter_selection[splitter]
        if len(used_options) != 1:
            # not sure what to do in this case
            return
        option = used_options[0]
        for index,parameter_subspace in enumerate(parameter_subspaces):
            if option in parameter_subspace.parameter_options(splitter):
                candidate_policies[index] = policy
                return

    def split(self, parameter_space, prop, parameter_selection, splitter, policy):
        # split the parameter
        used_options = parameter_selection[splitter]
        if len(used_options) > 1:
            # used_options = used_options[0:1]
            core_suboptions = [[option] for option in used_options]
            other_suboptions = [option for option in parameter_space.parameter_options(splitter) if option not in used_options]
            if other_suboptions:
                other_suboptions = [other_suboptions]
            else:
                other_suboptions = []
            suboptions = other_suboptions + core_suboptions # DFS solves core first
        else:
            options = parameter_space.parameter_options(splitter)
            assert len(options) > 1
            half = len(options) // 2
            suboptions = [options[:half], options[half:]]

        parameter_subspaces = parameter_space.split(splitter,suboptions)
        candidate_policies = [None for _ in parameter_subspaces]

        if not self.task.discard_unreachable_choices:
            self.assign_candidate_policy(parameter_subspaces, candidate_policies, parameter_selection, splitter, policy)

        return suboptions,parameter_subspaces,candidate_policies


    def evaluate_all(self, parameter_space, prop, keep_value_only=False):
        assert not prop.reward, "expecting reachability probability propery"
        game_solver = self.colored_mdp.build_game_abstraction_solver(prop)
        policy_tree = PolicyTree(parameter_space)

        undecided_leaves = [policy_tree.root]
        while undecided_leaves:

            # gi = self.stat.iterations_game
            # if gi is not None and gi > 1000:
            #     return None

            node = undecided_leaves.pop(-1)
            result = self.verify_parameter_space(node,game_solver,prop)
            node.candidate_policy = None

            if result.policy is not None:
                self.explore(node.parameter_space)
                if node != policy_tree.root:
                    node.mdp = None
                if result.policy is False:
                    node.sat = False
                else:
                    node.sat = True
                    node.policy_index = policy_tree.new_policy(result.policy)
                continue

            # refine
            suboptions,parameter_subspaces,candidate_policies = self.split(node.parameter_space, prop, result.parameter_selection, result.splitter, result.game_policy)
            if node != policy_tree.root:
                node.mdp = None
            node.attach_children(result.splitter,suboptions,parameter_subspaces,candidate_policies)
            undecided_leaves += node.child_nodes

        if PolicyTreeSynthesizer.double_check_policy_tree_leaves:
            policy_tree.double_check(self.colored_mdp, prop)
        policy_tree.print_stats()

        self.stat.num_mdps_total = self.colored_mdp.parameter_space.size
        self.stat.num_mdps_sat = sum([n.parameter_space.size for n in policy_tree.collect_sat()])
        self.stat.num_nodes = len(policy_tree.collect_all())
        self.stat.num_leaves = len(policy_tree.collect_leaves())
        self.stat.num_policies = len(policy_tree.policies)
        postprocessing_time = policy_tree.postprocess(self.colored_mdp, prop)
        policy_tree.print_stats()
        self.stat.postprocessing_time = postprocessing_time
        self.stat.num_nodes_merged = len(policy_tree.collect_all())
        self.stat.num_leaves_merged = len(policy_tree.collect_leaves())
        self.stat.num_policies_merged = len(policy_tree.policies)
        self.policy_tree = policy_tree

        # convert policy tree to parameter space evaluations
        evaluations = []
        for node in policy_tree.collect_leaves():
            policy = policy_tree.policies[node.policy_index] if node.sat else None
            evaluation = paynt.synthesizer.synthesizer.ParameterSpaceEvaluation(
                node.parameter_space,None,node.sat,policy=policy,selected_choices=node.selected_choices)
            evaluations.append(evaluation)
        return evaluations


    def run(self, optimum_threshold=None):
        return self.evaluate()


    def export_evaluation_result(self, evaluations, export_filename_base):
        import json
        policies = self.policy_tree.extract_policies(self.colored_mdp)
        policies_json = {}
        for index,key_value in enumerate(policies.items()):
            policy_id,policy = key_value
            policy_json = self.colored_mdp.policy_to_json(policy)
            policies_json[policy_id] = policy_json
        policies_string = json.dumps(policies_json, indent=4)

        policies_filename = export_filename_base + ".json"
        with open(policies_filename, 'w') as file:
            file.write(policies_string)

        logger.info(f"exported policies to {policies_filename}")

        tree = self.policy_tree.extract_policy_tree(self.colored_mdp)
        tree_filename = export_filename_base + ".dot"
        with open(tree_filename, 'w') as file:
            file.write(tree.source)
        logger.info(f"exported policy tree to {tree_filename}")

        tree_visualization_filename = export_filename_base + ".png"
        tree.render(export_filename_base, format="png", cleanup=True) # using export_filename_base since graphviz appends .png by default
        logger.info(f"exported policy tree visualization to {tree_visualization_filename}")
