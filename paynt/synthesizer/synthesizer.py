import logging
import os
import subprocess

import stormpy

import payntbind

import paynt.synthesizer.statistic
import paynt.utils.timer
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

        callDTNest = True
        if callDTNest:
            self.counters_reset()
            # call the synthesizer to generate the decision tree for every policy from policy tree

            # filter empty policies
            all_policies_and_families = [(evaluation.policy[0], evaluation.family) for evaluation in evaluations if
                                         evaluation.policy is not None]
            
            eval_choices = [evaluation.mdp_fixed_choices for evaluation in evaluations if
                                         evaluation.policy is not None]
            
            
            base_export_name = self.export_synthesis_filename_base
            
            family_args_len = len(all_policies_and_families[0][1].hole_to_name)
            
            # create backup hardcopy of current quotient_mdp
            
            self.quotient_bp = self.quotient.quotient_mdp

            for counter, (policy, family) in enumerate(all_policies_and_families):
                # TODO: iterate over evaluations 
                eval_choice = eval_choices[counter]
                
                # update quotient_mdp with fixed choices
                self.quotient.quotient_mdp = self.quotient.build_from_choice_mask(eval_choice).model

                # we need to convert action to choice

                # get all actions with no_label choice (to later discard)
                no_label_choices = []
                for i, action in enumerate(policy):
                    action_index_for_state = policy[i] or 0
                    if (action_index_for_state == 0):
                        no_label_choices.append(i)

                # list of choices for each state
                choices = [
                    self.quotient.state_action_choices[i][policy[i] or 0]
                    for i in range(len(self.quotient.state_valuations))
                ]
                assert all(choice is not None for choice in choices)

                # if there are multiple choices executing one action pick the first one
                choices = [choice[0] if choice else None for choice in choices]

                # Remove no_label_choices
                choices = [choice for choice in choices if choice not in no_label_choices]

                self.quotient.state_is_relevant_bv = MdpFamilyQuotient.copy_bitvector(self.quotient.state_is_relevant_bv_backup)
                irrelevant_variables = self.quotient.irrelevant_variables
                if irrelevant_variables:
                    self.quotient.mark_irrelevant_states(irrelevant_variables)
                import json

                # filter relevant data from {base_export_name}.storm.json and sav it in model dir as scheduler.storm.json
                with open(f"{base_export_name}.storm.json", "r") as f:
                    storm_json = json.loads(f.read())

                    # filter data for current family
                    for i in range(family_args_len):
                        hole_name = family.hole_to_name[i]
                        hole_value = family.holes_options[i][0] # first is candidate
                        storm_json =  [entry for entry in storm_json if entry['s'].get(hole_name) == hole_value]

                model_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(self.quotient.tree_helper_path))))
                scheduler_path = os.path.join(model_dir, "scheduler.storm.json")
                if os.path.exists(scheduler_path):
                    os.remove(scheduler_path)
                with open(scheduler_path, "w") as f:
                    f.write(json.dumps(storm_json, indent=4))

                # os.path.normpath(os.path.join(self.quotient.tree_helper_path, *([".."] * 4))
                os.path.basename(model_dir)
                self.dtcontrol_calls += 1

                command = ["/home/lada/repo/diplomka/PAYNT/.venv_fpmk/bin/dtcontrol", "--input",
                           "scheduler.storm.json", "-r", "--use-preset", "default"]
                subprocess.run(command, cwd=f"{model_dir}")
                # perhaps save to model dir and run dtcontrol from there

                # get family for the policy
                #family = self.quotient.build_family(choices)

                dt_map_synthetiser = paynt.synthesizer.decision_tree.SynthesizerDecisionTree(self.quotient)
                self.use_dtcontrol = True
                # unique export name for each policy
                dt_map_synthetiser.export_synthesis_filename_base = base_export_name + f"_p{counter}" if base_export_name else None
                #dt_map_synthetiser.run(policy=choices)
                
                #1a) create MDP restricting min player
                #1b) add random choices
                #2) make mapping between dtcoutput to my vars

                if MdpFamilyQuotient.DONT_CARE_ACTION_LABEL not in self.quotient.action_labels and MdpFamilyQuotient.add_dont_care_action:
                # LADA TODO: adding don't care must come later to single mdp
                    # identify relevant states again
                    state_relevant_bp = stormpy.BitVector(self.quotient.quotient_mdp.nr_states, True)


                    logger.debug("adding explicit don't-care action to relevant states...")
                    self.quotient.quotient_mdp = payntbind.synthesis.addDontCareAction(self.quotient.quotient_mdp,state_relevant_bp)
                    self.quotient.choice_destinations = payntbind.synthesis.computeChoiceDestinations(self.quotient.quotient_mdp)
                    self.quotient.action_labels, self.quotient.choice_to_action = payntbind.synthesis.extractActionLabels(self.quotient.quotient_mdp)
                    logger.info(f"MDP has {len(self.quotient.action_labels)} actions")
                
                
                dt_map_synthetiser.run() # policy got via dtcontrol
                
                # LADA TODO: only tring 1st policy for now
                break

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
