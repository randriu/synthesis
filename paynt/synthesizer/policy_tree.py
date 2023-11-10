import stormpy.synthesis

import paynt.quotient.holes
import paynt.quotient.models
import paynt.synthesizer.synthesizer

import logging
logger = logging.getLogger(__name__)


class MdpFamilyResult:
    def __init__(self):
        # if True, then all family is sat; if False, then all family is UNSAT; otherwise it is None
        self.sat = None
        # if not None, then contains a satisfying policy for all MDPs in the family
        self.satisfying_policy = None

        self.scheduler_choices = None
        self.hole_selection = None

    def __str__(self):
        return str(self.sat)


class PolicyTreeNode:

    def __init__(self, family):
        self.family = family

        self.family_is_solvable = None
        self.policy = None
        
        self.splitter = None
        self.suboptions = None
        self.child_nodes = None

    def unsolved(self):
        self.family_is_solvable = False

    def solved(self, policy):
        self.family_is_solvable = True
        self.policy = policy

    def split(self, splitter, suboptions, subfamilies):
        self.splitter = splitter
        self.suboptions = suboptions
        self.child_nodes = []
        for subfamily in subfamilies:
            child_node = PolicyTreeNode(subfamily)
            self.child_nodes.append(child_node)


class PolicyTree:

    def __init__(self, family):
        self.root = PolicyTreeNode(family)

    def __str__(self):
        pass

    def collect_leaves(self):
        node_queue = [self.root]
        leaves = []
        while node_queue:
            node = node_queue.pop(0)
            if node.child_nodes is None:
                leaves.append(node)
            else:
                node_queue = node_queue + node.child_nodes
        return leaves

    def collect_stats(self):
        
        members_total = self.root.family.size
        members_satisfied = 0
        members_verified_individually = 0
        
        leaves = self.collect_leaves()
        for leaf in leaves:
            if leaf.family.size==1:
                members_verified_individually += 1
            if leaf.family_is_solvable == True:
                members_satisfied += leaf.family.size
        return members_total,members_satisfied,members_verified_individually





class SynthesizerPolicyTree(paynt.synthesizer.synthesizer.Synthesizer):

    @property
    def method_name(self):
        return "AR (policy tree)"


    def verify_family(self, family, game_solver, prop):
        self.quotient.build(family)

        mdp_family_result = MdpFamilyResult()

        if family.size == 1:
            self.stat.iteration_mdp(family.mdp.states)
            primary_primary_result = family.mdp.model_check_property(prop)
            # logger.debug("primary-primary direction solved, value is {}".format(primary_primary_result.value))
            mdp_family_result.sat = primary_primary_result.sat
            if primary_primary_result.sat:
                # extract policy
                # TODO optimize this
                scheduler = primary_primary_result.result.scheduler
                choices = scheduler.compute_action_support(family.mdp.model.nondeterministic_choice_indices)
                # dtmc,_,choice_map = self.quotient.restrict_mdp(family.mdp.model, choices)
                # choices = [ choice_map[state] for state in range(dtmc.nr_states) ]
                quotient_choice_mask = stormpy.BitVector(self.quotient.quotient_mdp.nr_choices, False)
                for choice in choices:
                    quotient_choice_mask.set(family.mdp.quotient_choice_map[choice],True)
                policy = [self.quotient.num_actions] * self.quotient.quotient_mdp.nr_states
                tm = self.quotient.quotient_mdp.transition_matrix
                for state in range(self.quotient.quotient_mdp.nr_states):
                    for choice in range(tm.get_row_group_start(state),tm.get_row_group_end(state)):
                        if quotient_choice_mask[choice]:
                            policy[state] = self.quotient.choice_to_action[choice]
                mdp_family_result.satisfying_policy = policy
            return mdp_family_result


        # construct and solve the game abstraction
        # logger.debug("solving the game...")
        self.stat.iteration_game(family.mdp.states)
        game_solver.solve(family.selected_actions_bv, prop.maximizing, prop.minimizing)
        # logger.debug("game solved, value is {}".format(game_solver.solution_value))
        game_result_sat = prop.satisfies_threshold(game_solver.solution_value)
        
        if True:
            model,state_map,choice_map = self.quotient.restrict_mdp(self.quotient.quotient_mdp, game_solver.solution_reachable_choices)
            assert(model.nr_states == model.nr_choices)
            dtmc = paynt.quotient.models.DTMC(model, self.quotient, state_map, choice_map)
            dtmc_result = dtmc.model_check_property(prop)
            # print("double-checking game value: ", game_solver.solution_value, dtmc_result)
            if abs(dtmc_result.value-game_solver.solution_value) > 0.1:
                logger.error("game solution is {}, but DTMC model checker yielded {}".format(game_solver.solution_value,dtmc_result.value))

        if game_result_sat:
            # logger.debug("verifying game policy...")
            mdp_family_result.sat = True
            # apply player 1 actions to the quotient
            policy = game_solver.solution_state_to_player1_action

            mdp = self.quotient.keep_actions(family, policy)
            self.stat.iteration_mdp(mdp.states)
            policy_result = mdp.model_check_property(prop, alt=True)
            if policy_result.sat:
                # this scheduler is good for all MDPs in the family
                mdp_family_result.satisfying_policy = policy
                return mdp_family_result
        else:
            # logger.debug("solving primary-primary direction...")
            # solve primary-primary direction for the family
            self.stat.iteration_mdp(family.mdp.states)
            primary_primary_result = family.mdp.model_check_property(prop)
            # logger.debug("primary-primary direction solved, value is {}".format(primary_primary_result.value))
            if not primary_primary_result.sat:
                mdp_family_result.sat = False
                return mdp_family_result
        
        # undecided: prepare to split
        scheduler_choices = game_solver.solution_reachable_choices
        ev = self.quotient.expected_visits(self.quotient.quotient_mdp, prop, scheduler_choices)
        for choice in scheduler_choices:
            assert choice in family.selected_actions_bv

        # map scheduler choices to hole options and check consistency
        hole_selection = [set() for hole_index in self.quotient.design_space.hole_indices]
        for choice in scheduler_choices:
            choice_options = self.quotient.coloring.action_to_hole_options[choice]
            for hole_index,option in choice_options.items():
                hole_selection[hole_index].add(option)
        hole_selection = [list(options) for options in hole_selection]
        for hole_index,options in enumerate(hole_selection):
            assert all([option in family[hole_index].options for option in options])
        mdp_family_result.scheduler_choices = scheduler_choices
        mdp_family_result.hole_selection = hole_selection
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
        
        # splitter = self.choose_splitter(family,prop,scheduler_choices,state_values,hole_selection)
        splitter = self.choose_splitter_round_robin(family,prop,scheduler_choices,state_values,hole_selection)
        # split the hole
        used_options = hole_selection[splitter]
        if len(used_options) > 1:
            core_suboptions = [[option] for option in used_options]
            other_suboptions = [option for option in family[splitter].options if option not in used_options]
        else:
            assert len(family[splitter].options) > 1
            options = family[splitter].options
            half = len(options) // 2
            core_suboptions = [options[:half], options[half:]]
            other_suboptions = []

        if len(other_suboptions) == 0:
            suboptions = core_suboptions
        else:
            suboptions = [other_suboptions] + core_suboptions  # DFS solves core first
        
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
        
        policy_tree_leaves = [policy_tree.root]
        while policy_tree_leaves:
            policy_tree_node = policy_tree_leaves.pop(-1)
            family = policy_tree_node.family
            # logger.info("investigating family of size {}".format(family.size))
            result = self.verify_family(family,game_solver,prop)

            if result.sat == False:
                # logger.info("satisfying scheduler cannot be obtained for the following family {}".format(family))
                self.explore(family)
                policy_tree_node.unsolved()
                continue

            if result.satisfying_policy is not None:
                # logger.info("found policy for all MDPs in the family")
                self.explore(family)
                policy_tree_node.solved(result.satisfying_policy)
                continue

            # refine
            splitter,suboptions,subfamilies = self.split(
                family, prop, game_solver.solution_reachable_choices, game_solver.solution_state_values, result.hole_selection
            )
            policy_tree_node.split(splitter,suboptions,subfamilies)
            policy_tree_leaves = policy_tree_leaves + policy_tree_node.child_nodes

        logger.info("all families are explored")
        members_total,members_satisfied,members_verified_individually = policy_tree.collect_stats()
        logger.info("individual MDPs verified: {}".format(members_verified_individually))
        satisfied_percentage = round(members_satisfied/members_total*100,0)
        logger.info("found satisfying policies for {}/{} family members ({}%)".format(members_satisfied,members_total,satisfied_percentage))
        return "yes"

    

    def synthesize(self, family = None):
        if family is None:
            family = self.quotient.design_space
        self.stat.start()
        logger.info("synthesis initiated, design space: {}".format(family.size))
        policy_tree = self.synthesize_policy_tree(family)
        self.stat.finished(policy_tree)
        return policy_tree

    
    def run(self):
        ''' Synthesize meta-policy that satisfies all family members. '''
        self.quotient.design_space.constraint_indices = self.quotient.specification.all_constraint_indices()

        spec = self.quotient.specification
        assert not spec.has_optimality and spec.num_properties == 1 and not spec.constraints[0].reward, \
            "expecting a single reachability probability constraint"
        
        self.synthesize()
        self.stat.print()
    