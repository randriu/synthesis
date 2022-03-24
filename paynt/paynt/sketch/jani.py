import stormpy

from .property import Property, OptimalityProperty, Specification
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
        properties = sketch.specification.stormpy_properties()
        
        # construct jani
        jani, new_properties = sketch.prism.to_jani(properties)

        # unpack properties
        properties = new_properties
        opt = None
        eps = None
        if sketch.specification.has_optimality:
            properties = new_properties[:-1]
            opt = new_properties[-1]
            eps = sketch.specification.optimality.epsilon

        # when translating PRISM to JANI, some properties may change their
        # atoms, so we need to re-wrap all properties
        properties = [Property(p) for p in properties]
        optimality_property = OptimalityProperty(opt, eps) if opt is not None else None
        self.specification = Specification(properties,optimality_property)

        # unfold holes in the program
        self.hole_expressions = sketch.hole_expressions
        self.jani_unfolded = None
        self.combination_coloring = None
        self.edge_to_color = None
        self.unfold_jani(jani, sketch.design_space, sketch.export_jani)


    # Unfold holes in the jani program
    def unfold_jani(self, jani, design_space, export_jani):
        # ensure that jani.constants are in the same order as our holes
        open_constants = [c for c in jani.constants if not c.defined]
        expression_variables = [c.expression_variable for c in open_constants]
        assert len(open_constants) == design_space.num_holes
        for hole_index,hole in enumerate(design_space):
            assert hole.name == open_constants[hole_index].name

        self.combination_coloring = CombinationColoring(design_space)

        jani_program = stormpy.JaniModel(jani)
        new_automata = dict()
        for aut_index, automaton in enumerate(jani_program.automata):
            if not self.automaton_has_holes(automaton, set(expression_variables)):
                continue
            new_aut = self.construct_automaton(automaton, design_space, expression_variables)
            new_automata[aut_index] = new_aut
        for aut_index, aut in new_automata.items():
            jani_program.replace_automaton(aut_index, aut)
        [jani_program.remove_constant(hole.name) for hole in design_space]

        jani_program.set_model_type(stormpy.JaniModelType.MDP)
        jani_program.finalize()
        jani_program.check_valid()

        if export_jani:
            filename = "output.jani"
            logger.debug(f"Writing unfolded program to {filename}")
            with open(filename, "w") as f:
                f.write(str(jani_program))
            logger.debug("Done writing file.")
            exit()

        # collect colors of each edge
        edge_to_hole_options = {}
        edge_to_color = {}
        for aut_index, automaton in enumerate(jani_program.automata):
            for edge_index, edge in enumerate(automaton.edges):
                global_index = jani_program.encode_automaton_and_edge_index(aut_index, edge_index)
                edge_to_color[global_index] = edge.color

                if edge.color == 0:
                    continue
                options = self.combination_coloring.reverse_coloring[edge.color]
                options = {hole_index:option for hole_index,option in enumerate(options) if option is not None}
                edge_to_hole_options[global_index] = options

        self.jani_unfolded = jani_program
        self.edge_to_color = edge_to_color
        self.edge_to_hole_options = edge_to_hole_options

    def automaton_has_holes(self, automaton, expression_variables):
        for edge_index, e in enumerate(automaton.edges):
            if e.guard.contains_variable(expression_variables):
                return True
            for dest in e.destinations:
                if dest.probability.contains_variable(expression_variables):
                    return True
                for assignment in dest.assignments:
                    if assignment.expression.contains_variable(expression_variables):
                        return True
        return False

    def construct_automaton(self, automaton, design_space, expression_variables):
        new_aut = stormpy.storage.JaniAutomaton(automaton.name, automaton.location_variable)
        [new_aut.add_location(loc) for loc in automaton.locations]
        [new_aut.add_initial_location(idx) for idx in automaton.initial_location_indices]
        [new_aut.variables.add_variable(var) for var in automaton.variables]
        for edge in automaton.edges:
            new_edges = self.construct_edges(edge, design_space, expression_variables)
            for new_edge in new_edges:
                new_aut.add_edge(new_edge)
        return new_aut

    def construct_edges(self, edge, design_space, expression_variables):

        # relevant holes in guard
        variables = edge.template_edge.guard.get_variables()
        relevant_guard = {hole_index for hole_index in design_space.hole_indices if expression_variables[hole_index] in variables}

        # relevant holes in probabilities
        variables = set().union(*[d.probability.get_variables() for d in edge.destinations])
        relevant_probs = {hole_index for hole_index in design_space.hole_indices if expression_variables[hole_index] in variables}

        # relevant holes in updates
        variables = set()
        for dest in edge.template_edge.destinations:
            for assignment in dest.assignments:
                variables |= assignment.expression.get_variables()
        relevant_updates = {hole_index for hole_index in design_space.hole_indices if expression_variables[hole_index] in variables}
        
        # all relevant holes
        relevant_holes = relevant_guard | relevant_probs | relevant_updates

        new_edges = []
        if not relevant_holes:
            # copy without unfolding
            new_edges.append(self.construct_edge(edge))
            return new_edges

        # unfold all combinations
        combinations = [
            (design_space[hole_index].options if hole_index in relevant_holes else [None])
            for hole_index in design_space.hole_indices
        ]
        for combination in itertools.product(*combinations):
            substitution = {
                expression_variables[hole_index] : self.hole_expressions[hole_index][combination[hole_index]]
                for hole_index in design_space.hole_indices
                if combination[hole_index] is not None
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