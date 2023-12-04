import stormpy
import stormpy.synthesis
import stormpy.pomdp

from .models import MarkovChain,MDP,DTMC
from .holes import Hole,Holes,DesignSpace
from .quotient import QuotientContainer
from .coloring import Coloring
from .pomdp_family import FSC

import math
import re

import logging
logger = logging.getLogger(__name__)


class POMDPQuotientContainer(QuotientContainer):

    # implicit size for POMDP unfolding
    initial_memory_size = 1

    # TODO
    export_optimal_result = False

    # if True, posterior-aware unfolding will be applied
    posterior_aware = False

    
    def __init__(self, pomdp, specification, decpomdp_manager=None):
        super().__init__(specification = specification)

        # unfolded POMDP
        self.quotient_mdp = None
        self.design_space = None
        self.coloring = None

        # attributes associated with a (folded) POMDP

        # default POMDP model
        self.pomdp = None
        # a (simplified) label for each observation
        self.observation_labels = None
        # number of actions available at each observation
        self.actions_at_observation = None
        # action labels corresponding to ^
        self.action_labels_at_observation = None
        # for each observation, a prototype of an action hole
        self.action_hole_prototypes = None
        # for each observation, number of states associated with it
        self.observation_states = None
        
        # attributes associated with an unfolded quotient MDP
        
        # number of memory states allocated to each observation
        self.observation_memory_size = None
        # Storm POMDP manager
        self.pomdp_manager = None

        # for each observation, a prototype of a memory hole
        self.memory_hole_prototypes = None
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

        logger.info(f"Constructed POMDP having {self.observations} observations.")
        
        # extract observation labels
        if self.pomdp.has_observation_valuations():
            ov = self.pomdp.observation_valuations
            self.observation_labels = [ov.get_string(obs) for obs in range(self.observations)]
            self.observation_labels = [self.simplify_label(label) for label in self.observation_labels]
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
        # logger.debug(f"Observation labels: {self.observation_labels}")

        # compute actions available at each observation
        self.actions_at_observation = [0] * self.observations
        for state in range(self.pomdp.nr_states):
            obs = self.pomdp.observations[state]
            if self.actions_at_observation[obs] != 0:
                continue
            self.actions_at_observation[obs] = self.pomdp.get_nr_available_actions(state)

        # collect labels of actions available at each observation
        self.action_labels_at_observation = [[] for obs in range(self.observations)]
        for state in range(self.pomdp.nr_states):
            obs = self.pomdp.observations[state]
            if self.action_labels_at_observation[obs] != []:
                continue
            actions = self.pomdp.get_nr_available_actions(state)
            for offset in range(actions):
                choice = self.pomdp.get_choice_index(state,offset)
                labels = self.pomdp.choice_labeling.get_labels_of_choice(choice)
                self.action_labels_at_observation[obs].append(labels)

        # construct action hole prototypes
        self.action_hole_prototypes = [None] * self.observations
        for obs in range(self.observations):
            num_actions = self.actions_at_observation[obs]
            if num_actions <= 1:
                continue
            name = self.create_hole_name(obs,mem="*",is_action_hole=True)
            options = list(range(num_actions))
            option_labels = [str(labels) for labels in self.action_labels_at_observation[obs]]
            hole = Hole(name, options, option_labels)
            self.action_hole_prototypes[obs] = hole

        # mark perfect observations
        self.observation_states = [0 for obs in range(self.observations)]
        for state in range(self.pomdp.nr_states):
            obs = self.pomdp.observations[state]
            self.observation_states[obs] += 1

        # initialize POMDP manager
        if not self.posterior_aware:
            self.pomdp_manager = stormpy.synthesis.PomdpManager(self.pomdp)
        else:
            self.pomdp_manager = stormpy.synthesis.PomdpManagerAposteriori(self.pomdp)

        # do initial unfolding
        self.set_imperfect_memory_size(POMDPQuotientContainer.initial_memory_size)
        # self.set_global_memory_size(POMDPQuotientContainer.initial_memory_size)

    
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

    def simplify_label(self,label):
        label = re.sub(r"\s+", "", label)
        label = label[1:-1]

        output = "[";
        first = True
        for p in label.split("&"):
            if not p.endswith("=0"):
                if first:
                    first = False
                else:
                    output += " & "
                output += p
        output += "]"
        return output

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

    
    def design_space_counter(self):
        ds = self.design_space.copy()
        print("ds: ", ds)
        for obs in range(self.observations):
            print(self.observation_memory_holes[obs])
            for mem,hole in enumerate(self.observation_memory_holes[obs]):
                print(ds[hole])
                new_options = [mem]
                if mem < max(ds[hole].options):
                    new_options += [mem+1]
                print(new_options)
                ds[hole].assume_options(new_options)
                print(ds[hole])
                print()
        self.design_space = ds


    def create_coloring(self):

        # short aliases
        pm = self.pomdp_manager
        pomdp = self.pomdp
        mdp = self.quotient_mdp

        # detect which observations now involve memory updates
        self.memory_hole_prototypes = [None] * self.observations
        for obs in range(self.observations):
            num_updates = pm.max_successor_memory_size[obs]
            if num_updates <= 1:
                continue
            name = self.create_hole_name(obs,mem="*",is_action_hole=False)
            options = list(range(num_updates))
            option_labels = [str(x) for x in range(num_updates)]
            hole = Hole(name,options,option_labels)
            self.memory_hole_prototypes[obs] = hole

        # create holes
        all_holes = Holes()
        self.observation_action_holes = []
        self.observation_memory_holes = []
        self.is_action_hole = []

        for obs in range(self.observations):
            
            # action holes
            holes = []
            prototype = self.action_hole_prototypes[obs]
            if prototype is not None:
                for mem in range(self.observation_memory_size[obs]):
                    hole = prototype.copy()
                    hole.name = self.create_hole_name(obs,mem,True)
                    holes.append(all_holes.num_holes)
                    all_holes.append(hole)
                    self.is_action_hole.append(True)
            self.observation_action_holes.append(holes)

            # memory holes
            holes = []
            prototype = self.memory_hole_prototypes[obs]
            if prototype is not None:
                for mem in range(self.observation_memory_size[obs]):
                    hole = prototype.copy()
                    hole.name = self.create_hole_name(obs,mem,False)
                    holes.append(all_holes.num_holes)
                    all_holes.append(hole)
                    self.is_action_hole.append(False)
            self.observation_memory_holes.append(holes)

        # create the coloring
        action_to_hole_options = []
        for action in range(mdp.nr_choices):
            hole_options = {}
            h = pm.row_action_hole[action]
            if h != pm.num_holes:
                hole_options[h] = pm.row_action_option[action]
            h = pm.row_memory_hole[action]
            if h != pm.num_holes:
                hole_options[h] = pm.row_memory_option[action] 
            action_to_hole_options.append(hole_options)

        return all_holes, action_to_hole_options

    def create_coloring_aposteriori(self):
        # a posteriori unfolding
        action_to_hole_options = self.pomdp_manager.coloring
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
            options = list(range(num_options))
            option_labels = [str(labels) for labels in self.action_labels_at_observation[prior]]
            hole = Hole(name,options,option_labels)

            holes[index] = hole

        # update holes
        for key,index in update_holes.items():
            num_options = hole_num_options[index]
            if num_options <= 1:
                continue
            mem,prior,posterior = key

            name = self.create_hole_name_aposteriori(False,mem,prior,posterior)
            options = list(range(num_options))
            option_labels = [str(x) for x in range(num_options)]
            hole = Hole(name,options,option_labels)

            holes[index] = hole

        # filter out trivial holes
        all_holes = Holes()
        old_to_new_indices = [None] * len(holes)
        for index,hole in enumerate(holes):
            if hole is None:
                continue
            old_to_new_indices[index] = all_holes.num_holes
            all_holes.append(hole)

        action_to_hole_options_new = []
        for hole_options in action_to_hole_options:
            hole_options_new = {old_to_new_indices[hole]:v for hole,v in hole_options.items() if old_to_new_indices[hole] is not None}
            action_to_hole_options_new.append(hole_options_new)
        action_to_hole_options = action_to_hole_options_new

        # creating this list to make it work with Paynt-Storm integration
        self.observation_action_holes = [[] for obs in range(self.observations)]
        for key,index in action_holes.items():
            _,prior = key
            new_index = old_to_new_indices[index]
            if new_index is not None:
                self.observation_action_holes[prior].append(new_index)

        return all_holes, action_to_hole_options

    
    def unfold_memory(self):
        
        # reset attributes
        self.quotient_mdp = None
        self.coloring = None
        self.memory_hole_prototypes = None
        
        self.observation_action_holes = None
        self.observation_memory_holes = None
        self.is_action_hole = None
        
        logger.debug(
            "Unfolding POMDP using the following memory allocation vector: {} ..."
            .format(self.observation_memory_size))
        self.quotient_mdp = self.pomdp_manager.construct_mdp()
        logger.debug(f"Constructed quotient MDP having {self.quotient_mdp.nr_states} states and {self.quotient_mdp.nr_choices} actions.")

        if not POMDPQuotientContainer.posterior_aware:
            all_holes, action_to_hole_options = self.create_coloring()
        else:
            all_holes, action_to_hole_options = self.create_coloring_aposteriori()

        self.coloring = Coloring(self.quotient_mdp, all_holes, action_to_hole_options)
        self.design_space = DesignSpace(all_holes)

    

    
    def estimate_scheduler_difference(self, mdp, inconsistent_assignments, choice_values, expected_visits=None):

        if POMDPQuotientContainer.posterior_aware:
            return super().estimate_scheduler_difference(mdp,inconsistent_assignments,choice_values,expected_visits)

        # note: the code below is optimized for a priori unfolding

        # create inverse map
        # TODO optimize this for multiple properties
        if mdp.quotient_to_restricted_action_map is None:
            quotient_to_restricted_action_map = [None] * self.quotient_mdp.nr_choices
            for action in range(mdp.choices):
                quotient_to_restricted_action_map[mdp.quotient_choice_map[action]] = action

        # map choices to their origin states
        choice_to_state = []
        tm = mdp.model.transition_matrix
        for state in range(mdp.model.nr_states):
            for choice in range(tm.get_row_group_start(state),tm.get_row_group_end(state)):
                choice_to_state.append(state)


        # for each hole, compute its difference sum and a number of affected states
        inconsistent_differences = {}
        for hole_index,options in inconsistent_assignments.items():
            difference_sum = 0
            states_affected = 0
            edges_0 = self.coloring.hole_option_to_actions[hole_index][options[0]]
            for choice_index,_ in enumerate(edges_0):

                choice_0_global = edges_0[choice_index]
                choice_0 = quotient_to_restricted_action_map[choice_0_global]
                if choice_0 is None:
                    continue
                
                source_state = choice_to_state[choice_0]
                source_state_visits = 1
                if expected_visits is not None:
                    source_state_visits = expected_visits[source_state]

                # assert source_state_visits != 0
                if source_state_visits == 0:
                    continue

                state_values = []
                for option in options:

                    assert len(self.coloring.hole_option_to_actions[hole_index][option]) > choice_index
                    choice_global = self.coloring.hole_option_to_actions[hole_index][option][choice_index]
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
                restricted_family[hole].assume_options(options)

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
        choice_labeling = stormpy.storage.ChoiceLabeling(dtmc.choices)
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
        dtmc = self.build_chain(assignment)
        mc_result = dtmc.check_specification(self.specification)
        policy = self.collect_policy(dtmc, mc_result)
        return policy

    
    def policy_size(self, assignment):
        '''
        Compute how many natural numbers are needed to encode the mu-FSC under
        the current memory model mu.
        '''

        # going through the induced DTMC, too lazy to parse hole names
        dtmc = self.build_chain(assignment)
        
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

    
    # constructs pomdp from the quotient MDP, used for computing POMDP abstraction bounds
    def get_family_pomdp(self, mdp):
        no_obs = self.pomdp.nr_observations
        tm = mdp.model.transition_matrix
        components = stormpy.storage.SparseModelComponents(tm, mdp.model.labeling, mdp.model.reward_models)

        full_observ_list = []
        for state in range(self.pomdp.nr_states):
            obs = self.pomdp.get_observation(state)
            for mem in range(self.observation_memory_size[obs]):
                full_observ_list.append(obs + mem * no_obs)

        choice_labeling = stormpy.storage.ChoiceLabeling(mdp.choices)

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
        for choice in range(mdp.choices):
            choice_labeling.add_label_to_choice(str(labels_list[choice]), choice)

        components.choice_labeling = choice_labeling
        components.observability_classes = observ_list

        pomdp = stormpy.storage.SparsePomdp(components)
        pomdp = stormpy.pomdp.make_canonic(pomdp)

        return pomdp
    

    # TODO there should be a more efficient way to implement this
    def evaluate_given_fsc(self, fsc):
        memory_list = []
        for ind in range(len(self.observation_labels)):
            count = 0
            for x in fsc.action_function:
                if x[ind] is not None:
                    count += 1
            memory_list.append(count)

        self.observation_memory_size = memory_list
        self.set_manager_memory_vector()

        self.unfold_memory()
        logger.info("memory unfolded")

        fsc_fam = self.design_space.copy()
        for obs in range(self.observations):
            for act_hole, index in zip(self.observation_action_holes[obs], range(len(self.observation_action_holes[obs]))):
                fsc_fam[act_hole].assume_options([fsc.action_function[index][obs]])
            for mem_holes, index in zip(self.observation_memory_holes[obs], range(len(self.observation_memory_holes[obs]))):
                fsc_fam[mem_holes].assume_options([fsc.update_function[index][obs]])

        self.build(fsc_fam)
        res = fsc_fam.mdp.check_specification(self.specification, short_evaluation=True)
        fsc_fam.analysis_result = res
        
        return fsc_fam.analysis_result.improving_value
