import stormpy
import payntbind

import paynt.verification.property
import paynt.quotient.models

import itertools
from collections import defaultdict

import logging
logger = logging.getLogger(__name__)


class CombinationColoring:
    '''
    Dictionary of colors associated with different hole combinations.
    Note: color 0 is reserved for general hole-free objects.
    '''
    def __init__(self):
        self.coloring = {}
        self.reverse_coloring = [None]

    @property
    def num_colors(self):
        return len(self.coloring)

    def get_or_make_color(self, hole_assignment):
        new_color = self.num_colors + 1
        color = self.coloring.get(hole_assignment, new_color)
        if color == new_color:
            self.coloring[hole_assignment] = color
            self.reverse_coloring.append(hole_assignment)
        return color


class JaniUnfolder:
    ''' Unfolder of hole combinations into JANI program. '''

    def __init__(self, prism, hole_expressions, specification, family):

        logger.debug("constructing JANI program...")
        
        # pack properties and translate Prism to Jani
        properties_old = specification.all_properties()
        stormpy_properties = [p.property for p in properties_old]
        jani,properties = prism.to_jani(stormpy_properties)

        # upon translation, some properties may change their atoms, so we need to re-wrap all properties
        properties_unpacked = []
        for index,prop_old in enumerate(properties_old):
            prop_new = properties[index]
            if type(prop_old) == paynt.verification.property.Property:
                p = paynt.verification.property.Property(prop_new)
            else:
                epsilon = prop_old.epsilon
                p = paynt.verification.property.OptimalityProperty(prop_new,epsilon)
            properties_unpacked.append(p)
        self.specification = paynt.verification.property.Specification(properties_unpacked)
        paynt.quotient.models.Mdp.initialize(self.specification)

        # unfold holes in the program
        self.hole_expressions = hole_expressions
        self.jani_unfolded = None
        self.combination_coloring = None
        self.unfold_jani(jani, family)
        logger.debug("constructing the quotient...")

        # construct the explicit quotient
        quotient_mdp = stormpy.build_sparse_model_with_options(self.jani_unfolded, paynt.quotient.models.Mdp.builder_options)

        # associate each action of a quotient MDP with hole options
        # reconstruct choice labels from choice origins
        logger.debug("associating choices of the quotient with hole assignments...")
        choice_is_valid,choice_to_hole_options = payntbind.synthesis.janiMapChoicesToHoleAssignments(
            quotient_mdp,family.family,self.edge_to_hole_options
        )

        # handle conflicting colors
        num_choices_all = quotient_mdp.nr_choices
        num_choices_valid = choice_is_valid.number_of_set_bits()
        if num_choices_valid < num_choices_all:
            logger.debug("keeping {}/{} choices with non-conflicting hole assignments...".format(num_choices_valid,num_choices_all))
            keep_unreachable_states = False
            subsystem_builder_options = stormpy.SubsystemBuilderOptions()
            subsystem_builder_options.build_action_mapping = True
            all_states = stormpy.storage.BitVector(quotient_mdp.nr_states, True)
            submodel_construction = stormpy.construct_submodel(
                quotient_mdp, all_states, choice_is_valid, keep_unreachable_states, subsystem_builder_options
            )
            quotient_mdp = submodel_construction.model
            choice_map = list(submodel_construction.new_to_old_action_mapping)
            choice_to_hole_options = [choice_to_hole_options[choice_map[choice]] for choice in range(quotient_mdp.nr_choices)]

        self.quotient_mdp = quotient_mdp
        self.choice_to_hole_options = choice_to_hole_options
        return


    # Unfold holes in the jani program
    def unfold_jani(self, jani, family):
        # ensure that jani.constants are in the same order as our holes
        open_constants = [c for c in jani.constants if not c.defined]
        expression_variables = [c.expression_variable for c in open_constants]
        assert len(open_constants) == family.num_holes
        for hole in range(family.num_holes):
            assert family.hole_name(hole) == open_constants[hole].name

        self.combination_coloring = CombinationColoring()

        jani_program = stormpy.JaniModel(jani)
        new_automata = dict()
        for aut_index, automaton in enumerate(jani_program.automata):
            if not self.automaton_has_holes(automaton, set(expression_variables)):
                continue
            new_aut = self.construct_automaton(automaton, family, expression_variables)
            new_automata[aut_index] = new_aut
        for aut_index, aut in new_automata.items():
            jani_program.replace_automaton(aut_index, aut)
        for hole in range(family.num_holes):
            jani_program.remove_constant(family.hole_name(hole))

        jani_program.set_model_type(stormpy.JaniModelType.MDP)
        jani_program.finalize()
        jani_program.check_valid()

        # collect label and color of each edge
        edge_to_hole_options = {}
        for aut_index, automaton in enumerate(jani_program.automata):
            for edge_index, edge in enumerate(automaton.edges):
                global_index = jani_program.encode_automaton_and_edge_index(aut_index, edge_index)

                if edge.color == 0:
                    continue
                options = self.combination_coloring.reverse_coloring[edge.color]
                options = [(hole_index,option) for hole_index,option in enumerate(options) if option is not None]
                edge_to_hole_options[global_index] = options

        self.jani_unfolded = jani_program
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

    def construct_automaton(self, automaton, family, expression_variables):
        new_aut = stormpy.storage.JaniAutomaton(automaton.name, automaton.location_variable)
        [new_aut.add_location(loc) for loc in automaton.locations]
        [new_aut.add_initial_location(idx) for idx in automaton.initial_location_indices]
        [new_aut.variables.add_variable(var) for var in automaton.variables]
        for edge in automaton.edges:
            new_edges = self.construct_edges(edge, family, expression_variables)
            for new_edge in new_edges:
                new_aut.add_edge(new_edge)
        return new_aut

    def construct_edges(self, edge, family, expression_variables):

        # relevant holes in guard
        variables = edge.template_edge.guard.get_variables()
        relevant_guard = {hole for hole in range(family.num_holes) if expression_variables[hole] in variables}

        # relevant holes in probabilities
        variables = set().union(*[d.probability.get_variables() for d in edge.destinations])
        relevant_probs = {hole for hole in range(family.num_holes) if expression_variables[hole] in variables}

        # relevant holes in updates
        variables = set()
        for dest in edge.template_edge.destinations:
            for assignment in dest.assignments:
                variables |= assignment.expression.get_variables()
        relevant_updates = {hole for hole in range(family.num_holes) if expression_variables[hole] in variables}
        
        # all relevant holes
        relevant_holes = relevant_guard | relevant_probs | relevant_updates

        new_edges = []
        if not relevant_holes:
            # copy without unfolding
            new_edges.append(self.construct_edge(edge))
            return new_edges

        # unfold all combinations
        combinations = [
            (list(range(family.hole_num_options(hole))) if hole in relevant_holes else [None])
            for hole in range(family.num_holes)
        ]
        for combination in itertools.product(*combinations):
            substitution = {
                expression_variables[hole] : self.hole_expressions[hole][combination[hole]]
                for hole in range(family.num_holes)
                if combination[hole] is not None
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

    def write_jani(self, output_path):
        logger.debug(f"Writing unfolded program to {output_path}")
        with open(output_path, "w") as f:
            f.write(str(self.jani_unfolded))
