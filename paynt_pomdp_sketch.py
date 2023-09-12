# using PAYNT for POMDP sketches

import paynt.cli
import paynt.parser.sketch

import os

# enable PAYNT logging
paynt.cli.setup_logger()

# load sketch
project_path="/home/roman/phd/synthesis/models/pomdp-sketch"
project_path = os.path.abspath(project_path)
sketch_path = os.path.join(project_path, "sketch.templ")
properties_path = os.path.join(project_path, "sketch.props")
pomdp_sketch = paynt.parser.sketch.Sketch.load_sketch(sketch_path, properties_path)


