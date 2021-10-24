import stormpy

from .property import Property
from .holes import CombinationColoring

import itertools
from collections import defaultdict

import logging
logger = logging.getLogger(__name__)

class JaniUnfolder():

    def __init__(self, sketch):
        logger.debug("Constructing JANI program...")
        
        # pack properties
        properties = [p.property for p in sketch.properties]
        if sketch.optimality_property is not None:
            properties += [sketch.optimality_property.property]

        # construct jani
        jani, new_properties = sketch.prism.to_jani(properties)

        # unpack properties
        properties = new_properties
        opt = None
        eps = None
        if sketch.optimality_property is not None:
            properties = new_properties[:-1]
            opt = new_properties[-1]
            eps = sketch.optimality_property.epsilon

        # re-wrap properties
        self.properties = [Property(p) for p in properties]
        self.optimality_property = Property(opt, eps) if opt is not None else None
        self.design_space = sketch.design_space

        # unfold holes in the program
        self.unfold_jani(jani)

    # Unfold holes in the jani program
    def unfold_jani(self, jani):
        self.open_constants = [c for c in jani.constants if not c.defined]
        assert len(self.open_constants) == self.design_space.hole_count
        self.expr_to_const = {c.expression_variable : c for c in self.open_constants}

        self.combination_coloring = CombinationColoring(self.design_space)
        
        jani_program = stormpy.JaniModel(jani)
        new_automata = dict()
        for aut_index, automaton in enumerate(jani_program.automata):
            if not self.automaton_has_holes(automaton):
                continue
            logger.debug(f"Reconstructing automaton {automaton.name} ...")
            new_aut = stormpy.storage.JaniAutomaton(automaton.name, automaton.location_variable)
            [new_aut.add_location(loc) for loc in automaton.locations]
            [new_aut.add_initial_location(idx) for idx in automaton.initial_location_indices]
            [new_aut.variables.add_variable(var) for var in automaton.variables]
            for edge in automaton.edges:
                for new_edge in self.construct_edges(edge):
                    new_aut.add_edge(new_edge)

            logger.debug(f"Reconstructed automaton {new_aut.name}.")
            new_automata[aut_index] = new_aut
        for aut_index, aut in new_automata.items():
            jani_program.replace_automaton(aut_index, aut)
        [jani_program.remove_constant(c.name) for c in self.open_constants]        
        logger.debug(f"Number of colors: {self.combination_coloring.colors}")

        jani_program.set_model_type(stormpy.JaniModelType.MDP)
        jani_program.finalize()
        jani_program.check_valid()

        filename = "output.jani"
        logger.debug(f"Writing unfolded program to {filename}")
        with open(filename, "w") as f:
            f.write(str(jani_program))
        logger.debug("Done writing file.")

        # color_to_edge_indices = dict()
        # for aut_index, automaton in enumerate(jani_program.automata):
        #     for edge_index, edge in enumerate(automaton.edges):
        #         new_list = color_to_edge_indices.get(edge.color, stormpy.FlatSet())
        #         new_list.insert(jani_program.encode_automaton_and_edge_index(aut_index, edge_index))
        #         color_to_edge_indices[edge.color] = new_list
        # logger.debug(",".join([f'{k}: {v}' for k, v in color_to_edge_indices.items()]))

        color_to_edge_indices = defaultdict(stormpy.FlatSet)
        for aut_index, automaton in enumerate(jani_program.automata):
            for edge_index, edge in enumerate(automaton.edges):
                global_index = jani_program.encode_automaton_and_edge_index(aut_index, edge_index)
                color_to_edge_indices[edge.color].insert(global_index)

        self.jani_unfolded = jani_program
        self.color_to_edge_indices = color_to_edge_indices

        # map choice origins to colors (maybe do it on the sketch level?)
        self.choice_origin_to_color = defaultdict(int)
        for automaton in jani_program.automata:
            automaton_index = jani_program.get_automaton_index(automaton.name)
            for edge_index, edge in enumerate(automaton.edges):
                if edge.color != 0:
                    self.choice_origin_to_color[jani_program.encode_automaton_and_edge_index(automaton_index, edge_index)] = edge.color

    def automaton_has_holes(self, automaton):
        variables = {hole.expression_variable for hole in self.open_constants}
        for edge_index, e in enumerate(automaton.edges):
            if e.guard.contains_variable(variables):
                return True
            for dest in e.destinations:
                if dest.probability.contains_variable(variables):
                    return True
                for assignment in dest.assignments:
                    if assignment.expression.contains_variable(variables):
                        return True
        return False
    

    def construct_edges(self, edge):
        
        # relevant holes in guard
        variables = edge.template_edge.guard.get_variables()
        relevant_guard = {v for k,v in self.expr_to_const.items() if k in variables}

        # relevant holes in probabilities
        variables = set().union(*[d.probability.get_variables() for d in edge.destinations])
        relevant_probs = {v for k,v in self.expr_to_const.items() if k in variables}

        # relevant holes in updates
        variables = set()
        for dest in edge.template_edge.destinations:
            for assignment in dest.assignments:
                variables |= assignment.expression.get_variables()
        relevant_updates = {v for k,v in self.expr_to_const.items() if k in variables}
        
        # all relevant holes
        relevant_holes = relevant_guard | relevant_probs | relevant_updates

        new_edges = []
        if not relevant_holes:
            # copy without unfolding
            new_edges.append(self.construct_edge(edge))

        else:
            # unfold all combinations
            combinations = [
                (range(len(self.design_space[c.name])) if c in relevant_holes else [None])
                for c in self.open_constants
            ]
            for combination in itertools.product(*combinations):
                substitution = {
                    c.expression_variable: self.design_space[c.name][v]
                    for c,v in zip(self.open_constants, combination) if v is not None
                }
                new_edge = self.construct_edge(edge,substitution)
                new_edge.color = self.combination_coloring.get_or_make_color(combination)
                new_edges.append(new_edge)
        return new_edges

    def construct_edge(self, edge, substitution = None):

        guard = stormpy.Expression(edge.template_edge.guard)
        dests = [(d.target_location_index, d.probability) for d in edge.destinations]

        if substitution is not None:
            guard = guard.substitute(substitution)
            dests = [(t, p.substitute(substitution)) for (t,p) in dests]

        templ_edge = stormpy.storage.JaniTemplateEdge(guard)
        for templ_edge_dest in edge.template_edge.destinations:
            assignments = templ_edge_dest.assignments.clone()
            if substitution is not None:
                assignments.substitute(substitution)
            templ_edge.add_destination(stormpy.storage.JaniTemplateEdgeDestination(assignments))

        new_edge = stormpy.storage.JaniEdge(
            edge.source_location_index, edge.action_index, edge.rate, templ_edge, dests
        )
            

        return new_edge