import stormpy

from paynt.verification.property import Property, OptimalityProperty, Specification
from ..quotient.holes import CombinationColoring
from ..quotient.models import MarkovChain

import itertools
from collections import defaultdict

import logging
logger = logging.getLogger(__name__)

class JaniUnfolder():
    ''' Unfolder of hole combinations into JANI program. '''

    def __init__(self, prism, hole_expressions, specification, design_space):

        logger.debug("constructing JANI program...")
        
        # pack properties
        properties = specification.stormpy_properties()
        
        # construct jani
        jani, new_properties = prism.to_jani(properties)

        # unpack properties
        properties = new_properties
        opt = None
        eps = None
        if specification.has_optimality:
            properties = new_properties[:-1]
            opt = new_properties[-1]
            eps = specification.optimality.epsilon

        # when translating PRISM to JANI, some properties may change their
        # atoms, so we need to re-wrap all properties
        properties = [Property(p) for p in properties]
        optimality_property = OptimalityProperty(opt, eps) if opt is not None else None
        self.specification = Specification(properties,optimality_property)
        MarkovChain.initialize(self.specification)

        # unfold holes in the program
        self.hole_expressions = hole_expressions
        self.jani_unfolded = None
        self.combination_coloring = None
        self.edge_to_color = None
        self.unfold_jani(jani, design_space)

        # construct the explicit quotient
        quotient_mdp = stormpy.build_sparse_model_with_options(self.jani_unfolded, MarkovChain.builder_options)

        # associate each action of a quotient MDP with hole options
        # reconstruct choice labels from choice origins
        # TODO handle conflicting colors
        action_to_hole_options = []
        tm = quotient_mdp.transition_matrix
        for choice in range(quotient_mdp.nr_choices):
            # co = quotient_mdp.choice_origins
            # print(dir(quotient_mdp.choice_origins))
            # i = co.get_choice_info(choice)
            # print(type(i))
            # print(dir(i))
            # print(i)
            # exit()

            edges = quotient_mdp.choice_origins.get_edge_index_set(choice)
            hole_options = {}
            for edge in edges:
                combination = self.edge_to_hole_options.get(edge, None)
                if combination is None:
                    continue
                for hole_index,option in combination.items():
                    options = hole_options.get(hole_index,set())
                    options.add(option)
                    hole_options[hole_index] = options

            for hole_index,options in hole_options.items():
                assert len(options) == 1
            hole_options = {hole_index:list(options)[0] for hole_index,options in hole_options.items()}
            action_to_hole_options.append(hole_options)

        self.quotient_mdp = quotient_mdp
        self.action_to_hole_options = action_to_hole_options
        return


    # Unfold holes in the jani program
    def unfold_jani(self, jani, design_space):
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

        # collect label and color of each edge
        edge_to_hole_options = {}
        edge_to_color = {}
        # print(jani_program)
        # print(dir(jani_program))
        # print(type(jani_program))
        # exit()
        for aut_index, automaton in enumerate(jani_program.automata):
            # print(dir(automaton))
            # print(str(automaton))
            # print(automaton.name)
            # exit()
            for edge_index, edge in enumerate(automaton.edges):
                # print(type(edge))
                # print(dir(edge))
                # print(edge.action_index)
                # print(edge.color)
                # print(edge.destinations)
                # print(edge.guard)
                # print(edge.has_silent_action())
                # print(edge.rate)
                # exit()
                # print(edge.template_edge)
                # te = edge.template_edge
                # print(dir(te))
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
        # exit()

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

    def write_jani(self, sketch_path):
        from . import sketch
        output_path = sketch.Sketch.substitute_suffix(sketch_path, '.', 'jani')
        logger.debug(f"Writing unfolded program to {output_path}")
        with open(output_path, "w") as f:
            f.write(str(self.jani_unfolded))
        logger.debug("Write OK, aborting...")
