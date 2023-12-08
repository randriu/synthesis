import stormpy.synthesis

import paynt.quotient.holes
import paynt.quotient.coloring
import paynt.quotient.models
import paynt.synthesizer.synthesizer

import paynt.verification.property_result
from paynt.verification.property import Property

import logging
logger = logging.getLogger(__name__)


class MdpFamilyResult:
    def __init__(self):
        # if None, then family is undediced
        # if False, then all family is UNSAT
        # otherwise, then contains a satisfying policy for all MDPs in the family
        self.policy = None
        self.policy_source = ""

        self.hole_selection = None
        self.splitter = None

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
            self.child_nodes[target].family[self.splitter].assume_options(self.suboptions[target])
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
        
        print()
        print("X  -  number of nodes solved with policy of type X")
        for key,number in self.count_policy_sources().items():
            print(key, " - ", number)
        print("--------------------")


    

    
    def postprocess(self, quotient, prop):
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
        self.print_stats()

        logger.info("merging solved siblings...")
        PolicyTreeNode.merged = 0
        all_nodes = self.collect_all()
        for node in reversed(all_nodes):
            node.merge_children_solved()
        logger.info("merged {} pairs".format(PolicyTreeNode.merged))
        self.print_stats()



class SynthesizerPolicyTree(paynt.synthesizer.synthesizer.Synthesizer):

    # if True, then the game scheduler will be used for splitting (incompatible with randomized abstraction)
    use_optimistic_splitting = True
    # if True, tree leaves will be double-checked after synthesis
    double_check_policy_tree_leaves = False
    
    @property
    def method_name(self):
        return "AR (policy tree)"

    @staticmethod
    def double_check_policy(quotient, family, prop, policy):
        mdp = quotient.apply_policy_to_family(family, policy)
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
        mdp = self.quotient.apply_policy_to_family(family, policy)
        policy_result = mdp.model_check_property(prop, alt=True)
        self.stat.iteration_mdp(mdp.states)
        return policy_result.sat

    
    def solve_singleton(self, family, prop):
        result = family.mdp.model_check_property(prop)
        self.stat.iteration_mdp(family.mdp.states)
        if not result.sat:
            return False
        policy = self.quotient.scheduler_to_policy(result.result.scheduler, family.mdp)
    
        # uncomment below to preemptively double-check the policy
        # SynthesizerPolicyTree.double_check_policy(self.quotient, family, prop, policy)
        return policy


    def solve_game_abstraction(self, family, prop, game_solver):
        # construct and solve the game abstraction
        # logger.debug("solving game abstraction...")
        game_solver.solve(family.selected_actions_bv, prop.maximizing, prop.minimizing)
        self.stat.iteration_game(family.mdp.states)
        # logger.debug("game solved, value is {}".format(game_solver.solution_value))
        game_policy = game_solver.solution_state_to_player1_action
        # fix irrelevant choices
        policy = self.quotient.empty_policy()
        for state,action in enumerate(game_policy):
            if action < self.quotient.num_actions:
                policy[state] = action
        policy_sat = prop.satisfies_threshold(game_solver.solution_value)
        
        if False:
            # double-check game value
            model,state_map,choice_map = self.quotient.restrict_mdp(self.quotient.quotient_mdp, game_solver.solution_reachable_choices)
            assert(model.nr_states == model.nr_choices)
            dtmc = paynt.quotient.models.DTMC(model, self.quotient, state_map, choice_map)
            dtmc_result = dtmc.model_check_property(prop)
            # print("double-checking game value: ", game_solver.solution_value, dtmc_result)
            if abs(dtmc_result.value-game_solver.solution_value) > 0.01:
                logger.error("game solution is {}, but DTMC model checker yielded {}".format(game_solver.solution_value,dtmc_result.value))

        return policy, policy_sat

    
    def verify_family(self, family, game_solver, prop, reference_policy=None):
        # logger.info("investigating family of size {}".format(family.size))
        self.quotient.build(family)
        mdp_family_result = MdpFamilyResult()

        if family.size <= 8 and False:
            policy_is_unique, unsat_mdps, sat_mdps, sat_policies = self.synthesize_policy_for_family(family, prop)
            if policy_is_unique:
                policy = merge_policies(sat_policies)
                assert policy is not None

        if False and reference_policy is not None:
            # try reference policy
            reference_policy_sat = self.verify_policy(family,prop,reference_policy)
            if reference_policy_sat:
                # print("reference policy worked!")
                mdp_family_result.policy = reference_policy
                mdp_family_result.policy_source = "reference"
                return mdp_family_result

        if family.size == 1:
            mdp_family_result.policy = self.solve_singleton(family,prop)
            mdp_family_result.policy_source = "singleton"
            return mdp_family_result

        
        game_policy,game_sat = self.solve_game_abstraction(family,prop,game_solver)
        if game_sat:
            game_policy_sat = self.verify_policy(family,prop,game_policy)
            if game_policy_sat:
                mdp_family_result.policy = game_policy
                mdp_family_result.policy_source = "game abstraction"
                return mdp_family_result
            else:
                print("game YES but nor forall family of size ", family.size)
        
        if not game_sat or not SynthesizerPolicyTree.use_optimistic_splitting:
            # solve primary-primary direction for the family
            # logger.debug("solving primary-primary direction...")
            primary_primary_result = family.mdp.model_check_property(prop)
            self.stat.iteration_mdp(family.mdp.states)
            # logger.debug("primary-primary direction solved, value is {}".format(primary_primary_result.value))
            if not primary_primary_result.sat:
                mdp_family_result.policy = False
                return mdp_family_result
    
        # undecided: choose scheduler choices to be used for splitting
        if SynthesizerPolicyTree.use_optimistic_splitting:
            state_values = game_solver.solution_state_values
            state_to_choice = game_solver.solution_state_to_quotient_choice
            state_to_choice = self.quotient.keep_reachable_choices_of_scheduler(state_to_choice)
        else:
            state_to_choice = self.quotient.scheduler_to_state_to_choice(family.mdp, primary_primary_result.result.scheduler)
            state_values = [0] * self.quotient.quotient_mdp.nr_states
            for state in range(family.mdp.states):
                quotient_state = family.mdp.quotient_state_map[state]
                state_values[quotient_state] = primary_primary_result.result.at(state)

        # map reachable scheduler choices to hole options
        scheduler_choices = self.quotient.state_to_choice_to_choices(state_to_choice)
        hole_selection = self.quotient.coloring.choices_to_hole_selection(scheduler_choices)
        
        if False:
            # sanity check
            for choice in scheduler_choices:
                assert choice in family.selected_actions_bv
            for hole_index,options in enumerate(hole_selection):
                assert all([option in family[hole_index].options for option in options])

        # pick splitter
        splitter = self.choose_splitter(family,prop,scheduler_choices,state_values,hole_selection)
        
        # done
        mdp_family_result.splitter = splitter
        mdp_family_result.hole_selection = hole_selection
        return mdp_family_result


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
            expected_visits = None
            if self.quotient.compute_expected_visits:
                expected_visits = self.quotient.expected_visits(mdp, prop, scheduler_choices)
            quotient_mdp_wrapped = self.quotient.design_space.mdp
            scores = self.quotient.estimate_scheduler_difference(quotient_mdp_wrapped, inconsistent_assignments, choice_values, expected_visits)
            splitters = self.quotient.holes_with_max_score(scores)
            splitter = splitters[0]
        assert splitter is not None
        return splitter
    
    
    def split(self, family, prop, hole_selection, splitter):
        
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
        
        return suboptions,subfamilies


    def create_action_coloring(self):

        quotient_mdp = self.quotient.quotient_mdp
        holes = paynt.quotient.holes.Holes()
        choice_to_hole_options = [{} for choice in range(quotient_mdp.nr_choices)]

        for state in range(quotient_mdp.nr_states):

            state_actions = self.quotient.state_to_actions[state]
            if len(state_actions) <= 1:
                # hole is not needed
                continue

            # create fresh hole
            hole_index = holes.num_holes
            name = f'state_{state}'
            options = list(range(len(state_actions)))
            option_labels = [self.quotient.action_labels[action] for action in state_actions]
            hole = paynt.quotient.holes.Hole(name, options, option_labels)
            holes.append(hole)

            for action_index,action in enumerate(state_actions):
                color = {hole_index: action_index}
                for choice in self.quotient.state_action_choices[state][action]:
                    choice_to_hole_options[choice] = color

        coloring = paynt.quotient.coloring.Coloring(quotient_mdp, holes, choice_to_hole_options)
        self.action_coloring = coloring
        return
    

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
        :returns to each SAT MDP, a corresponding policy
        '''
        sat_mdp_families = []
        sat_mdp_policies = []
        unsat_mdp_families = []

        # create MDP subfamilies
        for hole_assignment in family.all_combinations():
            subfamily = family.copy()
            for hole_index, hole_option in enumerate(hole_assignment):
                subfamily.assume_hole_options(hole_index, [hole_option])

            # find out which mdps are sat and unsat
            if not all_sat:
                self.quotient.build(subfamily)
                primary_result = subfamily.mdp.model_check_property(prop)
                assert primary_result.result.has_scheduler
                self.stat.iteration_mdp(subfamily.mdp.states)
    
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
     
        action_family = paynt.quotient.holes.DesignSpace(self.action_coloring.holes)
        action_family_stack = [action_family]
        iter = 0

        # AR for policies
        while action_family_stack:

            if iteration_limit>0 and iter>iteration_limit:
                break

            current_action_family = action_family_stack.pop(-1)
            current_results = []

            score_lists = {hole:[] for hole in current_action_family.hole_indices if len(current_action_family[hole].options) > 1}

            # try to find controller inconsistency across the MDPs
            # if the controllers are consistent, return True
            for index, mdp_subfamily in enumerate(sat_mdp_families):
                self.quotient.build_with_second_coloring(mdp_subfamily, self.action_coloring, current_action_family) # maybe copy to new family?

                mc_result = stormpy.model_checking(
                    current_action_family.mdp.model, prop.formula, extract_scheduler=True, environment=Property.environment)
                value = mc_result.at(current_action_family.mdp.initial_state)
                primary_result = paynt.verification.property_result.PropertyResult(prop, mc_result, value)
                self.stat.iteration_mdp(current_action_family.mdp.states)

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
                for index, (result, family) in enumerate(zip(current_results, sat_mdp_families)):
                    policy = self.quotient.scheduler_to_policy(result.result.scheduler, family.mdp)
                    sat_mdp_policies[index] = policy
                return True, unsat_mdp_families, sat_mdp_families, sat_mdp_policies

            if False in current_results:
                continue

            used_options = score_lists[splitter]
            core_suboptions = [[option] for option in used_options]
            other_suboptions = [option for option in current_action_family[splitter].options if option not in used_options]
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
                action_subfamily = paynt.quotient.holes.DesignSpace(subholes)
                action_subfamily.assume_hole_options(splitter, suboption)
                subfamilies.append(action_subfamily)

            action_family_stack = action_family_stack + subfamilies

            iter += 1

        # compute policies for the sat mdps that were never analysed
        mdps_without_policy = [index for index, policy in enumerate(sat_mdp_policies) if policy is None]
        for mdp_index in mdps_without_policy:
            self.quotient.build(sat_mdp_families[mdp_index])
            primary_result = sat_mdp_families[mdp_index].mdp.model_check_property(prop)
            assert primary_result.result.has_scheduler
            self.stat.iteration_mdp(sat_mdp_families[mdp_index].mdp.states)
            policy = self.quotient.scheduler_to_policy(primary_result.result.scheduler, sat_mdp_families[mdp_index].mdp)
            sat_mdp_policies[mdp_index] = policy

        return False, unsat_mdp_families, sat_mdp_families, sat_mdp_policies
        


    def synthesize_policy_tree(self, family):

        prop = self.quotient.get_property()
        game_solver = self.quotient.build_game_abstraction_solver(prop)
        policy_tree = PolicyTree(family)
        self.create_action_coloring()

        if False:
            self.quotient.build(policy_tree.root.family)
            policy_exists,_,_,_ = self.synthesize_policy_for_family(policy_tree.root.family, prop, all_sat=True)
            print("Policy exists: ", policy_exists)
            return None

        reference_policy = None
        policy_tree_leaves = [policy_tree.root]
        while policy_tree_leaves:

            policy_tree_node = policy_tree_leaves.pop(-1)
            family = policy_tree_node.family
            result = self.verify_family(family,game_solver,prop,reference_policy)
            policy_tree_node.policy = result.policy
            policy_tree_node.policy_source = result.policy_source

            if result.policy == False:
                reference_policy = None
                self.explore(family)
                continue

            if result.policy is not None:
                reference_policy = result.policy
                self.explore(family)
                continue

            reference_policy = None

            # refine
            suboptions,subfamilies = self.split(family, prop, result.hole_selection, result.splitter)
            policy_tree_node.split(result.splitter,suboptions,subfamilies)
            policy_tree_leaves = policy_tree_leaves + policy_tree_node.child_nodes

        if SynthesizerPolicyTree.double_check_policy_tree_leaves:
            policy_tree.double_check(self.quotient, prop)
        policy_tree.print_stats()
        policy_tree.postprocess(self.quotient, prop)
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
    