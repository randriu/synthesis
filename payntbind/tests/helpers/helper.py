import os
import stormpy
import stormpy.examples
import stormpy.examples.files

example_dir = stormpy.examples.files.testfile_dir


def get_example_path(*paths):
    return os.path.join(example_dir, *paths)

def get_builder_options():
    builder_options = stormpy.BuilderOptions()
    builder_options.set_build_state_valuations(True)
    builder_options.set_build_with_choice_origins(True)
    builder_options.set_build_all_labels(True)
    builder_options.set_build_choice_labels(True)
    builder_options.set_add_overlapping_guards_label(True)
    builder_options.set_build_observation_valuations(True)
    builder_options.set_build_all_reward_models(True)
    return builder_options
