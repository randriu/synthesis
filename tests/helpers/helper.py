import os
import stormpy
import stormpy.examples
import stormpy.examples.files

from paynt.examples import paynt_models_dir

stormpy_example_dir = stormpy.examples.files.testfile_dir


def get_stormpy_example_path(*paths):
    return os.path.join(stormpy_example_dir, *paths)

def get_sketch_paths(project_path, sketch_name="sketch.templ", props_name="sketch.props"):
    return os.path.join(paynt_models_dir, project_path, sketch_name), os.path.join(paynt_models_dir, project_path, props_name)
