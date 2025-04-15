import payntbind
import stormpy

import logging
logger = logging.getLogger(__name__)

class IpomdpQuotient(): # todo derive from Quotient?

    def __init__(self, ipomdp, specification):
        self.ipomdp = ipomdp
        self.specification = specification

        self.game_abstraction = self.create_game_abstraction()

    def row_has_interval(self, row):
        return any(not entry.value().isPointInterval() for entry in row)

    # For a given row with intervals, generate actions corresponding to various combinations of interval bounds.
    # Every destination in the row will be once considered as a target.
    # For the target destination, the upper bound of the interval will be taken and for the rest, the lower bound.
    # So for a row with n destinations, n actions will be generated
    # Return: list of dictionaries [{destination : probability}, {... : ...}, ...]
    def generate_actions(self, row):
        assert sum([transition.value().lower() for transition in row]) <= 1.0, \
            'The sum of lower bounds of intervals of a single action must be less or equal to 1'
        assert sum([transition.value().upper() for transition in row]) >= 1.0, \
            'The sum of upper bounds of intervals of a single action must be greater or equal to 1'

        actions = []
        for target_transition in row:
            target_destination = target_transition.column
            action = {}
            for transition in row:
                destination = transition.column
                interval = transition.value()
                if destination == target_destination:
                    action[destination] = interval.upper()
                else:
                    action[destination] = interval.lower()

            assert sum(action.values()) == 1, \
                'For each row with intervals and each upper bound, the sum of this upper bound and all other lower bounds must be equal to 1'
            actions.append(action)

        assert len(actions) == len(row)
        return actions

    # add new state for each row with interval values
    # these rows will be replaced with a single transition leading to the corresponding new state with probability 1
    # the new states will have new action representing combinations of lower and upper bound of the interval
    # new states (and their actions) will be at the end of the matrix
    # IDEA use p1state,p2state,choice(action),destination,transition,probability or originalState,newState,row,column,entry,value?
    # IDEA return just new state count instead of new states
    def build_transition_matrix(self, transition_matrix):
        matrix_builder = stormpy.SparseMatrixBuilder(has_custom_row_grouping=True)

        original_state_count = transition_matrix.nr_columns
        # stores rows containing intervals that will be replaced with new states
        interval_rows = []
        new_state = original_state_count

        # original states
        for state in range(original_state_count):
            row_idxs = transition_matrix.get_rows_for_group(state)
            matrix_builder.new_row_group(row_idxs[0])
            for row_idx in row_idxs:
                row = transition_matrix.get_row(row_idx)
                if self.row_has_interval(row):
                    # add transition to new state
                    interval_rows.append(row)
                    matrix_builder.add_next_value(row_idx, new_state, 1)
                    new_state += 1
                else:
                    # copy original transitions
                    for transition in row:
                        col = transition.column
                        assert transition.value().lower() == transition.value().upper()
                        val = transition.value().lower()

                        matrix_builder.add_next_value(row_idx, col, val)

        # add new states
        row_idx = transition_matrix.nr_rows
        for row in interval_rows:
            matrix_builder.new_row_group(row_idx)
            actions = self.generate_actions(row)
            for action in actions:
                for col, val in action.items():
                    matrix_builder.add_next_value(row_idx, col, val)
                row_idx += 1


        # build matrix
        new_transition_matrix = matrix_builder.build()

        new_states = [state for state in range(original_state_count, new_state)]
        new_choices = [choice for choice in range(transition_matrix.nr_rows, new_transition_matrix.nr_rows)]
        return new_transition_matrix, new_states, new_choices

    def resize_bit_vector(self, bit_vector, new_size):
        new_bit_vector = stormpy.storage.BitVector(new_size, False)
        for bit in bit_vector:
            new_bit_vector[bit] = True

        return new_bit_vector

    def create_state_labeling(self, original_labeling, new_state_count):
        new_labeling = stormpy.storage.StateLabeling(new_state_count)
        for label in original_labeling.get_labels():
            new_labeling.add_label(label)
            original_states = original_labeling.get_states(label)
            new_states = self.resize_bit_vector(original_states, new_state_count)
            new_labeling.set_states(label, new_states)

        return new_labeling

    def create_choice_labeling(self, original_labeling, new_choice_count):
        new_labeling = stormpy.storage.ChoiceLabeling(new_choice_count)
        for label in original_labeling.get_labels():
            new_labeling.add_label(label)
            original_choices = original_labeling.get_choices(label)
            new_choices = self.resize_bit_vector(original_choices, new_choice_count)
            new_labeling.set_choices(label, new_choices)

        return new_labeling

    def create_reward_models(self, original_reward_models, p2_choice_count):
        new_reward_models = {}
        for name, original_reward_model in original_reward_models.items():
            assert original_reward_model.has_state_action_rewards and \
                not original_reward_model.has_state_rewards and \
                not original_reward_model.has_transition_rewards, \
                'Only state action rewards are supported.'
            original_state_action_rewards = original_reward_model.state_action_rewards

            assert all([interval.isPointInterval() for interval in original_state_action_rewards]), \
                'Interval rewards are not supported.'
            new_state_action_rewards = [interval.lower() for interval in original_state_action_rewards]
            new_state_action_rewards += [0 for choice in range(p2_choice_count)] # all actions of player 2 have reward 0

            new_reward_model = stormpy.SparseRewardModel(optional_state_action_reward_vector=new_state_action_rewards)
            new_reward_models[name] = new_reward_model

        return new_reward_models

    def create_state_player_indications(self, p1_state_count, p2_state_count):
        return [0 for p1s in range(p1_state_count)] + [1 for p2s in range(p2_state_count)]

    def create_observations(self, original_observations, p2_state_count):
        new_observation = max(original_observations) + 1
        return original_observations + [new_observation for state in range(p2_state_count)]


    def create_game_abstraction(self):
        transition_matrix, p2states, p2choices = self.build_transition_matrix(self.ipomdp.transition_matrix)
        new_state_count = transition_matrix.nr_columns
        new_choice_count = transition_matrix.nr_rows

        state_labeling = self.create_state_labeling(self.ipomdp.labeling, new_state_count)
        reward_models = self.create_reward_models(self.ipomdp.reward_models, len(p2choices))

        components = stormpy.SparseModelComponents(
            transition_matrix=transition_matrix,
            state_labeling=state_labeling,
            reward_models=reward_models)

        if self.ipomdp.has_choice_labeling():
            components.choice_labeling = self.create_choice_labeling(self.ipomdp.choice_labeling, new_choice_count)

        state_player_indications = self.create_state_player_indications(self.ipomdp.nr_states, len(p2states))
        assert len(state_player_indications) == new_state_count, 'Each state must belong to some player'
        components.state_player_indications = state_player_indications

        smg = stormpy.storage.SparseSmg(components)

        observations = self.create_observations(self.ipomdp.observations, len(p2states))
        assert len(observations) == new_state_count, 'Each state must have an observation'

        posmg = payntbind.synthesis.posmg_from_smg(smg, observations)

        return posmg


