import paynt.synthesizer.synthesizer_ar
import paynt.quotient.mdp
import paynt.utils.timer

from paynt.utils.tree_helper import parse_tree_helper

import paynt.utils.tree_helper
import stormpy
import payntbind

import json

import os
import shutil
import subprocess

import logging
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
        if family.mdp is None:
            self.num_families_skipped += 1
            return

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
        if SynthesizerDecisionTree.scheduler_path is not None:
            return
        self.harmonize_inconsistent_scheduler(family)


    def counters_reset(self):
        self.num_families_considered = 0
        self.num_families_skipped = 0
        self.num_families_model_checked = 0
        self.num_schedulers_preserved = 0
        self.num_harmonizations = 0
        self.num_harmonization_succeeded = 0

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
        with open(tree_filename, 'w') as file:
            file.write(tree.source)
        logger.info(f"exported decision tree to {tree_filename}")

        tree_visualization_filename = export_filename_base + ".png"
        tree.render(export_filename_base, format="png", cleanup=True) # using export_filename_base since graphviz appends .png by default
        logger.info(f"exported decision tree visualization to {tree_visualization_filename}")
    

    def create_tree_node_queue_heuristic(self, helper_tree, desired_depth=6):
        nodes = helper_tree.collect_nodes(lambda node : node.get_depth() == desired_depth)
        if nodes is None or len(nodes) == 0:
            return None
        helper_nodes = [self.quotient.tree_helper[node.identifier] for node in nodes]
        helper_node_stats = []
        for helper_node in helper_nodes:
            if helper_node["id"] == 0:
                continue
            helper_tree_node = helper_tree.collect_nodes(lambda node : node.identifier == helper_node["id"])[0]
            stats = {"id": helper_node["id"], "states": self.quotient.get_state_space_for_tree_helper_node(helper_node["id"]), "nodes": helper_tree_node.get_number_of_descendants(), "predicates": {pred : eval for pred, eval in helper_node["evaluations"].items() if eval <= list(helper_node["evaluations"].values())[0]*1.05}}
            helper_node_stats.append(stats)

        if len(helper_node_stats) == 0:
            return []

        helper_node_stats = sorted(helper_node_stats, key=lambda x : len(x["states"])/x["nodes"])
        helper_node_stats = sorted(helper_node_stats, key=lambda x : len(x["predicates"]), reverse=True)

        return helper_node_stats
    

    def synthesize_subtrees(self, eps_optimum_threshold):

        # complete init
        self.counters_reset()

        # initialize from external tree
        tree_helper_tree = self.quotient.build_tree_helper_tree()
        logger.info(f'initial external tree has depth {tree_helper_tree.get_depth()} and {len(tree_helper_tree.collect_nodes())} nodes')
        node_queue = self.create_tree_node_queue_heuristic(tree_helper_tree)

        while len(node_queue) > 0:
        
            node = node_queue.pop(0)
            # print(tree_helper_tree.to_graphviz([node["id"]]))

            # subtree synthesis
            submdp = self.quotient.get_submdp_from_unfixed_states(node["states"])
            logger.info(f"subtree quotient has {submdp.model.nr_states} states and {submdp.model.nr_choices} choices")
            subtree_quotient = paynt.quotient.mdp.MdpQuotient(submdp.model, self.quotient.specification)
            subtree_synthesizer = SynthesizerDecisionTree(subtree_quotient)
            # depth = 2
            # subtree_synthesizer.synthesize_tree(depth)
            subtree_synthesizer.synthesize_tree_sequence(eps_optimum_threshold, overall_timeout=60, max_depth=6)

            # create new tree
            if subtree_synthesizer.best_tree is not None:
                logger.info(f"admissible subtree found from node {node['id']}")
                relevant_state_valuations = [self.quotient.relevant_state_valuations[state] for state in self.quotient.state_is_relevant_bv]
                subtree_synthesizer.best_tree.simplify(relevant_state_valuations)
                tree_helper_tree.append_tree_as_subtree(subtree_synthesizer.best_tree, node["id"])
                tree_helper_tree.root.assign_identifiers()
                logger.info(f'new tree has depth {tree_helper_tree.get_depth()} and {len(tree_helper_tree.collect_nodes())} nodes')
                # print(tree_helper_tree.to_graphviz([node["id"]]))

                # create scheduler 
                # print(tree_helper_tree.to_scheduler_json())

                os.makedirs("subtree_test", exist_ok=True)
                open("subtree_test/scheduler.storm.json", "w").write(tree_helper_tree.to_scheduler_json())

                command = ["dtcontrol", "--input", "scheduler.storm.json", "-r", "--use-preset", "default"]
                subprocess.run(command, cwd="subtree_test")

                new_tree_helper = paynt.utils.tree_helper.parse_tree_helper("subtree_test/decision_trees/default/scheduler/default.json")
                new_tree_helper_tree = self.quotient.build_tree_helper_tree(new_tree_helper)
                logger.info(f'new dtcontrol tree has depth {new_tree_helper_tree.get_depth()} and {len(new_tree_helper_tree.collect_nodes())} nodes')

                # TODO for now I will always switch to the tree produced by dtControl as it contains all the information I need
                # however, for the future I should compare the trees and choose the one that is smaller
                if len(new_tree_helper_tree.collect_nodes()) < len(tree_helper_tree.collect_nodes()):
                    logger.info(f"New DtControl tree is smaller")
                else:
                    logger.info(f"Current PAYNT tree is smaller")
                self.quotient.tree_helper = new_tree_helper
                tree_helper_tree = new_tree_helper_tree
                # print(tree_helper_tree.to_graphviz())
                node_queue = self.create_tree_node_queue_heuristic(tree_helper_tree)

                # shutil.rmtree("subtree_test")
                exit()
            else:
                logger.info(f"no admissible subtree found from node {node['id']}")
            
            exit()

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

    def synthesize_tree_sequence(self, opt_result_value, overall_timeout=None, max_depth=None):
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
        depth_timeout = overall_timeout / 2 / (max_depth-1)
        for depth in range(max_depth):
            print()
            self.quotient.reset_tree(depth)
            best_assignment_old = self.best_assignment
            family = self.quotient.family
            self.explored = 0
            self.counters_reset()
            self.stat = paynt.synthesizer.statistic.Statistic(self)
            self.stat.start(family)
            timeout = depth_timeout if depth < max_depth-1 else None
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

                if abs( (self.best_assignment_value-opt_result_value)/opt_result_value ) < 1e-3:
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

        # self.counters_print()

    def run(self, optimum_threshold=None):

        scheduler_choices = None
        if SynthesizerDecisionTree.scheduler_path is None:
            paynt_mdp = paynt.models.models.Mdp(self.quotient.quotient_mdp)
            mc_result = paynt_mdp.model_check_property(self.quotient.get_property())
        else:
            opt_result_value = None
            with open(SynthesizerDecisionTree.scheduler_path, 'r') as f:
                scheduler_json = json.load(f)
            scheduler_choices = self.quotient.scheduler_json_to_choices(scheduler_json)
            submdp = self.quotient.build_from_choice_mask(scheduler_choices)
            mc_result = submdp.model_check_property(self.quotient.get_property())
        opt_result_value = mc_result.value
        logger.info(f"the optimal scheduler has value: {opt_result_value}")

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
            self.set_optimality_threshold(optimum_threshold)

            if self.quotient.tree_helper is not None:
                self.synthesize_subtrees(optimum_threshold)
            elif not SynthesizerDecisionTree.tree_enumeration:
                self.synthesize_tree(SynthesizerDecisionTree.tree_depth)
            else:
                self.synthesize_tree_sequence(opt_result_value)

        logger.info(f"the optimal scheduler has value: {opt_result_value}")
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
            logger.info(f"printing the synthesized tree below:")
            print(self.best_tree.to_string())
            # print(self.best_tree.to_graphviz())
            # logger.info(f"printing the PRISM module below:")
            # print(self.best_tree.to_prism())

            if self.export_synthesis_filename_base is not None:
                self.export_decision_tree(self.best_tree, self.export_synthesis_filename_base)
        time_total = round(paynt.utils.timer.GlobalTimer.read(),2)
        logger.info(f"synthesis finished after {time_total} seconds")

        # print()
        # for name,time in self.quotient.coloring.getProfilingInfo():
        #     time_percent = round(time/time_total*100,1)
        #     print(f"{name} = {time} s ({time_percent} %)")

        return self.best_tree
