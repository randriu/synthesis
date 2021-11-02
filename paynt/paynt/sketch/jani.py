import stormpy

from .property import Property, OptimalityProperty
from .holes import CombinationColoring

import itertools
from collections import defaultdict

import logging
logger = logging.getLogger(__name__)

class JaniUnfolder():
    ''' Unfolder of hole combinations into JANI program. '''

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

        # when translating PRISM to JANI, some properties may change their
        # atoms, so we need to re-wrap all properties
        self.properties = [Property(p) for p in properties]
        self.optimality_property = OptimalityProperty(opt, eps) if opt is not None else None

        # unfold holes in the program
        self.jani_unfolded = None
        self.combination_coloring = None
        self.edge_to_color = None
        self.unfold_jani(jani, sketch.design_space)

    # Unfold holes in the jani program
    def unfold_jani(self, jani, design_space):
        open_constants = [c for c in jani.constants if not c.defined]
        assert len(open_constants) == design_space.hole_count
        expr_to_const = {c.expression_variable : c for c in open_constants}

        self.combination_coloring = CombinationColoring(design_space)
        
        jani_program = stormpy.JaniModel(jani)
        new_automata = dict()
        for aut_index, automaton in enumerate(jani_program.automata):
            if not self.automaton_has_holes(automaton, open_constants):
                continue
            new_aut = self.construct_automaton(automaton, open_constants, expr_to_const, design_space)
            new_automata[aut_index] = new_aut
        for aut_index, aut in new_automata.items():
            jani_program.replace_automaton(aut_index, aut)
        [jani_program.remove_constant(c.name) for c in open_constants]

        jani_program.set_model_type(stormpy.JaniModelType.MDP)
        jani_program.finalize()
        jani_program.check_valid()
        # print("colors: ", self.combination_coloring.colors)

        filename = "output.jani"
        logger.debug(f"Writing unfolded program to {filename}")
        with open(filename, "w") as f:
            f.write(str(jani_program))
        logger.debug("Done writing file.")

        # collect colors of each edge
        edge_to_color = {}
        for aut_index, automaton in enumerate(jani_program.automata):
            for edge_index, edge in enumerate(automaton.edges):
                global_index = jani_program.encode_automaton_and_edge_index(aut_index, edge_index)
                edge_to_color[global_index] = edge.color

        self.jani_unfolded = jani_program
        self.edge_to_color = edge_to_color

    def automaton_has_holes(self, automaton, holes):
        variables = {hole.expression_variable for hole in holes}
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

    def construct_automaton(self, automaton, open_constants, expr_to_const, design_space):
        new_aut = stormpy.storage.JaniAutomaton(automaton.name, automaton.location_variable)
        [new_aut.add_location(loc) for loc in automaton.locations]
        [new_aut.add_initial_location(idx) for idx in automaton.initial_location_indices]
        [new_aut.variables.add_variable(var) for var in automaton.variables]
        for edge in automaton.edges:
            new_edges = self.construct_edges(edge, open_constants, expr_to_const, design_space)
            for new_edge in new_edges:
                new_aut.add_edge(new_edge)
        return new_aut

    def construct_edges(self, edge, open_constants, expr_to_const, design_space):
        
        # relevant holes in guard
        variables = edge.template_edge.guard.get_variables()
        relevant_guard = {c for ev,c in expr_to_const.items() if ev in variables}

        # relevant holes in probabilities
        variables = set().union(*[d.probability.get_variables() for d in edge.destinations])
        relevant_probs = {c for ev,c in expr_to_const.items() if ev in variables}

        # relevant holes in updates
        variables = set()
        for dest in edge.template_edge.destinations:
            for assignment in dest.assignments:
                variables |= assignment.expression.get_variables()
        relevant_updates = {c for ev,c in expr_to_const.items() if ev in variables}
        
        # all relevant holes
        relevant_holes = relevant_guard | relevant_probs | relevant_updates

        new_edges = []
        if not relevant_holes:
            # copy without unfolding
            new_edges.append(self.construct_edge(edge))
            return new_edges

        # unfold all combinations
        combinations = [
            (range(len(design_space[c.name])) if c in relevant_holes else [None])
            for c in open_constants
        ]
        for combination in itertools.product(*combinations):
            substitution = {
                c.expression_variable: design_space[c.name][v]
                for c,v in zip(open_constants, combination) if v is not None
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