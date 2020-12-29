import enum
import itertools
import logging

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
        self._fill_constants_to_automata()
        self.holes_memory_ep = {
            c: self.expression_manager.create_integer_variable(c + "_memory") for c in self._open_constants
        }

    def _make_memory_var(self, constant, ep_var, nr_options):
        return stormpy.storage.JaniBoundedIntegerVariable(
            constant.name + "_memory", ep_var, self.expression_manager.create_integer(0),
            self.expression_manager.create_integer(0), self.expression_manager.create_integer(nr_options)
        )

    def _fill_constants_to_automata(self):
        self._open_constants_to_automata = dict()
        self._automata_to_open_constants = dict()
        for automaton in self.original_model.automata:
            self._automata_to_open_constants[automaton.name] = []
        for constant in self._open_constants.values():
            self._open_constants_to_automata[constant.name] = []
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

    def construct(self, holes_options, remember=None, init_all_in_one=None):
        if init_all_in_one is None:
            init_all_in_one = {}
        if remember is None:
            remember = {}
        assert len(remember) == 0, "Remember options have not been tested in a long time"
        self._counter = self._counter + 1
        init_all_in_one_by_replacement = True
        logger.info(f"Construct Jani Model with {holes_options} options and {remember} as remember")
        edge_coloring = EdgeColoring(holes_options)
        jani_program = stormpy.JaniModel(self.original_model)

        holes_memory_vars = {
            c.name: self._make_memory_var(c, self.holes_memory_ep[c.name], len(holes_options[c.name]))
            for c in self._open_constants.values()
        }

        new_automata = dict()

        for aut_index, automaton in enumerate(jani_program.automata):
            if len([x for x in self._automata_to_open_constants[automaton.name] if x not in init_all_in_one]) == 0:
                continue
            logger.debug(f"Reconstructing automaton {automaton.name}")
            new_aut = stormpy.storage.JaniAutomaton(automaton.name + "", automaton.location_variable)
            for loc in automaton.locations:
                new_aut.add_location(loc)
            for idx in automaton.initial_location_indices:
                new_aut.add_initial_location(idx)
            for var in automaton.variables:
                new_aut.variables.add_variable(var)

            for c in remember.intersection(self._automata_to_open_constants[automaton.name]):
                holes_memory_vars[c] = new_aut.variables.add_bounded_integer_variable(holes_memory_vars[c])
                logger.debug(f"added {holes_memory_vars[c]}")

            for edge in automaton.edges:
                expand_td = dict()
                expand_guard = set()

                for c in self._open_constants.values():
                    if init_all_in_one_by_replacement and c in init_all_in_one:
                        continue
                    if edge.template_edge.guard.contains_variable({c.expression_variable}):
                        expand_guard.add(c)

                for ted_idx, ted in enumerate(edge.template_edge.destinations):
                    for c in self._open_constants.values():
                        if init_all_in_one_by_replacement and c in init_all_in_one:
                            # For init_all_in_one_by_replacement, we do not substitute the values.
                            continue
                        for assignment in ted.assignments:
                            if assignment.expression.contains_variable({c.expression_variable}):
                                if c in expand_td:
                                    expand_td[c].append(ted_idx)
                                expand_td[c] = [ted_idx]

                if len(expand_td) > 0 or len(expand_guard) > 0:
                    if len(expand_guard) == 0:
                        guard_expr = stormpy.Expression(edge.template_edge.guard)

                    for combination in itertools.product(
                        *[range(len(holes_options[c.name])) if (c in expand_td or c in expand_guard) else [None]
                            for c in self._open_constants.values()]
                    ):

                        substitution = {
                            c.expression_variable: holes_options[c.name][v]
                            for c, v in zip(self._open_constants.values(), combination) if v is not None
                        }

                        if len(expand_guard) > 0:
                            guard_expr = stormpy.Expression(edge.template_edge.guard)
                            guard_expr = guard_expr.substitute(substitution)

                        te = stormpy.storage.JaniTemplateEdge(guard_expr)
                        remember_addition = {
                            c: v + 1 for c, v in
                            zip(self._open_constants.values(), combination) if v is not None and c.name in remember
                        }

                        for ted in edge.template_edge.destinations:
                            assignments = ted.assignments.clone()
                            remember_here = set()
                            for x in remember_addition:
                                for a in ted.assignments:
                                    if a.expression.contains_variable({x.expression_variable}):
                                        remember_here.add(x)
                            for x in remember_here:
                                # logger.debug(
                                #   f"Remember {x.name} in {holes_memory_vars[x.name]}={remember_addition[x]}"
                                # )
                                memory_assignment = stormpy.JaniAssignment(
                                    holes_memory_vars[x.name],
                                    self.expression_manager.create_integer(remember_addition[x])
                                )
                                assignments.add(memory_assignment)
                                guard_mem_set_before = stormpy.Expression.Eq(
                                    holes_memory_vars[x.name].expression_variable.get_expression(),
                                    self.expression_manager.create_integer(0)
                                )
                                guard_mem_not_set = stormpy.Expression.Eq(
                                    holes_memory_vars[x.name].expression_variable.get_expression(),
                                    self.expression_manager.create_integer(remember_addition[x])
                                )
                                te.guard = stormpy.Expression.And(
                                    te.guard, stormpy.Expression.Or(guard_mem_set_before, guard_mem_not_set)
                                )
                            assignments.substitute(substitution)

                            te.add_destination(stormpy.storage.JaniTemplateEdgeDestination(assignments))

                        dests = [(d.target_location_index, d.probability) for d in edge.destinations]
                        expand_d = set()
                        for c in self._open_constants.values():
                            for (t, p) in dests:
                                if p.contains_variable({c.expression_variable}):
                                    expand_d.add(c)
                        expand_d = list(expand_d)
                        assert len(expand_d) == 0

                        new_edge = stormpy.storage.JaniEdge(
                            edge.source_location_index, edge.action_index, edge.rate, te, dests
                        )

                        new_edge.color = edge_coloring.get_or_make_color(combination)
                        new_aut.add_edge(new_edge)
                else:
                    assert len(expand_guard) == 0
                    guard_expr = stormpy.Expression(edge.template_edge.guard)
                    te = stormpy.storage.JaniTemplateEdge(guard_expr)

                    # Just copy the stuff over.
                    for ted in edge.template_edge.destinations:
                        assignment = ted.assignments.clone()
                        te.add_destination(stormpy.storage.JaniTemplateEdgeDestination(assignment))

                    dests = [(d.target_location_index, d.probability) for d in edge.destinations]
                    expand_d = set()
                    for c in self._open_constants.values():
                        for (t, p) in dests:
                            if p.contains_variable({c.expression_variable}):
                                expand_d.add(c)
                    expand_d = list(expand_d)

                    if len(expand_d) > 0:  # TODO
                        for combination in itertools.product(
                            *[(range(len(holes_options[c.name])) if c in expand_d else [None])
                                for c in self._open_constants.values()]
                        ):
                            edge_color = edge_coloring.get_or_make_color(combination)
                            substitution = {
                                c.expression_variable: holes_options[c.name][v]
                                for c, v in zip(self._open_constants.values(), combination) if v is not None
                            }
                            new_dests = [
                                (d.target_location_index, d.probability.substitute(substitution))
                                for d in edge.destinations
                            ]
                            new_edge = stormpy.storage.JaniEdge(
                                edge.source_location_index, edge.action_index, edge.rate, te, new_dests
                            )
                            new_edge.color = edge_color
                            new_aut.add_edge(new_edge)
                    else:
                        new_edge = stormpy.storage.JaniEdge(
                            edge.source_location_index, edge.action_index, edge.rate, te, dests
                        )
                        new_aut.add_edge(new_edge)
            logger.debug(f"Done rewriting {new_aut.name}")
            new_automata[aut_index] = new_aut

        logger.debug("Replacing automata...")

        for idx, aut in new_automata.items():
            jani_program.replace_automaton(idx, aut)

        logger.debug(f"Number of colors: {len(edge_coloring)}")

        logger.debug("Removing constants...")
        remove_constant_names = [c.name for c in self._open_constants.values()]
        new_variables = []
        for c, vs in holes_options.items():
            if c not in init_all_in_one:
                continue
            # TODO use evaluation
            min_val = min([int(str(v)) for v in vs])
            max_val = max([int(str(v)) for v in vs])
            logger.debug(f"Variable {c} with options {vs} ranges from {min_val} to {max_val}")
            upper_bound = self.expression_manager.create_integer(max_val)
            expr_var = self._open_constants[c].expression_variable
            var_restriction = self.expression_manager.create_boolean(False)
            for v in vs:
                var_restriction = stormpy.Expression.Or(
                    var_restriction, stormpy.Expression.Eq(expr_var.get_expression(), v)
                )
            jani_program.initial_states_restriction = stormpy.Expression.And(
                jani_program.initial_states_restriction, var_restriction
            )
            # TODO if using an initializer automaton, change the way variables are initialises
            lower_bound = self.expression_manager.create_integer(min_val)
            new_variables.append(stormpy.storage.JaniBoundedIntegerVariable(c, expr_var, lower_bound, upper_bound))
        for cname in remove_constant_names:
            jani_program.remove_constant(cname)

        for n in new_variables:
            jani_program.global_variables.add_bounded_integer_variable(n)

        if len(init_all_in_one) != len(holes_options):
            # also do this with initializer automata
            jani_program.set_model_type(stormpy.JaniModelType.MDP)
        jani_program.finalize()
        jani_program.check_valid()

        filename = f"output_{self._counter}.jani"
        logger.debug(f"Write to {filename}")
        with open(filename, "w") as F:
            # jani_program.make_standard_compliant()
            F.write(str(jani_program))
            pass
        logger.debug("done writing file.")

        color_to_edge_indices = dict()
        for aut_index, automaton in enumerate(jani_program.automata):
            for edge_index, edge in enumerate(automaton.edges):
                new_list = color_to_edge_indices.get(edge.color, stormpy.FlatSet())
                new_list.insert(jani_program.encode_automaton_and_edge_index(aut_index, edge_index))
                color_to_edge_indices[edge.color] = new_list
        print(",".join([f"{k}: {v}" for k, v in color_to_edge_indices.items()]))

        return JaniQuotientContainer(jani_program, edge_coloring, holes_options, color_to_edge_indices)
