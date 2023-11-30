import stormpy.synthesis

import paynt.quotient.holes
import paynt.quotient.models
import paynt.synthesizer.synthesizer

import logging
logger = logging.getLogger(__name__)


class MdpFamilyResult:
    def __init__(self):
        # if None, then family is undediced
        # if False, then all family is UNSAT
        # otherwise, then contains a satisfying policy for all MDPs in the family
        self.policy = None

        self.scheduler_choices = None
        self.hole_selection = None

    def __str__(self):
        return str(self.sat)


def merge_policies(policy1, policy2, dont_care_action):

    num_states = len(policy1)
    # agree_mask = stormpy.storage.BitVector(num_states,False)
    # for state in range(num_states):
    #     agree_mask.set(policy1[state] == policy2[state],True)

    policy12 = policy1.copy()
    policy21 = policy2.copy()
    for state in range(num_states):
        a1 = policy1[state]
        a2 = policy2[state]
        if a1 == dont_care_action:
            policy12[state] = a2
        if a2 == dont_care_action:
            policy21[state] = a1
    return policy12,policy21


def test_nodes(quotient, prop, node1, node2):
    dont_care_action = quotient.num_actions
    policy1 = node1.policy
    policy2 = node2.policy
    policy12,policy21 = merge_policies(policy1,policy2, dont_care_action)

    # try policy1 for family2
    policy,choice_mask = quotient.fix_policy_for_family(node2.family, policy12)
    mdp = quotient.build_from_choice_mask(choice_mask)
    policy_result = mdp.model_check_property(prop, alt=True)
    if policy_result.sat:
        return policy

    # try policy2 for family1
    policy,choice_mask = quotient.fix_policy_for_family(node1.family, policy21)
    mdp = quotient.build_from_choice_mask(choice_mask)
    policy_result = mdp.model_check_property(prop, alt=True)
    if policy_result.sat:
        return policy

    # neither fits
    return None



class PolicyTreeNode:

    merged = 0

    def __init__(self, family):
        self.family = family

        self.parent = None
        self.policy = None
        
        self.splitter = None
        self.suboptions = []
        self.child_nodes = []

    @property
    def is_leaf(self):
        return len(self.child_nodes) == 0
    
    @property
    def solved(self):
        return self.policy != False and self.policy is not None

    def split(self, splitter, suboptions, subfamilies):
        self.splitter = splitter
        self.suboptions = suboptions
        self.child_nodes = []
        for subfamily in subfamilies:
            child_node = PolicyTreeNode(subfamily)
            child_node.parent = self
            self.child_nodes.append(child_node)    


    def double_check(self, quotient, prop):
        assert self.policy is not None
        if self.policy == False:
            result = self.family.mdp.model_check_property(prop)
            assert not result.sat
        else:
            mdp = quotient.apply_policy_to_family(self.family, self.policy)
            result = mdp.model_check_property(prop, alt=True)
            assert result.sat


    def merge_child_nodes(self, quotient, prop):
        if self.is_leaf:
            return

        i = 0
        while i < len(self.child_nodes):
            child1 = self.child_nodes[i]
            
            if child1.policy is None:
                i += 1
                continue
            
            
            join_to_i = []
            if child1.policy == False:
                # merge all UNSAT children
                for j in range(i+1,len(self.child_nodes)):
                    child2 = self.child_nodes[j]
                    if child2.policy == False:
                        join_to_i.append(j)
            else:
                # collect other childs to merge to i
                for j in range(i+1,len(self.child_nodes)):
                    child2 = self.child_nodes[j]
                    if not child2.solved:
                        continue
                    policy = test_nodes(quotient,prop,child1,child2)
                    if policy is None:
                        continue
                    # nodes can be merged
                    child1.policy = policy
                    join_to_i.append(j)
            
            # merge
            for j in reversed(join_to_i):
                PolicyTreeNode.merged += 1
                self.suboptions[i] += self.suboptions[j]
                self.suboptions.pop(j)
                self.child_nodes.pop(j)

            i += 1

        if len(self.child_nodes)>1:
            return
        # only 1 child node that can be moved to this node
        PolicyTreeNode.merged += 1
        self.policy = self.child_nodes[0].policy
        self.splitter = None
        self.suboptions = []
        self.child_nodes = []









class PolicyTree:

    def __init__(self, family):
        self.root = PolicyTreeNode(family)

    def __str__(self):
        pass

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

    def collect_solved(self):
        node_queue = [self.root]
        solved = []
        while node_queue:
            node = node_queue.pop(0)
            if node.solved:
                solved.append(node)
            else:
                node_queue += node.child_nodes
        return solved


    def double_check_all_families(self, quotient, prop):
        leaves = self.collect_leaves()
        logger.info("double-checking {} families...".format(len(leaves)))
        for leaf in leaves:
            leaf.double_check(quotient,prop)
        logger.info("all solutions are OK")

    
    def count_diversity(self):
        from collections import defaultdict
        children_stats = defaultdict(int)
        for node in self.collect_all():
            if node.policy is not None:
                continue
            with_none = len([node for node in node.child_nodes if node.policy is None])
            with_policy = len([node for node in node.child_nodes if node.policy is not None])
            with_false = len([node for node in node.child_nodes if node.policy==False])
            children_stats[(with_none,with_policy,with_false)] += 1
        return children_stats

    
    def print_stats(self):
        members_total = self.root.family.size
        members_satisfied = 0
        num_leaves_singleton = 0
        num_policies = 0
        
        leaves = self.collect_leaves()
        for node in leaves:
            if node.family.size==1:
                num_leaves_singleton += 1
            if node.policy is not None and node.policy != False:
                num_policies += 1
                members_satisfied += node.family.size
        satisfied_percentage = round(members_satisfied/members_total*100,0)
        members_unsatisfied = members_total-members_satisfied

        num_nodes = len(self.collect_all())
        num_leaves = len(leaves)
        num_leaves_solvable = num_policies
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
        print("found {} satisfying policies for {}/{} family members ({}%)".format(
            num_policies,members_satisfied,members_total,satisfied_percentage))
        print("policy tree has {} nodes, {} of them are leaves:".format(num_nodes, num_leaves))
        print("\t  solvable leaves: {} (avg.size: {})".format(num_leaves_solvable,leaf_solvable_avg))
        print("\tunsolvable leaves: {} (avg.size: {})".format(num_leaves_unsolvable,leaf_unsolvable_avg))
        print("\t singleton leaves: {}".format(num_leaves_singleton))

        print()
        print("(X, Y, Z)  -  number of internal nodes having X unresolved, Y satisfied and Z unsatisfied children")
        for key,number in self.count_diversity().items():
            print(key, " - ", number)
        print("--------------------")


    

    
    def postprocess(self, quotient, prop):

        # find two leafs that can be merged
        logger.info("post-processing the policy tree...")

        # can_be_merged = 0
        # leaves = self.collect_leaves()
        # for i,leaf2 in enumerate(leaves):
        #     if i == 0:
        #         continue
        #     leaf1 = leaves[i-1]
        #     if leaf1.solved and leaf2.solved and leaf1.parent == leaf2.parent:
        #         result = test_nodes(quotient,prop,leaf1,leaf2)
        #         if result is not None:
        #             can_be_merged += 1
        # print("num leaves: ", len(leaves))
        # print("can merge: ", can_be_merged)

        PolicyTreeNode.merged = 0
        all_nodes = self.collect_all()
        for node in reversed(all_nodes):
            node.merge_child_nodes(quotient,prop)
        logger.info("post-processing over, merged {} pairs".format(PolicyTreeNode.merged))
        
        


                






class SynthesizerPolicyTree(paynt.synthesizer.synthesizer.Synthesizer):

    @property
    def method_name(self):
        return "AR (policy tree)"

    def verify_family(self, family, game_solver, prop, reference_policy=None):
        self.quotient.build(family)
        mdp_family_result = MdpFamilyResult()

        reference_policy = None
        if reference_policy is not None:
            # check if reference policy works
            mdp = self.quotient.apply_policy_to_family(family, reference_policy)
            policy_result = mdp.model_check_property(prop, alt=True)
            self.stat.iteration_mdp(mdp.states)
            if policy_result.sat:
                # this scheduler is good for all MDPs in the family
                mdp_family_result.policy = reference_policy
                return mdp_family_result

        if family.size == 1:
            primary_primary_result = family.mdp.model_check_property(prop)
            self.stat.iteration_mdp(family.mdp.states)
            # logger.debug("primary-primary direction solved, value is {}".format(primary_primary_result.value))
            if not primary_primary_result.sat:
                mdp_family_result.policy = False
                return mdp_family_result
            # extract satisfying policy
            scheduler = primary_primary_result.result.scheduler
            choices = scheduler.compute_action_support(family.mdp.model.nondeterministic_choice_indices)
            quotient_choice_mask = stormpy.BitVector(self.quotient.quotient_mdp.nr_choices, False)
            for choice in choices:
                quotient_choice_mask.set(family.mdp.quotient_choice_map[choice],True)
            quotient_choice_mask = self.quotient.keep_reachable_choices(quotient_choice_mask)
            policy = self.quotient.choices_to_policy(quotient_choice_mask)
            mdp_family_result.policy = policy
            return mdp_family_result

        # construct and solve the game abstraction
        # logger.debug("solving the game...")
        game_solver.solve(family.selected_actions_bv, prop.maximizing, prop.minimizing)
        self.stat.iteration_game(family.mdp.states)
        # logger.debug("game solved, value is {}".format(game_solver.solution_value))
        game_result_sat = prop.satisfies_threshold(game_solver.solution_value)
        
        if False:
            model,state_map,choice_map = self.quotient.restrict_mdp(self.quotient.quotient_mdp, game_solver.solution_reachable_choices)
            assert(model.nr_states == model.nr_choices)
            dtmc = paynt.quotient.models.DTMC(model, self.quotient, state_map, choice_map)
            dtmc_result = dtmc.model_check_property(prop)
            # print("double-checking game value: ", game_solver.solution_value, dtmc_result)
            if abs(dtmc_result.value-game_solver.solution_value) > 0.01:
                logger.error("game solution is {}, but DTMC model checker yielded {}".format(game_solver.solution_value,dtmc_result.value))

        if game_result_sat:
            # logger.debug("verifying game policy...")
            # apply player 1 actions to the quotient
            policy = game_solver.solution_state_to_player1_action
            mdp = self.quotient.apply_policy_to_family(family, policy)
            policy_result = mdp.model_check_property(prop, alt=True)
            self.stat.iteration_mdp(mdp.states)
            if policy_result.sat:
                # this scheduler is good for all MDPs in the family
                mdp_family_result.policy = policy
                return mdp_family_result
        else:
            # logger.debug("solving primary-primary direction...")
            # solve primary-primary direction for the family
            primary_primary_result = family.mdp.model_check_property(prop)
            self.stat.iteration_mdp(family.mdp.states)
            # logger.debug("primary-primary direction solved, value is {}".format(primary_primary_result.value))
            if not primary_primary_result.sat:
                mdp_family_result.policy = False
                return mdp_family_result
        
        # undecided: prepare to split
        # map scheduler choices to hole options and check consistency
        scheduler_choices = game_solver.solution_reachable_choices
        hole_selection = self.quotient.choices_to_hole_selection(scheduler_choices)
        mdp_family_result.scheduler_choices = scheduler_choices
        mdp_family_result.hole_selection = hole_selection
        if True:
            for choice in scheduler_choices:
                assert choice in family.selected_actions_bv
            for hole_index,options in enumerate(hole_selection):
                assert all([option in family[hole_index].options for option in options])
        return mdp_family_result


    def choose_splitter_round_robin(self, family, prop, scheduler_choices, state_values, hole_selection):
        splitter = (self.last_splitter+1) % family.num_holes
        while family[splitter].size == 1:
            splitter = (splitter+1) % family.num_holes
        return splitter

    def choose_splitter(self, family, prop, scheduler_choices, state_values, hole_selection):
        splitter = None
        inconsistent_assignments = {hole_index:options for hole_index,options in enumerate(hole_selection) if len(options) > 1}
        if len(inconsistent_assignments)==0:
            for hole_index,hole in enumerate(family):
                if hole.size > 1:
                    splitter = hole_index
                    break
        elif len(inconsistent_assignments)==1:
            for hole_index in inconsistent_assignments.keys():
                splitter = hole_index
                break
        else:
            # compute scores for inconsistent holes
            mdp = self.quotient.quotient_mdp
            choice_values = self.quotient.choice_values(mdp, prop, state_values)
            expected_visits = self.quotient.expected_visits(mdp, prop, scheduler_choices)
            quotient_mdp_wrapped = self.quotient.design_space.mdp
            scores = self.quotient.estimate_scheduler_difference(quotient_mdp_wrapped, inconsistent_assignments, choice_values, expected_visits)
            splitters = self.quotient.holes_with_max_score(scores)
            splitter = splitters[0]
        assert splitter is not None
        return splitter
    
    
    def split(self, family, prop, scheduler_choices, state_values, hole_selection):
        
        splitter = self.choose_splitter(family,prop,scheduler_choices,state_values,hole_selection)
        # splitter = self.choose_splitter_round_robin(family,prop,scheduler_choices,state_values,hole_selection)
        # split the hole
        used_options = hole_selection[splitter]
        if len(used_options) > 1:
            # used_options = used_options[0:1]
            core_suboptions = [[option] for option in used_options]
            other_suboptions = [option for option in family[splitter].options if option not in used_options]
            if other_suboptions:
                other_suboptions = [other_suboptions]
            else:
                other_suboptions = []
            suboptions = other_suboptions + core_suboptions # DFS solves core first
        else:
            assert len(family[splitter].options) > 1
            options = family[splitter].options
            half = len(options) // 2
            suboptions = [options[:half], options[half:]]

        # construct corresponding design subspaces
        subfamilies = []
        family.splitter = splitter
        new_design_space = family.copy()
        for suboption in suboptions:
            subholes = new_design_space.subholes(splitter, suboption)
            subfamily = paynt.quotient.holes.DesignSpace(subholes)
            subfamily.assume_hole_options(splitter, suboption)
            subfamilies.append(subfamily)
        return splitter,suboptions,subfamilies
        


    def synthesize_policy_tree(self, family):

        self.last_splitter = -1
        prop = self.quotient.specification.constraints[0]
        game_solver = self.quotient.build_game_abstraction_solver(prop)
        policy_tree = PolicyTree(family)
        reference_policy = None

        
        policy_tree_leaves = [policy_tree.root]
        while policy_tree_leaves:
            policy_tree_node = policy_tree_leaves.pop(-1)
            family = policy_tree_node.family
            # logger.info("investigating family of size {}".format(family.size))
            result = self.verify_family(family,game_solver,prop,reference_policy)
            policy_tree_node.policy = result.policy

            if result.policy == False:
                # logger.info("satisfying scheduler cannot be obtained for the following family {}".format(family))
                self.explore(family)
                continue

            if result.policy is not None:
                # logger.info("found policy for all MDPs in the family")
                # print(self.policy_str(result.policy))
                reference_policy = result.policy
                self.explore(family)
                continue

            # refine
            splitter,suboptions,subfamilies = self.split(
                family, prop, game_solver.solution_reachable_choices, game_solver.solution_state_values, result.hole_selection
            )
            policy_tree_node.split(splitter,suboptions,subfamilies)
            policy_tree_leaves = policy_tree_leaves + policy_tree_node.child_nodes

        policy_tree.double_check_all_families(self.quotient, prop)
        policy_tree.print_stats()
        policy_tree.postprocess(self.quotient, prop)
        policy_tree.print_stats()
        return policy_tree

    

    def synthesize(self, family = None):
        if family is None:
            family = self.quotient.design_space
        self.stat.start()
        logger.info("synthesis initiated, design space: {}".format(family.size))
        policy_tree = self.synthesize_policy_tree(family)
        self.stat.finished("yes")
        return policy_tree

    
    def run(self):
        ''' Synthesize meta-policy that satisfies all family members. '''
        self.quotient.design_space.constraint_indices = self.quotient.specification.all_constraint_indices()

        spec = self.quotient.specification
        assert not spec.has_optimality and spec.num_properties == 1 and not spec.constraints[0].reward, \
            "expecting a single reachability probability constraint"
        
        policy_tree = self.synthesize()
        self.stat.print()
    