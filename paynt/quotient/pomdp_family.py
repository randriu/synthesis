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
    def __init__(self, prop, quotient_num_actions, choice_to_action):
        self.quotient_num_actions = quotient_num_actions
        self.choice_to_action = choice_to_action

        self.solution_value = None
        self.solution_state_values = None
        self.solution_state_to_player1_action = None
        self.solution_state_to_quotient_choice = None

        self.posmg_specification = self.create_posmg_specification(prop)

    # warning: target state(s) in sketch.props must be specified using label (not formula),
    # because property is parsed without prism context
    # e.g. P>=0.95 [F "goal"] not P>=0.95 [F goal]
    def create_posmg_specification(self, prop):
        formula_str = prop.formula.__str__() # contains optimality property
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


    def solve(self, quotient_choice_mask, player1_maximizing, palyer2_maximizing):
        # pomdp representing the game
        # from self.pomdp and quotient_choice_mask. Add states for player2
        # Roman will implement this method
        pomdp_game, state_player_indications = None

        posmg = payntbind.synthesis.create_posmg(pomdp_game, state_player_indications)

        posmgQuotient = paynt.quotient.posmg.PosmgQuotient(posmg, self.posmg_specification)

        synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR(posmgQuotient)
        # for fsc synthesis (we probably dont want)
        # synthesizer = paynt.synthesizer.synthesizer_posmg.SynthesizerPosmg(quotient)

        assignment = synthesizer.synthesize(keep_optimum=True, print_stats=False)

        self.solution_value = synthesizer.best_assignment_value

        self.solution_state_values = None # todo

        self.solution_state_to_quotient_choice = None # todo

        self.solution_state_to_player1_action = self.calculate_state_to_player1_action(
                                                    self.solution_state_to_quotient_choice,
                                                    self.choice_to_action,
                                                    self.quotient_num_actions)




class PomdpFamilyQuotient(paynt.quotient.mdp_family.MdpFamilyQuotient):

    def __init__(self, quotient_mdp, family, coloring, specification, obs_evaluator):
        super().__init__(quotient_mdp = quotient_mdp, family = family, coloring = coloring, specification = specification)
        self.obs_evaluator = obs_evaluator

        # for each observation, a list of actions (indices) available
        self.observation_to_actions = None
        # POMDP manager used for unfolding the memory model into the quotient POMDP
        self.fsc_unfolder = None

        # identify actions available at each observation
        self.observation_to_actions = [None] * self.num_observations
        state_to_observation = self.state_to_observation
        for state,available_actions in enumerate(self.state_to_actions):
            obs = state_to_observation[state]
            if self.observation_to_actions[obs] is not None:
                assert self.observation_to_actions[obs] == available_actions,\
                    f"two states in observation cla ss {obs} differ in available actions"
                continue
            self.observation_to_actions[obs] = available_actions

        # quotient pomdp representing the whole family of pomdps
        self.pomdp = self.create_pomdp()


    @property
    def num_observations(self):
        return self.obs_evaluator.num_obs_classes

    @property
    def state_to_observation(self):
        return self.obs_evaluator.state_to_obs_class

    def observation_is_trivial(self, obs):
        return len(self.observation_to_actions[obs])==1

    # build pomdp model from mdp and state->observation map
    def create_pomdp(self):
        mdp = self.quotient_mdp
        observability_classes = self.state_to_observation

        transition_matrix = mdp.transition_matrix
        state_labeling = mdp.labeling
        components = stormpy.SparseModelComponents(
            transition_matrix=transition_matrix,
            state_labeling=state_labeling)

        components.observability_classes=observability_classes

        if mdp.has_choice_labeling():
            components.choice_labeling = mdp.choice_labeling

        return stormpy.storage.SparsePomdp(components)

    def build_game_abstraction_solver(self, prop):
        return GameAbstractionSolver(prop, len(self.action_labels), self.choice_to_action)

################################################################################

    def build_pomdp(self, family):
        ''' Construct the sub-POMDP from the given hole assignment. '''
        assert family.size == 1, "expecting family of size 1"

        choices = self.coloring.selectCompatibleChoices(family.family)
        mdp,state_map,choice_map = self.restrict_quotient(choices)
        pomdp = self.obs_evaluator.add_observations_to_submdp(mdp,state_map)
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
