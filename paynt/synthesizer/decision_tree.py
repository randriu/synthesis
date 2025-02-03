import paynt.synthesizer.synthesizer_ar
import paynt.quotient.mdp
import paynt.utils.timer

from paynt.utils.tree_helper import parse_tree_helper

import paynt.utils.tree_helper
import stormpy
import payntbind

import os
import json

import os
import shutil
import subprocess

import logging
from datetime import datetime
logger = logging.getLogger(__name__)

class SynthesizerDecisionTree(paynt.synthesizer.synthesizer_ar.SynthesizerAR):

    # tree depth
    tree_depth = 0
    # if set, all trees of size at most tree_depth will be enumerated
    tree_enumeration = False
    # path to a scheduler to be mapped to a decision tree
    scheduler_path = None

    def __init__(self, *args):
        super().__init__(*args)
        self.best_tree = None
        self.best_tree_value = None

    @property
    def method_name(self):
        return "AR (decision tree)"

    def verify_hole_selection(self, family, hole_selection):
        spec = self.quotient.specification
        assignment = family.assume_options_copy(hole_selection)
        dtmc = self.quotient.build_assignment(assignment)
        res = dtmc.check_specification(spec)
        if not res.constraints_result.sat:
            return
        if not spec.has_optimality:
            family.analysis_result.improving_assignment = assignment
            family.analysis_result.can_improve = False
            return
        assignment_value = res.optimality_result.value
        if spec.optimality.improves_optimum(assignment_value):
            # logger.info(f"harmonization achieved value {res.optimality_result.value}")
            self.num_harmonization_succeeded += 1
            family.analysis_result.improving_assignment = assignment
            family.analysis_result.improving_value = assignment_value
            family.analysis_result.can_improve = True
            self.update_optimum(family)


    def harmonize_inconsistent_scheduler(self, family):
        self.num_harmonizations += 1
        mdp = family.mdp
        result = family.analysis_result.undecided_result()
        hole_selection = result.primary_selection
        harmonizing_hole = [hole for hole,options in enumerate(hole_selection) if len(options)>1][0]
        selection_1 = hole_selection.copy(); selection_1[harmonizing_hole] = [selection_1[harmonizing_hole][0]]
        selection_2 = hole_selection.copy(); selection_2[harmonizing_hole] = [selection_2[harmonizing_hole][1]]
        for selection in [selection_1,selection_2]:
            self.verify_hole_selection(family,selection)


    def verify_family(self, family):
        self.num_families_considered += 1
        self.quotient.build(family)

        self.stat.iteration(family.mdp)
        if family.parent_info is not None:
            for choice in family.parent_info.scheduler_choices:
                if not family.selected_choices[choice]:
                    break
            else:
                # scheduler preserved in the sub-family
                self.num_schedulers_preserved += 1
                family.analysis_result = family.parent_info.analysis_result
                family.scheduler_choices = family.parent_info.scheduler_choices
                consistent,hole_selection = self.quotient.are_choices_consistent(family.scheduler_choices, family)
                assert not consistent
                family.analysis_result.optimality_result.primary_selection = hole_selection
                return

        self.num_families_model_checked += 1
        self.check_specification(family)
        if not family.analysis_result.can_improve:
            return
        self.harmonize_inconsistent_scheduler(family)


    def counters_reset(self):
        self.num_families_considered = 0
        self.num_families_skipped = 0
        self.num_families_model_checked = 0
        self.num_schedulers_preserved = 0
        self.num_harmonizations = 0
        self.num_harmonization_succeeded = 0

        # integration stats
        self.dtcontrol_calls = 0
        self.dtcontrol_successes = 0
        self.paynt_calls = 0
        self.paynt_successes_smaller = 0
        self.paynt_tree_found = 0
        self.both_larger = 0

    def counters_print(self):
        logger.info(f"families considered: {self.num_families_considered}")
        logger.info(f"families skipped by construction: {self.num_families_skipped}")
        logger.info(f"families with schedulers preserved: {self.num_schedulers_preserved}")
        logger.info(f"families model checked: {self.num_families_model_checked}")
        logger.info(f"harmonizations attempted: {self.num_harmonizations}")
        logger.info(f"harmonizations succeeded: {self.num_harmonization_succeeded}")
        print()

    def export_decision_tree(self, decision_tree, export_filename_base):
        tree = decision_tree.to_graphviz()
        tree_filename = export_filename_base + ".dot"
        directory = os.path.dirname(tree_filename)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(tree_filename, 'w') as file:
            file.write(tree.source)
        logger.info(f"exported decision tree to {tree_filename}")

        tree_visualization_filename = export_filename_base + ".png"
        tree.render(export_filename_base, format="png", cleanup=True) # using export_filename_base since graphviz appends .png by default
        logger.info(f"exported decision tree visualization to {tree_visualization_filename}")
    

    def create_tree_node_queue_heuristic(self, helper_tree, desired_depth=6):
        nodes = helper_tree.collect_nodes(lambda node : node.get_depth() == desired_depth)
        if nodes is None or len(nodes) == 0:
            return []
        helper_nodes = [self.quotient.tree_helper[node.identifier] for node in nodes]
        helper_node_stats = []
        for helper_node in helper_nodes:
            if helper_node["id"] == 0:
                continue
            helper_tree_node = helper_tree.collect_nodes(lambda node : node.identifier == helper_node["id"])[0]
            # stats = {"id": helper_node["id"], "states": self.quotient.get_state_space_for_tree_helper_node(helper_node["id"]), "nodes": helper_tree_node.get_number_of_descendants()}
            stats = {"id": helper_node["id"], "nodes": helper_tree_node.get_number_of_descendants()}

            # this happens for nodes created outside of DtControl
            if "evaluations" not in helper_node.keys():
                stats["predicates"] = {}
            else:
                stats["predicates"] = {pred : eval for pred, eval in helper_node["evaluations"].items() if eval <= list(helper_node["evaluations"].values())[0]*1.05}
            helper_node_stats.append(stats)

            # TODO remove this
            # assert stats["states"] == self.quotient.get_state_space_for_tree_helper_node_old(helper_node["id"]), "new implementation does not match old implementation"

        if len(helper_node_stats) == 0:
            return []

        # helper_node_stats = sorted(helper_node_stats, key=lambda x : x["states"].number_of_set_bits()/x["nodes"])
        helper_node_stats = sorted(helper_node_stats, key=lambda x : x["nodes"], reverse=True)
        helper_node_stats = sorted(helper_node_stats, key=lambda x : len(x["predicates"]), reverse=True)

        return helper_node_stats
    

    def synthesize_subtrees(self, opt_result_value, random_result_value=None):

        # SETTINGS
        subtree_depth = 7
        max_iter = 1000
        epsilon = 0.05
        timeout = 1200
        depth_fine_tuning = True # experimental
        break_on_small_tree = True
        use_dtcontrol = True

        # complete init
        self.counters_reset()
        if random_result_value is None:
            mc_result_positive = opt_result_value > 0
            if self.quotient.specification.optimality.maximizing == mc_result_positive:
                epsilon *= -1
            eps_optimum_threshold = opt_result_value * (1 + epsilon)
        else: # this should result in normalised value of the produced tree being within espilon
            opt_random_diff = opt_result_value - random_result_value
            eps_optimum_threshold = opt_result_value - 0.01 * opt_random_diff
        self.synthesis_timer = paynt.utils.timer.Timer(timeout)
        self.synthesis_timer.start()

        # initialize from external tree
        self.quotient.tree_helper_tree = self.quotient.build_tree_helper_tree()
        tree_helper_tree = self.quotient.tree_helper_tree
        logger.info(f'initial external tree has depth {tree_helper_tree.get_depth()} and {len(tree_helper_tree.collect_nonterminals())} nodes')
        
        current_iter = 0
        current_depth = subtree_depth

        # TODO think about this fine tuning more...
        while (depth_fine_tuning and current_depth > 1) or (current_depth == subtree_depth):

            if self.synthesis_timer.time_limit_reached():
                    logger.info(f"timeout reached")
                    break

            logger.info(f"starting iteration with subtree depth {current_depth}")
            # TODO this is not guaranteed to work in subsequent iterations when the PAYNT tree is used
            node_queue = self.create_tree_node_queue_heuristic(tree_helper_tree, desired_depth=current_depth)

            while len(node_queue) > 0 and (True or (current_iter < max_iter)):

                if self.synthesis_timer.time_limit_reached():
                    logger.info(f"timeout reached")
                    break

                logger.info(f"starting iteration {current_iter} with {len(node_queue)} nodes in node queue")
                logger.info(f"current tree size: {len(tree_helper_tree.collect_nodes())} nodes")
            
                current_iter += 1
                node = node_queue.pop(0)

                # print(tree_helper_tree.to_graphviz([node["id"]]))

                # subtree synthesis
                node_states = self.quotient.get_state_space_for_tree_helper_node(node["id"])
                submdp = self.quotient.get_submdp_from_unfixed_states(node_states)
                logger.info(f"subtree quotient has {submdp.model.nr_states} states and {submdp.model.nr_choices} choices")
                subtree_spec = self.quotient.specification.copy()
                subtree_quotient = paynt.quotient.mdp.MdpQuotient(submdp.model, subtree_spec)
                # if subtree_quotient.self.state_is_relevant_bv.number_of_set_bits() == 0:
                #     logger.info(f"no relevant states in subtree quotient")
                #     continue
                subtree_quotient.specification.optimality.update_optimum(eps_optimum_threshold)
                subtree_synthesizer = SynthesizerDecisionTree(subtree_quotient)
                # depth = 2
                # subtree_synthesizer.synthesize_tree(depth)
                self.paynt_calls += 1
                subtree_synthesizer.synthesize_tree_sequence(opt_result_value, overall_timeout=60, max_depth=current_depth, break_if_found=break_on_small_tree)

                # create new tree
                if subtree_synthesizer.best_tree is not None:
                    logger.info(f"admissible subtree found from node {node['id']}")
                    self.paynt_tree_found += 1
                    relevant_state_valuations = [subtree_quotient.relevant_state_valuations[state] for state in subtree_quotient.state_is_relevant_bv]
                    subtree_synthesizer.best_tree.simplify(relevant_state_valuations)
                    tree_helper_tree_copy = tree_helper_tree.copy()
                    tree_helper_tree_copy.append_tree_as_subtree(subtree_synthesizer.best_tree, node["id"], subtree_quotient)
                    tree_helper_tree_copy.root.assign_identifiers(keep_old=True)
                    logger.info(f'new tree has depth {tree_helper_tree_copy.get_depth()} and {len(tree_helper_tree_copy.collect_nonterminals())} nodes')

                    self.quotient.tree_helper_tree = tree_helper_tree_copy

                    submdp_for_tree = self.quotient.get_submdp_from_unfixed_states()
                    # double check
                    # res = submdp.check_specification(self.quotient.specification)
                    # print(res)
                    # TODO debugging the value getting below eps_optimum_threshold
                    # if opt_result_value < eps_optimum_threshold:
                    #     assert res.optimality_result.value <= eps_optimum_threshold, f"optimum value {res.optimality_result.value} is not below threshold {eps_optimum_threshold}"
                    # else:
                    #     assert res.optimality_result.value >= eps_optimum_threshold, f"optimum value {res.optimality_result.value} is not above threshold {eps_optimum_threshold}"
                    reachable_states = stormpy.BitVector(submdp_for_tree.model.nr_states, False)
                    for state in range(submdp_for_tree.model.nr_states):
                        reachable_states.set(submdp_for_tree.quotient_state_map[state], True)

                    # print(tree_helper_tree.to_graphviz([node["id"]]))

                    # create scheduler 
                    # print(tree_helper_tree.to_scheduler_json())

                    # calling dtcontrol
                    if use_dtcontrol:
                        self.dtcontrol_calls += 1
                        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
                        temp_file_name = "subtree_test" + timestamp
                        os.makedirs(temp_file_name, exist_ok=True)
                        open(f"{temp_file_name}/scheduler.storm.json", "w").write(tree_helper_tree_copy.to_scheduler_json(reachable_states))

                        command = ["dtcontrol", "--input", "scheduler.storm.json", "-r", "--use-preset", "default"]
                        subprocess.run(command, cwd=f"{temp_file_name}")

                        logger.info(f"parsing new dtcontrol tree")
                        new_tree_helper = paynt.utils.tree_helper.parse_tree_helper(f"{temp_file_name}/decision_trees/default/scheduler/default.json")
                        new_tree_helper_tree = self.quotient.build_tree_helper_tree(new_tree_helper)
                        logger.info(f'new dtcontrol tree has depth {new_tree_helper_tree.get_depth()} and {len(new_tree_helper_tree.collect_nonterminals())} nodes')

                        shutil.rmtree(f"{temp_file_name}")

                    # TODO if none of the trees produced are smaller here I would like to revert to the original tree
                    # if False: # TODO remove this
                    if use_dtcontrol and len(new_tree_helper_tree.collect_nonterminals()) <= len(tree_helper_tree_copy.collect_nonterminals()) and len(new_tree_helper_tree.collect_nonterminals()) < len(tree_helper_tree.collect_nonterminals()):
                        logger.info(f"New DtControl tree is smaller")
                        self.dtcontrol_successes += 1
                        self.quotient.tree_helper = new_tree_helper
                        self.quotient.tree_helper_tree = new_tree_helper_tree
                        tree_helper_tree = new_tree_helper_tree
                        # print(tree_helper_tree.to_graphviz())
                        node_queue = self.create_tree_node_queue_heuristic(tree_helper_tree)
                    elif len(tree_helper_tree_copy.collect_nonterminals()) < len(tree_helper_tree.collect_nonterminals()):
                        logger.info(f"Current PAYNT tree is smaller")
                        self.paynt_successes_smaller += 1
                        tree_helper_tree = tree_helper_tree_copy
                        self.quotient.tree_helper_tree = tree_helper_tree
                        for node in node_queue:
                            nodes = self.quotient.tree_helper_tree.collect_nodes(lambda x : x.old_identifier == node["id"])
                            assert len(nodes) == 1, f'only one node should have the old_identifier equal to {node["id"]}'
                            new_node = nodes[0]
                            node["id"] = new_node.identifier
                    else:
                        logger.info(f"None of the new trees are smaller, continuing with current tree")
                        self.both_larger += 1
                        self.quotient.tree_helper_tree = tree_helper_tree
                    
                    # exit()
                else:
                    logger.info(f"no admissible subtree found from node {node['id']}")

            current_depth -= 1

        self.quotient.tree_helper_tree = tree_helper_tree
        
        # print(self.quotient.tree_helper_tree.to_graphviz())
        
        self.synthesis_timer.stop()

        # double check
        dtmc = self.quotient.get_submdp_from_unfixed_states()
        # TODO why would it not be a DTMC here???
        if dtmc.model.nr_states != dtmc.model.nr_choices:
            logger.info(f"tree did not induce dtmc?")
        # assert dtmc.model.nr_states == dtmc.model.nr_choices, "tree did not induce dtmc"
        result = dtmc.check_specification(self.quotient.specification)
        result_negate = dtmc.check_specification(self.quotient.specification.negate())

        print(result)
        print(result_negate)
        print()

        # TODO find out why this would not hold????
        if opt_result_value < eps_optimum_threshold:
            assert result.optimality_result.value <= eps_optimum_threshold, f"optimum value {result.optimality_result.value} is not below threshold {eps_optimum_threshold}"
        else:
            assert result.optimality_result.value >= eps_optimum_threshold, f"optimum value {result.optimality_result.value} is not above threshold {eps_optimum_threshold}"

        self.best_tree = self.quotient.tree_helper_tree
        self.best_tree_value = result.optimality_result.value

        logger.info(f'final tree has value {result.optimality_result.value} with depth {self.quotient.tree_helper_tree.get_depth()} and {len(self.quotient.tree_helper_tree.collect_nonterminals())} nodes')

        print(result.optimality_result.value, round(self.synthesis_timer.read(), 2), self.quotient.tree_helper_tree.get_depth(), len(self.quotient.tree_helper_tree.collect_nonterminals()))

        # exit()

    def synthesize_tree(self, depth:int, family=None):
        self.counters_reset()
        self.quotient.reset_tree(depth)
        self.best_assignment = self.best_assignment_value = None
        self.synthesize(keep_optimum=True)
        if self.best_assignment is not None:
            self.quotient.decision_tree.root.associate_assignment(self.best_assignment)
            self.best_tree = self.quotient.decision_tree
            self.best_tree_value = self.best_assignment_value
        self.best_assignment = self.best_assignment_value = None
        self.counters_print()

    def synthesize_tree_sequence(self, opt_result_value, overall_timeout=None, max_depth=None, break_if_found=False):
        self.best_tree = self.best_tree_value = None

        if max_depth is None:
            max_depth = SynthesizerDecisionTree.tree_depth+1
        if overall_timeout is None:
            global_timeout = paynt.utils.timer.GlobalTimer.global_timer.time_limit_seconds
            if global_timeout is None: global_timeout = 900
            overall_timeout = global_timeout
            tree_sequence_timer = None
        else:
            tree_sequence_timer = paynt.utils.timer.Timer(overall_timeout)
            tree_sequence_timer.start()
        depth_timeout = overall_timeout / 2 / (max_depth-1) if max_depth > 1 else overall_timeout / 2
        for depth in range(max_depth):
            print()
            self.quotient.reset_tree(depth)
            best_assignment_old = self.best_assignment
            family = self.quotient.family
            self.explored = 0
            self.counters_reset()
            self.stat = paynt.synthesizer.statistic.Statistic(self)
            self.stat.start(family)
            timeout = depth_timeout if depth < max_depth-1 else overall_timeout / 2 # second half of the time for the last depth
            self.synthesis_timer = paynt.utils.timer.Timer(timeout)
            self.synthesis_timer.start()
            families = [family]

            if self.best_tree is not None:
                subfamily = family.copy()
                self.quotient.decision_tree.root.apply_hint(subfamily,self.best_tree.root)
                families = [subfamily,family]

            for family in families:
                self.synthesize_one(family)
            self.stat.finished_synthesis()
            self.stat.print()
            self.synthesis_timer = None
            self.counters_print()

            new_assignment_synthesized = self.best_assignment != best_assignment_old
            if new_assignment_synthesized:
                logger.info("printing synthesized assignment below:")
                logger.info(self.best_assignment)

                if self.best_assignment is not None and self.best_assignment.size == 1:
                    dtmc = self.quotient.build_assignment(self.best_assignment)
                    result = dtmc.check_specification(self.quotient.specification)
                    logger.info(f"double-checking specification satisfiability: {result}")

                self.best_tree = self.quotient.decision_tree
                self.best_tree.root.associate_assignment(self.best_assignment)
                self.best_tree_value = self.best_assignment_value

                if break_if_found or abs( (self.best_assignment_value-opt_result_value)/opt_result_value ) < 1e-3:
                    break

            if self.resource_limit_reached() or tree_sequence_timer is not None and tree_sequence_timer.time_limit_reached():
                break

    def map_scheduler(self, scheduler_choices):
        self.counters_reset()
        for depth in range(SynthesizerDecisionTree.tree_depth+1):
            self.quotient.reset_tree(depth,enable_harmonization=False)
            family = self.quotient.family.copy()
            family.analysis_result = self.quotient.build_unsat_result()
            self.quotient.build(family)
            consistent,hole_selection = self.quotient.are_choices_consistent(scheduler_choices, family)
            if consistent:
                self.verify_hole_selection(family,hole_selection)
                if self.best_assignment is not None:
                    self.best_tree = self.quotient.decision_tree
                    self.best_tree.root.associate_assignment(self.best_assignment)
                    self.best_tree_value = self.best_assignment_value
                    break

            if self.resource_limit_reached():
                break

    def run(self, optimum_threshold=None):
        scheduler_choices = None
        if SynthesizerDecisionTree.scheduler_path is None:
            paynt_mdp = paynt.models.models.Mdp(self.quotient.quotient_mdp)
            mc_result = paynt_mdp.model_check_property(self.quotient.get_property())
        else:
            opt_result_value = None
            with open(SynthesizerDecisionTree.scheduler_path, 'r') as f:
                scheduler_json = json.load(f)
            scheduler_choices,scheduler_json_relevant = self.quotient.scheduler_json_to_choices(scheduler_json, discard_unreachable_states=True)

            # export transformed scheduler
            # import os
            # directory = os.path.dirname(SynthesizerDecisionTree.scheduler_path)
            # transformed_name = f"scheduler-reachable.storm.json"
            # scheduler_relevant_path = os.path.join(directory, transformed_name)
            # with open(scheduler_relevant_path, 'w') as f:
            #     json.dump(scheduler_json_relevant, f, indent=4)
            # logger.debug(f"stored transformed scheduler to {scheduler_relevant_path}")
            # exit()

            submdp = self.quotient.build_from_choice_mask(scheduler_choices)
            mc_result = submdp.model_check_property(self.quotient.get_property())
        opt_result_value = mc_result.value
        logger.info(f"the optimal scheduler has value: {opt_result_value}")

        if self.quotient.DONT_CARE_ACTION_LABEL in self.quotient.action_labels:
            random_choices = self.quotient.get_random_choices()
            submdp_random = self.quotient.build_from_choice_mask(random_choices)
            mc_result_random = submdp_random.model_check_property(self.quotient.get_property())
            random_result_value = mc_result_random.value
            logger.info(f"the random scheduler has value: {random_result_value}")
            # self.set_optimality_threshold(random_result_value)

        self.best_assignment = self.best_assignment_value = None
        self.best_tree = self.best_tree_value = None
        if scheduler_choices is not None:
            self.map_scheduler(scheduler_choices)
        else:
            if self.quotient.specification.has_optimality:
                epsilon = 0.05
                mc_result_positive = opt_result_value > 0
                if self.quotient.specification.optimality.maximizing == mc_result_positive:
                    epsilon *= -1
                optimum_threshold = opt_result_value * (1 + epsilon)
            # self.set_optimality_threshold(optimum_threshold)

            if self.quotient.tree_helper is not None:
                self.synthesize_subtrees(opt_result_value, random_result_value)
            elif not SynthesizerDecisionTree.tree_enumeration:
                self.synthesize_tree(SynthesizerDecisionTree.tree_depth)
            else:
                self.synthesize_tree_sequence(opt_result_value)

        logger.info(f"the optimal scheduler has value: {opt_result_value}")
        if self.quotient.DONT_CARE_ACTION_LABEL in self.quotient.action_labels:
            logger.info(f"the random scheduler has value: {random_result_value}")
        if self.best_tree is None:
            logger.info("no admissible tree found")
        else:
            relevant_state_valuations = [self.quotient.relevant_state_valuations[state] for state in self.quotient.state_is_relevant_bv]
            self.best_tree.simplify(relevant_state_valuations)
            depth = self.best_tree.get_depth()
            num_nodes = len(self.best_tree.collect_nonterminals())
            logger.info(f"synthesized tree of depth {depth} with {num_nodes} decision nodes")
            if self.quotient.specification.has_optimality:
                logger.info(f"the synthesized tree has value {self.best_tree_value}")
            if self.quotient.DONT_CARE_ACTION_LABEL in self.quotient.action_labels:
                logger.info(f"the synthesized tree has relative value: {(self.best_tree_value-random_result_value)/(opt_result_value-random_result_value) if opt_result_value-random_result_value != 0 else None}")
            logger.info(f"printing the synthesized tree below:")

            # integration logs
            if self.quotient.tree_helper is not None:
                logger.info(f"dtcontrol calls: {self.dtcontrol_calls}")
                logger.info(f"dtcontrol successes: {self.dtcontrol_successes}")
                logger.info(f"paynt calls: {self.paynt_calls}")
                logger.info(f"paynt successes smaller: {self.paynt_successes_smaller}")
                logger.info(f"paynt tree found: {self.paynt_tree_found}")
                logger.info(f"both larger: {self.both_larger}")

            # print(self.best_tree.to_string())
            # print(self.best_tree.to_graphviz())
            # logger.info(f"printing the PRISM module below:")
            # print(self.best_tree.to_prism())

            if self.export_synthesis_filename_base is not None:
                self.export_decision_tree(self.best_tree, self.export_synthesis_filename_base)
        time_total = round(paynt.utils.timer.GlobalTimer.read(),2)
        logger.info(f"synthesis finished after {time_total} seconds")

        print()
        if False: # TODO remove this
            for name,time in self.quotient.coloring.getProfilingInfo():
                time_percent = round(time/time_total*100,1)
                print(f"{name} = {time} s ({time_percent} %)")

        return self.best_tree
