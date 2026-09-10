from __future__ import annotations

from typing import Any

import paynt.synthesizer.synthesizer_ar
import paynt.synthesizer.search_node
import paynt.parameter_space.parameter_space
from paynt.pomdp.saynt.control import StormPOMDPControl

from time import sleep

import logging

logger = logging.getLogger(__name__)


# Abstraction Refinement + Storm splitting
class SynthesizerARStorm(paynt.synthesizer.synthesizer_ar.SynthesizerAR):

    # parameter space exploration order: True = DFS, False = BFS
    exploration_order_dfs = True

    # buffer containing parameter subspaces to be checked after the main restricted parameter space -- plain
    # ParameterSpace values, set externally by SayntSynthesizer, wrapped into search nodes only on consumption
    parameter_subspaces_buffer: list[paynt.parameter_space.parameter_space.ParameterSpace] | None = None

    main_parameter_space: paynt.parameter_space.parameter_space.ParameterSpace | None = None

    # if True, Storm over-approximation will be run to help with parameter-space pruning
    storm_pruning = False

    storm_control: StormPOMDPControl | None = None
    s_queue: Any = None

    saynt_timer: Any = None

    @property
    def method_name(self) -> str:
        return "AR"

    # performs splitting of the parameter space according to Storm result
    # main parameter spaces contain only those actions that were considered by best found Storm FSC
    def storm_split(
        self, nodes: list[paynt.synthesizer.search_node.SearchNode]
    ) -> tuple[list[paynt.synthesizer.search_node.SearchNode], list[paynt.parameter_space.parameter_space.ParameterSpace]]:
        """
        :param nodes the current active worklist (search nodes)
        :returns (main_nodes, parameter_subspaces) -- main_nodes are search nodes (the new active worklist,
            used immediately by the caller), parameter_subspaces are plain ParameterSpace values (stored into
            self.parameter_subspaces_buffer, matching the plain-value contract SayntSynthesizer itself uses
            when writing that buffer -- wrapped into nodes only once actually consumed, in synthesize_one)
        """
        assert self.storm_control is not None
        parameter_subspaces = []
        main_nodes = []

        # split each parameter space in the current buffer into a main parameter space and corresponding subspaces
        for node in nodes:
            if self.storm_control.use_cutoffs:
                result_dict = self.storm_control.result_dict
            else:
                result_dict = self.storm_control.result_dict_no_cutoffs
            main_p = self.storm_control.get_main_restricted_parameter_space(node.parameter_space, result_dict)
            if main_p is None:
                parameter_subspaces.append(node.parameter_space)
                continue

            main_nodes.append(self.search_node_type(main_p))
            parameter_subspace_restrictions = self.storm_control.get_parameter_subspaces_restrictions(node.parameter_space, result_dict)
            parameter_subspaces_p = self.storm_control.get_parameter_subspaces(parameter_subspace_restrictions, node.parameter_space)
            parameter_subspaces.extend(parameter_subspaces_p)

        logger.info(f"State after Storm splitting: Main parameter spaces - {len(main_nodes)}, Parameter subspaces - {len(parameter_subspaces)}")

        # if there are no main parameter spaces we don't have to prioritize search
        if len(main_nodes) == 0:
            main_nodes = [self.search_node_type(parameter_subspace) for parameter_subspace in parameter_subspaces]
            parameter_subspaces = []

        return main_nodes, parameter_subspaces

    def verify_parameter_space(self, node: paynt.synthesizer.search_node.SearchNode) -> None:
        assert self.storm_control is not None
        assert self.stat is not None
        node.mdp, node.selected_choices = self.colored_mdp.build(node.parameter_space)
        self.check_specification(node)

        assert node.analysis_result is not None
        assert self.task.specification.optimality is not None
        if node.analysis_result.improving_value is not None:
            fsc_size = self.colored_mdp.policy_size(node.analysis_result.improving_assignment)  # type: ignore[attr-defined]
            if self.saynt_timer is not None:
                elapsed = round(self.saynt_timer.read(), 1)
                print(
                    f"-----------PAYNT----------- \n" f"Value = {node.analysis_result.improving_value} | Time elapsed = {elapsed}s | FSC size = {fsc_size}\n",
                    flush=True,
                )
            else:
                self.stat.new_fsc_found(node.analysis_result.improving_value, node.analysis_result.improving_assignment, fsc_size)
            self.task.specification.optimality.update_optimum(node.analysis_result.improving_value)

        # storm pruning runs Storm POMDP over-approximation analysis and on the sub-POMDP given by a parameter space
        # this serves as a better abstraction for pruning, however is much more computationally intensive.
        # NOTE: storm_pruning has no CLI wiring and no other writer anywhere in the codebase (always False),
        # so this whole branch is currently dead code -- found via type-hint work, along with a stray
        # reference to an undefined name "res" below (fixed to what was clearly intended), but left disabled
        # since nothing currently exercises it to verify the fix against.
        if self.task.specification.optimality.optimum and node.analysis_result.can_improve and self.storm_pruning:

            parameter_space_pomdp = self.colored_mdp.get_parameter_space_pomdp(node.mdp)

            storm_res = StormPOMDPControl.storm_pomdp_analysis(parameter_space_pomdp, self.task.specification.stormpy_formulae())

            # compare computed bounds to the current optimum to see if the parameter space can be pruned
            if self.task.specification.optimality.minimizing:
                if self.task.specification.optimality.optimum <= storm_res.lower_bound:
                    node.analysis_result.can_improve = False
                    logger.info(
                        f"Used Storm result to prune a parameter space with Storm value: {storm_res.lower_bound} compared to "
                        f"current optimum {self.task.specification.optimality.optimum}. "
                        f"Underlying MDP value: {node.analysis_result.optimality_result.primary.value}"
                    )
            else:
                if self.task.specification.optimality.optimum >= storm_res.upper_bound:
                    node.analysis_result.can_improve = False
                    logger.info(
                        f"Used Storm result to prune a parameter space with Storm value: {storm_res.upper_bound} compared to "
                        f"current optimum {self.task.specification.optimality.optimum}. "
                        f"Underlying MDP value: {node.analysis_result.optimality_result.primary.value}"
                    )

    def synthesize_one(self, node: paynt.synthesizer.search_node.SearchNode) -> paynt.parameter_space.parameter_space.ParameterSpace | None:
        assert self.storm_control is not None
        assert self.stat is not None

        self.best_assignment = None

        # main_parameter_space is set externally (by SayntSynthesizer) as a plain ParameterSpace value --
        # wrap it into a search node at the point of consumption, here
        if self.main_parameter_space is not None:
            node = self.search_node_type(self.main_parameter_space)

        nodes = [node]

        while nodes:

            # check whether PAYNT should be paused
            if self.s_queue is not None:
                # if the queue is non empty, pause for PAYNT was requested
                if not self.s_queue.empty():
                    if self.best_assignment is not None:
                        assert self.task.specification.optimality is not None
                        self.storm_control.latest_paynt_result = self.best_assignment
                        self.storm_control.paynt_export = self.colored_mdp.extract_policy(self.best_assignment, self.task.specification)  # type: ignore[attr-defined]
                        self.storm_control.paynt_bounds = self.task.specification.optimality.optimum
                        self.storm_control.paynt_fsc_size = self.colored_mdp.policy_size(self.storm_control.latest_paynt_result)  # type: ignore[attr-defined]
                        self.storm_control.latest_paynt_result_fsc = self.colored_mdp.assignment_to_fsc(self.storm_control.latest_paynt_result)  # type: ignore[attr-defined]
                        self.storm_control.update_data()
                    logger.info("Pausing synthesis")
                    self.s_queue.get()
                    self.stat.synthesis_timer.stop()
                    # check for the signal that PAYNT can be resumed or terminated
                    while self.s_queue.empty():
                        sleep(1)
                    status = self.s_queue.get()
                    if status == "resume":
                        logger.info("Resuming synthesis")
                        if self.storm_control.is_storm_better:
                            # if the result found by Storm is better and needs more memory end the current synthesis and add memory
                            if self.storm_control.is_memory_needed():
                                logger.info("Additional memory needed")
                                return self.best_assignment
                            logger.info("Applying parameter-space split according to Storm results")
                            nodes, self.parameter_subspaces_buffer = self.storm_split(nodes)
                        # if Storm's result is not better continue with the synthesis normally
                        else:
                            logger.info("PAYNT's value is better. Prioritizing synthesis results")
                        self.stat.synthesis_timer.start()

                    elif status == "terminate":
                        logger.info("Terminating controller synthesis")
                        return self.best_assignment

            if SynthesizerARStorm.exploration_order_dfs:
                node = nodes.pop(-1)
            else:
                node = nodes.pop(0)

            # simulate sequential
            node.parent_info = None

            self.verify_parameter_space(node)
            assert node.analysis_result is not None
            if node.analysis_result.improving_assignment is not None:
                self.best_assignment = node.analysis_result.improving_assignment
            # parameter space can be pruned
            if not node.analysis_result.can_improve:
                self.explore(node.parameter_space)
                # if there are no more parameter spaces in the main buffer continue the exploration in the subspaces
                if not nodes and self.parameter_subspaces_buffer:
                    logger.info("Main parameter space synthesis done")
                    logger.info(f"Parameter subspaces buffer contains: {len(self.parameter_subspaces_buffer)} parameter spaces")
                    # parameter_subspaces_buffer holds plain ParameterSpace values (see storm_split) -- wrap
                    # each into a fresh search node before feeding it back into the active worklist
                    nodes = [self.search_node_type(parameter_subspace) for parameter_subspace in self.parameter_subspaces_buffer]
                    self.parameter_subspaces_buffer = []
                continue

            # undecided
            child_nodes = self.split_undecided_space(node)
            nodes = nodes + child_nodes

        return self.best_assignment
