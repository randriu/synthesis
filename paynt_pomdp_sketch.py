# using Paynt for POMDP sketches

import paynt.cli
import paynt.parser.sketch
import paynt.quotient.pomdp_family
import paynt.synthesizer.synthesizer_onebyone
import paynt.synthesizer.synthesizer_ar

import os
import random

def load_sketch(project_path):
    project_path = os.path.abspath(project_path)
    sketch_path = os.path.join(project_path, "sketch.templ")
    properties_path = os.path.join(project_path, "sketch.props")    
    pomdp_sketch = paynt.parser.sketch.Sketch.load_sketch(sketch_path, properties_path)

    target_label = pomdp_sketch.get_property().get_target_label()
    target_states = pomdp_sketch.quotient_mdp.labeling.get_states(target_label)
    for state in pomdp_sketch.quotient_mdp.labeling.get_states("deadlock"):
        assert state in target_states, "have deadlock in a non-target state {}".format(state)

    return pomdp_sketch


def investigate_hole_assignment(pomdp_sketch, hole_assignment):
    print("investigating hole assignment: ", hole_assignment)
    pomdp = pomdp_sketch.build_pomdp(hole_assignment)

    # create a random k-FSC
    fsc_is_deterministic = False
    num_nodes = 3
    fsc = paynt.quotient.pomdp_family.FSC(num_nodes, pomdp_sketch.num_observations, fsc_is_deterministic)
    fsc.fill_trivial_actions(pomdp_sketch.observation_to_actions)
    # fsc.fill_trivial_updates(pomdp_sketch.observation_to_actions)
    for node in range(num_nodes):
        for obs in range(pomdp_sketch.num_observations):
            available_actions = pomdp_sketch.observation_to_actions[obs]
            if fsc.is_deterministic:
                # random deterministic FSC
                fsc.action_function[node][obs] = random.choice(available_actions)
            else:
                # random randomized FSC
                num_samples = min(len(available_actions),node+1)
                sampled_actions = random.sample(available_actions,num_samples)
                prob = 1/num_samples
                randomized_action_selection = {action:prob for action in sampled_actions}
                fsc.action_function[node][obs] = randomized_action_selection
            
            fsc.update_function[node][obs] = random.randrange(num_nodes)

    return fsc


# random.seed(42)

# enable PAYNT logging
paynt.cli.setup_logger()

# load sketch
project_path="models/pomdp/sketches/obstacles"
# project_path="models/pomdp/sketches/avoid"
pomdp_sketch = load_sketch(project_path)
print("specification: ", pomdp_sketch.specification)
print("design space:\n", pomdp_sketch.design_space)
print("number of holes: ", pomdp_sketch.design_space.num_holes)
print("design space size: {} members".format(pomdp_sketch.design_space.size))

# fix some hole options
hole_options = [[hole.options[0]] for hole in pomdp_sketch.design_space]
hole_assignment = pomdp_sketch.design_space.assume_options_copy(hole_options)

# investigate this hole assignment and return an FSC
fsc = investigate_hole_assignment(pomdp_sketch, hole_assignment)

# apply this FSC to a POMDP sketch, obtaining a DTMC sketch
dtmc_sketch = pomdp_sketch.build_dtmc_sketch(fsc)
# qvalues = pomdp_sketch.compute_qvalues_for_fsc(dtmc_sketch)

# to each (sub-family of) environment(s), assign a value corresponding to the minimum specification satisfiability
synthesizer = paynt.synthesizer.synthesizer_onebyone.SynthesizerOneByOne(dtmc_sketch)
family_to_value = synthesizer.evaluate_all()

# pick the worst environment
# TODO
worst_family,worst_value = family_to_value[0]

print("the worst value has value {}, printing the worst family below:".format(worst_value))
print(worst_family)
