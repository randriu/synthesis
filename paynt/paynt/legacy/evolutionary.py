
import stormpy
from .synthesizer import Synthesizer, DTMC
from ..sketch import DesignSpace

import numpy
import random

import logging
logger = logging.getLogger(__name__)

class EvolutionaryDesignSpace(DesignSpace):

    def random_assignment(self):
        return [random.choice(self[hole]) for hole in self.holes]
    
    def random_population(self, number):
        return [self.random_assignment() for i in range(number)]

# class Population(list):
    
    # def evaluate
            
class EvolutionarySynthesizer(Synthesizer):
    """Integrated checker."""

    def fitness_function(self, results):
        sat = [1 if formula.satisfied(results[index]) else 0 for index,formula in enumerate(self.formulae)]
        return numpy.sum(sat)

    def evaluate_assignment(self, assignment):
        dtmc = DTMC(self.sketch, assignment)
        self.stat.iteration_dtmc(dtmc.states)
        results = [dtmc.model_check(index) for index in range(len(self.formulae))]
        # print(results)
        return self.fitness_function(results)

    def evaluate_population(self, population):
        return [self.evaluate_assignment(a) for a in population]    

    def select_mates(self, population, fitness, mate_number):
        mates = []
        pop_size = len(population)
        for i in range(mate_number):
            x = random.randint(0,pop_size-1)
            y = random.randint(0,pop_size-1)
            w = x if fitness[x] > fitness[y] else y
            mates.append(w) 
        return mates

    def run(self):
        self.stat.start()
        satisfying_assignment = None

        self.sketch.design_space = EvolutionaryDesignSpace(self.sketch.design_space)
        pop = self.sketch.design_space.random_population(10)
        fit = self.evaluate_population(pop)
        mates = self.select_mates(pop, fit, 10)
        print(mates)
        exit()

        # create initial population
        for assignment in self.sketch.design_space.all_assignments():
            
            self.stat.pruned(1)

        optimal_value = self.sketch.optimality_formula.optimal_value if self.has_optimality_formula else None
        self.stat.finished(satisfying_assignment,optimal_value)
        
