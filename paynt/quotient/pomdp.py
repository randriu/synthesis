import stormpy
import stormpy.pomdp
import payntbind

import paynt.family.family
import paynt.quotient.quotient
import paynt.quotient.fsc

import math
import re
import collections

import logging
logger = logging.getLogger(__name__)


class PomdpQuotient(paynt.quotient.quotient.Quotient):

    # implicit size for POMDP unfolding
    initial_memory_size = 1
    # if True, posterior-aware unfolding will be applied
    posterior_aware = False

    # label associated with un-labelled choices
    EMPTY_LABEL = "__no_label__"

    
    def __init__(self, pomdp, specification, decpomdp_manager=None):
        super().__init__(specification=specification)

        # unfolded POMDP
        self.quotient_mdp = None
        self.family = None
        self.coloring = None
        # to each hole-option pair a list of actions colored by this combination (reverse coloring)
        self.hole_option_to_actions = None

        # attributes associated with a (folded) POMDP

        # default POMDP model
        self.pomdp = None
        # a (simplified) label for each observation
        self.observation_labels = None
        # number of actions available at each observation
        self.actions_at_observation = None
        # action labels corresponding to ^
        self.action_labels_at_observation = None
        # for each observation, number of states associated with it
        self.observation_states = None
        
        # attributes associated with an unfolded quotient MDP
        
        # number of memory states allocated to each observation
        self.observation_memory_size = None
        # Storm POMDP manager
        self.pomdp_manager = None

        # for each observation, a list of action holes
        self.observation_action_holes = None
        # for each observation, a list of memory holes
        self.observation_memory_holes = None
        # for each hole, an indication whether this is an action or a memory hole
        self.is_action_hole = None

        # construct the quotient POMDP
        self.pomdp = stormpy.pomdp.make_canonic(pomdp)
        # ^ this also asserts that states with the same observation have the
        # same number and the same order of available actions

        logger.info(f"constructed POMDP having {self.observations} observations.")
        
        state_obs = self.pomdp.observations.copy()
        
        # extract observation labels
        if self.pomdp.has_observation_valuations():
            ov = self.pomdp.observation_valuations
            self.observation_labels = [ov.get_string(obs) for obs in range(self.observations)]
        else:
            if decpomdp_manager is None:
                self.observation_labels = list(range(self.observations))
                self.observation_labels = [str(label) for label in self.observation_labels]
            else:
                # map each 'joint' observation to the agent's observation and use the corresponding label
                self.observation_labels = []
                for obs in range(self.observations):
                    agent_obs = decpomdp_manager.joint_observations[obs][0]
                    agent_obs_label = decpomdp_manager.agent_observation_labels[0][agent_obs]
                    self.observation_labels.append(agent_obs_label)

        # compute actions available at each observation
        self.actions_at_observation = [0] * self.observations
        for state in range(self.pomdp.nr_states):
            obs = state_obs[state]
            if self.actions_at_observation[obs] != 0:
                continue
            self.actions_at_observation[obs] = self.pomdp.get_nr_available_actions(state)

        # collect labels of actions available at each observation
        self.action_labels_at_observation = [[] for obs in range(self.observations)]
        for state in range(self.pomdp.nr_states):
            obs = state_obs[state]
            if self.action_labels_at_observation[obs] != []:
                continue
            for offset in range(self.actions_at_observation[obs]):
                choice = self.pomdp.get_choice_index(state,offset)
                labels = self.pomdp.choice_labeling.get_labels_of_choice(choice)
                assert len(labels) <= 1, "expected at most 1 label"
                if len(labels) == 0:
                    label = PomdpQuotient.EMPTY_LABEL
                else :
                    label = list(labels)[0]
                self.action_labels_at_observation[obs].append(label)

        # mark perfect observations
        self.observation_states = [0 for obs in range(self.observations)]
        for state in range(self.pomdp.nr_states):
            self.observation_states[state_obs[state]] += 1

        # initialize POMDP manager
        if not PomdpQuotient.posterior_aware:
            self.pomdp_manager = payntbind.synthesis.PomdpManager(self.pomdp)
        else:
            self.pomdp_manager = payntbind.synthesis.PomdpManagerAposteriori(self.pomdp)

        # do initial unfolding
        self.set_imperfect_memory_size(PomdpQuotient.initial_memory_size)
        # self.set_global_memory_size(PomdpQuotient.initial_memory_size)

    
    @property
    def observations(self):
        return self.pomdp.nr_observations

    def create_hole_name(self, obs, mem, is_action_hole):
        category = "A" if is_action_hole else "M"
        obs_label = self.observation_labels[obs]
        return "{}({},{})".format(category,obs_label,mem)

    def create_hole_name_aposteriori(self, is_action_hole, mem, prior, posterior=None):
        category = "A" if is_action_hole else "M"
        prior_label = self.observation_labels[prior]
        if posterior is None:
            return "{}({},{})".format(category,mem,prior_label)
        else:
            posterior_label = self.observation_labels[posterior]
            return "{}({},{},{})".format(category,mem,prior_label,posterior_label)


    def decode_hole_name(self, name):
        result = re.search(r"([A|M])\((.*?),(\d+)\)", name)
        is_action_hole = result.group(1) == "A"
        observation_label = result.group(2)
        memory = int(result.group(3))

        observation = None
        for obs in range(self.observations):
            if observation_label == self.observation_labels[obs]:
                observation = obs
                break
        return (is_action_hole, observation, memory)

    def set_manager_memory_vector(self):
        for obs in range(self.observations):
            mem = self.observation_memory_size[obs]
            self.pomdp_manager.set_observation_memory_size(obs,mem)

    def set_global_memory_size(self, memory_size):
        self.observation_memory_size = [memory_size] * self.observations
        self.set_manager_memory_vector()
        self.unfold_memory()

    def set_imperfect_memory_size(self, memory_size):
        ''' Set given memory size only to imperfect observations. '''
        self.observation_memory_size = [
            memory_size if self.observation_states[obs]>1 else 1
            for obs in range(self.observations)
        ]
        self.set_manager_memory_vector()
        self.unfold_memory()
    
    def increase_memory_size(self, obs):
        self.observation_memory_size[obs] += 1
        self.set_manager_memory_vector()
        self.unfold_memory()

    def set_memory_from_dict(self, obs_memory_dict):
        memory_list = []

        for obs in range(self.observations):
            memory_list.append(obs_memory_dict[obs])

        self.observation_memory_size = memory_list
        self.set_manager_memory_vector()
        self.unfold_memory()

    def set_memory_from_result_new(self, obs_memory_dict, obs_memory_dict_cutoff, memory_limit):
        memory_list = []

        for obs in range(self.observations):
            #memory = self.observation_memory_size[obs]
            if self.observation_states[obs] <= 1:
                memory = 1
            elif obs in obs_memory_dict.keys():
                memory = max(obs_memory_dict[obs], self.observation_memory_size[obs]+1)
            elif obs in obs_memory_dict_cutoff.keys():
                memory = obs_memory_dict_cutoff[obs]
            else:
                memory = memory_limit

            memory_list.append(memory)

        self.observation_memory_size = memory_list
        self.set_manager_memory_vector()
        self.unfold_memory()

    
    def create_coloring(self):
        if PomdpQuotient.posterior_aware:
            return self.create_coloring_aposteriori()

        # create holes
        family = paynt.family.family.Family()
        self.observation_action_holes = []
        self.observation_memory_holes = []
        self.is_action_hole = []

        for obs in range(self.observations):
            
            # action holes
            hole_indices = []
            num_actions = self.actions_at_observation[obs]
            if num_actions > 1:
                option_labels = self.action_labels_at_observation[obs]
                for mem in range(self.observation_memory_size[obs]):
                    hole_indices.append(family.num_holes)
                    name = self.create_hole_name(obs,mem,True)
                    family.add_hole(name,option_labels)
                    self.is_action_hole.append(True)
            self.observation_action_holes.append(hole_indices)

            # memory holes
            hole_indices = []
            num_updates = self.pomdp_manager.max_successor_memory_size[obs]
            if num_updates > 1:
                option_labels = [str(x) for x in range(num_updates)]
                for mem in range(self.observation_memory_size[obs]):
                    name = self.create_hole_name(obs,mem,False)
                    hole_indices.append(family.num_holes)
                    family.add_hole(name,option_labels)
                    self.is_action_hole.append(False)
            self.observation_memory_holes.append(hole_indices)

        # create the coloring
        assert self.pomdp_manager.num_holes == family.num_holes
        num_holes = family.num_holes
        choice_action_hole = self.pomdp_manager.row_action_hole
        choice_memory_hole = self.pomdp_manager.row_memory_hole
        choice_action_option = self.pomdp_manager.row_action_option
        choice_memory_option = self.pomdp_manager.row_memory_option
        choice_to_hole_options = []
        for choice in range(self.quotient_mdp.nr_choices):
            hole_options = []
            hole = choice_action_hole[choice]
            if hole != num_holes:
                hole_options.append( (hole,choice_action_option[choice]) )
            hole = choice_memory_hole[choice]
            if hole != num_holes:
                hole_options.append( (hole,choice_memory_option[choice]) )
            choice_to_hole_options.append(hole_options)

        return family, choice_to_hole_options

    def create_coloring_aposteriori(self):
        # a posteriori unfolding
        choice_to_hole_options = self.pomdp_manager.coloring
        hole_num_options = self.pomdp_manager.hole_num_options
        action_holes = self.pomdp_manager.action_holes
        update_holes = self.pomdp_manager.update_holes

        holes = [None] * len(hole_num_options)
        
        # action holes
        for key,index in action_holes.items():
            num_options = hole_num_options[index]
            if num_options <= 1:
                continue
            mem,prior = key
            name = self.create_hole_name_aposteriori(True,mem,prior)
            option_labels = [str(labels) for labels in self.action_labels_at_observation[prior]]
            holes[index] = (name,option_labels)

        # update holes
        for key,index in update_holes.items():
            num_options = hole_num_options[index]
            if num_options <= 1:
                continue
            mem,prior,posterior = key
            name = self.create_hole_name_aposteriori(False,mem,prior,posterior)
            option_labels = [str(x) for x in range(num_options)]
            holes[index] = (name,option_labels)

        # filter out trivial holes
        family = paynt.family.family.Family()
        old_to_new_indices = [None] * len(holes)
        for index,name_labels in enumerate(holes):
            if name_labels is None:
                continue
            old_to_new_indices[index] = family.num_holes
            name,option_labels = name_labels
            family.add_hole(name,option_labels)

        choice_to_hole_options_new = []
        for hole_options in choice_to_hole_options:
            hole_options_new = [ (old_to_new_indices[hole],v) for hole,v in hole_options.items() if old_to_new_indices[hole] is not None ]
            choice_to_hole_options_new.append(hole_options_new)
        choice_to_hole_options = choice_to_hole_options_new

        # creating this list to make it work with Paynt-Storm integration
        self.observation_action_holes = [[] for obs in range(self.observations)]
        for key,index in action_holes.items():
            _,prior = key
            new_index = old_to_new_indices[index]
            if new_index is not None:
                self.observation_action_holes[prior].append(new_index)

        return family, choice_to_hole_options

    
    def unfold_memory(self):
        
        # reset attributes
        self.quotient_mdp = None
        self.coloring = None
        self.hole_option_to_actions = None
        
        self.observation_action_holes = None
        self.observation_memory_holes = None
        self.is_action_hole = None
        
        logger.debug("unfolding {}-FSC template into POMDP...".format(max(self.observation_memory_size)))
        self.quotient_mdp = self.pomdp_manager.construct_mdp()
        self.choice_destinations = payntbind.synthesis.computeChoiceDestinations(self.quotient_mdp)
        logger.debug(f"constructed quotient MDP having {self.quotient_mdp.nr_states} states and {self.quotient_mdp.nr_choices} actions.")

        self.family, choice_to_hole_options = self.create_coloring()

        self.coloring = payntbind.synthesis.Coloring(self.family.family, self.quotient_mdp.nondeterministic_choice_indices, choice_to_hole_options)

        # to each hole-option pair a list of actions colored by this combination
        self.hole_option_to_actions = [[] for hole in range(self.family.num_holes)]
        for hole in range(self.family.num_holes):
            self.hole_option_to_actions[hole] = [[] for option in self.family.hole_options(hole)]
        for choice in range(self.quotient_mdp.nr_choices):
            for hole,option in choice_to_hole_options[choice]:
                self.hole_option_to_actions[hole][option].append(choice)


    
    def estimate_scheduler_difference(self, mdp, quotient_choice_map, inconsistent_assignments, choice_values, expected_visits):

        if PomdpQuotient.posterior_aware:
            return super().estimate_scheduler_difference(mdp,quotient_choice_map,inconsistent_assignments,choice_values,expected_visits)

        # note: the code below is optimized for posterior-unaware unfolding

        # create inverse quotient-choice-to-mdp-choice map
        # TODO optimize this for multiple properties
        quotient_to_restricted_action_map = [None] * self.quotient_mdp.nr_choices
        for choice in range(mdp.nr_choices):
            quotient_to_restricted_action_map[quotient_choice_map[choice]] = choice

        # map choices to their origin states
        choice_to_state = []
        tm = mdp.transition_matrix
        for state in range(mdp.nr_states):
            for choice in tm.get_rows_for_group(state):
                choice_to_state.append(state)

        # for each hole, compute its difference sum and a number of affected states
        inconsistent_differences = {}
        for hole_index,options in inconsistent_assignments.items():
            difference_sum = 0
            states_affected = 0
            edges_0 = self.hole_option_to_actions[hole_index][options[0]]
            for choice_index,_ in enumerate(edges_0):

                choice_0_global = edges_0[choice_index]
                choice_0 = quotient_to_restricted_action_map[choice_0_global]
                if choice_0 is None:
                    continue
                
                source_state = choice_to_state[choice_0]
                source_state_visits = expected_visits[source_state]

                # assert source_state_visits != 0
                if source_state_visits == 0:
                    continue

                state_values = []
                for option in options:

                    assert len(self.hole_option_to_actions[hole_index][option]) > choice_index
                    choice_global = self.hole_option_to_actions[hole_index][option][choice_index]
                    choice = quotient_to_restricted_action_map[choice_global]
                    choice_value = choice_values[choice]
                    state_values.append(choice_value)

                min_value = min(state_values)
                max_value = max(state_values)
                difference = (max_value - min_value) * source_state_visits
                assert not math.isnan(difference)
                difference_sum += difference
                states_affected += 1
            
            if states_affected == 0:
                hole_score = 0
            else:
                hole_score = difference_sum / states_affected
            inconsistent_differences[hole_index] = hole_score

        return inconsistent_differences


    
    
    def sift_actions_and_updates(self, obs, hole, options):
        actions = set()
        updates = set()
        num_updates = self.pomdp_manager.max_successor_memory_size[obs]
        for option in options:
            actions.add(option // num_updates)
            updates.add(option %  num_updates)
        return actions,updates

    def break_symmetry_uai(self, family, action_inconsistencies, memory_inconsistencies):
        
        # go through each observation of interest and break symmetry
        restricted_family = family.copy()
        for obs in range(self.observations):
            
            num_actions = self.actions_at_observation[obs]
            num_updates = self.pomdp_manager.max_successor_memory_size[obs]

            obs_holes = self.obs_to_holes[obs]
            num_holes = len(obs_holes)


            all_actions = [action for action in range(num_actions)]
            selected_actions = [all_actions.copy() for hole in obs_holes]
            
            all_updates = [update for update in range(num_updates)]
            selected_updates = [all_updates.copy() for hole in obs_holes]

            inconsistencies = list(action_inconsistencies[obs])
            num_inc = len(inconsistencies)
            if num_inc > 1:
                # action inconsistency: allocate inconsistent actions between holes
                ignored_actions = [action for action in all_actions if action not in inconsistencies]
                selected_actions = [ignored_actions.copy() for hole in obs_holes]
                for index in range(max(num_holes,num_inc)):
                    selected_actions[index % num_holes].append(inconsistencies[index % num_inc])
            else:
                inconsistencies = list(memory_inconsistencies[obs])
                num_inc = len(inconsistencies)
                if num_inc > 1:
                    # memory inconsistency: distribute inconsistent updates between holes
                    ignored_updates = [update for update in all_updates if update not in inconsistencies]
                    selected_updates = [ignored_updates.copy() for hole in obs_holes]
                    for index in range(max(num_holes,num_inc)):
                        selected_updates[index % num_holes].append(inconsistencies[index % num_inc])

            # create options for each hole
            for index in range(num_holes):
                hole = obs_holes[index]
                actions = selected_actions[index]
                updates = selected_updates[index]
                options = []
                for action in actions:
                    for update in updates:
                        options.append(action * num_updates + update)
                restricted_family.hole_set_options(hole,options)

        # print(restricted_family)
        logger.debug("Symmetry breaking: reduced design space from {} to {}".format(family.size, restricted_family.size))

        return restricted_family

    
    
    def export_result(self, dtmc, mc_result):
        self.export_pomdp()
        self.export_optimal_dtmc(dtmc)
        self.export_policy(dtmc, mc_result)

    
    def export_pomdp(self):
        pomdp_path = "pomdp.drn"
        logger.info("Exporting POMDP to {}".format(pomdp_path))
        stormpy.export_to_drn(self.pomdp, pomdp_path)

    
    def export_optimal_dtmc(self, dtmc):

        # label states with a pomdp_state:memory_node pair
        # label choices with a pomdp_choice:memory_update pair
        state_labeling = dtmc.model.labeling
        choice_labeling = stormpy.storage.ChoiceLabeling(dtmc.model.nr_choices)
        for state in range(dtmc.states):
            mdp_state = dtmc.quotient_state_map[state]
            mdp_choice = dtmc.quotient_choice_map[state]

            pomdp_state = self.pomdp_manager.state_prototype[mdp_state]
            memory_node = self.pomdp_manager.state_memory[mdp_state]
            state_label = "{}:{}".format(pomdp_state,memory_node)
            if not state_labeling.contains_label(state_label):
                state_labeling.add_label(state_label)
            state_labeling.add_label_to_state(state_label,state)

            pomdp_action_index = self.pomdp_manager.row_action_option[mdp_choice]
            pomdp_choice = self.pomdp.get_choice_index(pomdp_state, pomdp_action_index)
            memory_update = self.pomdp_manager.row_memory_option[mdp_choice]
            choice_label = "{}:{}".format(pomdp_choice,memory_update)
            if not choice_labeling.contains_label(choice_label):
                choice_labeling.add_label(choice_label)
            # state and choices indices coincide for DTMCs
            choice_labeling.add_label_to_choice(choice_label,state)    

        # add choice labeling to the model
        m = dtmc.model
        components = stormpy.storage.SparseModelComponents(m.transition_matrix,m.labeling,m.reward_models)
        components.choice_labeling = choice_labeling
        dtmc.model = stormpy.storage.SparseDtmc(components)

        # export DTMC
        dtmc_path = "dtmc.drn"
        logger.info("Exporting optimal DTMC to {}".format(dtmc_path))
        stormpy.export_to_drn(dtmc.model, dtmc_path)

    
    def collect_policy(self, dtmc, mc_result):
        # assuming single optimizing property
        assert self.specification.num_properties == 1 and self.specification.has_optimality
        dtmc_state_value = mc_result.optimality_result.result.get_values()

        # map states of the DTMC to their POMDP counterparts
        # label states with the value achieved in the state
        # group results by observation
        policy = []
        for obs in range(self.observations):
            mem_size = self.observation_memory_size[obs]
            mem_info = [ {} for _ in range(mem_size) ]
            policy.append(mem_info)

        for dtmc_state in range(dtmc.states):
            value = dtmc_state_value[dtmc_state]
            mdp_state = dtmc.quotient_state_map[dtmc_state]
            # mdp_choice = dtmc.quotient_choice_map[dtmc_state]

            pomdp_state = self.pomdp_manager.state_prototype[mdp_state]
            memory_node = self.pomdp_manager.state_memory[mdp_state]
            observation = self.pomdp.get_observation(pomdp_state)

            policy[observation][memory_node][pomdp_state] = value

        return policy

    def export_policy(self, dtmc, mc_result):

        policy = self.collect_policy(dtmc, mc_result)

        # use JSON as output format
        obs_info = []
        for obs in range(self.observations):
            policies = []
            for mem in range(self.pomdp_manager.observation_memory_size[obs]):
                if len(policy[obs][mem]) == 0:
                    continue
                state_values = [ {state:value} for state,value in policy[obs][mem].items() ]
                
                sub_policy = {}
                sub_policy["memory_node"] = mem
                sub_policy["state_values"] = state_values

                policies.append( sub_policy )
            obs_info.append(policies)

        # export JSON
        import json
        output_json = json.dumps(obs_info, indent=4)
        # print(output_json)
        scheduler_path = "scheduler.json"
        logger.info("Exporting optimal scheduler to {}".format(scheduler_path))
        with open(scheduler_path, 'w') as f:
            print(output_json, file=f)

    def extract_policy(self, assignment):
        dtmc = self.build_assignment(assignment)
        mc_result = dtmc.check_specification(self.specification)
        policy = self.collect_policy(dtmc, mc_result)
        return policy

    
    def policy_size(self, assignment):
        '''
        Compute how many natural numbers are needed to encode the mu-FSC under
        the current memory model mu.
        '''

        # going through the induced DTMC, too lazy to parse hole names
        dtmc = self.build_assignment(assignment)
        
        # size of action function gamma:
        #   for each memory node, a list of prior-action pairs
        size_gamma = sum(self.observation_memory_size) # explicit
        # size_gamma = sum([len(x) for x in prior_observations]) * 2 # sparse
        
        if not self.posterior_aware:
            # size of update function delta of a posterior-unaware FSC:
            #   for each memory node, a list of prior-update pairs
            size_delta = sum(self.observation_memory_size) # explicit
            return size_gamma + size_delta
        
        # posterior-aware update selection
        # for each memory node and for each prior, collect a set of possible posteriors
        max_mem = max(self.observation_memory_size)
        memory_prior_posteriors = [[set() for _ in range(self.observations)] for _ in range(max_mem)]
        for state in range(dtmc.states):
            mdp_state = dtmc.quotient_state_map[state]

            # get prior
            pomdp_state = self.pomdp_manager.state_prototype[mdp_state]
            memory_node = self.pomdp_manager.state_memory[mdp_state]
            prior = self.pomdp.get_observation(pomdp_state)
            # prior_observations[memory_node].add(prior)

            # get posterior observations
            for entry in dtmc.model.transition_matrix.get_row(state):
                successor = entry.column
                mdp_successor = dtmc.quotient_state_map[successor]
                pomdp_successor = self.pomdp_manager.state_prototype[mdp_successor]
                posterior = self.pomdp.get_observation(pomdp_successor)
                memory_prior_posteriors[memory_node][prior].add(posterior)

        # size of update function delta of a posterior-aware FSC:
        #   for each memory node and for each possible prior, a list of posterior-action pairs
        #   assuming sparse representation (not including delimeters)
        size_delta = 0
        for n_prior_posteriors in memory_prior_posteriors:
            for n_z_posteriors in n_prior_posteriors:
                size_delta += 2 * len(n_z_posteriors)

        return size_gamma + size_delta

    
    def get_family_pomdp(self, mdp):
        '''
        Constructs POMDP from the quotient MDP. Used for computing POMDP abstraction bounds.
        '''
        no_obs = self.pomdp.nr_observations
        tm = mdp.model.transition_matrix
        components = stormpy.storage.SparseModelComponents(tm, mdp.model.labeling, mdp.model.reward_models)

        full_observ_list = []
        for state in range(self.pomdp.nr_states):
            obs = self.pomdp.get_observation(state)
            for mem in range(self.observation_memory_size[obs]):
                full_observ_list.append(obs + mem * no_obs)

        choice_labeling = stormpy.storage.ChoiceLabeling(mdp.model.nr_choices)

        # assign observations to states
        observ_list = []
        choice_labels = []
        for state in range(mdp.model.nr_states):
            original_state = mdp.quotient_state_map[state]
            observ_list.append(full_observ_list[original_state])
            actions = [action for action in range(mdp.model.get_nr_available_actions(state))]
            choice_labels.append(actions)

        # construct labeling
        labels_list = [item for sublists in choice_labels for item in sublists]
        labels = list(set(labels_list))
        for label in labels:
            choice_labeling.add_label(str(label))
        for choice in range(mdp.model.nr_choices):
            choice_labeling.add_label_to_choice(str(labels_list[choice]), choice)

        components.choice_labeling = choice_labeling
        components.observability_classes = observ_list

        pomdp = stormpy.storage.SparsePomdp(components)
        pomdp = stormpy.pomdp.make_canonic(pomdp)

        return pomdp


    def assignment_to_fsc(self, assignment):
        assert assignment.size == 1, "expected family of size 1"
        num_nodes = max(self.observation_memory_size)
        fsc = paynt.quotient.fsc.FSC(num_nodes, self.observations, is_deterministic=True)
        fsc.observation_labels = self.observation_labels

        # collect action labels
        action_labels = set()
        for labels in self.action_labels_at_observation:
            action_labels.update(labels)
        action_labels = list(action_labels)
        fsc.action_labels = action_labels

        # map observations to unique indices of available actions
        action_label_indices = {label:index for index,label in enumerate(action_labels)}
        observation_to_actions = [[] for obs in range(self.observations)]
        for obs,action_labels in enumerate(self.action_labels_at_observation):
            observation_to_actions[obs] = [action_label_indices[label] for label in action_labels]

        fsc.fill_trivial_actions(observation_to_actions)
        fsc.fill_zero_updates()

        # convert hole assignment to FSC
        for obs,holes in enumerate(self.observation_action_holes):
            for memory,hole in enumerate(holes):
                option = assignment.hole_options(hole)[0]
                action_label = self.action_labels_at_observation[obs][option]
                action = action_label_indices[action_label]
                fsc.action_function[memory][obs] = action
        for obs,holes in enumerate(self.observation_memory_holes):
            for memory,hole in enumerate(holes):
                option = assignment.hole_options(hole)[0]
                fsc.update_function[memory][obs] = option

        # fixing the FSC for not fully unrolled quotients
        fsc.fill_implicit_actions_and_updates()

        fsc.check(observation_to_actions)

        return fsc


    def compute_qvalues(self, assignment):
        '''
        Given an MDP obtained after applying an FSC to a POMDP, compute for each state s, (reachable) memory node n
        the Q-value Q(s,n).
        :param assignment hole assignment encoding an FSC; it is assumed the assignment is the one obtained
            for the current unfolding
        :note Q(s,n) may be None if (s,n) exists in the unfolded POMDP but is not reachable in the induced DTMC
        '''
        # model check
        submdp = self.build_assignment(assignment)
        prop = self.get_property()
        result = submdp.model_check_property(prop)
        state_submdp_to_value = result.result.get_values()

        # map states of a sub-MDP to the states of the quotient MDP to the state-memory pairs of the POMDPxFSC
        state_memory_value = collections.defaultdict(lambda: None)
        for submdp_state,value in enumerate(state_submdp_to_value):
            mdp_state = submdp.quotient_state_map[submdp_state]
            pomdp_state = self.pomdp_manager.state_prototype[mdp_state]
            memory_node = self.pomdp_manager.state_memory[mdp_state]
            state_memory_value[ (pomdp_state,memory_node) ] = value

        # make this mapping total
        memory_size = 1 + max([memory for state,memory in state_memory_value.keys()])
        state_memory_value_total = [[None for memory in range(memory_size)] for state in range(self.pomdp.nr_states)]
        for state in range(self.pomdp.nr_states):
            for memory in range(memory_size):
                value = state_memory_value[(state,memory)]
                if value is None:
                    obs = self.pomdp.observations[state]
                    if memory < self.observation_memory_size[obs]:
                        # case 1: (s,n) exists but is not reachable in the induced DTMC
                        value = None
                    else:
                        # case 2: (s,n) does not exist because n memory was not allocated for s
                        # i.e. (s,n) has the same value as (s,0)
                        value = state_memory_value[(state,0)]
                state_memory_value_total[state][memory] = value

        return state_memory_value_total


    def next_belief(self, belief, action_label, next_obs):
        any_belief_state = list(belief.keys())[0]
        obs = self.pomdp.observations[any_belief_state]
        action = self.action_labels_at_observation[obs].index(action_label)
        new_belief = collections.defaultdict(float)
        ndi = self.pomdp.nondeterministic_choice_indices.copy()
        for state,state_prob in belief.items():
            choice = self.pomdp.get_choice_index(state,action)
            for entry in self.pomdp.transition_matrix.get_row(choice):
                next_state = entry.column
                if self.pomdp.observations[next_state] == next_obs:
                    new_belief[next_state] += state_prob * entry.value()
        prob_sum = sum(new_belief.values())
        new_belief = {state:prob/prob_sum for state,prob in new_belief.items()}
        return new_belief
