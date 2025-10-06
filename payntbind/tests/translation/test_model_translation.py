import stormpy
import payntbind

from helpers.helper import get_stormpy_example_path, get_builder_options


class TestModelTranslation:

    def test_add_dont_care_action(self):
        # setup
        program = stormpy.parse_prism_program(get_stormpy_example_path("mdp", "tiny_rewards.nm"), prism_compat=True)
        program = program.label_unlabelled_commands({}) # this is something we always do in PAYNT but without it this will throw segfault!
        mdp = stormpy.build_sparse_model_with_options(program, get_builder_options())
        state_bitvector = stormpy.BitVector(mdp.nr_states, True)

        # test
        mdp_with_dont_care_action = payntbind.synthesis.addDontCareAction(mdp, state_bitvector)

        # assert
        assert mdp_with_dont_care_action.choice_labeling.contains_label("__random__")
        assert mdp_with_dont_care_action.nr_states == mdp.nr_states
        assert mdp_with_dont_care_action.nr_choices == mdp.nr_choices + mdp.nr_states

        nci = mdp_with_dont_care_action.nondeterministic_choice_indices.copy()
        reward_model = mdp_with_dont_care_action.reward_models['']
        for state in range(mdp_with_dont_care_action.nr_states):
            probs = [0.0,0.0,0.0]
            rews = 0.0
            num_non_dont_care_choices = nci[state + 1] - nci[state] - 1
            for choice in range(nci[state], nci[state + 1]):
                if "__random__" in mdp_with_dont_care_action.choice_labeling.get_labels_of_choice(choice):
                    for entry in mdp_with_dont_care_action.transition_matrix.get_row(choice):
                        state = entry.column
                        prob = entry.value()
                        assert prob == probs[state] / num_non_dont_care_choices
                        assert reward_model.state_action_rewards[choice] == rews / num_non_dont_care_choices 
                else:
                    for entry in mdp_with_dont_care_action.transition_matrix.get_row(choice):
                        state = entry.column
                        prob = entry.value()
                        probs[state] += prob
                        rews += reward_model.state_action_rewards[choice]

    def test_add_dont_care_action_exact(self):
        # setup
        program = stormpy.parse_prism_program(get_stormpy_example_path("mdp", "tiny_rewards.nm"), prism_compat=True)
        program = program.label_unlabelled_commands({}) # this is something we always do in PAYNT but without it this will throw segfault!
        mdp = stormpy.build_sparse_exact_model_with_options(program, get_builder_options())
        state_bitvector = stormpy.BitVector(mdp.nr_states, True)

        # test
        mdp_with_dont_care_action = payntbind.synthesis.addDontCareActionExact(mdp, state_bitvector)

        # assert
        assert mdp_with_dont_care_action.choice_labeling.contains_label("__random__")
        assert mdp_with_dont_care_action.nr_states == mdp.nr_states
        assert mdp_with_dont_care_action.nr_choices == mdp.nr_choices + mdp.nr_states

        nci = mdp_with_dont_care_action.nondeterministic_choice_indices.copy()
        reward_model = mdp_with_dont_care_action.reward_models['']
        for state in range(mdp_with_dont_care_action.nr_states):
            probs = [0,0,0]
            rews = 0
            num_non_dont_care_choices = nci[state + 1] - nci[state] - 1
            for choice in range(nci[state], nci[state + 1]):
                if "__random__" in mdp_with_dont_care_action.choice_labeling.get_labels_of_choice(choice):
                    for entry in mdp_with_dont_care_action.transition_matrix.get_row(choice):
                        state = entry.column
                        prob = entry.value()
                        assert prob == probs[state] / num_non_dont_care_choices
                        assert reward_model.state_action_rewards[choice] == rews / num_non_dont_care_choices 
                else:
                    for entry in mdp_with_dont_care_action.transition_matrix.get_row(choice):
                        state = entry.column
                        prob = entry.value()
                        probs[state] += prob
                        rews += reward_model.state_action_rewards[choice]

    # TODO add more tests
    # TODO also add test for exact models

