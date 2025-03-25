import paynt.quotient.pomdp
import stormpy
import payntbind

import paynt.models.models
import paynt.quotient.quotient
import paynt.quotient.mdp_family
import paynt.quotient.posmg
import paynt.verification.property


import logging
logger = logging.getLogger(__name__)

class SubPomdp:
    '''
    Simple container for a (sub-)POMDP created from the quotient.
    '''
    def __init__(self, model, quotient, quotient_state_map, quotient_choice_map):
        # the Stormpy POMDP
        self.model = model
        # POMDP family quotient from which this POMDP was constructed
        # self.quotient = quotient
        # for each state of the POMDP, a state in the quotient
        self.quotient_state_map = quotient_state_map
        # for each choice of the POMDP, a choice in the quotient
        self.quotient_choice_map = quotient_choice_map


class GameAbstractionSolver():
    def __init__(self, quotient_mdp, state_to_observation, prop, quotient_num_actions, choice_to_action):
        self.quotient_mdp = quotient_mdp
        self.state_to_observation = state_to_observation
        self.quotient_num_actions = quotient_num_actions
        self.choice_to_action = choice_to_action

        self.solution_value = None
        self.solution_state_values = [None for state in range(quotient_mdp.nr_states)]
        self.solution_state_to_player1_action = [None for state in range(quotient_mdp.nr_states)]
        self.solution_state_to_quotient_choice = [None for state in range(quotient_mdp.nr_states)]

        self.posmg_specification = self.create_posmg_specification(prop)

    def specify_target_with_label(self, labeling, prop):
        '''
        If the target is specified by a label return this label.
        If the target is specified by an expression, mark all target states with a new
        label and return this label.
        '''
        target = prop.formula.subformula.subformula
        target_label = prop.get_target_label()

        target_is_label = isinstance(target, stormpy.logic.AtomicLabelFormula)
        if target_is_label:
            return target_label

        # target is an expression
        new_target_label = 'goal'

        while labeling.contains_label(new_target_label):
            new_target_label += '_' # add arbitrary character at the end to make new label unique

        labeling.add_label(new_target_label)
        target_states = labeling.get_states(target_label)
        labeling.set_states(new_target_label, target_states)

        return new_target_label

    def create_posmg_specification(self, prop):
        formula_str = prop.formula.__str__()

        target_label = prop.get_target_label()
        new_target_label = self.specify_target_with_label(self.quotient_mdp.labeling, prop)
        if target_label != new_target_label:
            formula_str = formula_str.replace(target_label, '"' + new_target_label + '"')

        optimizing_player = 0 # hard coded. Has to correspond with state_player_indications
        game_fromula_str = f"<<{optimizing_player}>> " + formula_str

        storm_property = stormpy.parse_properties(game_fromula_str)[0]
        property = paynt.verification.property.construct_property(storm_property, 0) # realtive error?
        specification = paynt.verification.property.Specification([property])

        return specification


    def calculate_state_to_player1_action(self, state_to_quotient_choice, choice_to_action, num_actions):
        num_choices = len(choice_to_action)

        state_to_player1_action = []
        for choice in state_to_quotient_choice:
            if choice == num_choices:
                state_to_player1_action.append(num_actions)
            else:
                state_to_player1_action.append(choice_to_action[choice])

        return state_to_player1_action

    def solve_smg(self, quotient_choice_mask):
        # initialize results
        self.solution_value = 0
        for state in range(self.quotient_mdp.nr_states):
            self.solution_state_to_player1_action[state] = self.quotient_num_actions
            self.solution_state_to_quotient_choice[state] = self.quotient_mdp.nr_choices
            self.solution_state_values[state] = 0

        # create game abstraction
        smg_abstraction = payntbind.synthesis.SmgAbstraction(
            self.quotient_mdp,
            self.quotient_num_actions,
            self.choice_to_action,
            quotient_choice_mask)

        # create posmg
        smg_state_observation = []
        for smg_state in range(smg_abstraction.smg.nr_states):
            quotient_state, _ = smg_abstraction.state_to_quotient_state_action[smg_state]
            obs = self.state_to_observation[quotient_state]
            smg_state_observation.append(obs)
        posmg = payntbind.synthesis.posmg_from_smg(smg_abstraction.smg,smg_state_observation)

        # solve posmg
            # the unfolding (if looking for k-FSCs) was already done in PomdpFamilyQuotient init, so set mem to 1 to prevent another unfold
        paynt.quotient.posmg.PosmgQuotient.initial_memory_size = 1
        posmgQuotient = paynt.quotient.posmg.PosmgQuotient(posmg, self.posmg_specification)
        synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR(posmgQuotient)
        assignment = synthesizer.synthesize(print_stats=False)

        # TODO modify for rewards
        #   assignment can be None even for optimality property if the value is infinity
        assert assignment is not None, 'The model contains a non-goal sink state. For such case, the reward model checking returns infinity (=non valid result)'

        # extract results
        state_player_indications = posmgQuotient.posmg_manager.get_state_player_indications()
        choices = posmgQuotient.coloring.selectCompatibleChoices(assignment.family)
        model, game_state_map, game_choice_map = posmgQuotient.restrict_mdp(posmgQuotient.quotient_mdp, choices)
        dtmc = paynt.models.models.Mdp(model)
        result = dtmc.check_specification(self.posmg_specification)

        # fill solution_state_to_player1_action
        for dtmc_state, game_state in enumerate(game_state_map):
            if state_player_indications[game_state] == 0:
                game_choice = game_choice_map[dtmc_state]
                quotient_choice = smg_abstraction.choice_to_quotient_choice[game_choice]
                selected_action = self.choice_to_action[quotient_choice]

                quotient_state, _ = smg_abstraction.state_to_quotient_state_action[game_state]
                self.solution_state_to_player1_action[quotient_state] = selected_action

        # fill solution_state_to_quotient_choices
        for dtmc_state, game_state in enumerate(game_state_map):
            if state_player_indications[game_state] != 1:
                continue
            quotient_state, selected_action = smg_abstraction.state_to_quotient_state_action[game_state]
            if selected_action != self.solution_state_to_player1_action[quotient_state]: # is this necessary? wont these states be removed during restrict mdp?
                continue
            game_choice = game_choice_map[dtmc_state]
            quotient_choice = smg_abstraction.choice_to_quotient_choice[game_choice]
            self.solution_state_to_quotient_choice[quotient_state] = quotient_choice

        # fill solution_value
        self.solution_value = result.optimality_result.result.at(self.quotient_mdp.initial_states[0])


        # fill solution_state_values
        for dtmc_state, game_state in enumerate(game_state_map):
            if state_player_indications[game_state] == 0:
                value = result.optimality_result.result.at(dtmc_state)
                quotient_state, _ = smg_abstraction.state_to_quotient_state_action[game_state]
                self.solution_state_values[quotient_state] = value



class PomdpFamilyQuotient(paynt.quotient.mdp_family.MdpFamilyQuotient):
    MAX_MEMORY = 1

    def __init__(self, quotient_mdp, family, coloring, specification, obs_evaluator):
        self.obs_evaluator = obs_evaluator
        self.unfolded_state_to_observation = None

        # for each memory size (1 ... MAX_MEMORY) a choice mask enabling corresponding memory updates in the quotient mdp
        self.restricted_choices = None

        if self.MAX_MEMORY > 1:
            quotient_mdp, self.unfolded_state_to_observation, coloring, self.restricted_choices = self.unfold_quotient(
                quotient_mdp, self.state_to_observation, specification, self.MAX_MEMORY, family, coloring)
        else: # max memory is 1
            self.unfolded_state_to_observation = self.state_to_observation
            self.restricted_choices = {self.MAX_MEMORY: stormpy.storage.BitVector(quotient_mdp.nr_choices, True)}

        super().__init__(quotient_mdp = quotient_mdp, family = family, coloring = coloring, specification = specification)

        # The code below has been currently commented, because of the changes in observations.
        # Uncomment and fix according to new unfolded observations if needed.

        # # for each observation, a list of actions (indices) available
        # self.observation_to_actions = None
        # # POMDP manager used for unfolding the memory model into the quotient POMDP
        # self.fsc_unfolder = None

        # # identify actions available at each observation
        # self.observation_to_actions = [None] * self.num_observations
        # state_to_observation = self.state_to_observation
        # for state,available_actions in enumerate(self.state_to_actions):
        #     obs = state_to_observation[state]
        #     if self.observation_to_actions[obs] is not None:
        #         assert self.observation_to_actions[obs] == available_actions,\
        #             f"two states in observation cla ss {obs} differ in available actions"
        #         continue
        #     self.observation_to_actions[obs] = available_actions


    @property
    def num_observations(self):
        return self.obs_evaluator.num_obs_classes

    @property
    def state_to_observation(self):
        return self.obs_evaluator.state_to_obs_class

    def observation_is_trivial(self, obs):
        return len(self.observation_to_actions[obs])==1

    # construct the quotient for the family
    # the family is a intersection of policy tree family and memory family
    def build(self, family):
        # TODO decide which memory size to use
        memory_size = self.MAX_MEMORY

        member_selection_choices = self.coloring.selectCompatibleChoices(family.family)
        memory_selection_choices = self.restricted_choices[memory_size]
        choices = member_selection_choices & memory_selection_choices
        family.mdp = self.build_from_choice_mask(choices)
        family.selected_choices = choices
        family.mdp.family = family

    # restrict the options of all memory holes to only 0 ... max_memory
    # family - family of unfolded quotient
    # max_memory - maximum memory
    def restrict_family_to_memory(self, family, max_memory):
        # do I need parent info?
        # should I copy the family?
        restricted_family = family.copy()
        permited_options = [memory for memory in range(max_memory)]
        for hole, name in enumerate(family.hole_to_name):
            if name[0] == 'M': # it is a memory hole
                restricted_family.hole_set_options(hole, permited_options)

        return restricted_family

    def calculate_restricted_choices(self, family, coloring, max_memory):
        restricted_choices = {}

        for memory in range(1, max_memory):
            restricted_family = self.restrict_family_to_memory(family, memory)
            choices = coloring.selectCompatibleChoices(restricted_family.family)
            restricted_choices[memory] = choices

        choices = coloring.selectCompatibleChoices(family.family) # should be all '1's
        restricted_choices[max_memory] = choices

        return restricted_choices

    # unfold the quotient pomdp (represented as mdp + observation map) to maximum memory
    def unfold_quotient(self, quotient_mdp, state_to_observation, specification, max_memory, family, coloring):
        new_quotient_mdp = None
        new_state_to_observation = None
        new_coloring = None
        restricted_choices = None

        # unfolding is done in the __init__ of PomdpQuotient
        paynt.quotient.pomdp.PomdpQuotient.initial_memory_size = max_memory
        pomdp = self.pomdp_from_mdp(quotient_mdp, state_to_observation)
        pomdpQuotient = paynt.quotient.pomdp.PomdpQuotient(pomdp, specification, make_canonic=False)

        unfolded_quotient = pomdpQuotient.quotient_mdp
        state_prototypes = pomdpQuotient.pomdp_manager.state_prototype
        choice_prototypes = pomdpQuotient.pomdp_manager.row_prototype

        # Update state to observation mapping. Create new observations for states with memory>1
        state_memory = pomdpQuotient.pomdp_manager.state_memory
        observation_count = pomdpQuotient.observations
        new_state_to_observation = []
        for state in range(unfolded_quotient.nr_states):
            state_prototype = state_prototypes[state]
            observation = state_to_observation[state_prototype]
            memory = state_memory[state]
            new_observation = memory * observation_count + observation
            new_state_to_observation.append(new_observation)

        # Update choice labeling. Append the memory update to each choice label.
        # (choice labeling of a model cannot be modified. therefore a new model is created)
        transition_matrix = unfolded_quotient.transition_matrix
        state_labeling = unfolded_quotient.labeling
        reward_models = unfolded_quotient.reward_models
        components = stormpy.SparseModelComponents(
            transition_matrix=transition_matrix,
            state_labeling=state_labeling,
            reward_models=reward_models)

        choice_memory_update = pomdpQuotient.pomdp_manager.row_memory_option
        choice_labeling = stormpy.storage.ChoiceLabeling(unfolded_quotient.nr_choices)
        for choice in range(unfolded_quotient.nr_choices):
            memory_update = choice_memory_update[choice]
            choice_prototype = choice_prototypes[choice]
            labels = quotient_mdp.choice_labeling.get_labels_of_choice(choice_prototype)

            for label in labels:
                new_label = f'{label}_{memory_update}'
                if not choice_labeling.contains_label(new_label):
                    choice_labeling.add_label(new_label)
                choice_labeling.add_label_to_choice(new_label, choice)
        components.choice_labeling = choice_labeling

        new_quotient_mdp = stormpy.storage.SparseMdp(components)

        # Update coloring.
        choice_to_hole_options = coloring.getChoiceToAssignment()
        new_choice_to_hole_options = []
        for choice in range(new_quotient_mdp.nr_choices):
            choice_prototype = choice_prototypes[choice]
            hole_options = choice_to_hole_options[choice_prototype]
            new_choice_to_hole_options.append(hole_options)

        new_coloring = payntbind.synthesis.Coloring(
            family.family, new_quotient_mdp.nondeterministic_choice_indices, new_choice_to_hole_options)

        restricted_choices = self.calculate_restricted_choices(pomdpQuotient.family, pomdpQuotient.coloring, max_memory)

        return new_quotient_mdp, new_state_to_observation, new_coloring, restricted_choices


    def pomdp_from_mdp(self, mdp, observability_classes):
        transition_matrix = mdp.transition_matrix
        state_labeling = mdp.labeling
        reward_models = mdp.reward_models
        components = stormpy.SparseModelComponents(
            transition_matrix=transition_matrix,
            state_labeling=state_labeling,
            reward_models=reward_models)

        components.observability_classes=observability_classes

        if mdp.has_choice_labeling():
            components.choice_labeling = mdp.choice_labeling

        return stormpy.storage.SparsePomdp(components)

    def build_game_abstraction_solver(self, prop):
        return GameAbstractionSolver(self.quotient_mdp, self.unfolded_state_to_observation, prop, len(self.action_labels), self.choice_to_action)

    # mdp - SubMdp, represents one pomdp from the pomdp family
    # pomodp_quotient - quotient used for pomdp synthesis
    # assignment - result of pomdp synthesis
    def assignment_to_policy(self, mdp, pomdp_quotient, assignment):
        policy = self.empty_policy()

        choices = pomdp_quotient.coloring.selectCompatibleChoices(assignment.family)
        dtmc, mdp_state_map, mdp_choice_map = self.restrict_mdp(mdp.model, choices)

        for dtmc_state, mdp_state in enumerate(mdp_state_map):
            quotient_state = mdp.quotient_state_map[mdp_state]

            mdp_choice = mdp_choice_map[dtmc_state]
            quotient_choice = mdp.quotient_choice_map[mdp_choice]
            quotient_action = self.choice_to_action[quotient_choice]

            policy[quotient_state] = quotient_action

        return policy

################################################################################

    def build_pomdp(self, family):
        ''' Construct the sub-POMDP from the given hole assignment. '''
        assert family.size == 1, "expecting family of size 1"
        choices = self.coloring.selectCompatibleChoices(family.family)
        mdp,state_map,choice_map = self.restrict_quotient(choices)
        pomdp = self.obs_evaluator.add_observations_to_submdp(mdp,state_map)
        # for state,quotient_state in enumerate(state_map):
        #     assert pomdp.observations[state] == self.state_to_observation[quotient_state]
        # assert pomdp.nr_observations == self.num_observations
        return SubPomdp(pomdp,self,state_map,choice_map)


    def build_dtmc_sketch(self, fsc, negate_specification=True):
        '''
        Construct the family of DTMCs representing the execution of the given FSC in different environments.
        '''

        # create the product
        fsc.check_action_function(self.observation_to_actions)


        self.fsc_unfolder = payntbind.synthesis.FscUnfolder(
            self.quotient_mdp, self.state_to_observation, self.num_actions, self.choice_to_action
        )
        self.fsc_unfolder.apply_fsc(fsc.action_function, fsc.update_function)
        product = self.fsc_unfolder.product
        product_choice_to_choice = self.fsc_unfolder.product_choice_to_choice

        # the product inherits the design space
        product_family = self.family.copy()

        # the choices of the product inherit colors of the quotient
        product_choice_to_hole_options = []
        quotient_num_choces = self.quotient_mdp.nr_choices
        choice_to_hole_assignment = self.coloring.getChoiceToAssignment()
        for product_choice in range(product.nr_choices):
            choice = product_choice_to_choice[product_choice]
            if choice == quotient_num_choces:
                hole_options = []
            else:
                hole_options = [(hole,option) for hole,option in choice_to_hole_assignment[choice]]
            product_choice_to_hole_options.append(hole_options)
        product_coloring = payntbind.synthesis.Coloring(product_family.family, product.nondeterministic_choice_indices, product_choice_to_hole_options)

        # copy the specification
        product_specification = self.specification.copy()
        if negate_specification:
            product_specification = product_specification.negate()

        dtmc_sketch = paynt.quotient.quotient.Quotient(product, product_family, product_coloring, product_specification)
        return dtmc_sketch




### LEGACY CODE, NOT UP-TO-DATE ###

    def compute_qvalues_for_product_submdp(self, product_submdp : paynt.models.models.SubMdp):
        '''
        Given an MDP obtained after applying FSC to a family of POMDPs, compute for each state s, (reachable)
        memory node n, and action a, the Q-value Q((s,n),a).
        :note it is assumed that a randomized FSC was used
        :note it is assumed the provided DTMC sketch is the one obtained after the last unfolding, i.e. no other DTMC
            sketch was constructed afterwards
        :return a dictionary mapping (s,n,a) to Q((s,n),a)
        '''
        assert isinstance(self.product_pomdp_fsc, payntbind.synthesis.ProductPomdpRandomizedFsc), \
            "to compute Q-values, unfolder for randomized FSC must have been used"

        # model check
        prop = self.get_property()
        result = product_submdp.model_check_property(prop)
        product_state_sub_to_value = result.result.get_values()

        # map states of a sub-MDP to the states of the quotient-MDP to the state-memory pairs of the quotient POMDP
        # map states values to the resulting map
        product_state_to_state_memory_action = self.product_pomdp_fsc.product_state_to_state_memory_action.copy()
        state_memory_action_to_value = {}
        invalid_action = self.num_actions
        for product_state_sub in range(product_submdp.model.nr_states):
            product_state = product_submdp.quotient_state_map[product_state_sub]
            state,memory_action = product_state_to_state_memory_action[product_state]
            memory,action = memory_action
            if action == invalid_action:
                continue
            value = product_state_sub_to_value[product_state_sub]
            state_memory_action_to_value[(state,memory,action)] = value
        return state_memory_action_to_value


    def translate_path_to_trace(self, dtmc, path):
        invalid_choice = self.quotient_mdp.nr_choices
        trace = []
        for dtmc_state in path:
            product_choice = dtmc.quotient_choice_map[dtmc_state]
            choice = self.product_pomdp_fsc.product_choice_to_choice[product_choice]
            if choice == invalid_choice:
                # randomized FSC: we are in the intermediate state, move on to the next one
                continue

            product_state = dtmc.quotient_state_map[dtmc_state]
            state = self.product_pomdp_fsc.product_state_to_state[product_state]
            obs = self.state_to_observation[state]
            action = self.choice_to_action[choice]
            trace.append( (obs,action) )

        # in the last state, we remove the action since it was not actually used
        trace[-1] = (obs,None)

        # sanity check
        for obs,action in trace[:-1]:
            assert action in self.observation_to_actions[obs], "invalid trace"

        return trace


    def compute_witnessing_traces(self, dtmc_sketch, satisfying_assignment, num_traces, trace_max_length):
        '''
        Generate witnessing paths in the DTMC induced by the DTMC sketch and a satisfying assignment.
        If the set of target states is not reachable, then random traces are simulated
        :return a list of state-action pairs
        :note the method assumes that the DTMC sketch is the one that was last constructed using build_dtmc_sketch()
        '''
        fsc_is_randomized = isinstance(self.product_pomdp_fsc, payntbind.synthesis.ProductPomdpRandomizedFsc)
        if fsc_is_randomized:
            # double the trace length to account for intermediate states
            trace_max_length *= 2

        # logger.debug("constructing witnesses...")
        dtmc = dtmc_sketch.build_assignment(satisfying_assignment)

        # assuming a single probability reachability property
        spec = dtmc_sketch.specification
        assert spec.num_properties == 1, "expecting a single property"
        prop = spec.all_properties()[0]
        if prop.is_reward:
            logger.warning("WARNING: specification is a reward property, but generated traces \
                will be based on transition probabilities")

        target_label = self.extract_target_label()
        target_states = dtmc.model.labeling.get_states(target_label)

        traces = []
        if target_states.number_of_set_bits()==0:
            # target is not reachable: use Stormpy simulator to obtain some random walk in a DTMC
            logger.debug("target is not reachable, generating random traces...")
            simulator = stormpy.core._DiscreteTimeSparseModelSimulatorDouble(dtmc.model)
            for _ in range(num_traces):
                simulator.reset_to_initial_state()
                path = [simulator.get_current_state()]
                for _ in range(trace_max_length):
                    success = simulator.random_step()
                    if not success:
                        break
                    path.append(simulator.get_current_state())
                trace = self.translate_path_to_trace(dtmc,path)
                traces.append(trace)
        else:
            # target is reachable: use KSP
            logger.debug("target is reachable, computing shortest paths to...")
            if prop.minimizing:
                logger.debug("...target states")
                shortest_paths_generator = stormpy.utility.ShortestPathsGenerator(dtmc.model, target_label)
            else:
                logger.debug("...BSCCs from which target states are unreachable...")
                phi_states = stormpy.storage.BitVector(dtmc.model.nr_states,True)
                states0,_ = stormpy.core._compute_prob01states_double(dtmc.model,phi_states,target_states)
                shortest_paths_generator = stormpy.utility.ShortestPathsGenerator(dtmc.model, states0)
            for k in range(1,num_traces+1):
                path = shortest_paths_generator.get_path_as_list(k)
                path.reverse()
                trace = self.translate_path_to_trace(dtmc,path)
                traces.append(trace)
        return traces
