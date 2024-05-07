from paynt.synthesizer.synthesizer import Synthesizer
from paynt.synthesizer.synthesizer_ar import SynthesizerAR

import os
import time
import multiprocessing

import logging
logger = logging.getLogger(__name__)


import cProfile, pstats

# global variables
# when a new process is spawned (forked), it will inherit these variables from the parent
quotient = None
profiler = None

# helper functions for family serialization
def family_to_hole_options(family):
    return [family.hole_options(hole) for hole in range(family.num_holes)]

def hole_options_to_family(hole_options):
    family = quotient.design_space.copy()
    for hole,options in enumerate(hole_options):
        family.hole_set_options(hole,options)
    return family


def solve_family(args):
    '''
    Build the quotient, analyze it and, if necessary, split into subfamilies.
    '''
    try:

        if args is None:
            pstats.Stats(profiler).sort_stats('tottime').print_stats(10)
            return

        hole_options, optimum = args
        # re-construct the family
        family = hole_options_to_family(hole_options)

        # synchronize optimum
        if optimum is not None:
            quotient.specification.optimality.optimum = optimum

        quotient.build(family)
        res = quotient.check_specification_for_mdp(family.mdp, family.constraint_indices)
        family.analysis_result = res
        improving_value = res.improving_value
        improving_assignment = res.improving_assignment
        if improving_assignment is not None:
            improving_assignment = family_to_hole_options(improving_assignment)
        
        subfamilies = []
        if res.can_improve:
            subfamilies = quotient.split(family, Synthesizer.incomplete_search)
            subfamilies = [ family_to_hole_options(family) for family in subfamilies ]

        return (family.mdp.states, improving_value, improving_assignment, subfamilies)

    except:
        logger.error("Worker sub-process encountered an error.")
        return None
        


class SynthesizerMultiCoreAR(SynthesizerAR):

    @property
    def method_name(self):
        return "AR (multicore)"

    def synthesize_one(self, family):

        satisfying_assignment = None
        families = [family]

        global quotient
        quotient = self.quotient
        profiling = False
        if profiling:
            global profiler
            profiler = cProfile.Profile()
            profiler.enable()

        # create a pool of processes
        # by default, os.cpu_count() processes will be spawned
        with multiprocessing.Pool(
            # processes=1
        ) as pool:
            
            while families:

                # get current optimum
                optimum = None
                if self.quotient.specification.has_optimality:
                    optimum = self.quotient.specification.optimality.optimum

                # work with some number of families
                # print("submitting ", len(families), " families")

                split = os.cpu_count() * 1
                input_families = families[-split:]
                input_families_size = sum([family.size for family in input_families])
                remaining_families = families[:-split]
                input_families = [family_to_hole_options(family) for family in input_families]
                
                inputs = zip(input_families, [optimum] * len(input_families))

                results = pool.map(solve_family, inputs)
                # results = pool.imap_unordered(solve_family, inputs, chunksize=10)
                # results = pool.map(solve_batch, inputs)

                # process the results
                new_families = []
                for r in results:
                    if r is None:
                        logger.error("Worker sub-process encountered an error.")
                        exit()
                    mdp_states, improving_value, improving_assignment, subfamilies_hole_options = r
                    self.stat.iteration_mdp(mdp_states)

                    if improving_value is not None:
                        if self.quotient.specification.optimality.improves_optimum(improving_value):
                            self.quotient.specification.optimality.update_optimum(improving_value)
                            improving_assignment = hole_options_to_family(improving_assignment)
                            satisfying_assignment = improving_assignment

                    subfamilies = [hole_options_to_family(hole_options) for hole_options in subfamilies_hole_options]
                    new_families += subfamilies

                new_families_size = sum([family.size for family in new_families])
                self.explored += input_families_size-new_families_size

                families = remaining_families + new_families

            if profiling:
                pool.apply(solve_family, (None,))

        if profiling:
            pstats.Stats(profiler).sort_stats('tottime').print_stats(10)
        return satisfying_assignment
