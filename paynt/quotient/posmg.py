import payntbind
import stormpy

import paynt.quotient.quotient
import paynt.quotient.pomdp

import paynt.verification.property

import logging
logger = logging.getLogger(__name__)


class PosmgQuotient(paynt.quotient.quotient.Quotient):

    # implicit size for POSMG unfolding
    initial_memory_size = 1

    # the index of optimizing player
    optimizing_player = 0

    def __init__(self, posmg, specification):
        super().__init__(specification = specification)


        # defualt POSMG model
        self.posmg = posmg

        # unfolded POSMG
        self.quotient_mdp = None
        self.design_space = None
        self.coloring = None

        # number of actions available at each optimizing player observation
        self.actions_at_opt_player_observation = None
        # action labels corresponding to ^
        self.action_labels_at_opt_player_observation = None
        # action labels at each posmg state
        self.action_labels_at_posmg_state = None
        # number of observations of optimizing player
        self.opt_player_observation_count = self.posmg.get_p0_observation_count()
        # for each optimizing player observation, number of states associated with it
        self.opt_player_observation_states = None
        # number of memory states allocated to each optimizing player observation
        self.opt_player_observation_memory_size = None
        # POSMG manager
        self.posmg_manager = None

        # for each optimizing player observation, a list of action holes
        self.opt_player_observation_action_holes = None
        # for each optimizing player observation, a list of memory holes
        self.opt_player_observation_memory_holes = None
        # for each hole, an indication whether this is an action or a memory hole
        self.is_action_hole = None

        # state player indications
        state_players = self.posmg.get_state_player_indications()
        # all observation
        state_obs = self.posmg.get_observations()


        # initialize posmg manager
        self.posmg_manager = payntbind.synthesis.PosmgManager(self.posmg, self.optimizing_player)

        # optimizing player observations
        self.opt_player_observations = self.posmg_manager.get_observation_mapping()


        # compute actions available at each optimizing player observation
        self.actions_at_opt_player_observation = {obs:0 for obs in self.opt_player_observations}
        for state in range(self.posmg.nr_states):
            if state_players[state] == self.optimizing_player:
                obs = state_obs[state]
                if self.actions_at_opt_player_observation[obs] != 0:
                    assert self.posmg.get_nr_available_actions(state) == self.actions_at_opt_player_observation[obs]
                    continue
                self.actions_at_opt_player_observation[obs] = self.posmg.get_nr_available_actions(state)

        # collect lables of action available for each prototype
        self.action_labels_at_posmg_state = [[] for state in range(self.posmg.nr_states)]
        for state in range(self.posmg.nr_states):
            if self.action_labels_at_posmg_state[state] != []:
                continue
            actions = self.posmg.get_nr_available_actions(state)
            for offset in range(actions):
                choice = self.posmg.get_choice_index(state, offset)
                labels = self.posmg.choice_labeling.get_labels_of_choice(choice)
                assert len(labels) <= 1, "expected at most 1 label"
                if len(labels) == 0:
                    label = self.EMPTY_LABEL
                else:
                    label = list(labels)[0]
                self.action_labels_at_posmg_state[state].append(label)

        # collect labels of actions available at each observation
        self.action_labels_at_opt_player_observation = {}
        for state in range(self.posmg.nr_states):
            if state_players[state] == self.optimizing_player:
                obs = state_obs[state]
                labels = self.action_labels_at_posmg_state[state]
                self.action_labels_at_opt_player_observation[obs] = labels

        # mark perfect observations
        #self.opt_player_observation_states = [0 for _ in range(self.opt_player_observation_count)]
        self.opt_player_observation_states = {obs:0 for obs in self.opt_player_observations}
        for state in range(self.posmg.nr_states):
            if state_players[state] == self.optimizing_player:
                obs = state_obs[state]
                self.opt_player_observation_states[obs] += 1

        self.set_imperfect_memory_size(PosmgQuotient.initial_memory_size)
        self.current_memory_size = PosmgQuotient.initial_memory_size



    def set_manager_memory_vector(self):
        for obs, memory in self.opt_player_observation_memory_size.items():
            self.posmg_manager.set_observation_memory_size(obs, memory)

    def set_imperfect_memory_size(self, memory_size):
        self.opt_player_observation_memory_size = { obs:(memory_size if obs_states > 1 else 1) for obs, obs_states in self.opt_player_observation_states.items() }

        self.set_manager_memory_vector()
        self.unfold_memory()



    def create_hole_name(self, player, value, mem, is_action_hole):
        category = "A" if is_action_hole else "M"
        # obs_label = self.observation_labels[obs] # TODO maybe we will have this in the future
        if player == self.optimizing_player:
            return "{}(P{},O{},M{})".format(category,player,value,mem)
        else:
            return "{}(P{},S{},M{})".format(category,player,value,mem)

    # version where each state of non optimising players has it's own action hole
    def create_coloring(self):

        # create holes
        family = paynt.family.family.Family()
        # self.observation_action_holes = [] # TODO maybe needed?
        # self.observation_memory_holes = [] # TODO maybe needed?
        # self.is_action_hole = [] # TODO maybe needed?

        for opt_player_obs in self.opt_player_observations:

            # action holes
            hole_indices = []
            num_actions = self.actions_at_opt_player_observation[opt_player_obs]
            if num_actions > 1:
                option_labels = self.action_labels_at_opt_player_observation[opt_player_obs]
                for mem in range(self.opt_player_observation_memory_size[opt_player_obs]):
                    hole_indices.append(family.num_holes)
                    name = self.create_hole_name(self.optimizing_player,opt_player_obs,mem,True)
                    family.add_hole(name,option_labels)
                    # self.is_action_hole.append(True)
            # self.observation_action_holes.append(hole_indices)

            # memory holes
            hole_indices = []
            num_updates = self.posmg_manager.max_successor_memory_size[opt_player_obs]
            if num_updates > 1:
                option_labels = [str(x) for x in range(num_updates)]
                for mem in range(self.opt_player_observation_memory_size[opt_player_obs]):
                    name = self.create_hole_name(self.optimizing_player,opt_player_obs,mem,False)
                    hole_indices.append(family.num_holes)
                    family.add_hole(name,option_labels)
                    # self.is_action_hole.append(False)
            # self.observation_memory_holes.append(hole_indices)

        for state in range(self.quotient_mdp.nr_states):
            quotient_state_player_indication = self.posmg_manager.get_state_player_indications()
            if quotient_state_player_indication[state] != self.optimizing_player:
                num_actions = self.posmg_manager.get_action_count(state)
                if num_actions > 1:
                    posmg_state = self.posmg_manager.state_prototype[state]
                    mem = self.posmg_manager.state_memory[state]
                    option_labels = self.action_labels_at_posmg_state[posmg_state]
                    hole_indices.append(family.num_holes)
                    name = self.create_hole_name(quotient_state_player_indication[state],posmg_state,mem,True)
                    family.add_hole(name,option_labels)

        # create the coloring
        assert self.posmg_manager.num_holes == family.num_holes
        num_holes = family.num_holes
        choice_action_hole = self.posmg_manager.row_action_hole
        choice_memory_hole = self.posmg_manager.row_memory_hole
        choice_action_option = self.posmg_manager.row_action_option
        choice_memory_option = self.posmg_manager.row_memory_option
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


    def unfold_memory(self):

        # reset attributes
        self.quotient_mdp = None
        self.coloring = None
        self.hole_option_to_actions = None

        # self.observation_action_holes = None
        # self.observation_memory_holes = None
        # self.is_action_hole = None

        logger.debug("unfolding {}-FSC template into one-sided POSMG...".format(max(self.opt_player_observation_memory_size.values())))
        self.quotient_mdp = self.posmg_manager.construct_mdp()
        self.choice_destinations = payntbind.synthesis.computeChoiceDestinations(self.quotient_mdp)
        logger.debug(f"constructed quotient MDP having {self.quotient_mdp.nr_states} states and {self.quotient_mdp.nr_choices} actions.")

        family, choice_to_hole_options = self.create_coloring()

        self.coloring = payntbind.synthesis.Coloring(family.family, self.quotient_mdp.nondeterministic_choice_indices, choice_to_hole_options)

        # to each hole-option pair a list of actions colored by this combination
        self.hole_option_to_actions = [[] for hole in range(family.num_holes)]
        for hole in range(family.num_holes):
            self.hole_option_to_actions[hole] = [[] for option in family.hole_options(hole)]
        for choice in range(self.quotient_mdp.nr_choices):
            for hole,option in choice_to_hole_options[choice]:
                self.hole_option_to_actions[hole][option].append(choice)

        self.design_space = paynt.family.family.DesignSpace(family)


    def check_specification(self, mdp, constraint_indices=None, double_check=True):
        '''
        Check specification.
        :param specification containing constraints and optimality
        :param constraint_indices a selection of property indices to investigate (default: all)
        :param double_check if True, the new optimum is double-checked
        '''
        quotient_player_indications = self.posmg_manager.get_state_player_indications()

        transition_matrix = mdp.model.transition_matrix
        state_labeling = mdp.model.labeling
        components = stormpy.SparseModelComponents(
            transition_matrix=transition_matrix,
            state_labeling=state_labeling)

        if mdp.model.has_choice_labeling():
            components.choice_labeling = mdp.model.choice_labeling

        state_player_inidcations = []
        for state in range(mdp.states):
            quotient_state = mdp.quotient_state_map[state]
            player = quotient_player_indications[quotient_state]
            state_player_inidcations.append(player)
        components.state_player_indications = state_player_inidcations

        smg = stormpy.storage.SparseSmg(components)

        # check constraints
        if constraint_indices is None:
            constraint_indices = range(len(self.specification.constraints))
        results = [None for _ in self.specification.constraints]
        # TODO ADD IMPLEMENTATION FOR CONSTRAINTS
        # for index in constraint_indices:
        #     constraint = self.specification.constraints[index]
        #     constraint_str = constraint.property.raw_formula.__str__()
        #     game_formula_str = f"<<{self.optimizing_player}>> " + constraint_str
        #     formulas = stormpy.parse_properties(game_formula_str)
        #     result = paynt.verification.property_result.MdpPropertyResult(constraint)

        #     # check primary direction
        #     # result.primary = mdp.model_check_property(constraint)

        #     smg_result = payntbind.synthesis.smg_model_checking(smg, formulas[0].raw_formula,
        #                                                     only_initial_states=False, set_produce_schedulers=True,
        #                                                     env=paynt.verification.property.Property.environment)
        #     value = smg_result.at(smg.initial_states[0])
        #     result.primary = paynt.verification.property_result.PropertyResult(opt, smg_result, value)

        #     # no need to check secondary direction if primary direction yields UNSAT
        #     if not result.primary.sat:
        #         result.sat = False
        #     else:
        #         # check secondary direction
        #         result.secondary = mdp.model_check_property(constraint, alt=True)
        #         if mdp.is_deterministic and result.primary.value != result.secondary.value:
        #             logger.warning("WARNING: model is deterministic but min<max")
        #         if result.secondary.sat:
        #             result.sat = True

        #     # primary direction is SAT
        #     if result.sat is None:
        #         # check if the primary scheduler is consistent
        #         result.primary_selection,consistent = self.scheduler_is_consistent(mdp, constraint, result.primary.result)
        #         if not consistent:
        #             result.primary_choice_values,result.primary_expected_visits,result.primary_scores = \
        #                 self.scheduler_get_quantitative_values(mdp, constraint, result.primary.result, result.primary_selection)

        #     results[index] = result
        #     if result.sat is False:
        #         break
        constraints_result = paynt.verification.property_result.ConstraintsResult(results)

        # check optimality
        optimality_result = None
        # if self.specification.has_optimality and not constraints_result.sat is False:
        if self.specification.has_optimality:
            opt = self.specification.optimality
            opt_str = opt.property.raw_formula.__str__()
            game_formula_str = f"<<{self.optimizing_player}>> " + opt_str
            formulas = stormpy.parse_properties(game_formula_str)
            result = paynt.verification.property_result.MdpOptimalityResult(opt)

            smg_result = payntbind.synthesis.smg_model_checking(smg, formulas[0].raw_formula,
                                                            only_initial_states=False, set_produce_schedulers=True,
                                                            env=paynt.verification.property.Property.environment)
            value = smg_result.at(smg.initial_states[0])
            result.primary = paynt.verification.property_result.PropertyResult(opt, smg_result, value)

            if not result.primary.improves_optimum:
                # OPT <= LB
                result.can_improve = False
            else:
                # LB < OPT
                # check if LB is tight
                result.primary_selection,consistent = self.scheduler_is_consistent(mdp, opt, result.primary.result)
                if not consistent:
                    result.primary_choice_values,result.primary_expected_visits,result.primary_scores = \
                        self.scheduler_get_quantitative_values(mdp, opt, result.primary.result, result.primary_selection)
                if consistent:
                    # LB is tight and LB < OPT
                    result.improving_assignment = mdp.design_space.assume_options_copy(result.primary_selection)
                    result.can_improve = False
                else:
                    result.can_improve = True
            optimality_result = result

            if optimality_result.improving_assignment is not None and double_check:
                optimality_result.improving_assignment, optimality_result.improving_value = self.double_check_assignment(optimality_result.improving_assignment)
        return paynt.verification.property_result.MdpSpecificationResult(constraints_result, optimality_result)

