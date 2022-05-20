import stormpy

from .property import Property, OptimalityProperty, Specification
from .holes import Hole, Holes, DesignSpace
from ..synthesizers.models import MarkovChain
from ..synthesizers.quotient import *
from ..synthesizers.quotient_pomdp import *
from ..profiler import Profiler

from collections import defaultdict

import os
import re
import uuid

import logging

class PomdpParser:

    @classmethod
    def read_pomdp_model(cls, sketch_path):
        # attempt to read in a pomdp-solve format
        drn = PomdpParser.read_pomdp_solve_format(sketch_path)
        if drn is None:
            # failure
            explicit_model = PomdpParser.read_explicit_format(sketch_path)
        else:
            # success: write drn model to temporary file and try to parse
            drn_path = sketch_path + str(uuid.uuid4())
            with open(drn_path, 'w') as f:
                f.write(drn)
            explicit_model = PomdpParser.read_explicit_format(drn_path)

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



    
    
    