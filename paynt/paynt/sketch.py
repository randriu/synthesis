
import stormpy

import os
import re
import numpy
import uuid
import itertools
import math
import operator
import z3

from collections import defaultdict, OrderedDict

from .synthesizers.edge_coloring import EdgeColoring

import logging
logger = logging.getLogger(__name__)

class Property:
    def __init__(self, prop, program, epsilon = None):
        '''
        :param epsilon if not None, then this is an optimality formula
        '''

        self.property = prop
        rf = self.property.raw_formula
        self.optimality = rf.has_optimality_type

        self.comparison_type = None
        self.op = None
        self.threshold = None

        self.optimal_value = None
        self.epsilon = epsilon
        self.expression_manager = program.expression_manager
        
        self.formula = None
        self.formula_alt = None

        # set comparison type
        self.comparison_type = rf.comparison_type
        if self.optimality:
            if rf.optimality_type == stormpy.OptimizationDirection.Minimize:
                self.comparison_type = stormpy.ComparisonType.LESS 
            else:
                self.comparison_type = stormpy.ComparisonType.GREATER
        
        # set operator
        self.op = {
            stormpy.ComparisonType.LESS: operator.lt,
            stormpy.ComparisonType.LEQ: operator.le,
            stormpy.ComparisonType.GREATER: operator.gt,
            stormpy.ComparisonType.GEQ: operator.ge
        }[self.comparison_type]

        # construct quantitative formula (without bound)
        self.formula = rf.clone()
        if not self.optimality:
            # formula is qualitative and does not have optimality type
            self.formula.remove_bound()
            if self.minimizing:
                self.formula.set_optimality_type(stormpy.OptimizationDirection.Minimize)
            else:
                self.formula.set_optimality_type(stormpy.OptimizationDirection.Maximize)

        # construct alternative quantitative formula for AR
        self.formula_alt = self.formula.clone()
        if self.minimizing:
            self.formula_alt.set_optimality_type(stormpy.OptimizationDirection.Maximize)
        else:
            self.formula_alt.set_optimality_type(stormpy.OptimizationDirection.Minimize)

        # threshold for constraints
        if self.optimality:
            if self.minimizing:
                # self.threshold = math.inf if self.reward else 1
                self.threshold = math.inf
            else:
                # self.threshold = 0
                self.threshold = -math.inf
        else:
            self.threshold = rf.threshold_expr.evaluate_as_double()

        # qualitatitve formula to display constraints
        self.formula_str = self.formula
        if not self.optimality:
            self.formula_str = rf

    def __str__(self):
        return str(self.formula_str)

    @property
    def reward(self):
        return self.formula.is_reward_operator

    @property
    def minimizing(self):
        return self.comparison_type in [stormpy.ComparisonType.LESS, stormpy.ComparisonType.LEQ]

    def value_valid(self, value):
        # reward properties are satisfied only when result is defined
        if self.reward and value == math.inf:
            return False
        return True

    def meets_threshold(self, result):
        ''' check if model checking result meets threshold wrt operator '''
        # precision_multiplier = 1.0000000001
        # if self.minimizing:
        #     result /= precision_multiplier
        # else:
        #     result *= precision_multiplier
        return self.op(result, self.threshold)

    def satisfied(self, result):
        ''' check if model checking result satisfies the property '''
        return self.value_valid(result) and self.meets_threshold(result)

    def decided(self, result_min, result_max):
        '''
        process MDP model checking results
        :return
          True if both min and max meet the treshold (all SAT)
          False if neither meet the threshold (all UNSAT)
          None otherwise (undecided)
        '''
        a = self.meets_threshold(result_min)
        b = self.meets_threshold(result_max)
        if a != b:
            return None
        return a

    def update_optimum(self, new_value):
        '''
        update threshold if the new value improves current optimum
        return True if update took place
        '''
        if not self.value_valid(new_value):
            return False
        if self.optimal_value is not None and not self.op(new_value, self.optimal_value):
            return False

        # optimal value improved
        logger.info(f"New optimal value: {new_value}")
        self.optimal_value = new_value

        # update threshold
        if self.minimizing:
            self.threshold = new_value * (1 - self.epsilon)
        else:
            self.threshold = new_value * (1 + self.epsilon)

        return True


class HoleOptions(OrderedDict):
    '''
    Mapping of hole names to hole options (and to corresponding program constants).
    '''
    
    def __init__(self, *args):
        super().__init__(*args)

    @property
    def holes(self):
        return list(self.keys())

    @property
    def hole_count(self):
        return len(self.holes)

    @property
    def size(self):
        return numpy.prod([len(v)*1.0 for v in self.values()])

    def all_hole_combinations(self):
        return itertools.product(*self.values())

    def __str__(self):
        hole_options = []
        for hole,options in self.items():
            if len(options) > 1:
                hole_options.append("{}: {}".format(hole,options))
            else:
                hole_options.append("{}={}".format(hole,options[0]))
        return ", ".join(hole_options)

    def __repr__(self):
        return self.__str__()

    def pick_any(self):
        assignment = HoleOptions()
        for hole in self.holes:
            assignment[hole] = [self[hole][0]]
        return assignment

    # def construct_assignment(self, hole_combination):
    #     return HoleOptions({hole:[hole_combination[index]] for index,hole in enumerate(self.holes)})

    # def readable_assignment(self, assignment):
    #     return ",".join([f"{hole}={options[0]}" for hole,options in assignment.items()])

    

class DesignSpace(HoleOptions):
    ''' Hole options equipped with z3 encoding. '''

    # z3 solver
    solver = None
    # mapping of z3 variables to hole names
    solver_var_to_hole = None

    # mapping of holes to their indices
    hole_indices = None
    # mapping of hole options to their indices for each hole
    hole_option_indices = None

    def __init__(self, hole_options, properties = None):
        super().__init__(hole_options)   
        # constraints to investigate in this design space
        self.properties = properties
        # z3 formula encoding this design space
        self.encoding = None

    def set_properties(self, properties):
        self.properties = properties

    def z3_initialize(self):
        ''' Use this design space as a baseline for future refinements. '''
        DesignSpace.solver = z3.Solver()
        DesignSpace.solver_var_to_hole = OrderedDict()
        for hole, options in self.items():
            var = z3.Int(hole)
            DesignSpace.solver.add(var >= 0)
            DesignSpace.solver.add(var < len(options))
            DesignSpace.solver_var_to_hole[var] = hole

        # map holes to their indices and hole options to their indices
        DesignSpace.hole_indices = {hole:index for index,hole in enumerate(self.holes)}
        DesignSpace.hole_option_indices = dict()
        for hole, options in self.items():
            indices = {option:index for index,option in enumerate(options)}
            DesignSpace.hole_option_indices[hole] = indices

    def z3_encode(self):
        ''' Encode this family. '''
        hole_clauses = dict()
        for var, hole in DesignSpace.solver_var_to_hole.items():
            hole_clauses[hole] = z3.Or(
                [var == DesignSpace.hole_option_indices[hole][option] for option in self[hole]]
            )
        self.encoding = z3.And(list(hole_clauses.values()))

    def pick_assignment(self):
        '''
        Pick any (feasible) hole assignment.
        :return None if no instance remains
        '''
        # get satisfiable assignment within this design space
        solver_result = DesignSpace.solver.check(self.encoding)
        if solver_result != z3.sat:
            # no further instances
            return None

        # construct the corresponding singleton (a single-member family)
        sat_model = DesignSpace.solver.model()
        assignment = HoleOptions()
        for var, hole in DesignSpace.solver_var_to_hole.items():
            assignment[hole] = [self[hole][sat_model[var].as_long()]]
        return assignment

    def exclude_assignment(self, assignment, conflict):
        '''
        Exclude assignment from all design spaces using provided conflict.
        :param assignment hole option that yielded DTMC of interest
        :param indices of relevant holes in the counterexample
        '''
        counterexample_clauses = dict()
        for var, hole in DesignSpace.solver_var_to_hole.items():
            if DesignSpace.hole_indices[hole] in conflict:
                option_index = DesignSpace.hole_option_indices[hole][assignment[hole][0]]
                counterexample_clauses[hole] = (var == option_index)
            else:
                all_options = [var == DesignSpace.hole_option_indices[hole][option] for option in self[hole]]
                counterexample_clauses[hole] = z3.Or(all_options)
        counterexample_encoding = z3.Not(z3.And(list(counterexample_clauses.values())))
        DesignSpace.solver.add(counterexample_encoding)

    def index_map(self, subspace):
        '''
        Map options of a supplied subspace to indices of the corresponding
        options in this design space.
        '''
        result = OrderedDict()
        for hole,values in subspace.items():
            result[hole] = []
            for v in values:
                for index, ref in enumerate(self[hole]):
                    if ref == v:
                        result[hole].append(index)
        return result

class EdgeColoring:

    def __init__(self, hole_options):
        self.hole_options = hole_options

        self.coloring = dict()
        self.reverse_coloring = dict()

    def __len__(self):
        return len(self.reverse_coloring)

    def __str__(self):
        return "EdgeColors BW{0}\nEdgeColors BW{1}".format(
            ";".join([str(k) + ":" + self._hole_assignment_to_string(v) for k, v in self.reverse_coloring.items()]),
            ";".join([self._hole_assignment_to_string(v) + ": " + str(k) for v, k in self.coloring.items()])
        )

    def _hole_assignment_to_string(self, v):
        return f"{', '.join(['{}: {}'.format(x, y) for x, y in zip(self.hole_options.keys(), v) if y is not None])}"

    def _full_hole_assignment(self, partial_hole_assignment):
        # result = [partial_hole_assignment.get(key, None) for key in self.hole_options]
        return tuple(self._full_hole_assignment(partial_hole_assignment))

    def get_or_make_color(self, full_hole_assignment):
        _fha = full_hole_assignment  # self._full_hole_assignment(partial_hole_assignment)
        color = self.coloring.get(_fha, len(self.coloring) + 1)
        if color == len(self.coloring) + 1:
            self.coloring[_fha] = color
            self.reverse_coloring[color] = _fha

        # print("{} gets color {}".format(full_hole_assignment, color))
        return color

    def get_hole_assignment(self, color):
        assert color != 0
        return self.reverse_coloring[color]

    def subcolors(self, sub_hole_options):
        assert sub_hole_options.keys() == self.hole_options.keys()
        colors = set()
        for hole_assignment, color in self.coloring.items():
            # print(f"Consider hole_assignment {self._hole_assignment_to_string(hole_assignment)} with color {color}")
            contained = True
            for hole, assignment in zip(sub_hole_options, hole_assignment):
                if assignment is None:
                    continue
                if assignment not in sub_hole_options[hole]:
                    # print(f"Do not add for assignment {assignment} on hole {hole}")
                    contained = False
                    break
            if contained:
                colors.add(color)
        return colors

    def get_hole_assignment_set_colors(self, colors):
        result = dict()
        for color in colors:
            if color == 0:
                continue
            _fha = self.get_hole_assignment(color)
            for hole, assignment in zip(self.hole_options, _fha):
                if assignment is not None:
                    old = result.get(hole, set())
                    old.add(assignment)
                    result[hole] = old

        return result

    def get_hole_assignments(self, lists_colors):
        result = dict()
        for index, colors in enumerate(lists_colors):
            for color in colors:
                if color == 0:
                    continue
                _fha = self.get_hole_assignment(color)
                for hole, assignment in zip(self.hole_options, _fha):
                    if assignment is not None:
                        old = result.get(hole, dict())
                        new_list = old.get(assignment, [])
                        new_list.append(index)
                        old[assignment] = new_list
                        result[hole] = old
        return result

    def violating_colors(self):
        for _, __ in self.coloring.items():
            pass

class Sketch:
    
    # TODO command-line option

    def __init__(self, sketch_path, properties_path, constant_str):
        self.constant_str = constant_str
        self.properties = None
        self.optimality_property = None
        self.design_space = None
        self.pomdp_memory_size = 3 # FIXME as a CLI argument

        self.prism = None
        self.jani = None

        logger.info(f"Loading sketch from {sketch_path} with constants {constant_str} ...")
        self.prism, hole_options = Sketch.load_sketch(sketch_path, constant_str)

        logger.info(f"Loading properties from {properties_path} with constants {constant_str} ...")
        self.properties, self.optimality_property = Sketch.parse_properties(self.prism, properties_path, constant_str)
        
        self.design_space = DesignSpace(hole_options, self.properties)

        logger.debug(f"Sketch has {self.design_space.hole_count} holes: {self.design_space.holes}")
        logger.debug(f"Hole options: {self.design_space}")
        logger.info(f"Design space: {self.design_space.size}")


    @classmethod
    def constants_map(cls, prism, constant_str):
        constant_str = constant_str.replace(" ", "")
        if constant_str == "":
            return dict()
        constants_map = dict()
        kvs = constant_str.split(",")
        ep = stormpy.storage.ExpressionParser(prism.expression_manager)
        ep.set_identifier_mapping(dict())

        holes = {c.name:c for c in prism.constants}

        for kv in kvs:
            key_value = kv.split("=")
            if len(key_value) != 2:
                raise ValueError(f"Expected key=value pair, got '{kv}'.")

            expr = ep.parse(key_value[1])
            constants_map[holes[key_value[0]].expression_variable] = expr
        return constants_map
    

    @classmethod
    def load_sketch(cls, sketch_path, constant_str):
        # read lines
        with open(sketch_path) as f:
            sketch_lines = f.readlines()

        # strip hole definitions
        hole_re = re.compile(r'^hole\s+(.*?)\s+(.*?)\s+in\s+\{(.*?)\};$')
        sketch_output = []
        hole_definitions = OrderedDict()
        for line in sketch_lines:
            match = hole_re.search(line)
            if match is not None:
                hole_name = match.group(2)
                hole_definitions[hole_name] = match.group(3).replace(" ", "")
                line = f"const {match.group(1)} {hole_name};"
            sketch_output.append(line)

        # store stripped sketch to a temporary file
        tmp_path = sketch_path + str(uuid.uuid4())
        with open(tmp_path, 'w') as f:
            for line in sketch_output:
                print(line, end="", file=f)

        # try to parse temporary sketch and then delete it
        parse_error = False
        try:
            prism = stormpy.parse_prism_program(tmp_path)
        except:
            parse_error = True
        os.remove(tmp_path)
        if parse_error:
            exit()

        # substitute constants
        prism = prism.define_constants(cls.constants_map(prism,constant_str))

        # parse hole definitions
        hole_options = HoleOptions()
        ep = stormpy.storage.ExpressionParser(prism.expression_manager)
        ep.set_identifier_mapping(dict())    
        for hole, definition in hole_definitions.items():
            options = definition.split(",")
            hole_options[hole] = [ep.parse(o) for o in options]

        # collect undefined constants (must be the holes)
        program_constants = OrderedDict([(c.name, c) for c in prism.constants if not c.defined])
        assert len(program_constants.keys()) == hole_options.hole_count, "some constants were unspecified"

        # convert single-valued holes to a defined constant
        constant_definitions = dict()
        holes_to_remove = []
        for hole,options in hole_options.items():
            if len(options) == 1:
                constant_definitions[program_constants[hole].expression_variable] = options[0]
                holes_to_remove.append(hole)
        
        for hole in holes_to_remove:
            del hole_options[hole]

        # define constants in the program
        prism = prism.define_constants(constant_definitions)
        prism = prism.substitute_constants()

        # success
        return prism, hole_options

 
    @classmethod
    def parse_properties(cls, prism, properites_path, constant_str):
        # read lines
        lines = []
        with open(properites_path) as file:
            for line in file:
                line = line.replace(" ", "")
                line = line.replace("\n", "")
                if not line or line == "" or line.startswith("//"):
                    continue
                lines.append(line)

        # strip relative error
        lines_properties = ""
        relative_error_re = re.compile(r'^(.*)\{(.*?)\}(=\?.*?$)')
        relative_error_str = None
        for line in lines:
            match = relative_error_re.search(line)
            if match is not None:
                relative_error_str = match.group(2)
                line = match.group(1) + match.group(3)
            lines_properties += line + ";"
        optimality_epsilon = float(relative_error_str) if relative_error_str is not None else 0

        # parse all properties
        properties = []
        optimality_property = None
        for prop in stormpy.parse_properties_for_prism_program(lines_properties, prism):
            rf = prop.raw_formula
            assert rf.has_bound != rf.has_optimality_type, "optimizing formula contains a bound or a comparison formula does not"
            if rf.has_bound:
                # comparison formula
                properties.append(prop)
            else:
                # optimality formula
                assert optimality_property is None, "two optimality formulae specified"
                optimality_property = prop

        # substitute constants in properties
        constants_map = cls.constants_map(prism, constant_str)
        for p in properties:
            p.raw_formula.substitute(constants_map)
        if optimality_property is not None:
            optimality_property.raw_formula.substitute(constants_map)

        # wrap properties
        properties = [Property(p, prism) for p in properties]
        if optimality_property is not None:
            optimality_property = Property(optimality_property, prism, optimality_epsilon)

        return properties, optimality_property


    # JANI stuff

    def construct_jani(self):
        logger.debug("Constructing JANI program...")
        
        # pack properties
        properties = [p.property for p in self.properties]
        if self.optimality_property is not None:
            properties += [self.optimality_property.property]

        # construct jani
        self.jani, new_properties = self.prism.to_jani(properties)
        assert self.prism.expression_manager == self.jani.expression_manager  # sanity check

        # unpack properties
        properties = new_properties
        optimality_property = None
        optimality_epsilon = None
        if self.optimality_property is not None:
            properties = new_properties[:-1]
            optimality_property = new_properties[-1]
            optimality_epsilon = self.optimality_property.epsilon

        # re-wrap properties
        self.properties = [Property(p, self.jani) for p in properties]
        self.optimality_property = Property(optimality_property, self.jani, optimality_epsilon) if optimality_property is not None else None
        self.design_space.set_properties(self.properties)

        # unfold holes in the program
        self.unfold_jani()

    # Unfold holes in the jani program
    def unfold_jani(self):
        jani = self.jani
        self.open_constants = [c for c in self.jani.constants if not c.defined]
        assert len(self.open_constants) == len(self.design_space.keys())
        self.expr_to_const = {c.expression_variable : c for c in self.open_constants}

        self.edge_coloring = EdgeColoring(self.design_space)
        
        jani_program = stormpy.JaniModel(self.jani)
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
        logger.debug(f"Number of colors: {len(self.edge_coloring)}")

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
                new_edges.append(self.construct_edge(edge,combination))
        return new_edges

    def construct_edge(self, edge, combination = None):

        guard = stormpy.Expression(edge.template_edge.guard)
        dests = [(d.target_location_index, d.probability) for d in edge.destinations]

        if combination is not None:
            substitution = {
                    c.expression_variable: self.design_space[c.name][v]
                    for c,v in zip(self.open_constants, combination) if v is not None
                }
            guard = guard.substitute(substitution)
            dests = [(t, p.substitute(substitution)) for (t,p) in dests]

        templ_edge = stormpy.storage.JaniTemplateEdge(guard)
        for templ_edge_dest in edge.template_edge.destinations:
            assignments = templ_edge_dest.assignments.clone()
            if combination is not None:
                assignments.substitute(substitution)
            templ_edge.add_destination(stormpy.storage.JaniTemplateEdgeDestination(assignments))

        new_edge = stormpy.storage.JaniEdge(
            edge.source_location_index, edge.action_index, edge.rate, templ_edge, dests
        )
        if combination is not None:
            new_edge.color = self.edge_coloring.get_or_make_color(combination)

        return new_edge

    def restrict(self, assignment):
        program_constants = OrderedDict([(c.name, c.expression_variable) for c in self.prism.constants if not c.defined])
        substitution = {program_constants[hole]:assignment[hole][0] for hole in assignment.keys()}
        program = self.prism.define_constants(substitution)
        return program


    