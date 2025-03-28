import heapq

import stormpy
import payntbind

import paynt.family.family
import paynt.synthesizer.synthesizer

import paynt.quotient.quotient
import paynt.verification.property_result
from paynt.verification.property import Property
import paynt.utils.timer

import paynt.family.smt
import paynt.synthesizer.conflict_generator.dtmc
import paynt.synthesizer.conflict_generator.mdp


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


class PolicyTreeNode:

    def __init__(self, family):
        self.family = family
        
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

    def split(self, splitter, suboptions, subfamilies):
        self.splitter = splitter
        self.suboptions = suboptions
        self.child_nodes = []
        for subfamily in subfamilies:
            child_node = PolicyTreeNode(subfamily)
            self.child_nodes.append(child_node)

    def double_check(self, quotient, prop, policies):
        assert self.sat is not None
        quotient.build(self.family)
        if self.sat is False:
            result = self.family.mdp.model_check_property(prop)
            assert not result.sat
        else:
            SynthesizerPolicyTree.double_check_policy(quotient, self.family, prop, policies[self.policy_index][0])


    def merge_children_indices(self, indices):
        if len(indices) <= 1:
            return
        target = indices[0]
        for j in reversed(indices[1:]):
            self.suboptions[target] += self.suboptions[j]
            self.child_nodes[target].family.hole_set_options(self.splitter,self.suboptions[target])
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

    def make_policies_compatible(quotient, prop, node1, node2, policies):
        if node1.changed:
            return None

        policy1 = policies[node1.policy_index]
        policy2 = policies[node2.policy_index]
        policy = merge_policies(policy1,policy2)
        if policy is not None:
            node1.changed = True
            return policy
        
        # try policy1 for family2
        mdp1 = quotient.apply_policy_to_family(node2.family, policy1[0])
        policy_result1 = mdp1.model_check_property(prop, alt=True)
        PolicyTreeNode.mdps_model_checked += 1

        # try policy2 for family1
        mdp2 = quotient.apply_policy_to_family(node1.family, policy2[0])
        policy_result2 = mdp2.model_check_property(prop, alt=True)
        PolicyTreeNode.mdps_model_checked += 2

        if policy_result1.sat and policy_result2.sat:
            mask1 = [state for state, action in enumerate(policy1[0]) if action is not None]
            mask2 = [state for state, action in enumerate(policy2[0]) if action is not None]
            if len(mask1) <= len(mask2):
                node1.changed = True
                return (policy1[0], mask1)
            else:
                node1.changed = True
                return (policy2[0], mask2)
        elif policy_result1.sat:
            mask1 = [state for state, action in enumerate(policy1[0]) if action is not None]
            node1.changed = True
            return (policy1[0], mask1)
        elif policy_result2.sat:
            mask2 = [state for state, action in enumerate(policy2[0]) if action is not None]
            node1.changed = True
            return (policy2[0], mask2)

        policy12,policy21 = merge_policies_exclusively(policy1,policy2)

        # try policy1 for family2
        policy,mdp = quotient.fix_and_apply_policy_to_family(node2.family, policy12)
        policy_result = mdp.model_check_property(prop, alt=True)
        PolicyTreeNode.mdps_model_checked += 1
        if policy_result.sat:
            node1.changed = True
            return policy

        # try policy2 for family1
        policy,mdp = quotient.fix_and_apply_policy_to_family(node1.family, policy21)
        policy_result = mdp.model_check_property(prop, alt=True)
        PolicyTreeNode.mdps_model_checked += 2
        if policy_result.sat:
            node1.changed = True
            return policy

        # neither fits
        return None

    def merge_children_having_compatible_policies(self, quotient, prop, policies):
        if self.is_leaf:
            return
        i = len(self.child_nodes) - 1
        # LDOK TODO: is reverse order ok ask roman
        # imo should be fine, this way i'm applying one policy to as many families as possible,
        # then repeating with next policy
        while i >= 0 and self.child_nodes:
            child1 = self.child_nodes[i]
            child1.changed = False  # policy can change only once, son is in future for further merging
            if child1.sat is not True:
                i -= 1
                continue

            join_to_i = [i]
            # collect other children to merge to i
            for j in range(i):
                child2 = self.child_nodes[j]
                if child2.sat is not True:
                    continue
                policy = PolicyTreeNode.make_policies_compatible(quotient, prop, child1, child2, policies)
                if policy is None:
                    continue
                # nodes can be merged
                policies[child1.policy_index] = policy
                policies[child2.policy_index] = None
                join_to_i.append(j)

            # assert len(join_to_i) <= 2
            self.merge_children_indices(join_to_i)
            i -= 1

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
        return str(self.family).replace(' ','').replace(':','=')

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

    def get_policy_family_from_index(self, index: int):
        if self.policy_index == index:
            return self.family # have to do node_id
        for child in self.child_nodes:
            family = child.get_policy_family_from_index(index)
            if family is not None:
                return family
        return None

    def add_edges_to_graphviz_tree(self, graphviz_tree):
        if self.splitter is None:
            return
        splitter_name = self.family.hole_name(self.splitter)
        for index,child in enumerate(self.child_nodes):
            edge_label = self.family.hole_options_to_string(self.splitter,self.suboptions[index])
            graphviz_tree.edge(self.node_id,child.node_id,label=edge_label)
            child.add_edges_to_graphviz_tree(graphviz_tree)



class PolicyTree:

    def __init__(self, family):
        self.root = PolicyTreeNode(family)
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


    def double_check(self, quotient, prop):
        leaves = self.collect_leaves()
        logger.info("double-checking {} families...".format(len(leaves)))
        for leaf in leaves:
            leaf.double_check(quotient,prop,self.policies)
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
        members_total = self.root.family.size
        num_policies = len(self.policies)
        
        members_satisfied = 0
        num_leaves_singleton = 0
        leaves = self.collect_leaves()
        for node in leaves:
            if node.family.size==1:
                num_leaves_singleton += 1
            if node.sat:
                members_satisfied += node.family.size
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

        print("--------------------")
        print("Policy tree summary:")
        print("found {} satisfying {} for {}/{} family members ({}%)".format(
            num_policies, "policy" if num_policies==1 else "policies", members_satisfied,members_total,satisfied_percentage))
        print("policy tree has {} nodes, {} of them are leaves:".format(num_nodes, num_leaves))
        print("\t  solvable leaves: {} (avg.size: {})".format(num_leaves_solvable,leaf_solvable_avg))
        print("\tunsolvable leaves: {} (avg.size: {})".format(num_leaves_unsolvable,leaf_unsolvable_avg))
        print("\t singleton leaves: {}".format(num_leaves_singleton))

        print("--------------------")

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
    
    def postprocess(self, quotient, prop):

        postprocessing_timer = paynt.utils.timer.Timer()
        postprocessing_timer.start()
        logger.info("post-processing the policy tree...")

        logger.info("merging SAT siblings solved by non-exclusively compatible policies...")
        PolicyTreeNode.mdps_model_checked = 0
        nodes_before = self.root.num_nodes()
        for node in reversed(self.collect_all()):
            node.merge_children_having_compatible_policies(quotient, prop, self.policies)
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

    
    def extract_policies(self, quotient, keep_family=False):
        return {
            f"p{policy_index}" : quotient.policy_to_state_valuation_actions(policy, self.root.get_policy_family_from_index(policy_index) if keep_family else None)
            for policy_index,policy in enumerate(self.policies)
        }

    def extract_policy_tree(self, quotient):
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
        self.hole_selection = None
        self.splitter = None

class SynthesizerPolicyTree(paynt.synthesizer.synthesizer.Synthesizer):

    # if True, tree leaves will be double-checked after synthesis
    double_check_policy_tree_leaves = False
    # if True, unreachable choices will be discarded from the splitting scheduler
    discard_unreachable_choices = False
    ldok_postprocessing_times = paynt.utils.timer.Timer()
    
    @property
    def method_name(self):
        return "AR (policy tree)"

    @staticmethod
    def double_check_policy(quotient, family, prop, policy):
        _,mdp = quotient.fix_and_apply_policy_to_family(family, policy)
        #if family.size == 1:
        #    # due to experimental state removal this may not hold in irrelevant states
        #    quotient.assert_mdp_is_deterministic(mdp, family)
        DOUBLE_CHECK_PRECISION = 1e-6
        default_precision = Property.model_checking_precision
        Property.set_model_checking_precision(DOUBLE_CHECK_PRECISION)
        policy_result = mdp.model_check_property(prop, alt=True)
        Property.set_model_checking_precision(default_precision)
        if not policy_result.sat:
            # logger.warning("policy should be SAT but (most likely due to model checking precision) has value {}".format(policy_result.value))
            return False
        return True
    
    
    def verify_policy(self, family, prop, policy):
        _,mdp = self.quotient.fix_and_apply_policy_to_family(family, policy)
        policy_result = mdp.model_check_property(prop, alt=True)
        self.stat.iteration(mdp)
        return policy_result.sat

    
    def solve_singleton(self, family, prop):
        result = family.mdp.model_check_property(prop)
        self.stat.iteration(family.mdp)
        if not result.sat:
            return False
        policy = self.quotient.scheduler_to_policy(result.result.scheduler, family.mdp)
    
        # uncomment below to preemptively double-check the policy
        # SynthesizerPolicyTree.double_check_policy(self.quotient, family, prop, policy)
        return policy


    def solve_game_abstraction(self, family, prop, game_solver):
        # construct and solve the game abstraction
        # logger.debug("solving game abstraction...")

        game_solver.solve_sg(family.selected_choices)
        # game_solver.solve_smg(family.selected_choices)

        # [1, 2, 4, 6, 8, 10, 13, 14, 17, 18, 19, 21]
        # bit vector(16/22) [0 1 2 4 6 7 8 9 10 13 14 16 17 18 19 20 ]
        # LADA TODO: maybe endstate self loop missing?
        game_value = game_solver.solution_value
        self.stat.iteration_game(family.mdp.states)
        game_sat = prop.satisfies_threshold_within_precision(game_value)
        # logger.debug("game solved, value is {}".format(game_value))
        game_policy = game_solver.solution_state_to_player1_action
        # fix irrelevant choices
        game_policy_fixed = self.quotient.empty_policy()
        for state,action in enumerate(game_policy):
            if action < self.quotient.num_actions:
                game_policy_fixed[state] = action
        game_policy = game_policy_fixed
        
        mdp_fixed_choices = game_solver.environment_choice_mask

        if game_sat:
            # logger.debug("debug: state to destination")
            # for n, (state,choice,prob) in enumerate(zip(self.quotient.state_valuations,game_solver.solution_state_to_quotient_choice,game_solver.solution_state_values)):
            #     if choice == len(self.quotient.choice_to_action):
            #         continue # usually sink state
            #     # print in format n: state [prob]  -> possible destinations
            #     logger.debug("{}:{} [{:.2f}] -> {}".format(n,state,prob,self.quotient.choice_destinations[game_solver.solution_state_to_quotient_choice[n]]))
            # logger.debug("debug: state to destination end")

            if self.ldokoupi_flag:
                self.ldok_postprocessing_times.start()
                # order is important - cut most diverging paths first
                # LADA TODO: skip for now
                # game_policy = self.post_process_game_policy_gradient(game_policy, game_solver, family, prop)
                # game_policy = self.post_process_game_policy_prob(game_policy, game_solver, family, prop)
                # game_policy = self.post_process_bruteforce(game_policy, game_solver, family, prop)
                self.ldok_postprocessing_times.stop()

        return game_policy,game_sat,mdp_fixed_choices

    
    def post_process_game_policy_gradient(self, game_policy, game_solver, family, prop, check_granularity=4):
        """ DFS only on non-descending gradient path until reaching the target
        then verify if the policy satisfies the property based on check_granularity
        if negative check every shortest path from init to end state / check_granularity
        This post is applicable iff self loop ( _stay_ ) is first action in MDP
        """
        # LDOK TODO: need to account for minimizing properties -> non-increasing gradient

        # self loop has to be first applicable action
        if self.quotient.action_labels[0] == "__no_label__":
            if not self.quotient.action_labels[1].startswith("_stay"):
                return game_policy
        else:
            if not self.quotient.action_labels[0].startswith("_stay"):
                return game_policy
        # self loops serves as verification against worst case scenario -> any other action is better

        depth = -1
        end_state = next((state for state in game_solver.state_is_target if state), -1)
        assert end_state != -1

        assert len(self.quotient.quotient_mdp.initial_states) == 1
        game_policy_post = self.quotient.empty_policy()

        explored_states = set()  # avoid cycles
        current_state = self.quotient.quotient_mdp.initial_states[0]
        state_stack = [(game_solver.solution_state_values[current_state], current_state)]
        bfs_flag = False
        que = []

        while state_stack or que:
            if state_stack:
                _, current_state = heapq.heappop(state_stack)
            else:
                current_state = que.pop(0)

            if current_state in explored_states:
                continue
            game_policy_post[current_state] = game_policy[current_state]
            explored_states.add(current_state)

            cur_choice = game_solver.solution_state_to_quotient_choice[current_state]
            target_states = self.quotient.choice_destinations[cur_choice]

            if len(target_states) != 1:
                depth += 1

            if current_state == end_state:
                bfs_flag = True
            if current_state == end_state and check_granularity < 0:
                check_granularity = depth // abs(check_granularity)  # shortest path length

            # Push the sorted target states onto the stack - highest gradient goes out first
            if not bfs_flag:
                for target_state in target_states:
                    heapq.heappush(state_stack, (-game_solver.solution_state_values[target_state], target_state))
            else:
                for target_state in target_states:
                    que.append(target_state)

            if end_state in explored_states and check_granularity > 0 and depth % check_granularity == 0:
                sat = SynthesizerPolicyTree.double_check_policy(self.quotient, family, prop, game_policy_post)
                if sat:
                    return game_policy_post

        # logger.debug("policy couldn't be simplified by gradient")
        return game_policy


    def post_process_game_policy_prob(self, game_policy, game_solver, family, prop, check_granularity=1):
        """ DFS only on max probability path until reaching the target
        then verify if the policy satisfies the property based on check_granularity
        if set to -1 then check every multiple of shortest path from init to end state
        This post is applicable iff self loop ( _stay_ ) is first action in MDP
        """

        def getProbForChoice(choice, target):
            choices_transition_matrix = self.quotient.quotient_mdp.transition_matrix
            for entry in choices_transition_matrix.get_row(choice):
                dst, prob = entry.column, entry.value()  # entry.getColumn(), entry.getValue()
                if dst == target:
                    return prob
            return 0.0

        # self loop has to be first applicable action
        if self.quotient.action_labels[0] == "__no_label__":
            if not self.quotient.action_labels[1].startswith("_stay"):
                return game_policy
        else:
            if not self.quotient.action_labels[0].startswith("_stay"):
                return game_policy
        # self loops serves as verification against worst case scenario -> any other action is better

        depth = -1
        end_state = next((state for state in game_solver.state_is_target if state), -1)
        assert end_state != -1

        assert len(self.quotient.quotient_mdp.initial_states) == 1
        game_policy_post = self.quotient.empty_policy()

        explored_states = set() # avoid cycles
        current_state = self.quotient.quotient_mdp.initial_states[0]
        state_stack = [(-1.0, current_state)]

        while state_stack:
            _, current_state = heapq.heappop(state_stack)
            if current_state in explored_states:
                continue

            game_policy_post[current_state] = game_policy[current_state]
            explored_states.add(current_state)

            cur_choice = game_solver.solution_state_to_quotient_choice[current_state]
            target_states = self.quotient.choice_destinations[cur_choice]

            depth += 1
            if current_state == end_state and check_granularity < 0:
                check_granularity = depth # shortest path length

            # Collect probabilities and corresponding target states
            for target_state in target_states:
                prob = getProbForChoice(cur_choice, target_state)
                heapq.heappush(state_stack, (-prob, target_state))

            if end_state in explored_states and check_granularity > 0 and depth % check_granularity == 0:
                sat = SynthesizerPolicyTree.double_check_policy(self.quotient, family, prop, game_policy_post)
                if sat:
                    return game_policy_post

        # logger.debug("policy couldn't be simplified by probability reach")
        return game_policy


    def post_process_bruteforce(self, game_policy, game_solver, family, prop):
        """ Brute force approach to find the pseudo smallest policy
        for totally correct results all permutations would be needed to check
        """

        game_policy_post = self.quotient.empty_policy()
        for state in range(len(game_policy)):
            game_policy_post[state] = game_policy[state]

        changed = True
        while changed:
            changed = False
            for state in range(len(game_policy)):
                if game_policy_post[state] is None:
                    continue
                # try set none and verify if fail, revert
                old_action = game_policy_post[state]
                game_policy_post[state] = None
                sat = SynthesizerPolicyTree.double_check_policy(self.quotient, family, prop, game_policy_post)
                if not sat:
                    game_policy_post[state] = old_action
                else:
                    changed = True
        return game_policy_post

    def state_to_choice_to_hole_selection(self, state_to_choice):
        if SynthesizerPolicyTree.discard_unreachable_choices:
            state_to_choice = self.quotient.discard_unreachable_choices(state_to_choice)
        scheduler_choices = self.quotient.state_to_choice_to_choices(state_to_choice)
        hole_selection = self.quotient.coloring.collectHoleOptions(scheduler_choices)
        return scheduler_choices,hole_selection

    def parse_game_scheduler(self, game_solver):
        state_to_choice = game_solver.solution_state_to_quotient_choice.copy()
        scheduler_choices,hole_selection = self.state_to_choice_to_hole_selection(state_to_choice)
        state_values = game_solver.solution_state_values
        return scheduler_choices,hole_selection,state_values

    def verify_family(self, family, game_solver, prop):
        # logger.info("investigating family of size {}".format(family.size))
        self.quotient.build(family)
        mdp_family_result = MdpFamilyResult()

        mdp_fixed_choices = None
        if family.candidate_policy is None or self.ldokoupi_flag:
            game_policy,game_sat,mdp_fixed_choices = self.solve_game_abstraction(family,prop,game_solver)
        else:
            game_policy = family.candidate_policy
            game_sat = False

        mdp_family_result.game_policy = game_policy
        mdp_family_result.mdp_fixed_choices = mdp_fixed_choices
        if game_sat:
            mdp_family_result.policy = game_policy
            return mdp_family_result

        if family.size == 1:
            # fallback method (usually UNSAT families or w/o candidate policy)
            mdp_family_result.policy = self.solve_singleton(family, prop)
            return mdp_family_result

        # solve primary direction for the MDP abstraction
        mdp_result = family.mdp.model_check_property(prop)
        mdp_value = mdp_result.value
        self.stat.iteration(family.mdp)
        # logger.debug("primary-primary direction solved, value is {}".format(mdp_value))
        if not mdp_result.sat:
            mdp_family_result.policy = False
            return mdp_family_result

        # undecided: choose scheduler choices to be used for splitting
        scheduler_choices,hole_selection,state_values = self.parse_game_scheduler(game_solver)

        splitter = self.choose_splitter(family,prop,scheduler_choices,state_values,hole_selection)
        mdp_family_result.splitter = splitter
        mdp_family_result.hole_selection = hole_selection
        return mdp_family_result
    
    def choose_splitter(self, family, prop, scheduler_choices, state_values, hole_selection):
        inconsistent_assignments = {hole:options for hole,options in enumerate(hole_selection) if len(options) > 1}
        if len(inconsistent_assignments)==0:
            # # pick any hole with multiple options involved in the hole selection
            for hole,options in enumerate(hole_selection):
                if family.hole_num_options(hole) > 1 and len(options) > 0:
                    return hole
            # pick any hole with multiple options
            # logger.debug("picking an arbitrary hole...")
            for hole in range(family.num_holes):
                if family.hole_num_options(hole) > 1:
                    return hole
        if len(inconsistent_assignments)==1:
            for hole in inconsistent_assignments.keys():
                return hole
        
        # compute scores for inconsistent holes
        scores = self.compute_scores(prop, scheduler_choices, state_values, inconsistent_assignments)
        splitters = self.quotient.holes_with_max_score(scores)
        splitter = splitters[0]
        return splitter
    
    def compute_scores(self, prop, scheduler_choices, state_values, inconsistent_assignments):
        mdp = self.quotient.quotient_mdp
        choice_values = self.quotient.choice_values(mdp, prop, state_values)
        expected_visits = None
        if self.quotient.compute_expected_visits:
            expected_visits = self.quotient.compute_expected_visits(mdp, prop, scheduler_choices)
        quotient_choice_map = [choice for choice in range(self.quotient.quotient_mdp.nr_choices)]
        scores = self.quotient.estimate_scheduler_difference(self.quotient.quotient_mdp, quotient_choice_map, inconsistent_assignments, choice_values, expected_visits)
        return scores

    def assign_candidate_policy(self, subfamilies, hole_selection, splitter, policy):
        policy_consistent = all([len(options) <= 1 for options in hole_selection])
        if not policy_consistent:
            return
        # associate the branch of the split that contains hole selection with the policy
        used_options = hole_selection[splitter]
        if len(used_options) != 1:
            # not sure what to do in this case
            return
        option = used_options[0]
        for subfamily in subfamilies:
            if option in subfamily.hole_options(splitter):
                subfamily.candidate_policy = policy
                return

    def split(self, family, prop, hole_selection, splitter, policy):
        # split the hole
        used_options = hole_selection[splitter]
        if len(used_options) > 1:
            # used_options = used_options[0:1]
            core_suboptions = [[option] for option in used_options]
            other_suboptions = [option for option in family.hole_options(splitter) if option not in used_options]
            if other_suboptions:
                other_suboptions = [other_suboptions]
            else:
                other_suboptions = []
            suboptions = other_suboptions + core_suboptions # DFS solves core first
        else:
            options = family.hole_options(splitter)
            assert len(options) > 1
            half = len(options) // 2
            suboptions = [options[:half], options[half:]]

        subfamilies = family.split(splitter,suboptions)
        for subfamily in subfamilies:
            subfamily.candidate_policy = None

        if not SynthesizerPolicyTree.discard_unreachable_choices:
            self.assign_candidate_policy(subfamilies, hole_selection, splitter, policy)

        return suboptions,subfamilies

    
    def evaluate_all(self, family, prop, keep_value_only=False):
        assert not prop.reward, "expecting reachability probability propery"
        game_solver = self.quotient.build_game_abstraction_solver(prop)
        family.candidate_policy = None
        policy_tree = PolicyTree(family)

        undecided_leaves = [policy_tree.root]
        while undecided_leaves:

            # gi = self.stat.iterations_game
            # if gi is not None and gi > 1000:
            #     return None

            policy_tree_node = undecided_leaves.pop(-1)
            policy_tree_node.mdp_fixed_choices = None
            family = policy_tree_node.family
            result = self.verify_family(family,game_solver,prop)
            family.candidate_policy = None

            if result.policy is not None:
                self.explore(family)
                if policy_tree_node != policy_tree.root:
                    family.mdp = None
                if result.policy is False:
                    policy_tree_node.sat = False
                else:
                    policy_tree_node.sat = True
                    policy_tree_node.policy_index = policy_tree.new_policy(result.policy)
                    policy_tree_node.mdp_fixed_choices = result.mdp_fixed_choices
                continue

            # refine
            suboptions,subfamilies = self.split(family, prop, result.hole_selection, result.splitter, result.game_policy)
            if policy_tree_node != policy_tree.root:
                family.mdp = None
            policy_tree_node.split(result.splitter,suboptions,subfamilies)
            undecided_leaves += policy_tree_node.child_nodes

        logger.debug(f"LDOKOUPI: postprocessing took {int(self.ldok_postprocessing_times.read())} s")
        if SynthesizerPolicyTree.double_check_policy_tree_leaves:
            policy_tree.double_check(self.quotient, prop)
        policy_tree.print_stats()

        self.stat.num_mdps_total = self.quotient.family.size
        self.stat.num_mdps_sat = sum([n.family.size for n in policy_tree.collect_sat()])
        self.stat.num_nodes = len(policy_tree.collect_all())
        self.stat.num_leaves = len(policy_tree.collect_leaves())
        self.stat.num_policies = len(policy_tree.policies)
        postprocessing_time = policy_tree.postprocess(self.quotient, prop)
        policy_tree.print_stats()
        # self.stat.postprocessing_time = postprocessing_time
        self.stat.num_nodes_merged = len(policy_tree.collect_all())
        self.stat.num_leaves_merged = len(policy_tree.collect_leaves())
        self.stat.num_policies_merged = len(policy_tree.policies)
        self.policy_tree = policy_tree

        # convert policy tree to family evaluation
        evaluations = []
        for node in policy_tree.collect_leaves():
            policy = policy_tree.policies[node.policy_index] if node.sat else None
            evaluation = paynt.synthesizer.synthesizer.FamilyEvaluation(node.family,None,node.sat,policy=policy, mdp_fixed_choices=node.mdp_fixed_choices)
            evaluations.append(evaluation)
        return evaluations


    def run(self, optimum_threshold=None):
        return self.evaluate()


    def export_evaluation_result(self, evaluations, export_filename_base):
        import json
        flag_bp = self.ldokoupi_flag
        # second export is in DTControl format
        for flag in [False, True]:
            if not self.ldokoupi_flag and flag is True:
                continue
            self.ldokoupi_flag = flag

            policies = self.policy_tree.extract_policies(self.quotient, keep_family=self.ldokoupi_flag)
            policies_json = [] if self.ldokoupi_flag else {}
            for index,key_value in enumerate(policies.items()):
                policy_id,policy = key_value
                policy_json = self.quotient.policy_to_json(policy, dt_control=self.ldokoupi_flag)

                if not self.ldokoupi_flag:
                    policies_json[policy_id] = policy_json
                else:
                    # for merging policy tree & DTs create long list as classification problem for DTCONTROL
                    policies_json.extend(policy_json)

            policies_string = json.dumps(policies_json, indent=4)

            policies_filename = export_filename_base + ".json" if not flag else export_filename_base + ".storm.json"
            with open(policies_filename, 'w') as file:
                file.write(policies_string)
            self.ldokoupi_flag = flag_bp
            logger.info(f"exported policies to {policies_filename}")

        tree = self.policy_tree.extract_policy_tree(self.quotient)
        tree_filename = export_filename_base + ".dot"
        with open(tree_filename, 'w') as file:
            file.write(tree.source)
        logger.info(f"exported policy tree to {tree_filename}")

        if self.ldokoupi_flag:
            return  # omit png
        tree_visualization_filename = export_filename_base + ".png"
        tree.render(export_filename_base, format="png", cleanup=True) # using export_filename_base since graphviz appends .png by default
        logger.info(f"exported policy tree visualization to {tree_visualization_filename}")
