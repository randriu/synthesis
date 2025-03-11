import paynt.verification.property
import payntbind
import stormpy

import pytest
from helpers.helper import get_sketch_paths, read_first_line
from math import inf


class TestSmgModelchecker:

    def test_simple_game_min(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/simple-game', props_name='circle-min.props')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=False,
                                                    set_produce_schedulers=True,
                                                    env=paynt.verification.property.Property.environment)
        # assert
        assert result._quantitative
        assert result.result_for_all_states
        assert result.get_values() == pytest.approx([21, 20, 0])

        assert result.has_scheduler
        assert result.scheduler.deterministic
        assert result.scheduler.memoryless
        assert result.scheduler.get_choice(0).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(1).get_deterministic_choice() == 1
        assert result.scheduler.get_choice(2).get_deterministic_choice() == 0

    def test_simple_game_max(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/simple-game', props_name='circle-max.props')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=False,
                                                    set_produce_schedulers=True,
                                                    env=paynt.verification.property.Property.environment)
        # assert
        assert result._quantitative
        assert result.result_for_all_states
        assert result.get_values() == pytest.approx([12, 10, 0])

        assert result.has_scheduler
        assert result.scheduler.deterministic
        assert result.scheduler.memoryless
        assert result.scheduler.get_choice(0).get_deterministic_choice() == 1
        assert result.scheduler.get_choice(1).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(2).get_deterministic_choice() == 0

    def test_simple_game_circle_ge(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/simple-game', props_name='circle-ge.props')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=False,
                                                    set_produce_schedulers=True,
                                                    env=paynt.verification.property.Property.environment)
        # assert
        assert result._qualitative
        assert result.result_for_all_states
        assert not result.at(0)
        assert not result.at(1)
        assert not result.at(2)

    def test_simple_game_circle_le(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/simple-game', props_name='circle-le.props')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=False,
                                                    set_produce_schedulers=True,
                                                    env=paynt.verification.property.Property.environment)
        # assert
        assert result._qualitative
        assert result.result_for_all_states
        assert not result.at(0)
        assert not result.at(1)
        assert result.at(2)

    def test_simple_game_square_ge(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/simple-game', props_name='square-ge.props')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=False,
                                                    set_produce_schedulers=True,
                                                    env=paynt.verification.property.Property.environment)
        # assert
        assert result._qualitative
        assert result.result_for_all_states
        assert result.at(0)
        assert result.at(1)
        assert not result.at(2)

    def test_simple_game_square_le(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/simple-game', props_name='square-le.props')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=False,
                                                    set_produce_schedulers=True,
                                                    env=paynt.verification.property.Property.environment)
        # assert
        assert result._qualitative
        assert result.result_for_all_states
        assert result.at(0)
        assert result.at(1)
        assert result.at(2)

    def test_distribution_min(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/distribution', props_name='circle-min.props')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=False,
                                                    set_produce_schedulers=True,
                                                    env=paynt.verification.property.Property.environment)
        # assert
        assert result._quantitative
        assert result.result_for_all_states
        assert result.get_values() == pytest.approx([3, 2, 0])

        assert result.has_scheduler
        assert result.scheduler.deterministic
        assert result.scheduler.memoryless
        assert result.scheduler.get_choice(0).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(1).get_deterministic_choice() == 0

    def test_distribution_max(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/distribution', props_name='circle-max.props')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=False,
                                                    set_produce_schedulers=True,
                                                    env=paynt.verification.property.Property.environment)
        # assert
        assert result._quantitative
        assert result.result_for_all_states
        assert result.get_values() == pytest.approx([3, 2, 0])

        assert result.has_scheduler
        assert result.scheduler.deterministic
        assert result.scheduler.memoryless
        assert result.scheduler.get_choice(0).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(1).get_deterministic_choice() == 0

    def test_medium_game_min(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/medium-game', props_name='circle-min.props')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=False,
                                                    set_produce_schedulers=True,
                                                    env=paynt.verification.property.Property.environment)

        # assert
        assert result._quantitative
        assert result.result_for_all_states
        assert result.get_values() == pytest.approx([2.5, 1.5, 0, inf])

        assert result.has_scheduler
        assert result.scheduler.deterministic
        assert result.scheduler.memoryless
        assert result.scheduler.get_choice(0).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(1).get_deterministic_choice() == 2
        assert result.scheduler.get_choice(2).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(3).get_deterministic_choice() == 0

    def test_medium_game_max(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/medium-game', props_name='circle-max.props')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=False,
                                                    set_produce_schedulers=True,
                                                    env=paynt.verification.property.Property.environment)

        # assert
        assert result._quantitative
        assert result.result_for_all_states
        assert result.get_values() == pytest.approx([inf, inf, 0, inf])

        assert result.has_scheduler
        assert result.scheduler.deterministic
        assert result.scheduler.memoryless
        assert result.scheduler.get_choice(0).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(1).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(2).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(3).get_deterministic_choice() == 0

    def test_zero_reward_end_component_min(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/zero-reward-end-component', props_name='circle-min.props')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=False,
                                                    set_produce_schedulers=True,
                                                    env=paynt.verification.property.Property.environment)

        # assert
        assert result.get_values() == pytest.approx([2, 1, 1, 0])

        assert result.scheduler.get_choice(0).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(1).get_deterministic_choice() == 1
        assert result.scheduler.get_choice(2).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(3).get_deterministic_choice() == 0

    def test_zero_reward_end_component_max(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/zero-reward-end-component', props_name='circle-max.props')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=False,
                                                    set_produce_schedulers=True,
                                                    env=paynt.verification.property.Property.environment)

        # assert
        assert result.get_values() == pytest.approx([inf, inf, inf, 0])

        assert result.scheduler.get_choice(0).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(1).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(2).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(3).get_deterministic_choice() == 0

    def test_self_loop_min(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/self-loop', props_name='circle-min.props')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=False,
                                                    set_produce_schedulers=True,
                                                    env=paynt.verification.property.Property.environment)

        # assert
        assert result.get_values() == pytest.approx([inf, inf, 0])

        assert result.scheduler.get_choice(0).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(1).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(2).get_deterministic_choice() == 0

    def test_self_loop_max(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/self-loop', props_name='circle-max.props')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=False,
                                                    set_produce_schedulers=True,
                                                    env=paynt.verification.property.Property.environment)

        # assert
        assert result.get_values() == pytest.approx([2, 1, 0])

        assert result.scheduler.get_choice(0).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(1).get_deterministic_choice() == 1
        assert result.scheduler.get_choice(2).get_deterministic_choice() == 0

    def test_no_scheduler(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/simple-game', props_name='circle-min.props')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=False,
                                                    set_produce_schedulers=False,
                                                    env=paynt.verification.property.Property.environment)

        # assert
        assert result.get_values() == pytest.approx([21, 20, 0])

        assert not result.has_scheduler


    def test_only_initial_states(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/simple-game', props_name='circle-min.props')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=False,
                                                    set_produce_schedulers=True,
                                                    env=paynt.verification.property.Property.environment)
        # assert
        assert result._quantitative
        assert result.result_for_all_states
        assert result.get_values() == pytest.approx([21, 20, 0])

        assert result.has_scheduler
        assert result.scheduler.deterministic
        assert result.scheduler.memoryless
        assert result.scheduler.get_choice(0).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(1).get_deterministic_choice() == 1
        assert result.scheduler.get_choice(2).get_deterministic_choice() == 0

    def test_only_initial_states(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/medium-game', props_name='circle-max.props')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=True,
                                                    set_produce_schedulers=True,
                                                    env=paynt.verification.property.Property.environment)
        # assert
        assert result._quantitative
        assert result.result_for_all_states # other states will be filled anyway
        assert result.get_values() == pytest.approx([inf, inf, 0, inf])

        assert result.has_scheduler
        assert result.scheduler.deterministic
        assert result.scheduler.memoryless
        assert result.scheduler.get_choice(0).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(1).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(2).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(3).get_deterministic_choice() == 0


    # the behavious is weird, but is the same as in storm and prism-games
    # in state 2, the maximizing player chooses an action that does not guarantee maximal reward
    # is is probably a bug in computing optimal choices in infinity states
    def test_weird_inf_state_choice(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/weird-inf-state-choice', props_name='circle-min.props')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=False,
                                                    set_produce_schedulers=True,
                                                    env=paynt.verification.property.Property.environment)
        # assert
        assert result._quantitative
        assert result.result_for_all_states
        assert result.get_values() == pytest.approx([inf, inf, inf, 0])

        assert result.has_scheduler
        assert result.scheduler.deterministic
        assert result.scheduler.memoryless
        assert result.scheduler.get_choice(0).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(1).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(2).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(3).get_deterministic_choice() == 0

    # model taken from prism examples
    def test_coins(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/coins')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=False,
                                                    set_produce_schedulers=True,
                                                    env=paynt.verification.property.Property.environment)
        # assert
        assert result._quantitative
        assert result.result_for_all_states
        assert result.get_values() == pytest.approx([inf, 5, inf, 5, 5, inf, inf, 5, inf, inf, 5, 5, inf, inf, 5, 0, inf, inf, 0])
        # note: When obtaining state values from prism with -exportvector option, the values might be in a different order than expected.
        #    This is because the states are permuted in ConstructModel.java 497

        assert result.has_scheduler
        assert result.scheduler.deterministic
        assert result.scheduler.memoryless

    def test_probability(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/probabilities')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=False,
                                                    set_produce_schedulers=True,
                                                    env=paynt.verification.property.Property.environment)
        # assert
        assert result._quantitative
        assert result.result_for_all_states
        assert result.get_values() == pytest.approx([0.5, 0.5, 1, 0])

        assert result.has_scheduler
        assert result.scheduler.deterministic
        assert result.scheduler.memoryless
        assert result.scheduler.get_choice(0).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(1).get_deterministic_choice() == 1
        assert result.scheduler.get_choice(2).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(3).get_deterministic_choice() == 0

    def test_probability_mec_exit(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/mec-exit')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=False,
                                                    set_produce_schedulers=True,
                                                    env=paynt.verification.property.Property.environment)
        # assert
        assert result._quantitative
        assert result.result_for_all_states
        assert result.get_values() == pytest.approx([0.5, 0.5, 0, 1, 0.5, 0.5])

        assert result.has_scheduler
        assert result.scheduler.deterministic
        assert result.scheduler.memoryless
        assert result.scheduler.get_choice(0).get_deterministic_choice() == 2
        assert result.scheduler.get_choice(1).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(2).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(3).get_deterministic_choice() == 0
        assert result.scheduler.get_choice(4).get_deterministic_choice() == 1
        assert result.scheduler.get_choice(5).get_deterministic_choice() == 0


    def test_probability_circle_ge(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/probability-qualitative', props_name='circle-ge.props')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=False,
                                                    set_produce_schedulers=True,
                                                    env=paynt.verification.property.Property.environment)
        # assert
        assert result._qualitative
        assert result.result_for_all_states
        assert not result.at(0)
        assert not result.at(1)
        assert result.at(2)

    def test_probability_circle_le(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/probability-qualitative', props_name='circle-le.props')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=False,
                                                    set_produce_schedulers=True,
                                                    env=paynt.verification.property.Property.environment)
        # assert
        assert result._qualitative
        assert result.result_for_all_states
        assert not result.at(0)
        assert not result.at(1)
        assert not result.at(2)

    def test_probability_square_ge(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/probability-qualitative', props_name='square-ge.props')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=False,
                                                    set_produce_schedulers=True,
                                                    env=paynt.verification.property.Property.environment)
        # assert
        assert result._qualitative
        assert result.result_for_all_states
        assert result.at(0)
        assert result.at(1)
        assert result.at(2)

    def test_probability_square_le(self):
        # setup
        smg_file, props_file = get_sketch_paths('smg/probability-qualitative', props_name='square-le.props')
        prop = read_first_line(props_file)
        program = stormpy.parse_prism_program(smg_file)
        properties = stormpy.parse_properties_for_prism_program(prop, program, None)
        model = stormpy.build_model(program, properties)
        paynt.verification.property.Property.initialize()

        # test
        result = payntbind.synthesis.model_check_smg(model, properties[0].raw_formula,
                                                    only_initial_states=False,
                                                    set_produce_schedulers=True,
                                                    env=paynt.verification.property.Property.environment)
        # assert
        assert result._qualitative
        assert result.result_for_all_states
        assert result.at(0)
        assert result.at(1)
        assert not result.at(2)