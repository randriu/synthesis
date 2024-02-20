
def example():
    pomdp = self.pomdp
    
    # the sub-POMDP builder can be created only once and then re-used, although this only saves allocation time
    # since nothing can be pre-computed
    sub_pomdp_builder = payntbind.synthesis.SubPomdpBuilder(pomdp)
    
    import random
            
    # create a trivial belief corresponding to the original initial state
    initial_state = pomdp.initial_states[0]
    # belief is a mapping from states to probabilities
    # using map (dictionary) to make sure that each state occurs exactly once
    initial_belief = { initial_state:1 }
    sub_pomdp = sub_pomdp_builder.start_from_belief(initial_belief)
    print(sub_pomdp)
    
    # note that the new initial state has a fresh observation
    assert sub_pomdp.nr_observations == pomdp.nr_observations+1
    new_initial_state = sub_pomdp.initial_states[0]
    assert sub_pomdp.observations[new_initial_state] == pomdp.nr_observations
    
    # also note that observation valuations are NOT translated: it's not trivial to implement and
    # I don't believe we need those
    # the observation indexing is not changed, so original observation valuations can be used
    assert not sub_pomdp.has_observation_valuations()
    
    # otherwise, the observations should be unchanged
    new_observation_states = [0 for obs in range(sub_pomdp.nr_observations)]
    for state in range(sub_pomdp.nr_states):
        new_observation_states[sub_pomdp.observations[state]] += 1
    for obs in range(pomdp.nr_observations):
        assert self.observation_states[obs] == new_observation_states[obs]
    
    # create a random belief with 3 states
    observations = [obs for obs,num_states in enumerate(self.observation_states) if num_states>=3]
    obs = random.choice(observations)
    states = [state for state in range(pomdp.nr_states) if pomdp.observations[state] == obs]
    initial_states = random.sample(states,3)
    initial_belief = { initial_states[0]:0.5, initial_states[1]:0.3, initial_states[2]:0.2 }
    sub_pomdp = sub_pomdp_builder.start_from_belief(initial_belief)
    print(sub_pomdp)

    sub_pomdp = sub_pomdp_builder.start_from_belief(belief)
    # mapping of states of the sub-POMDP to the states of the full POMDP
    state_sub_to_full = sub_pomdp_builder.state_sub_to_full
    # fresh states are mapped to an invalid value equal to the number of states in the full POMDP
    assert state_sub_to_full[sub_pomdp.initial_states[0]] == pomdp_quotient.pomdp.nr_states



import stormpy
import payntbind

import paynt.parser.sketch
import paynt.quotient.pomdp
import paynt.synthesizer.synthesizer_ar

import os


if __name__ == "__main__":
    project_path="models/pomdp/storm-integration/maze-alex"
    project_path = os.path.abspath(project_path)
    sketch_path = os.path.join(project_path, "sketch.templ")
    properties_path = os.path.join(project_path, "sketch.props")

    pomdp_quotient = paynt.parser.sketch.Sketch.load_sketch(sketch_path, properties_path)

    sub_pomdp_builder = payntbind.synthesis.SubPomdpBuilder(pomdp_quotient.pomdp)
    belief = {3: 0.1700638862954427, 2: 0.8299361137045573}

    sub_pomdp = sub_pomdp_builder.start_from_belief(belief)
    sub_pomdp_quotient = paynt.quotient.pomdp.PomdpQuotient(sub_pomdp, pomdp_quotient.specification)
    synthesizer = paynt.synthesizer.synthesizer_ar.SynthesizerAR(sub_pomdp_quotient)
    family = sub_pomdp_quotient.design_space

    assignment = synthesizer.synthesize(family)