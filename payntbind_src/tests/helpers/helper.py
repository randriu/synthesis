import os
import stormpy
import stormpy.examples
import stormpy.examples.files

from paynt.examples import paynt_models_dir

stormpy_example_dir = stormpy.examples.files.testfile_dir


def get_stormpy_example_path(*paths):
    return os.path.join(stormpy_example_dir, *paths)

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

def get_sketch_paths(project_path, sketch_name="sketch.templ", props_name="sketch.props"):
    return os.path.join(paynt_models_dir, project_path, sketch_name), os.path.join(paynt_models_dir, project_path, props_name)

def read_first_line(filepath):
    with open(filepath, 'r') as file:
        first_line = file.readline().strip()
    return first_line