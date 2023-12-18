from .statistic import Statistic
from .synthesizer import Synthesizer
from .synthesizer_ar import SynthesizerAR

import multiprocessing as mp
import os
import time

import logging
logger = logging.getLogger(__name__)


# global variable containing the quotient
# when a process is spawned (forked), it will inherit this quotient from the parent
quotient = None

import cProfile, pstats
profile = None


def solve_family(args):
    '''
    Build the quotient, analyze it and, if necessary, split into subfamilies.
    '''

    try:

        family, optimum = args

        if family is None:
            pstats.Stats(profile).sort_stats('tottime').print_stats(50)
            return

        # synchronize optimum
        if optimum is not None:
            quotient.specification.optimality.optimum = optimum

        quotient.build(family)
        # self.stat.iteration_mdp(family.mdp.states)

        res = family.mdp.check_specification(quotient.specification, constraint_indices = family.constraint_indices, short_evaluation = True)
        family.analysis_result = res
        
        subfamilies = []
        if family.analysis_result.can_improve:
            subfamilies = quotient.split(family, Synthesizer.incomplete_search)
            # remove parent info since Property is not pickleable
            for subfamily in subfamilies:
                subfamily.parent_info = None

        return ([family.mdp.states], family.analysis_result.improving_value, family.analysis_result.improving_assignment, subfamilies)

    except:
        logger.error("Worker sub-process encountered an error.")
        return None
        


class SynthesizerMultiCoreAR(SynthesizerAR):

    @property
    def method_name(self):
        return "AR (concurrent)"

    def synthesize_one(self, family):

        self.quotient.discarded = 0

        satisfying_assignment = None
        families = [family]

        start_time = time.perf_counter()

        global quotient
        quotient = self.quotient
        global profile
        profile = cProfile.Profile()
        # profile.enable()

        # create a pool of processes
        # by default, os.cpu_count() processes will be spawned
        with mp.Pool(
            # processes = 1
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
                    mdp_states, improving_value, improving_assignment, subfamilies = r
                        
                    for entry in mdp_states:
                        self.stat.iteration_mdp(entry)

                    if improving_value is not None:
                        if self.quotient.specification.optimality.improves_optimum(improving_value):
                            self.quotient.specification.optimality.update_optimum(improving_value)
                            satisfying_assignment = improving_assignment
                    
                    new_families += subfamilies

                new_families_size = sum([family.size for family in new_families])
                self.explored += input_families_size-new_families_size

                families = remaining_families + new_families

            # pool.apply(solve_family, ((None,None),))


        finish_time = time.perf_counter()
        total_time = round(finish_time-start_time, 3)
        
        logger.info("Synthesis finished in {} s (real time).".format(total_time))

        # pstats.Stats(profile).sort_stats('tottime').print_stats(10)

        return satisfying_assignment



def solve_batch(args):
    '''
    When an undecidable family is encountered, the subfamilies are processed
    up to a limit specified below.
    '''

    try:

        family, optimum = args

        # synchronize optimum
        if optimum is not None:
            quotient.specification.optimality.optimum = optimum

        mdp_states = []
        improving_value = None
        improving_assignment = None
        subfamilies = [family]

        # analyze the batch
        limit = 1
        for x in range(limit):

            if not subfamilies:
                break

            family = subfamilies.pop(-1)
            quotient.build(family)
            res = family.mdp.check_specification(quotient.specification, constraint_indices = family.constraint_indices, short_evaluation = True)
            family.analysis_result = res
            mdp_states.append(family.mdp.states)
            
            if family.analysis_result.can_improve:
                subfamilies += quotient.split(family, Synthesizer.incomplete_search)

            if family.analysis_result.improving_value is not None:
                break

        
        # remove parent info since Property is not pickleable
        for subfamily in subfamilies:
            subfamily.parent_info = None

        return (mdp_states, family.analysis_result.improving_value, family.analysis_result.improving_assignment, subfamilies)

    except:
        print("meaningful error message")
        return None