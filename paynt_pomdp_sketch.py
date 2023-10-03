# using PAYNT for POMDP sketches

import paynt.cli
import paynt.parser.sketch

import paynt.quotient.pomdp_family

import os

def load_sketch(project_path):
    project_path = os.path.abspath(project_path)
    sketch_path = os.path.join(project_path, "sketch.templ")
    properties_path = os.path.join(project_path, "sketch.props")    
    pomdp_sketch = paynt.parser.sketch.Sketch.load_sketch(sketch_path, properties_path)
    return pomdp_sketch

def investigate_hole_assignment(pomdp_sketch, hole_assignment):
    print("investigating hole assignment: ", hole_assignment)
    pomdp = pomdp_sketch.build_pomdp(hole_assignment)

    # return an arbitrary k-FSC
    actions_at_observation = pomdp_sketch.compute_actions_at_observation(pomdp)
    k = 2
    fsc = paynt.quotient.pomdp_family.FSC(k, pomdp.nr_observations)
    for node in range(k):
        for obs in range(pomdp.nr_observations):
            fsc.action_function[node][obs] = actions_at_observation[obs]-1
            fsc.update_function[node][obs] = k-1
    return fsc


# enable PAYNT logging
paynt.cli.setup_logger()

# load sketch
project_path="models/pomdp/sketches/obstacles"
pomdp_sketch = load_sketch(project_path)
print("design space:\n", pomdp_sketch.design_space)
print("number of holes: ", pomdp_sketch.design_space.num_holes)
print("design space size: {} members".format(pomdp_sketch.design_space.size))

# fix some hole options
hole_options = [[hole.options[0]] for hole in pomdp_sketch.design_space]
hole_assignment = pomdp_sketch.design_space.assume_options_copy(hole_options)

# investigate this hole assignment
fsc = investigate_hole_assignment(pomdp_sketch, hole_assignment)
print(fsc)


