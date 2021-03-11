import enum
import itertools
import logging

from collections import defaultdict

import stormpy

from .edge_coloring import EdgeColoring
from .quotient_container import JaniQuotientContainer


logger = logging.getLogger(__name__)


class SpecialReplacement(enum.Enum):
    GUARD = 0


class JaniQuotientBuilder:
    def __init__(self, original_model, _open_constants):
        self._counter = 0
        self.original_model = original_model
        self.expression_manager = original_model.expression_manager
        self._open_constants = _open_constants
        self._open_constants_to_automata = None
        self._automata_to_open_constants = None
        self.init_all_in_one = None
        self.remember = None
        self.edge_coloring = None
        self.holes_options = {}
        self.holes_memory_vars = {}
        self.parameters = []
        self.init_allin1_by_replace = True
        self._fill_constants_to_automata()
        self.holes_memory_ep = self._make_holes_memory_ep()

    @staticmethod
    def convert_expr_to_num(expr):
        def convert_rational(s):
            try:
                return float(s)
            except ValueError:
                num, denom = s.split('/')
                return float(num) / float(denom)

        if expr.type.is_integer:
            return int(str(expr))
        elif expr.type.is_rational:
            return convert_rational(str(expr))
        else:
            logger.error(f"Unsupported type of expression variable: {expr.type}")

    def _create_typed_variable(self, var_type, var_name):
        if var_type.is_integer:
            return self.expression_manager.create_integer_variable(var_name)
        elif var_type.is_rational:
            return self.expression_manager.create_rational_variable(var_name)
        else:
            logger.error(f"Unsupported type of expression variable: {var_type}")

    def _make_holes_memory_ep(self):
        holes_memory_ep = {}
        for c in self._open_constants.values():
            holes_memory_ep[c.name] = self._create_typed_variable(c.type, c.name + "_memory")
        return holes_memory_ep

    def _make_memory_var(self, constant, ep_var, nr_options):
        if constant.type.is_integer:
            return stormpy.storage.JaniBoundedIntegerVariable(
                constant.name + "_memory", ep_var, self.expression_manager.create_integer(0),
                self.expression_manager.create_integer(0), self.expression_manager.create_integer(nr_options)
            )
        elif constant.type.is_rational:
            return stormpy.storage.JaniRealVariable(
                constant.name + "_memory", ep_var, self.expression_manager.create_rational(stormpy.Rational(0.0)), False
            )
        else:
            logger.error(f"Unsupported type of expression variable: {constant.type}")

    def _fill_constants_to_automata(self):
        self._open_constants_to_automata = defaultdict(list)
        self._automata_to_open_constants = defaultdict(list)
        for constant in self._open_constants.values():
            for automaton in self.original_model.automata:
                if self._automaton_has_constant(automaton, constant):
                    self._open_constants_to_automata[constant.name].append(automaton.name)
                    self._automata_to_open_constants[automaton.name].append(constant.name)
                    logger.debug(f"Automaton {automaton.name} has constant {constant.name}")

    @staticmethod
    def _automaton_has_constant(automaton, constant):
        for edge_index, e in enumerate(automaton.edges):
            if e.guard.contains_variable({constant.expression_variable}):
                return True
            for dest in e.destinations:
                for assignment in dest.assignments:
                    if assignment.expression.contains_variable({constant.expression_variable}):
                        return True
                if dest.probability.contains_variable({constant.expression_variable}):
                    return True

    def _construct_expands(self, edge):
        expand_td = defaultdict(list)
        expand_guard = set()

        for c in self._open_constants.values():
            if not self.init_allin1_by_replace or c not in self.init_all_in_one:
                if edge.template_edge.guard.contains_variable({c.expression_variable}):
                    expand_guard.add(c)

        for ted_idx, ted in enumerate(edge.template_edge.destinations):
            for c in self._open_constants.values():
                if not self.init_all_in_one or c not in self.init_all_in_one:
                    for assignment in ted.assignments:
                        if assignment.expression.contains_variable({c.expression_variable}):
                            expand_td[c].append(ted_idx)

        return expand_td, expand_guard

    def _get_substitution(self, combination):
        return {
            c.expression_variable: self.holes_options[c.name][v]
            for c, v in zip(self._open_constants.values(), combination) if v is not None
            # for c, v in zip(self._open_constants.values(), combination)
            # if v is not None and c.name not in self.parameters
        }

    def _modify_dst_with_remember(self, edge, combination, templ_edge, substitution):
        remember_addition = {
            c: v + 1 for c, v in
            zip(self._open_constants.values(), combination) if v is not None and c.name in self.remember
        }

        for templ_edge_dest in edge.template_edge.destinations:
            assignments = templ_edge_dest.assignments.clone()
            remember_here = set()

            for x in remember_addition:
                for assignment in templ_edge_dest.assignments:
                    if assignment.expression.contains_variable({x.expression_variable}):
                        remember_here.add(x)

            for x in remember_here:
                x_expression = self.holes_memory_vars[x.name].expression_variable.get_expression()
                x_type = self._create_typed_variable(x.type, remember_addition[x])
                memory_assignment = stormpy.JaniAssignment(self.holes_memory_vars[x.name], x_type)
                guard_mem_set_before = stormpy.Expression.Eq(x_expression, self.expression_manager.create_integer(0))
                guard_mem_not_set = stormpy.Expression.Eq(x_expression, x_type)

                templ_edge.guard = stormpy.Expression.And(
                    templ_edge.guard, stormpy.Expression.Or(guard_mem_set_before, guard_mem_not_set)
                )
                assignments.add(memory_assignment)

            assignments.substitute(substitution)
            templ_edge.add_destination(stormpy.storage.JaniTemplateEdgeDestination(assignments))

        return templ_edge

    def _get_expand_d(self, edge):
        dests = [(d.target_location_index, d.probability) for d in edge.destinations]
        expand_d = set()
        for c in self._open_constants.values():
            [expand_d.add(c) for (t, p) in dests if p.contains_variable({c.expression_variable})]
        return list(expand_d), dests

    def _add_new_edge(self, new_automaton, edge, templ_edge, dests, combination=None):
        new_edge = stormpy.storage.JaniEdge(
            edge.source_location_index, edge.action_index, edge.rate, templ_edge, dests
        )
        if combination is not None:
            new_edge.color = self.edge_coloring.get_or_make_color(combination)
        new_automaton.add_edge(new_edge)
        return new_automaton

    def _construct_new_edge(self, edge, templ_edge, new_automaton):
        expand_d, dests = self._get_expand_d(edge)

        # expand_d = []
        if expand_d:
            for combination in itertools.product(
                    *[(range(len(self.holes_options[c.name])) if c in expand_d else [None])
                      for c in self._open_constants.values()]
            ):
                substitution = self._get_substitution(combination)
                new_dests = [
                    (d.target_location_index, d.probability.substitute(substitution)) for d in edge.destinations
                ]
                new_automaton = self._add_new_edge(new_automaton, edge, templ_edge, new_dests, tuple(combination))
        else:
            new_automaton = self._add_new_edge(new_automaton, edge, templ_edge, dests, None)

        return new_automaton

    def _construct_edges(self, edge, new_automaton):
        expand_td, expand_guard = self._construct_expands(edge)
        expand_d, dests = self._get_expand_d(edge)

        guard_expr = stormpy.Expression(edge.template_edge.guard)
        if expand_td or expand_guard:
            # without c in expand_d
            for combination in itertools.product(
                    *[(range(len(self.holes_options[c.name])) if (c in expand_td or c in expand_guard or c in expand_d)
                        else [None]) for c in self._open_constants.values()]
            ):
                substitution = self._get_substitution(combination)
                templ_edge = stormpy.storage.JaniTemplateEdge(
                    guard_expr.substitute(substitution) if len(expand_guard) > 0 else guard_expr
                )
                templ_edge = self._modify_dst_with_remember(edge, combination, templ_edge, substitution)
                new_dests = [
                    (d.target_location_index, d.probability.substitute(substitution)) for d in edge.destinations
                ] if expand_d else dests
                new_automaton = self._add_new_edge(new_automaton, edge, templ_edge, new_dests, combination)
        else:
            assert len(expand_guard) == 0
            templ_edge = stormpy.storage.JaniTemplateEdge(guard_expr)

            # Just copy the stuff over.
            for templ_edge_dest in edge.template_edge.destinations:
                assignment = templ_edge_dest.assignments.clone()
                templ_edge.add_destination(stormpy.storage.JaniTemplateEdgeDestination(assignment))
            new_automaton = self._construct_new_edge(edge, templ_edge, new_automaton)

        return new_automaton

    def _reconstruct_automaton(self, automaton):
        logger.debug(f"Reconstructing automaton {automaton.name}")
        new_aut = stormpy.storage.JaniAutomaton(automaton.name + "", automaton.location_variable)
        [new_aut.add_location(loc) for loc in automaton.locations]
        [new_aut.add_initial_location(idx) for idx in automaton.initial_location_indices]
        [new_aut.variables.add_variable(var) for var in automaton.variables]

        self.holes_memory_vars = {
            c.name: self._make_memory_var(c, self.holes_memory_ep[c.name], len(self.holes_options[c.name]))
            for c in self._open_constants.values()
        }
        for c in self.remember.intersection(self._automata_to_open_constants[automaton.name]):
            # TODO: When use remember then add rational variable also is required
            self.holes_memory_vars[c] = new_aut.variables.add_bounded_integer_variable(self.holes_memory_vars[c])
            logger.debug(f"added {self.holes_memory_vars[c]}")

        for edge in automaton.edges:
            new_aut = self._construct_edges(edge, new_aut)

        logger.debug(f"Done rewriting {new_aut.name}")
        return new_aut

    def _remove_constants(self, jani_program):
        new_variables = []
        for c, vs in self.holes_options.items():
            if c in self.init_all_in_one:
                min_val = min([self.convert_expr_to_num(v) for v in vs])
                max_val = max([self.convert_expr_to_num(v) for v in vs])
                upper_bound = self.expression_manager.create_integer(max_val) if isinstance(max_val, int) \
                    else self.expression_manager.create_rational(stormpy.Rational(max_val))
                lower_bound = self.expression_manager.create_integer(min_val) if isinstance(min_val, int) \
                    else self.expression_manager.create_rational(stormpy.Rational(min_val))
                logger.debug(f"Variable {c} with options {vs} ranges from {min_val} to {max_val}")

                expr_var = self._open_constants[c].expression_variable
                var_restriction = self.expression_manager.create_boolean(False)
                for v in vs:
                    var_restriction = stormpy.Expression.Or(
                        var_restriction, stormpy.Expression.Eq(expr_var.get_expression(), v)
                    )
                jani_program.initial_states_restriction = stormpy.Expression.And(
                    jani_program.initial_states_restriction, var_restriction
                )

                if self._open_constants[c].type.is_integer:
                    new_variables.append(
                        stormpy.storage.JaniBoundedIntegerVariable(c, expr_var, lower_bound, upper_bound)
                    )
                elif self._open_constants[c].type.is_rational:
                    new_variables.append(stormpy.storage.JaniRealVariable(
                        c, expr_var, self.expression_manager.create_rational(stormpy.Rational(0.0)), True
                    ))
                else:
                    logger.error(f"Unsupported type of expression variable: {self._open_constants[c].type}")

        [jani_program.remove_constant(cname) for cname in [c.name for c in self._open_constants.values()]]

        for new_var in new_variables:
            if new_var.is_bounded_integer_variable:
                jani_program.global_variables.add_bounded_integer_variable(new_var)
            elif new_var.is_real_variable:
                jani_program.global_variables.add_real_variable(new_var)
            else:
                logger.error(f"Unsupported type of expression variable: {new_var}")

        return jani_program

    def construct(self, holes_options, parameters, remember=None, init_all_in_one=None):
        self.holes_options = holes_options
        self.parameters = parameters
        self.init_all_in_one = init_all_in_one if init_all_in_one is not None else {}
        self.remember = remember if remember is not None else {}
        assert len(self.remember) == 0, "Remember options have not been tested in a long time"

        self._counter += 1
        logger.info(f"Construct Jani Model with {self.holes_options} options and {self.remember} as remember")
        self.edge_coloring = EdgeColoring(self.holes_options)
        jani_program = stormpy.JaniModel(self.original_model)

        new_automata = dict()
        for aut_index, automaton in enumerate(jani_program.automata):
            if len([x for x in self._automata_to_open_constants[automaton.name] if x not in self.init_all_in_one]) > 0:
                new_automata[aut_index] = self._reconstruct_automaton(automaton)

        logger.debug("Replacing automata...")
        for idx, aut in new_automata.items():
            jani_program.replace_automaton(idx, aut)
        logger.debug(f"Number of colors: {len(self.edge_coloring)}")

        logger.debug("Removing constants...")
        jani_program = self._remove_constants(jani_program)

        if len(self.init_all_in_one) != len(self.holes_options):
            jani_program.set_model_type(stormpy.JaniModelType.MDP)
        jani_program.finalize()
        jani_program.check_valid()

        # filename = f"output_{self._counter}.jani"
        # logger.debug(f"Write to {filename}")
        # with open(filename, "w") as F:
            # jani_program.make_standard_compliant()
            # F.write(str(jani_program))
            # pass
        # logger.debug("done writing file.")

        color_to_edge_indices = dict()
        for aut_index, automaton in enumerate(jani_program.automata):
            for edge_index, edge in enumerate(automaton.edges):
                new_list = color_to_edge_indices.get(edge.color, stormpy.FlatSet())
                new_list.insert(jani_program.encode_automaton_and_edge_index(aut_index, edge_index))
                color_to_edge_indices[edge.color] = new_list
        logger.debug(",".join([f'{k}: {v}' for k, v in color_to_edge_indices.items()]))

        return JaniQuotientContainer(jani_program, self.edge_coloring, self.holes_options, color_to_edge_indices)
