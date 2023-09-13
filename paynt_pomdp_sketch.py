# using PAYNT for POMDP sketches

import paynt.cli
import paynt.parser.sketch

import os

# enable PAYNT logging
paynt.cli.setup_logger()

# load the sketch
project_path="models/pomdp/sketches/obstacles"
project_path = os.path.abspath(project_path)
sketch_path = os.path.join(project_path, "sketch.templ")
properties_path = os.path.join(project_path, "sketch.props")

pomdp_sketch = paynt.parser.sketch.Sketch.load_sketch(sketch_path, properties_path)
print("design space:\n", pomdp_sketch.design_space)
print("number of holes: ", pomdp_sketch.design_space.num_holes)
print("design space size: {} members".format(pomdp_sketch.design_space.size))

# fix some hole options
hole_options = [[hole.options[0]] for hole in pomdp_sketch.design_space]
hole_assignment = pomdp_sketch.design_space.assume_options_copy(hole_options)
print("hole assignment: ", hole_assignment)

# build the POMDP
pomdp = pomdp_sketch.build_pomdp(hole_assignment)
