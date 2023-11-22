# using PAYNT for POMDP sketches

import paynt.cli
import paynt.parser.sketch

import paynt.quotient.pomdp_family
import paynt.synthesizer.synthesizer_all

import os
import random

def load_sketch(project_path):
    project_path = os.path.abspath(project_path)
    sketch_path = os.path.join(project_path, "sketch.templ")
    properties_path = os.path.join(project_path, "sketch.props")    
    pomdp_sketch = paynt.parser.sketch.Sketch.load_sketch(sketch_path, properties_path)
    return pomdp_sketch


def investigate_hole_assignment(pomdp_sketch, hole_assignment, fsc_is_deterministic):
    print("investigating hole assignment: ", hole_assignment)
    pomdp = pomdp_sketch.build_pomdp(hole_assignment)
    state_is_absorbing = pomdp_sketch.identify_absorbing_states(pomdp.model)
    print("trivial observations: ", [obs for obs in range(pomdp_sketch.num_observations) if pomdp_sketch.observation_is_trivial(obs)])

    # return a random k-FSC
    num_nodes = 3
    fsc = paynt.quotient.pomdp_family.FSC(num_nodes, pomdp_sketch.num_observations, fsc_is_deterministic)
    fsc.fill_trivial_actions(pomdp_sketch.observation_to_actions)
    # fsc.fill_trivial_updates(pomdp_sketch.observation_to_actions)
    for node in range(num_nodes):
        for obs in range(pomdp_sketch.num_observations):
            # random deterministic FSC
            if fsc.is_deterministic:
                fsc.action_function[node][obs] = random.choice(pomdp_sketch.observation_to_actions[obs])
            else:
                # random randomized FSC
                available_actions = pomdp_sketch.observation_to_actions[obs]
                num_samples = min(len(available_actions),node+1)
                sampled_actions = random.sample(available_actions,num_samples)
                prob = 1/num_samples
                randomized_action_selection = {action:prob for action in sampled_actions}
                fsc.action_function[node][obs] = randomized_action_selection
            
            fsc.update_function[node][obs] = random.randrange(num_nodes)

    return fsc


# enable PAYNT logging
# random.seed(42)
paynt.cli.setup_logger()

# need to specify beforehand whether FSCs will be deterministic or not
# since we initialize the FSC unfolder beforehand
fsc_is_deterministic = False

# load sketch
project_path="models/pomdp/sketches/obstacles"
# project_path="models/pomdp/sketches/avoid"
pomdp_sketch = load_sketch(project_path)
pomdp_sketch.initialize_fsc_unfolder(fsc_is_deterministic)
print("specification: ", pomdp_sketch.specification)
print("design space:\n", pomdp_sketch.design_space)
print("number of holes: ", pomdp_sketch.design_space.num_holes)
print("design space size: {} members".format(pomdp_sketch.design_space.size))

# fix some hole options
hole_options = [[hole.options[0]] for hole in pomdp_sketch.design_space]
hole_assignment = pomdp_sketch.design_space.assume_options_copy(hole_options)

# investigate this hole assignment and return an FSC
fsc = investigate_hole_assignment(pomdp_sketch, hole_assignment, fsc_is_deterministic)

# investigate this FSC and obtain a list of families of POMDPs for which this FSC is violating
# apply FSC to a PODMP sketch, obtaining a DTMC sketch
# we are negating the specification since we are looking for violating DTMCs
dtmc_sketch = pomdp_sketch.build_dtmc_sketch(fsc, negate_specification=True)
synthesizer = paynt.synthesizer.synthesizer_all.SynthesizerAll(dtmc_sketch)
violating_families = synthesizer.synthesize()
if not violating_families:
    print("all POMDPs were satisfied")
    exit()

print("found {} violating families, printing below:".format(len(violating_families)))
print([str(family) for family in violating_families])

# pick 1 assignment and generate violating traces
# pick first
# violating_assignment = violating_families[0].pick_any()
# pick random assignment from random family
violating_assignment = random.choice(violating_families).pick_random()

num_violating_traces = 5
trace_max_length = 11   # length of a trace in a DTMC with unreachable target
violating_traces = pomdp_sketch.compute_witnessing_traces(dtmc_sketch,violating_assignment,num_violating_traces,trace_max_length)
print("constructed {} violating traces, printing below:".format(len(violating_traces)))
for trace in violating_traces:
    print(trace)

