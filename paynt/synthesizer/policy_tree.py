import stormpy.synthesis

import paynt.family.family
import paynt.quotient.models
import paynt.synthesizer.synthesizer

import paynt.synthesizer.conflict_generator.dtmc
import paynt.synthesizer.conflict_generator.mdp
import paynt.family.smt

import paynt.verification.property_result
from paynt.verification.property import Property
import paynt.quotient.quotient

import logging
logger = logging.getLogger(__name__)


class MdpFamilyResult:
    def __init__(self):
        # if None, then family is undediced
        # if False, then all family is UNSAT
        # otherwise, contains a satisfying policy for all MDPs in the family
        self.policy = None
        self.policy_source = ""

        self.hole_selection = None
        self.splitter = None

        # policy search results
        self.sat_mdps = None
        self.sat_policies = None
        self.unsat_mdps = None

    def __str__(self):
        return str(self.sat)


def actions_are_compatible(a1, a2):
    return a1 is None or a2 is None or a1==a2

def policies_are_compatible(policy1, policy2):
    for state,a1 in enumerate(policy1):
        a2 = policy2[state]
        if not actions_are_compatible(a1,a2):
            return False
    return True

def merge_policies(policies):
    '''
    Attempt to merge multiple policies into one.
    :returns one policy or None if some policies were incompatible
    '''
    policy = policies[0].copy()
    for policy2 in policies[1:]:
        for state,a1 in enumerate(policy):
            a2 = policy2[state]
            if not actions_are_compatible(a1,a2):
                return None
            policy[state] = a1 or a2
    return policy


def merge_policies_exclusively(policy1, policy2):

    # num_states = len(policy1)
    # agree_mask = stormpy.storage.BitVector(num_states,False)
    # for state in range(num_states):
    #     agree_mask.set(policy1[state] == policy2[state],True)

    policy12 = policy1.copy()
    policy21 = policy2.copy()
    for state,a1 in enumerate(policy1):
        a2 = policy2[state]
        if a1 is None:
            policy12[state] = a2
        if a2 is None:
            policy21[state] = a1
    return policy12,policy21


def test_nodes(quotient, prop, node1, node2):
    policy1 = node1.policy
    policy2 = node2.policy
    policy = merge_policies([policy1,policy2])
    if policy is not None:
        return policy
    
    policy12,policy21 = merge_policies_exclusively(policy1,policy2)

    # try policy1 for family2
    policy,mdp = quotient.fix_and_apply_policy_to_family(node2.family, policy12)
    policy_result = mdp.model_check_property(prop, alt=True)
    if policy_result.sat:
        return policy

    # try policy2 for family1
    policy,mdp = quotient.fix_and_apply_policy_to_family(node1.family, policy21)
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
        return self.policy is not None and self.policy != False 

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
        quotient.build(self.family)
        if self.policy == False:
            result = self.family.mdp.model_check_property(prop)
            assert not result.sat
        else:
            SynthesizerPolicyTree.double_check_policy(quotient, self.family, prop, self.policy)

    
    def merge_if_single_child(self):
        if len(self.child_nodes) > 1:
            return
        self.policy = self.child_nodes[0].policy
        self.splitter = None
        self.suboptions = []
        self.child_nodes = []

    def merge_children_indices(self, indices):
        if len(indices) < 2:
            return
        target = indices[0]
        for j in reversed(indices[1:]):
            PolicyTreeNode.merged += 1
            self.suboptions[target] += self.suboptions[j]
            self.child_nodes[target].family.hole_set_options(self.splitter,self.suboptions[target])
            self.suboptions.pop(j)
            self.child_nodes.pop(j)
        self.merge_if_single_child()

    def merge_children_solved(self):
        if self.is_leaf:
            return
        indices = [i for i,child in enumerate(self.child_nodes) if child.solved]
        self.merge_children_indices(indices)
        
    def merge_children_unsat(self):
        if self.is_leaf:
            return
        indices = [i for i,child in enumerate(self.child_nodes) if child.policy==False]
        self.merge_children_indices(indices)


    def merge_children_compatible(self, quotient, prop):
        if self.is_leaf:
            return
        i = 0
        while i < len(self.child_nodes):
            child1 = self.child_nodes[i]
            
            if not child1.solved:
                i += 1
                continue

            join_to_i = [i]
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
            
            self.merge_children_indices(join_to_i)
            i += 1


        if len(self.child_nodes)>1:
            return
        # only 1 child node that can be moved to this node
        PolicyTreeNode.merged += 1


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


    def double_check(self, quotient, prop):
        leaves = self.collect_leaves()
        logger.info("double-checking {} families...".format(len(leaves)))
        for leaf in leaves:
            leaf.double_check(quotient,prop)
        logger.info("all solutions are OK")

    
    def count_diversity(self):
        from collections import defaultdict
        children_stats = defaultdict(int)
        for node in self.collect_all():
            if node.is_leaf:
                continue
            with_policy = len([node for node in node.child_nodes if node.solved])
            with_none = len([node for node in node.child_nodes if node.policy is None])
            with_false = len([node for node in node.child_nodes if node.policy==False])
            children_stats[(with_policy,with_none,with_false)] += 1
        return children_stats

    def count_policy_sources(self):
        from collections import defaultdict
        sources = defaultdict(int)
        for node in self.collect_leaves():
            if not node.solved:
                continue
            sources[node.policy_source] += 1
        return sources


    
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

        # print()
        # print("(X, Y, Z)  -  number of internal nodes having yes/?/no children")
        # for key,number in self.count_diversity().items():
        #     print(key, " - ", number)
        
        # print()
        # print("X  -  number of nodes solved with policy of type X")
        # for key,number in self.count_policy_sources().items():
        #     print(key, " - ", number)
        # print("--------------------")


    

    
    def postprocess(self, quotient, prop, stat):

        stat.num_mdps_total = quotient.design_space.size
        stat.num_mdps_sat = sum([n.family.size for n in self.collect_solved()])

        stat.num_policies = len(self.collect_solved())
        logger.info("post-processing the policy tree...")
        logger.info("merging unsat siblings...")
        PolicyTreeNode.merged = 0
        all_nodes = self.collect_all()
        for node in reversed(all_nodes):
            node.merge_children_unsat()
        logger.info("merged {} pairs".format(PolicyTreeNode.merged))
        # self.print_stats()

        logger.info("merging compatible siblings...")
        PolicyTreeNode.merged = 0
        all_nodes = self.collect_all()
        for node in reversed(all_nodes):
            node.merge_children_compatible(quotient,prop)
        logger.info("merged {} pairs".format(PolicyTreeNode.merged))
        stat.num_policies_merged = len(self.collect_solved())
        self.print_stats()

        # logger.info("merging solved siblings...")
        # PolicyTreeNode.merged = 0
        # all_nodes = self.collect_all()
        # for node in reversed(all_nodes):
        #     node.merge_children_solved()
        # logger.info("merged {} pairs".format(PolicyTreeNode.merged))
        # stat.num_policies_yes = len(self.collect_solved())
        # self.print_stats()



class SynthesizerPolicyTree(paynt.synthesizer.synthesizer.Synthesizer):

    # if True, tree leaves will be double-checked after synthesis
    double_check_policy_tree_leaves = False
    
    @property
    def method_name(self):
        return "AR (policy tree)"

    @staticmethod
    def double_check_policy(quotient, family, prop, policy):
        _,mdp = quotient.fix_and_apply_policy_to_family(family, policy)
        if family.size == 1:
            quotient.assert_mdp_is_deterministic(mdp, family)
        
        DOUBLE_CHECK_PRECISION = 1e-6
        default_precision = Property.model_checking_precision
        Property.set_model_checking_precision(DOUBLE_CHECK_PRECISION)
        policy_result = mdp.model_check_property(prop, alt=True)
        Property.set_model_checking_precision(default_precision)
        if not policy_result.sat:
            logger.warning("policy should be SAT but (most likely due to model checking precision) has value {}".format(policy_result.value))
        return
    
    
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
        game_solver.solve(family.selected_choices, prop.maximizing, prop.minimizing)
        self.stat.iteration_game(family.mdp.states)
        game_value = game_solver.solution_value
        game_sat = prop.satisfies_threshold(game_value)
        # logger.debug("game solved, value is {}".format(game_value))
        game_policy = game_solver.solution_state_to_player1_action
        # fix irrelevant choices
        game_policy_fixed = self.quotient.empty_policy()
        for state,action in enumerate(game_policy):
            if action < self.quotient.num_actions:
                game_policy_fixed[state] = action
        game_policy = game_policy_fixed
        return game_policy,game_value,game_sat

    def parse_game_scheduler(self, game_solver):
        state_values = game_solver.solution_state_values
        state_to_choice = game_solver.solution_state_to_quotient_choice.copy()
        # uncomment this to use only reachable choices of the game scheduler
        # state_to_choice = self.quotient.keep_reachable_choices_of_scheduler(state_to_choice)
        scheduler_choices = self.quotient.state_to_choice_to_choices(state_to_choice)
        hole_selection = self.quotient.coloring.collectHoleOptions(scheduler_choices)
        return scheduler_choices,state_values,hole_selection

    def parse_mdp_scheduler(self, family, mdp_result):
        state_to_choice = self.quotient.scheduler_to_state_to_choice(family.mdp, mdp_result.result.scheduler)
        scheduler_choices = self.quotient.state_to_choice_to_choices(state_to_choice)
        state_values = [0] * self.quotient.quotient_mdp.nr_states
        for state in range(family.mdp.states):
            quotient_state = family.mdp.quotient_state_map[state]
            state_values[quotient_state] = mdp_result.result.at(state)
        hole_selection = self.quotient.coloring.collectHoleOptions(scheduler_choices)
        return scheduler_choices,state_values,hole_selection

    
    def verify_family(self, family, game_solver, prop):
        # logger.info("investigating family of size {}".format(family.size))
        self.quotient.build(family)
        mdp_family_result = MdpFamilyResult()

        if family.size <= 8 and False:
            policy_is_unique, unsat_mdps, sat_mdps, sat_policies = self.synthesize_policy_for_family(family, prop, iteration_limit=100)
            if policy_is_unique:
                policy = sat_policies
                mdp_family_result.policy = policy
                mdp_family_result.policy_source = "policy search"
                return mdp_family_result
        
        if family.size == 1:
            mdp_family_result.policy = self.solve_singleton(family,prop)
            mdp_family_result.policy_source = "singleton"
            return mdp_family_result
        
        game_policy,game_value,game_sat = self.solve_game_abstraction(family,prop,game_solver)
        if game_sat:
            game_policy_sat = self.verify_policy(family,prop,game_policy)
            if game_policy_sat:
                mdp_family_result.policy = game_policy
                mdp_family_result.policy_source = "game abstraction"
                return mdp_family_result
            else:
                logger.debug(f"game YES but nor forall family of size {family.size}")
        
        mdp_result = None
        if not game_sat:
            # solve primary direction for the MDP abstraction
            mdp_result = family.mdp.model_check_property(prop)
            mdp_value = mdp_result.value
            self.stat.iteration(family.mdp)
            # logger.debug("primary-primary direction solved, value is {}".format(mdp_value))
            if not mdp_result.sat:
                mdp_family_result.policy = False
                return mdp_family_result
        
        # undecided: choose scheduler choices to be used for splitting
        scheduler_choices,state_values,hole_selection = self.parse_game_scheduler(game_solver)
        # scheduler_choices,state_values,hole_selection = self.parse_mdp_scheduler(family, mdp_result)

        splitter = self.choose_splitter(family,prop,scheduler_choices,state_values,hole_selection)
        mdp_family_result.splitter = splitter
        mdp_family_result.hole_selection = hole_selection
        return mdp_family_result
    
    def choose_splitter(self, family, prop, scheduler_choices, state_values, hole_selection):
        inconsistent_assignments = {hole:options for hole,options in enumerate(hole_selection) if len(options) > 1}
        if len(inconsistent_assignments)==0:
            # pick any hole with multiple options
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
            expected_visits = self.quotient.expected_visits(mdp, prop, scheduler_choices)
        quotient_mdp_wrapped = self.quotient.design_space.mdp
        scores = self.quotient.estimate_scheduler_difference(quotient_mdp_wrapped, inconsistent_assignments, choice_values, expected_visits)
        return scores

    def split(self, family, prop, hole_selection, splitter):
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

        # construct corresponding design subspaces
        subfamilies = []
        family.splitter = splitter
        new_design_space = family.copy()
        for suboption in suboptions:
            subholes = new_design_space.subholes(splitter, suboption)
            subfamily = paynt.family.family.DesignSpace(subholes)
            subfamily.hole_set_options(splitter, suboption)
            subfamilies.append(subfamily)
        return suboptions,subfamilies


    def create_action_coloring(self):

        quotient_mdp = self.quotient.quotient_mdp
        family = paynt.family.family.Family()
        choice_to_hole_options = [[] for choice in range(quotient_mdp.nr_choices)]

        for state in range(quotient_mdp.nr_states):

            state_actions = self.quotient.state_to_actions[state]
            if len(state_actions) <= 1:
                # hole is not needed
                continue

            # create fresh hole
            hole = family.num_holes
            name = f'state_{state}'
            option_labels = [self.quotient.action_labels[action] for action in state_actions]
            family.add_hole(name,option_labels)

            for action_index,action in enumerate(state_actions):
                color = [(hole,action_index)]
                for choice in self.quotient.state_action_choices[state][action]:
                    choice_to_hole_options[choice] = color

        coloring = stormpy.synthesis.Coloring(family.family, quotient_mdp.nondeterministic_choice_indices, choice_to_hole_options)
        self.action_coloring_family = family
        self.action_coloring = coloring
        return
    
    ###############################
    #### POLICY SEARCH SECTION ####

    def update_scores(self, score_lists, selection):
        for hole, score_list in score_lists.items():
            for choice in selection[hole]:
                if choice not in score_list:
                    score_list.append(choice)
        
    
    def synthesize_policy_for_family(self, family, prop, all_sat=False, iteration_limit=0):
        '''
        Synthesize one policy for family of MDPs (if such policy exists).
        :param all_sat if True, it is assumed that all MDPs are SAT
        :returns whether all SAT MDPs are solved using a single policy
        :returns a list of UNSAT MDPs
        :returns a list of SAT MDPs
        :returns one policy if all SAT MDPs are solved using single policy or list containing a corresponding policy for each SAT MDP
        '''
        sat_mdp_families = []
        sat_mdp_policies = []
        unsat_mdp_families = []

        # create MDP subfamilies
        for hole_assignment in family.all_combinations():
            subfamily = family.copy()
            for hole_index, hole_option in enumerate(hole_assignment):
                subfamily.hole_set_options(hole_index, [hole_option])

            # find out which mdps are sat and unsat
            if not all_sat:
                self.quotient.build(subfamily)
                primary_result = subfamily.mdp.model_check_property(prop)
                assert primary_result.result.has_scheduler
                self.stat.iteration(subfamily.mdp)
    
                if primary_result.sat == False:
                    unsat_mdp_families.append(subfamily)
                    continue
    
                sat_mdp_families.append(subfamily)
                policy = self.quotient.scheduler_to_policy(primary_result.result.scheduler, subfamily.mdp)
                sat_mdp_policies.append(policy)
            else:
                sat_mdp_families.append(subfamily)
     
        # no sat mdps
        if len(sat_mdp_families) == 0:
            return False, unsat_mdp_families, sat_mdp_families, sat_mdp_policies
        
        if len(sat_mdp_policies) == 0:
            sat_mdp_policies = [None for _ in sat_mdp_families]
     
        action_family = paynt.family.family.DesignSpace(self.action_coloring_family)
        action_family_stack = [action_family]
        iter = 0

        # AR for policies
        while action_family_stack:

            if iteration_limit>0 and iter>iteration_limit:
                break

            current_action_family = action_family_stack.pop(-1)
            current_results = []

            score_lists = {hole:[] for hole in range(current_action_family.num_holes) if current_action_family.hole_num_options(hole) > 1}

            # try to find controller inconsistency across the MDPs
            # if the controllers are consistent, return True
            for index, mdp_subfamily in enumerate(sat_mdp_families):
                self.quotient.build_with_second_coloring(mdp_subfamily, self.action_coloring, current_action_family) # maybe copy to new family?

                primary_result = current_action_family.mdp.model_check_property(prop)
                self.stat.iteration(current_action_family.mdp)

                # discard the family as soon as one MDP is unsat
                if primary_result.sat == False:
                    current_results.append(False)
                    break

                # add policy if current mdp doesn't have one yet
                # TODO maybe this can be done after some number of controllers are consistent?
                if sat_mdp_policies[index] is None:
                    policy = self.quotient.scheduler_to_policy(primary_result.result.scheduler, mdp_subfamily.mdp)
                    sat_mdp_policies[index] = policy

                current_results.append(primary_result)
                selection = self.quotient.scheduler_selection(current_action_family.mdp, primary_result.result.scheduler, self.action_coloring)
                self.update_scores(score_lists, selection)

                scores = {hole:len(score_list) for hole, score_list in score_lists.items()}
                
                splitters = self.quotient.holes_with_max_score(scores)
                splitter = splitters[0]

                # refinement as soon as the first inconsistency is found
                if scores[splitter] > 1:
                    break
            else:
                policy = self.quotient.empty_policy()
                for index, (result, family) in enumerate(zip(current_results, sat_mdp_families)):
                    mdp_policy = self.quotient.scheduler_to_policy(result.result.scheduler, family.mdp)
                    policy = merge_policies([policy, mdp_policy])
                    assert policy is not None
                return True, unsat_mdp_families, sat_mdp_families, policy

            if False in current_results:
                continue

            used_options = score_lists[splitter]
            core_suboptions = [[option] for option in used_options]
            other_suboptions = [option for option in current_action_family.hole_options(splitter) if option not in used_options]
            if other_suboptions:
                other_suboptions = [other_suboptions]
            else:
                other_suboptions = []
            suboptions = other_suboptions + core_suboptions # DFS solves core first

            subfamilies = []
            current_action_family.splitter = splitter
            new_design_space = current_action_family.copy()
            for suboption in suboptions:
                subholes = new_design_space.subholes(splitter, suboption)
                action_subfamily = paynt.family.family.DesignSpace(subholes)
                action_subfamily.hole_set_options(splitter, suboption)
                subfamilies.append(action_subfamily)

            action_family_stack = action_family_stack + subfamilies

            iter += 1

        # compute policies for the sat mdps that were never analysed
        mdps_without_policy = [index for index, policy in enumerate(sat_mdp_policies) if policy is None]
        for mdp_index in mdps_without_policy:
            self.quotient.build(sat_mdp_families[mdp_index])
            primary_result = sat_mdp_families[mdp_index].mdp.model_check_property(prop)
            assert primary_result.result.has_scheduler
            self.stat.iteration(sat_mdp_families[mdp_index].mdp)
            policy = self.quotient.scheduler_to_policy(primary_result.result.scheduler, sat_mdp_families[mdp_index].mdp)
            sat_mdp_policies[mdp_index] = policy

        return False, unsat_mdp_families, sat_mdp_families, sat_mdp_policies
    

    def double_check_policy_synthesis(self, unsat_mdp_families, sat_mdp_families, sat_mdp_policies, sat_mdp_to_policy_map, prop):

        for unsat_family in unsat_mdp_families:
            self.quotient.build(unsat_family)
            result = unsat_family.mdp.model_check_property(prop)
            assert not result.sat, "double check fail"
            unsat_family.mdp = None

        for sat_index, sat_family in enumerate(sat_mdp_families):
            self.quotient.build(sat_family)
            sat_policy = sat_mdp_policies[sat_mdp_to_policy_map[sat_index]]
            SynthesizerPolicyTree.double_check_policy(self.quotient, sat_family, prop, sat_policy)
            sat_family.mdp = None


    def synthesize_policy_for_family_linear(self, family, prop):
        '''
        Synthesize policies for mdps in family in linear time with respect to family size
        :returns a list of UNSAT MDP families
        :returns a list of SAT MDP families
        :returns list of policies for SAT MDP families
        :returns list that maps each SAT MDP family to its policy 
        '''
        sat_mdp_families = []
        sat_mdp_policies = []
        sat_mdp_to_policy_map = []
        unsat_mdp_families = []

        mdp_families = []

        for hole_assignment in family.all_combinations():
            subfamily = family.copy()
            for hole_index, hole_option in enumerate(hole_assignment):
                subfamily.hole_set_options(hole_index, [hole_option])
            mdp_families.append(subfamily)

        for family in mdp_families:
            self.quotient.build(family)

            result = family.mdp.model_check_property(prop)
            self.stat.iteration_mdp(family.mdp.states)
            self.explore(family)
            if not result.sat:
                family.mdp = None
                unsat_mdp_families.append(family)
                continue
            
            policy = self.quotient.scheduler_to_policy(result.result.scheduler, family.mdp)

            family.mdp = None

            for index, sat_policy in enumerate(sat_mdp_policies):
                merged_policy = merge_policies([sat_policy, policy])
                if merged_policy is None:
                    continue
                else:                 
                    sat_mdp_policies[index] = merged_policy
                    sat_mdp_families.append(family)
                    sat_mdp_to_policy_map.append(index)
                    break
            else:
                sat_mdp_families.append(family)
                sat_mdp_to_policy_map.append(len(sat_mdp_policies))
                sat_mdp_policies.append(policy)

        return unsat_mdp_families, sat_mdp_families, sat_mdp_policies, sat_mdp_to_policy_map

    
    def synthesize_policy_for_family_using_ceg(self, family, prop):
        '''
        Synthesize policies for mdps in family using counter-example generalization
        :returns a list of UNSAT MDP families
        :returns a list of SAT MDP families
        :returns list of policies for SAT MDP families
        :returns list that maps each SAT MDP family to its policy 
        '''

        sat_mdp_families = []
        sat_mdp_policies = []
        sat_mdp_to_policy_map = []
        unsat_mdp_families = []
        
        self.quotient.build(family)

        smt_solver = paynt.family.smt.SmtSolver(family)

        unsat_conflict_generator = paynt.synthesizer.conflict_generator.mdp.ConflictGeneratorMdp(self.quotient)
        unsat_conflict_generator.initialize()

        mdp_subfamily = smt_solver.pick_assignment(family)

        while mdp_subfamily is not None:

            self.quotient.build(mdp_subfamily)

            result = mdp_subfamily.mdp.model_check_property(prop)
            self.stat.iteration(mdp_subfamily.mdp)

            if not result.sat:
                # MDP CE
                requests = [(0, self.quotient.specification.all_properties()[0], None)]
                choices = self.quotient.coloring.selectCompatibleChoices(mdp_subfamily.family)
                model,state_map,choice_map = self.quotient.restrict_quotient(choices)
                model = paynt.quotient.models.MDP(model,self.quotient,state_map,choice_map,mdp_subfamily)
                conflicts = unsat_conflict_generator.construct_conflicts(family, mdp_subfamily, model, requests)

                # conflicts = [list(range(family.num_holes))] # UNSAT without CE generalization

                pruned = smt_solver.exclude_conflicts(family, mdp_subfamily, conflicts)
                self.explored += pruned

                # MDP CE
                unsat_family = family.copy()
                for hole_index in range(self.quotient.design_space.num_holes):
                    if hole_index in conflicts[0]:
                        unsat_family.hole_set_options(hole_index, mdp_subfamily.hole_options(hole_index))  

                mdp_subfamily.mdp = None
                unsat_family.mdp = None
                unsat_mdp_families.append(unsat_family)
            else:
                policy = self.quotient.scheduler_to_policy(result.result.scheduler, mdp_subfamily.mdp)
                policy, policy_quotient_mdp = self.quotient.fix_and_apply_policy_to_family(family, policy) # DTMC CE
                # policy_quotient_mdp = self.quotient.apply_policy_to_family(family, policy) # MDP SAT CE
                quotient_assignment = self.quotient.coloring.getChoiceToAssignment()
                choice_to_hole_options = []
                for choice in range(policy_quotient_mdp.choices):
                    quotient_choice = policy_quotient_mdp.quotient_choice_map[choice]
                    choice_to_hole_options.append(quotient_assignment[quotient_choice])

                coloring = stormpy.synthesis.Coloring(family.family, policy_quotient_mdp.model.nondeterministic_choice_indices, choice_to_hole_options)
                quotient_container = paynt.quotient.quotient.DtmcFamilyQuotient(policy_quotient_mdp.model, family, coloring, self.quotient.specification.negate())
                conflict_generator = paynt.synthesizer.conflict_generator.dtmc.ConflictGeneratorDtmc(quotient_container) # DTMC CE
                # conflict_generator = paynt.synthesizer.conflict_generator.mdp.ConflictGeneratorMdp(quotient_container) # MDP SAT CE
                conflict_generator.initialize()
                mdp_subfamily.constraint_indices = family.constraint_indices
                requests = [(0, quotient_container.specification.all_properties()[0], None)]

                model = quotient_container.build_assignment(mdp_subfamily) # DTMC CE

                # choices = coloring.selectCompatibleChoices(mdp_subfamily.family) # MDP SAT CE
                # model,state_map,choice_map = quotient_container.restrict_quotient(choices) # MDP SAT CE
                # model = paynt.quotient.models.MDP(model,quotient_container,state_map,choice_map,mdp_subfamily) # MDP SAT CE

                conflicts = conflict_generator.construct_conflicts(family, mdp_subfamily, model, requests)
                pruned = smt_solver.exclude_conflicts(family, mdp_subfamily, conflicts)
                self.explored += pruned

                sat_family = family.copy()
                for hole_index in range(self.quotient.design_space.num_holes):
                    if hole_index in conflicts[0]:
                        sat_family.hole_set_options(hole_index, mdp_subfamily.hole_options(hole_index))  

                sat_family.mdp = None
                sat_mdp_families.append(sat_family)
                sat_mdp_to_policy_map.append(len(sat_mdp_policies))
                sat_mdp_policies.append(policy)

            mdp_subfamily = smt_solver.pick_assignment(family)

        return unsat_mdp_families, sat_mdp_families, sat_mdp_policies, sat_mdp_to_policy_map
    
    #### POLICY SEARCH SECTION END ####
    ###################################
        


    def evaluate_all(self, family, prop, keep_value_only=False):
        assert not prop.reward, "expecting reachability probability propery"
        game_solver = self.quotient.build_game_abstraction_solver(prop)
        policy_tree = PolicyTree(family)

        ### POLICY SEARCH TESTING
        #self.create_action_coloring()

        # choose policy search method
        # unsat, sat, policies, policy_map = self.synthesize_policy_for_family_linear(policy_tree.root.family, prop)
        # unsat, sat, policies, policy_map = self.synthesize_policy_for_family_using_ceg(policy_tree.root.family, prop)
        
        # self.stat.synthesis_timer.stop()

        # unsat_mdps_count = sum([s.size for s in unsat])
        # sat_mdps_count = sum([s.size for s in sat])

        # print(f'unSAT MDPs: {unsat_mdps_count}\tunSAT families: {len(unsat)}\tavg. unSAT family size: {round(unsat_mdps_count/len(unsat),2) if len(unsat) != 0 else "N/A"}')
        # print(f'SAT MDPs: {sat_mdps_count}\tSAT families: {len(sat)}\tavg. SAT family size: {round(sat_mdps_count/len(sat),2) if len(sat) != 0 else "N/A"}')
        # print(f'policies: {len(policies)}\tpolicy per SAT MDP: {round(len(policies)/sat_mdps_count,2) if sat_mdps_count != 0 else "N/A"}')
        # print(f'iterations: {self.stat.iterations_mdp}')
        # print(f'time: {round(self.stat.synthesis_timer.time,2)}s')

        # self.double_check_policy_synthesis(unsat, sat, policies, policy_map, prop)
        # exit()
        ###

        if False:
            self.quotient.build(policy_tree.root.family)
            policy_exists,_,_,_ = self.synthesize_policy_for_family(policy_tree.root.family, prop, all_sat=True)
            print("Policy exists: ", policy_exists)
            return None

        policy_tree_leaves = [policy_tree.root]
        while policy_tree_leaves:

            # gi = self.stat.iterations_game
            # if gi is not None and gi > 1000:
            #     return None

            policy_tree_node = policy_tree_leaves.pop(-1)
            family = policy_tree_node.family
            result = self.verify_family(family,game_solver,prop)
            policy_tree_node.policy = result.policy
            policy_tree_node.policy_source = result.policy_source

            if result.policy is not None:
                self.explore(family)
                if policy_tree_node != policy_tree.root:
                    family.mdp = None   # memory optimization
                continue

            # refine
            suboptions,subfamilies = self.split(family, prop, result.hole_selection, result.splitter)
            if policy_tree_node != policy_tree.root:
                family.mdp = None   # memory optimization
            policy_tree_node.split(result.splitter,suboptions,subfamilies)
            policy_tree_leaves = policy_tree_leaves + policy_tree_node.child_nodes

        if SynthesizerPolicyTree.double_check_policy_tree_leaves:
            policy_tree.double_check(self.quotient, prop)
        policy_tree.print_stats()
        policy_tree.postprocess(self.quotient, prop, self.stat)

        # convert policy tree to family evaluation
        family_to_evaluation = []
        for node in policy_tree.collect_leaves():
            evaluation = paynt.synthesizer.synthesizer.FamilyEvaluation(None,node.solved,policy=node.policy)
            family_to_evaluation.append( (node.family,evaluation) )
        return family_to_evaluation
