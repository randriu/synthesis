# using Paynt for POMDP sketches

import paynt.cli
import paynt.parser.sketch
import paynt.quotient.pomdp_family
import paynt.synthesizer.synthesizer_onebyone
import paynt.synthesizer.synthesizer_ar

import os
import random
import cProfile, pstats

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

def compute_qvalues(pomdp_sketch, dtmc_sketch):
    print()
    subfamily = dtmc_sketch.design_space
    dtmc_sketch.build(subfamily)
    print("computing Q-values...")
    qvalues = pomdp_sketch.compute_qvalues_for_product_submdp(subfamily.mdp)
    print("Q-values computed")

def evaluate_all(dtmc_sketch):
    ''' To each singleton environment, assign a value corresponding to the specification satisfiability. '''
    print()
    synthesizer = paynt.synthesizer.synthesizer_onebyone.SynthesizerOneByOne(dtmc_sketch)
    family_to_value = synthesizer.evaluate(keep_value_only=True)

    # pick the worst family
    import numpy
    values = numpy.array([value for family,value in family_to_value])
    if dtmc_sketch.get_property().minimizing:
        worst_index = values.argmax()
    else:
        worst_index = values.argmin()

    worst_family,worst_value = family_to_value[worst_index]
    print("the worst family has value {}, printing the family below:".format(worst_value))
    print(worst_family)

def synthesize_worst(dtmc_sketch):
    '''Identify assignment with the worst specification satisfiability.'''
    print()
    dtmc_sketch.specification = dtmc_sketch.specification.negate()
    dtmc_sketch.specification.optimality.epsilon = 0.05
    synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR(dtmc_sketch)
    worst_assignment = synthesizer.synthesize(return_all=True)


profiling = False

if profiling:
    profiler = cProfile.Profile()
    profiler.enable()


# random.seed(11)

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
hole_assignment = pomdp_sketch.design_space.pick_any()

# investigate this hole assignment and return an FSC
fsc = investigate_hole_assignment(pomdp_sketch, hole_assignment)

# apply this FSC to a POMDP sketch, obtaining a DTMC sketch
dtmc_sketch = pomdp_sketch.build_dtmc_sketch(fsc)

# compute_qvalues(pomdp_sketch, dtmc_sketch)
# evaluate_all(dtmc_sketch)
# synthesize_worst(dtmc_sketch)

if profiling:
    profiler.disable()
    stats = profiler.create_stats()
    pstats.Stats(profiler).sort_stats('tottime').print_stats(20)
