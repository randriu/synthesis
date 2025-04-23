import copy
import logging
import os
import subprocess

import stormpy

import payntbind

import paynt.synthesizer.statistic
import paynt.utils.timer
from paynt.parser.prism_parser import PrismParser
from paynt.quotient.mdp_family import MdpFamilyQuotient

logger = logging.getLogger(__name__)


class FamilyEvaluation:
    '''Result associated with a family after its evaluation. '''

    def __init__(self, family, value, sat, policy,mdp_fixed_choices = None):
        self.family = family
        self.value = value
        self.sat = sat
        self.policy = policy
        self.mdp_fixed_choices = mdp_fixed_choices


class Synthesizer:
    # base filename (i.e. without extension) to export synthesis result
    export_synthesis_filename_base = None
    # ldokoupi flag for 2024-5 DIP experiments
    ldokoupi_flag = False

    @staticmethod
    def choose_synthesizer(quotient, method, fsc_synthesis=False, storm_control=None):

        # hiding imports here to avoid mutual top-level imports
        import paynt.quotient.mdp
        import paynt.quotient.mdp_family
        import paynt.quotient.posmg
        import paynt.synthesizer.synthesizer_onebyone
        import paynt.synthesizer.synthesizer_ar
        import paynt.synthesizer.synthesizer_cegis
        import paynt.synthesizer.synthesizer_hybrid
        import paynt.synthesizer.synthesizer_multicore_ar
        import paynt.synthesizer.synthesizer_pomdp
        import paynt.synthesizer.synthesizer_decpomdp
        import paynt.synthesizer.synthesizer_posmg
        import paynt.synthesizer.policy_tree
        import paynt.synthesizer.decision_tree

        if isinstance(quotient, paynt.quotient.pomdp_family.PomdpFamilyQuotient):
            logger.info("nothing to do with the POMDP sketch, aborting...")
            exit(0)
        if isinstance(quotient, paynt.quotient.mdp.MdpQuotient):
            return paynt.synthesizer.decision_tree.SynthesizerDecisionTree(quotient)
        # FSC synthesis for POMDPs
        if isinstance(quotient, paynt.quotient.pomdp.PomdpQuotient) and fsc_synthesis:
            return paynt.synthesizer.synthesizer_pomdp.SynthesizerPomdp(quotient, method, storm_control)
        # FSC synthesis for Dec-POMDPs
        if isinstance(quotient, paynt.quotient.decpomdp.DecPomdpQuotient) and fsc_synthesis:
            return paynt.synthesizer.synthesizer_decpomdp.SynthesizerDecPomdp(quotient)
        # Policy Tree synthesis for family of MDPs
        if isinstance(quotient, paynt.quotient.mdp_family.MdpFamilyQuotient):
            if method == "onebyone":
                return paynt.synthesizer.synthesizer_onebyone.SynthesizerOneByOne(quotient)
            else:
                return paynt.synthesizer.policy_tree.SynthesizerPolicyTree(quotient)
        # FSC synthesis for POSMGs
        if isinstance(quotient, paynt.quotient.posmg.PosmgQuotient) and fsc_synthesis:
            return paynt.synthesizer.synthesizer_posmg.SynthesizerPosmg(quotient)

        # synthesis engines
        if method == "onebyone":
            return paynt.synthesizer.synthesizer_onebyone.SynthesizerOneByOne(quotient)
        if method == "ar":
            return paynt.synthesizer.synthesizer_ar.SynthesizerAR(quotient)
        if method == "cegis":
            return paynt.synthesizer.synthesizer_cegis.SynthesizerCEGIS(quotient)
        if method == "hybrid":
            return paynt.synthesizer.synthesizer_hybrid.SynthesizerHybrid(quotient)
        if method == "ar_multicore":
            return paynt.synthesizer.synthesizer_multicore_ar.SynthesizerMultiCoreAR(quotient)
        raise ValueError("invalid method name")

    def __init__(self, quotient):
        self.quotient = quotient
        self.stat = None
        self.synthesis_timer = None
        self.explored = None
        self.best_assignment = None
        self.best_assignment_value = None

    @property
    def method_name(self):
        ''' to be overridden '''
        pass

    def time_limit_reached(self):
        if (self.synthesis_timer is not None and self.synthesis_timer.time_limit_reached()) or \
                paynt.utils.timer.GlobalTimer.time_limit_reached():
            logger.info("time limit reached, aborting...")
            return True
        return False

    def memory_limit_reached(self):
        if paynt.utils.timer.GlobalMemoryLimit.limit_reached():
            logger.info("memory limit reached, aborting...")
            return True
        return False

    def resource_limit_reached(self):
        return self.time_limit_reached() or self.memory_limit_reached()

    def set_optimality_threshold(self, optimum_threshold):
        if self.quotient.specification.has_optimality and optimum_threshold is not None:
            self.quotient.specification.optimality.update_optimum(optimum_threshold)
            logger.debug(f"optimality threshold set to {optimum_threshold}")

    def explore(self, family):
        self.explored += family.size

    def evaluate_all(self, family, prop, keep_value_only=False):
        ''' to be overridden '''
        pass

    def export_evaluation_result(self, evaluations, export_filename_base):
        ''' to be overridden '''
        pass

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
        self.dtcontrol_recomputed_calls = 0
        self.dtcontrol_recomputed_successes = 0
        self.paynt_calls = 0
        self.paynt_successes_smaller = 0
        self.paynt_tree_found = 0
        self.all_larger = 0

    def evaluate(self, family=None, prop=None, keep_value_only=False, print_stats=True):
        '''
        Evaluate each member of the family wrt the given property.
        :param family if None, then the design space of the quotient will be used
        :param prop if None, then the default property of the quotient will be used
            (assuming single-property specification)
        :param keep_value_only if True, only value will be associated with the family
        :param print_stats if True, synthesis statistic will be printed
        :param export_filename_base base filename used to export the evaluation results
        :returns a list of (family,evaluation) pairs
        '''
        if family is None:
            family = self.quotient.family
        if prop is None:
            prop = self.quotient.get_property()

        self.stat = paynt.synthesizer.statistic.Statistic(self)
        self.explored = 0
        logger.info("evaluation initiated, design space: {}".format(family.size))
        self.stat.start(family)
        evaluations = self.evaluate_all(family, prop, keep_value_only)
        self.stat.finished_evaluation(evaluations)
        logger.info("evaluation finished")

        if self.export_synthesis_filename_base is not None:
            self.export_evaluation_result(evaluations, self.export_synthesis_filename_base)

        callDTNest = False
        if callDTNest:
            self.run_dtnest_synthesis(evaluations)

        if print_stats:
            self.stat.print()

        return evaluations

    def synthesize_one(self, family):
        ''' to be overridden '''
        pass

    def synthesize(
            self, family=None, optimum_threshold=None, keep_optimum=False, return_all=False, print_stats=True,
            timeout=None
    ):
        '''
        :param family family of assignment to search in
        :param families alternatively, a list of families can be given
        :param optimum_threshold known bound on the optimum value
        :param keep_optimum if True, the optimality specification will not be reset upon finish
        :param return_all if True and the synthesis returns a family, all assignments will be returned instead of an
            arbitrary one
        :param print_stats if True, synthesis stats will be printed upon completion
        :param timeout synthesis time limit, seconds
        '''
        if family is None:
            family = self.quotient.family
        if family.constraint_indices is None:
            family.constraint_indices = list(range(len(self.quotient.specification.constraints)))

        self.set_optimality_threshold(optimum_threshold)
        self.synthesis_timer = paynt.utils.timer.Timer(timeout)
        self.synthesis_timer.start()
        self.stat = paynt.synthesizer.statistic.Statistic(self)
        self.explored = 0
        self.stat.start(family)
        self.synthesize_one(family)
        if self.best_assignment is not None and self.best_assignment.size > 1 and not return_all:
            self.best_assignment = self.best_assignment.pick_any()
        self.stat.finished_synthesis()
        if self.best_assignment is not None:
            logger.info("printing synthesized assignment below:")
            logger.info(self.best_assignment)

        if self.best_assignment is not None and self.best_assignment.size == 1:
            dtmc = self.quotient.build_assignment(self.best_assignment)
            result = dtmc.check_specification(self.quotient.specification)
            logger.info(f"double-checking specification satisfiability: {result}")

        if print_stats:
            self.stat.print()

        assignment = self.best_assignment
        if not keep_optimum:
            self.best_assignment = None
            self.best_assignment_value = None
            self.quotient.specification.reset()

        return assignment

    def run(self, optimum_threshold=None):
        return self.synthesize(optimum_threshold=optimum_threshold)

    def clean_choice_mask(self, eval_choice):
        """Remove redundant choices from the choice mask, keeping only one per state-action.

        If multiple choices are present for a single state-action pair, only the first one is kept.

        Args:
            eval_choice: The choice mask to clean

        Returns:
            The cleaned choice mask
        """
        for actions in self.quotient.state_action_choices:
            for choices in actions:
                seen_choice = False

                # Count how many choices from eval_choices are present
                count_eval_choices = 0
                for choice in choices:
                    if choice in eval_choice:
                        count_eval_choices += 1

                # If there's only one choice or no choices, no cleaning needed
                if count_eval_choices <= 1:
                    continue

                # Keep only the first choice
                for choice in choices:
                    if choice in eval_choice:
                        if seen_choice:
                            # Disable redundant choice
                            eval_choice.set(choice, False)
                        else:
                            seen_choice = True

        return eval_choice

    def update_quotient_with_choices(self, eval_choice):
        """Update the quotient MDP with fixed choices.

        Args:
            eval_choice: The choice mask to apply

        Returns:
            None, modifies quotient in place
        """
        working_mdp = self.quotient.build_from_choice_mask(eval_choice)
        self.quotient.quotient_mdp = working_mdp.model

        # Update state valuations
        new_state_valuations = []
        for i in working_mdp.quotient_state_map:
            new_state_valuations.append(self.quotient.state_valuations[i])
        self.quotient.relevant_state_valuations = new_state_valuations.copy()

    def assert_policy_choices(self, policy):
        """Extract choices from a policy.

        Args:
            policy: The policy to extract choices from

        Returns:
            tuple: (list of no-label choices, all choices)
        """
        # Get actions with no_label choice
        # no_label_choices = []
        # for i, action in enumerate(policy):
        #     action_index_for_state = policy[i] or 0
        #     if action_index_for_state == 0:
        #         no_label_choices.append(i)

        # Get list of choices for each state
        choices = [
            self.quotient.state_action_choices[i][policy[i] or 0]
            for i in range(len(self.quotient.state_valuations))
        ]
        assert all(choice is not None for choice in choices)

    def filter_storm_json_for_family(self, storm_json, family, family_args_len):
        """Filter the storm JSON data for a specific family.

        Args:
            storm_json: The JSON data to filter
            family: The family to filter for
            family_args_len: The length of family arguments

        Returns:
            The filtered storm JSON
        """
        if family_args_len is None:
            family_args_len = len(family.hole_to_name)

        # Filter data for current family
        for i in range(family_args_len):
            hole_name = family.hole_to_name[i]
            hole_value = family.holes_options[i][0]  # First is candidate
            storm_json = [entry for entry in storm_json if entry['s'].get(hole_name) == hole_value]

        return storm_json

    def run_dtcontrol(self, scheduler_path, model_dir):
        """Run DTControl on the scheduler file.

        Args:
            scheduler_path: Path to the scheduler file
            model_dir: Directory containing the model

        Returns:
            None
        """
        self.dtcontrol_calls += 1

        command = ["/home/lada/repo/diplomka/PAYNT/.venv_fpmk/bin/dtcontrol", "--input",
                   "scheduler.storm.json", "-r", "--use-preset", "default"]
        subprocess.run(command, cwd=f"{model_dir}")

    def prepare_quotient_for_dt_synthesis(self):
        """Prepare the quotient for decision tree synthesis.

        Adds don't-care actions if needed and sets relevance for all states.

        Returns:
            None, modifies quotient in place
        """
        if MdpFamilyQuotient.DONT_CARE_ACTION_LABEL not in self.quotient.action_labels and MdpFamilyQuotient.add_dont_care_action:
            # Identify relevant states again
            state_relevant_bp = stormpy.BitVector(self.quotient.quotient_mdp.nr_states, True)

            logger.debug("adding explicit don't-care action to relevant states...")
            self.quotient.quotient_mdp = payntbind.synthesis.addDontCareAction(self.quotient.quotient_mdp,
                                                                               state_relevant_bp)
            self.quotient.choice_destinations = payntbind.synthesis.computeChoiceDestinations(
                self.quotient.quotient_mdp)
            self.quotient.action_labels, self.quotient.choice_to_action = payntbind.synthesis.extractActionLabels(
                self.quotient.quotient_mdp)
            logger.info(f"MDP has {len(self.quotient.action_labels)} actions")

        self.quotient.state_is_relevant_bv = stormpy.BitVector(self.quotient.quotient_mdp.nr_states, True)
        self.quotient.specification = self.quotient.specification_alt

    def reconstruct_policy_from_storm_json(self, storm_json):
        """Reconstruct a policy from the storm JSON data.
        Args:
            storm_json: The JSON data containing the policy
        Returns:
            The reconstructed policy
        """
        reconstructed_policy = [None] * len(self.quotient.state_valuations)

        for entry in storm_json:
            state_valuation = entry['s']
            action_info = entry['c'][0]  # Assuming single action per state

            # If DTnest fails to improve, old JSON structure may still be present
            try:
                action_label = action_info['labels'][0]  # Assuming single label per action
            except KeyError:
                action_label = action_info['origin']['action-label']

            # Find the corresponding state index
            for state_index, valuation in enumerate(self.quotient.state_valuations):
                if all(state_valuation[var.name] == valuation[i] for i, var in enumerate(self.quotient.variables)):
                    action_index = self.quotient.action_labels.index(action_label) - 1  # Due to the don't care action
                    if self.quotient_bp.action_labels[action_index].startswith('_'):
                        continue  # Skip irrelevant/random actions
                    reconstructed_policy[state_index] = action_index
                    break

        return reconstructed_policy

    def create_storm_json_from_policy(self, policy, family):
        """Create storm JSON data from a policy.
        Args:
            policy: The policy to convert
            family: The family for the policy
        Returns:
            The storm JSON data
        """
        # Filter irrelevant data from storm_json by calling policy_to_state_valuation_actions
        storm_json = self.quotient_bp.policy_to_state_valuation_actions((policy, None), family)

        # Format the data properly
        storm_json_new = []
        for s_point, c_point in storm_json:
            # Filter out irrelevant data
            storm_json_datapoint = {'s': s_point, "c": [{"origin": {"action-label": c_point}}]}
            storm_json_new.append(storm_json_datapoint)

        return storm_json_new


    def run_dtnest_synthesis(self, evaluations):
        """Run DTNest synthesis for all evaluated policies.

        Args:
            evaluations: List of evaluation results

        Returns:
            None
        """
        import json

        self.counters_reset()
        # Call the synthesizer to generate the decision tree for every policy from policy tree

        base_export_name = self.export_synthesis_filename_base
        dt_nest_save_path = base_export_name + "_dtNest.storm.json"

        if os.path.exists(dt_nest_save_path):
            os.remove(dt_nest_save_path)

        family_args_len = None
        # Create backup hardcopy of current quotient_mdp
        self.quotient_bp = self.quotient.return_copy()

        counter = -1
        for evaluation in evaluations:
            if not evaluation.policy:
                continue  # Filter ∅ policies

            policy = evaluation.policy[0]
            family = evaluation.family
            eval_choice = evaluation.mdp_fixed_choices
            counter += 1

            self.quotient = self.quotient_bp.return_copy()

            # Clean up the choice mask
            eval_choice = self.clean_choice_mask(eval_choice)

            # Update quotient with fixed choices
            self.update_quotient_with_choices(eval_choice)

            # Assert that the policy is valid
            self.assert_policy_choices(policy)

            # Filter storm JSON for current family
            with open(f"{base_export_name}.storm.json", "r") as f:
                storm_json = json.loads(f.read())
                storm_json = self.filter_storm_json_for_family(storm_json, family, family_args_len)

            if not family_args_len:
                family_args_len = len(family.hole_to_name)

            if not storm_json:
                continue  # Multiple mapping to single family, only one is relevant

            # Prepare and run DTControl
            model_dir = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(self.quotient.tree_helper_path))))
            scheduler_path = os.path.join(model_dir, "scheduler.storm.json")

            if os.path.exists(scheduler_path):
                os.remove(scheduler_path)

            with open(scheduler_path, "w") as f:
                f.write(json.dumps(storm_json, indent=4))

            self.run_dtcontrol(scheduler_path, model_dir)

            # Set up decision tree synthesizer
            dt_map_synthetiser = paynt.synthesizer.decision_tree.SynthesizerDecisionTree(self.quotient)
            dt_map_synthetiser.export_synthesis_filename_base = base_export_name + f"_p{counter}" if base_export_name else None

            # Prepare quotient for synthesis
            self.prepare_quotient_for_dt_synthesis()

            # Run decision tree synthesis
            dt_map_synthetiser.run()  # Policy got via dtcontrol

            # Process results
            with open(scheduler_path, "r") as f:
                storm_json = json.loads(f.read())

            # Load or initialize the aggregated data
            if os.path.exists(dt_nest_save_path):
                with open(dt_nest_save_path, "r") as f:
                    existing_data = json.loads(f.read())
            else:
                existing_data = []

            # Reconstruct and process policy
            reconstructed_policy = self.reconstruct_policy_from_storm_json(storm_json)
            storm_json = self.create_storm_json_from_policy(reconstructed_policy, family)

            # Save the updated data
            existing_data.extend(storm_json)
            with open(dt_nest_save_path, "w") as f:
                f.write(json.dumps(existing_data, indent=4))

        return dt_nest_save_path