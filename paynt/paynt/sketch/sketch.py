import stormpy

from .property import Property, OptimalityProperty, Specification
from .holes import Hole, Holes, DesignSpace
from ..synthesizers.models import MarkovChain
from ..synthesizers.quotient import *
from ..profiler import Profiler

from collections import defaultdict

import os
import re
import uuid

import logging
logger = logging.getLogger(__name__)

class Sketch:

    # if True, unfolded JANI is exported and the program is aborted
    export_jani = False
    # if True, POMDP is exported to *.pomdp and the program is aborted
    export_pomdp = False
    # if True, the sketch is assumed to be a hole-free MDP
    hyperproperty_synthesis = False

    def __init__(self, sketch_path, properties_path, constant_str):

        Profiler.initialize()
        Profiler.start("sketch")
        
        self.explicit_model = None
        self.prism = None
        self.hole_expressions = None

        self.design_space = None
        self.specification = None
        self.quotient = None

        constant_map = None
        expression_parser = None

        logger.info(f"Loading sketch from {sketch_path}...")
        logger.info(f"Attempting to parse model as a POMDP in explicit format ...")
        self.explicit_model = Sketch.read_pomdp_model(sketch_path)

        if self.is_explicit:
            logger.info(f"Successfully parsed model in explicit format.")
            self.design_space = DesignSpace()
        else:
            logger.info(f"Assuming a sketch in a PRISM format ...")
            self.prism, hole_definitions = Sketch.load_sketch(sketch_path)

            expression_parser = stormpy.storage.ExpressionParser(self.prism.expression_manager)
            expression_parser.set_identifier_mapping(dict())

            if constant_str != '':
                logger.info(f"Assuming constant definitions: '{constant_str}' ...")
                constant_map = Sketch.map_constants(self.prism, expression_parser, constant_str)
                self.prism = self.prism.define_constants(constant_map)
                self.prism = self.prism.substitute_constants()

            if len(hole_definitions) == 0:
                logger.info("Sketch does not contain any hole definitions.")
                self.design_space = DesignSpace()
            else:
                logger.info("Processing hole definitions ...")
                self.prism, self.hole_expressions, self.design_space = Sketch.parse_holes(self.prism, expression_parser, hole_definitions)
                
                logger.info(f"Sketch has {self.design_space.num_holes} holes")
                # logger.info(f"Listing hole domains: {holes}"
                logger.info(f"Design space size: {self.design_space.size}")

        logger.info(f"Loading properties from {properties_path} ...")
        self.specification = Sketch.parse_specification(self.prism, constant_map, properties_path)
        logger.info(f"Found the following specification: {self.specification}")
        self.design_space.property_indices = self.specification.all_constraint_indices()
        MarkovChain.initialize(self.specification.stormpy_formulae())
        
        logger.info(f"Initializing the quotient ...")

        if self.is_dtmc:
            self.quotient = DTMCQuotientContainer(self)
        elif self.is_ma:
            self.quotient = MAQuotientContainer(self)
        elif self.is_mdp:
            if Sketch.hyperproperty_synthesis:
                self.quotient = HyperPropertyQuotientContainer(self)
            else:
                self.quotient = MDPQuotientContainer(self)
        elif self.is_pomdp:
            self.quotient = POMDPQuotientContainer(self)
            self.quotient.pomdp_manager.set_memory_size(POMDPQuotientContainer.pomdp_memory_size)
            self.quotient.unfold_memory()
            if Sketch.export_pomdp:
                Sketch.write_model_in_pomdp_solve_format(sketch_path, self.quotient)
                exit()
        else:
            raise TypeError("sketch type is not supported")

        logger.info(f"Sketch parsing complete.")
        Profiler.stop()


    @property
    def is_explicit(self):
        return self.explicit_model is not None

    @property
    def is_dtmc(self):
        return not self.is_explicit and self.prism.model_type == stormpy.storage.PrismModelType.DTMC
    
    @property
    def is_ctmc(self):
        return not self.is_explicit and self.prism.model_type == stormpy.storage.PrismModelType.CTMC

    @property
    def is_ma(self):
        return not self.is_explicit and self.prism.model_type == stormpy.storage.PrismModelType.MA

    @property
    def is_mdp(self):
        return not self.is_explicit and self.prism.model_type == stormpy.storage.PrismModelType.MDP

    @property
    def is_pomdp(self):
        if self.is_explicit:
            return self.explicit_model.is_nondeterministic_model and self.explicit_model.is_partially_observable
        else:
            return self.prism.model_type == stormpy.storage.PrismModelType.POMDP

    @classmethod
    def read_pomdp_model(cls, sketch_path):
        # attempt to read in a pomdp-solve format
        drn = Sketch.read_pomdp_solve_format(sketch_path)
        if drn is None:
            # failure
            explicit_model = Sketch.read_explicit_format(sketch_path)
        else:
            # success: write drn model to temporary file and try to parse
            drn_path = sketch_path + str(uuid.uuid4())
            with open(drn_path, 'w') as f:
                f.write(drn)
            explicit_model = Sketch.read_explicit_format(drn_path)

            # removing temporary file
            os.remove(drn_path)
        return explicit_model


    @classmethod
    def read_explicit_format(cls, sketch_path):
        explicit_model = None
        try:
            builder_options = stormpy.core.DirectEncodingParserOptions()
            builder_options.build_choice_labels = True
            explicit_model = stormpy.core._build_sparse_model_from_drn(sketch_path, builder_options)
        except:
            pass
        return explicit_model

    @classmethod
    def write_model_in_pomdp_solve_format(cls, path, quotient):

        pomdp = quotient.pomdp

        num_states = pomdp.nr_states
        num_obs = quotient.observations
        num_choices = max([quotient.actions_at_observation[obs] for obs in range(num_obs)])

        desc = """\
# auto-generated from PRISM program

discount: 0.95
values: reward
states: {}
actions: {}
observations: {}

""".format(num_states,num_choices,num_obs)

        # initial state
        state_init = pomdp.initial_states[0]
        initial_distr = [1 if state == state_init else 0 for state in range(num_states)]
        initial_distr = [str(x) for x in initial_distr]
        initial_distr = ' '.join(initial_distr)
        desc += f"start:\n{initial_distr}\n\n"

        # transition matrix
        desc += "# transition matrix\n\n"

        tm = pomdp.transition_matrix
        for state in range(num_states):
            action_index = 0
            group_start = tm.get_row_group_start(state)
            group_end = tm.get_row_group_end(state)
            trivial_action = group_end == group_start + 1
            for row_index in range(group_start, group_end):
                for entry in tm.get_row(row_index):
                    action_index_str = action_index if not trivial_action else "*"
                    desc += f"T: {action_index_str} : {state} : {entry.column} {entry.value()}\n"
                action_index += 1

        # observations
        desc += "\n# observations\n\n"
        for state in range(num_states):
            desc += f"O: * : {state} : {pomdp.observations[state]} 1\n"

        # rewards
        desc += "\n# rewards\n\n"

        rewards = next(iter(pomdp.reward_models.values()))
        assert rewards.has_state_rewards and not rewards.has_state_action_rewards
        for state in range(num_states):
            rew = rewards.state_rewards[state]
            if rew != 0:
                desc += f"R: * : {state} : * : * {rew}\n"


        output_path = path.split('.')
        output_path[-1] = '.pomdp'
        output_path = ''.join(output_path)
        property_path = path.split('/')
        property_path[-1] = 'props.pomdp'
        property_path = '/'.join(property_path)
        
        logger.info("Printing POMDP in pomdp-solve format to {} ...".format(output_path))
        with open(output_path, 'w') as f:
            f.write(desc)
        logger.info("Printing default discounting property to {} ...".format(property_path))
        with open(property_path, 'w') as f:
            f.write('R{"rew0"}max=? [F "target"]')
        logger.info("Write OK, aborting ...")
        exit()


    @classmethod
    def read_pomdp_solve_format(cls, path):

        # read lines
        with open(path) as f:
            sketch_lines = f.readlines()

        # function to read an explicit list of state/action/observation labels
        def explicit_labels(result):
            # try to split
            labels = result.group(1).split(' ')
            if len(labels) == 1:
                num_labels = int(result.group(1))
                labels = [str(label) for label in range(num_labels)]
            return labels

        def read_distribution(line, labels):
            distr = line.split()
            distr = [float(prob) for prob in distr]
            distr = {labels[index]:prob for index,prob in enumerate(distr) if prob > 0}
            return distr

        # read basic parameters
        discount = None
        state_list = None
        choice_list = None
        obs_list = None
        for line in sketch_lines:
            result = re.match(r'^\s*discount:(.*?)\s*$', line)
            if result is not None:
                discount = float(result.group(1))
            result = re.match(r'^\s*states:\s*(.*?)\s*$', line)
            if result is not None:
                state_list = explicit_labels(result)
            result = re.match(r'^\s*actions:\s*(.*?)\s*$', line)
            if result is not None:
                choice_list = explicit_labels(result)
            result = re.match(r'^\s*observations:\s*(.*?)\s*$', line)
            if result is not None:
                obs_list = explicit_labels(result)
        # if any of the basic parameters is missing, this is not a pomdp-solve format
        if discount is None:
            return None

        # add initial state and a sink state
        init_label = "_init"
        sink_label = "_sink"
        state_list_expanded = state_list + [init_label, sink_label]
        choice_list_expanded = choice_list + [init_label, sink_label]
        obs_list_expanded = obs_list + [init_label, sink_label]

        # read target states
        target_states = []
        for line in sketch_lines:
            result = re.match(r'^\s*#@targets:\s*(.*?)\s*$', line)
            if result is not None:
                target_states = result.group(1).split(' ')
                break
        target_states += [sink_label]

        # read observations
        state_to_obs = dict()
        state_to_obs[init_label] = init_label
        state_to_obs[sink_label] = sink_label
        
        # case 1: deterministic observations
        # O: action : dst : obs prob
        # -> O: * : state : obs 1
        for line in sketch_lines:
            result = re.match(r'^\s*O\s*:\s*\*\s*:\s*(\S+)\s*:\s*(\S+).*?$', line)
            if result is not None:
                state = result.group(1)
                obs = result.group(2)
                state_to_obs[state] = obs

        # case 2: for each state probabilistic observations
        # O: action : dst
        # -> O: * : state
        for index,line in enumerate(sketch_lines):
            result = re.match(r'^\s*O\s*:\s*\*\s*:\s*(\S+)\s*$', line)
            if result is not None:
                state = result.group(1)
                distr = read_distribution(sketch_lines[index+1], obs_list)
                obs = max(distr, key=distr.get)
                state_to_obs[state] = obs
                print("O: * : {} : {} 1".format(state,obs))

        # case 3: a list of observation distributions to each state
        # O: action -> O: *
        for index,line in enumerate(sketch_lines):
            result = re.match(r'^\s*O\s*:\s*\*\s*$', line)
            if result is not None:
                for state_index,state in enumerate(state_list):
                    next_line = sketch_lines[index+1+state_index]
                    distr = read_distribution(next_line, obs_list)
                    obs = max(distr, key=distr.get)
                    state_to_obs[state] = obs
                    print("O: * : {} : {} 1".format(state,obs))
        
        # construct transition matrix
        transition_matrix = {state:defaultdict(dict) for state in state_list_expanded}
        
        # initial distribution
        initial_distr = None
        for index,line in enumerate(sketch_lines):
            result = re.match(r'^\s*start:(.*?)\s*$', line)
            if result is not None:
                initial_distr = read_distribution(sketch_lines[index+1], state_list)
                break
        if initial_distr is None:
            # no initial distribution given = choose uniformly
            initial_distr = {state:1/len(state_list) for state in state_list}
        transition_matrix[init_label] = {init_label: initial_distr}

        # sink self-loop
        transition_matrix[sink_label] = {sink_label: {sink_label: 1}}

        # other states from file
        # note: in the following, action may be *
        
        # case 1: each transition separately
        # T: action : src : dst prob
        for line in sketch_lines:
            result = re.match(r'^\s*T\s*:\s*(\S*?)\s*:\s*(\S*?)\s*:\s*(\S*?)\s*(\S*?)\s*$', line)
            if result is not None:
                action = result.group(1)
                if action == '*':
                    applied_actions = choice_list
                else:
                    applied_actions = [action]
                src = result.group(2)
                dst = result.group(3)
                prob = float(result.group(4))
                for action in applied_actions:
                    transition_matrix[src][action][dst] = prob

        # case 2: to each state a probability distribution
        # T: action : src
        for index,line in enumerate(sketch_lines):
            result = re.match(r'^\s*T\s*:\s*(\S+?)\s*:\s*(\S+)\s*$', line)
            if result is not None:
                action = result.group(1)
                if action == '*':
                    applied_actions = choice_list
                else:
                    applied_actions = [action]
                src = result.group(2)
                for action in applied_actions:
                    next_line = sketch_lines[index+1]
                    distr = read_distribution(next_line, state_list)
                    transition_matrix[src][action] = distr

        # case 3: to a given action, for each state a probability distribution
        # T: action
        for index,line in enumerate(sketch_lines):
            result = re.match(r'^\s*T\s*:\s*(\S*?)\s*$', line)
            if result is not None:
                action = result.group(1)
                for state_index,state_label in enumerate(state_list):
                    next_line = sketch_lines[index+1+state_index]
                    distr = read_distribution(next_line, state_list)
                    transition_matrix[state_label][action] = distr

        # normalize wrt discount factor
        for state in state_list:
            rows = transition_matrix[state]
            rows_new = {}
            for action,row in rows.items():
                row_new = {dst:prob*discount for dst,prob in row.items()}
                row_new[sink_label] = 1-discount
                rows_new[action] = row_new
            transition_matrix[state] = rows_new

        # read state rewards
        state_rewards = defaultdict(int)
        # R: action : src : dst : obs rew
        # R: * : state : * : * rew
        for line in sketch_lines:
            result = re.match(r'^\s*R\s*:\s*\*\s*:\s*(\S*?)\s*:\s*\*\s*:\s*\*\s*(\S*?)\s*$', line)
            if result is not None:
                state = result.group(1)
                rew = float(result.group(2))
                state_rewards[state] = rew

        # compute the total number of rows
        num_states = len(state_list_expanded)
        num_choices = 0
        for state in state_list_expanded:
            num_choices += len(transition_matrix[state])

        # convert to explicit .drn model
        model = """\
@type: POMDP
@parameters

@nr_states
{}
@nr_choices
{}

@model
""".format(num_states,num_choices)

        def map_list_to_indices(lst):
            list_to_index = {}
            for index,x in enumerate(lst):
                list_to_index[x] = index
            return list_to_index

        state_to_index = map_list_to_indices(state_list_expanded)
        choice_to_index = map_list_to_indices(choice_list_expanded)
        obs_to_index = map_list_to_indices(obs_list_expanded)

        # map state to indices of observations
        state_to_obs_index = {}
        for state in state_list_expanded:
            obs = state_to_obs[state] if state in state_to_obs else state_to_obs["*"]
            obs_index = obs_to_index[obs]
            state_to_obs_index[state] = obs_index

        # write state transitions
        for state in state_list_expanded:
            model += "state " + str(state_to_index[state]) + " {" + str(state_to_obs_index[state]) + "}"
            if state == init_label:
                model += " init"
            if state in target_states:
                model += " target"
            model += "\n"

            for action,row in transition_matrix[state].items():
                model += "\taction {} [{}]\n".format(choice_to_index[action], state_rewards[state])
                for dst,prob in row.items():
                    model += "\t\t{} : {}\n".format(state_to_index[dst],prob)

        # print(model)
        # exit()
        return model



    @classmethod
    def load_sketch(cls, sketch_path):
        # read lines
        with open(sketch_path) as f:
            sketch_lines = f.readlines()

        # replace hole definitions with constants
        hole_re = re.compile(r'^hole\s+(.*?)\s+(.*?)\s+in\s+\{(.*?)\};$')
        sketch_output = []
        hole_definitions = {}
        for line in sketch_lines:
            match = hole_re.search(line)
            if match is not None:
                hole_type = match.group(1)
                hole_name = match.group(2)
                hole_options = match.group(3).replace(" ", "")
                hole_definitions[hole_name] = hole_options
                line = f"const {hole_type} {hole_name};"
            sketch_output.append(line)

        # store modified sketch to a temporary file
        tmp_path = sketch_path + str(uuid.uuid4())
        with open(tmp_path, 'w') as f:
            for line in sketch_output:
                print(line, end="", file=f)

        # try to parse temporary sketch and then delete it
        try:
            prism = stormpy.parse_prism_program(tmp_path, prism_compat=True)
            os.remove(tmp_path)
        except:
            os.remove(tmp_path)

        return prism, hole_definitions

 
    @classmethod
    def map_constants(cls, prism, expression_parser, constant_str):
        constant_str = constant_str.replace(" ", "")
        if constant_str == "":
            return dict()
        
        constant_map = dict()
        constant_definitions = constant_str.split(",")
        prism_constants = {c.name:c for c in prism.constants}

        for constant_definition in constant_definitions:
            key_value = constant_definition.split("=")
            if len(key_value) != 2:
                raise ValueError(f"Expected key=value pair, got '{constant_definition}'.")

            expr = expression_parser.parse(key_value[1])
            name = key_value[0]
            constant = prism_constants[name].expression_variable
            constant_map[constant] = expr
        return constant_map


    @classmethod
    def parse_holes(cls, prism, expression_parser, hole_definitions):

        # parse hole definitions
        holes = Holes()
        hole_expressions = []
        for hole_name,definition in hole_definitions.items():
            options = definition.split(",")
            expressions = [expression_parser.parse(o) for o in options]
            hole_expressions.append(expressions)

            options = list(range(len(expressions)))
            option_labels = [str(e) for e in expressions]
            hole = Hole(hole_name, options, option_labels)
            holes.append(hole)

        # check that all undefined constants are indeed the holes
        undefined_constants = [c for c in prism.constants if not c.defined]
        assert len(undefined_constants) == len(holes), "some constants were unspecified"

        # convert single-valued holes to a defined constant
        trivial_holes_definitions = {}
        nontrivial_holes = Holes()
        nontrivial_hole_expressions = []
        for hole_index,hole in enumerate(holes):
            if hole.size == 1:
                trivial_holes_definitions[prism.get_constant(hole.name).expression_variable] = hole_expressions[hole_index][0]
            else:
                nontrivial_holes.append(hole)
                nontrivial_hole_expressions.append(hole_expressions[hole_index])
        holes = nontrivial_holes
        hole_expressions = nontrivial_hole_expressions

        # substitute trivial holes
        prism = prism.define_constants(trivial_holes_definitions)
        prism = prism.substitute_constants()
    
        design_space = DesignSpace(holes)

        return prism, hole_expressions, design_space

 
    @classmethod
    def parse_specification(cls, prism, constant_map, properites_path):
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

        if prism is not None:
            props = stormpy.parse_properties_for_prism_program(lines_properties, prism)
        else:
            props = stormpy.parse_properties_without_context(lines_properties)
        for prop in props:
            rf = prop.raw_formula
            assert rf.has_bound != rf.has_optimality_type, "optimizing formula contains a bound or a comparison formula does not"
            if rf.has_bound:
                # comparison formula
                properties.append(prop)
            else:
                # optimality formula
                assert optimality_property is None, "two optimality formulae specified"
                optimality_property = prop

        if constant_map is not None:
            # substitute constants in properties
            for p in properties:
                p.raw_formula.substitute(constant_map)
            if optimality_property is not None:
                optimality_property.raw_formula.substitute(constant_map)

        # wrap properties
        properties = [Property(p) for p in properties]
        if optimality_property is not None:
            optimality_property = OptimalityProperty(optimality_property, optimality_epsilon)

        specification = Specification(properties,optimality_property)
        return specification
    

    def restrict_prism(self, assignment):
        assert assignment.size == 1
        substitution = {}
        for hole_index,hole in enumerate(assignment):
            ev = self.prism.get_constant(hole.name).expression_variable
            expr = self.hole_expressions[hole_index][hole.options[0]]
            substitution[ev] = expr
        program = self.prism.define_constants(substitution)
        model = stormpy.build_sparse_model_with_options(program, MarkovChain.builder_options)
        return model

    
    