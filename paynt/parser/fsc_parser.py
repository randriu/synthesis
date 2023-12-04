# Parser for FSCs extracted from SARSOP alpha-vectors
# Might support other FSC input formats in the future

from paynt.quotient.pomdp_family import FSC

import logging
logger = logging.getLogger(__name__)

class FSCParser:

    @classmethod
    def read_fsc_my_format(self, fsc_path, pomdp_obs_labels, pomdp_act_labels):
        with open(fsc_path) as f:
            fsc_lines = f.readlines()

        p_act_labels = self.transform_act_labels(pomdp_act_labels)
        p_obs_labels = list(pomdp_obs_labels)

        labels_not_available = True

        action_labels = []
        observation_labels = []
        node_actions = []

        fsc_transitions = {}

        try: 
            for line in fsc_lines:
                if line.startswith("#"):
                    continue
                if line.isspace():
                    continue
                if line.startswith("action labels:"):
                    line = line.split(":")
                    action_labels = line[1].strip().split(' ')
                    continue
                if line.startswith("observation labels:"):
                    line = line.split(":")
                    observation_labels = line[1].strip().split(' ')
                    continue
                if line.startswith("nodes:"):
                    line = line.split(":")
                    node_actions = line[1].strip().split(' ')
                    continue

                for label in action_labels:
                    if not label.isdigit():
                        labels_not_available = False
                        break
                
                for label in observation_labels:
                    if not label.isdigit():
                        labels_not_available = False
                        break

                s_init, obs, s_end, _ = line.split()

                if s_init not in fsc_transitions.keys():
                    fsc_transitions[s_init] = {}
                fsc_transitions[s_init][obs] = s_end

            # print(action_labels)
            # print(observation_labels)
            # print(node_actions)
            # print(len(node_actions))
            # print(p_obs_labels)
            # print(p_act_labels)
            # print(fsc_transitions)

            parsed_fsc = FSC(len(node_actions)+1, len(pomdp_obs_labels))

            # TODO I'm not sure that the indeces of the actions/observations in sarsop and here are the same! (SARSOP doesn't support labels in POMDPs right now)
            if labels_not_available:

                # init state, no_obs state, sink state
                # TODO not sure about the action and the memory update here for no_obs
                parsed_fsc.action_function[0][p_obs_labels.index('init')] = 0
                parsed_fsc.update_function[0][p_obs_labels.index('init')] = 0
                parsed_fsc.action_function[0][p_obs_labels.index('__no_obs__')] = int(action_labels[int(node_actions[0])])
                parsed_fsc.update_function[0][p_obs_labels.index('__no_obs__')] = 1
                parsed_fsc.action_function[0][p_obs_labels.index('discount_sink')] = 0
                parsed_fsc.update_function[0][p_obs_labels.index('discount_sink')] = 0
    
                for node_s, node_s_dict in fsc_transitions.items():
                    for obs, node_e in node_s_dict.items():
                        obs_index = int(observation_labels[int(obs)])
                        act_index = int(action_labels[int(node_actions[int(node_e)-1])])
                        parsed_fsc.action_function[int(node_s)][obs_index] = act_index
                        parsed_fsc.update_function[int(node_s)][obs_index] = int(node_e)

            else:

                # init state, no_obs state, sink state
                # TODO not sure about the action and the memory update here for no_obs
                parsed_fsc.action_function[0][p_obs_labels.index('init')] = 0
                parsed_fsc.update_function[0][p_obs_labels.index('init')] = 0
                parsed_fsc.action_function[0][p_obs_labels.index('__no_obs__')] = p_act_labels[0].index(action_labels[int(node_actions[0])])
                parsed_fsc.update_function[0][p_obs_labels.index('__no_obs__')] = 1
                parsed_fsc.action_function[0][p_obs_labels.index('discount_sink')] = 0
                parsed_fsc.update_function[0][p_obs_labels.index('discount_sink')] = 0
    
                for node_s, node_s_dict in fsc_transitions.items():
                    for obs, node_e in node_s_dict.items():
                        obs_index = p_obs_labels.index(observation_labels[int(obs)])
                        act_index = p_act_labels[obs_index].index(action_labels[int(node_actions[int(node_e)-1])])
                        parsed_fsc.action_function[int(node_s)][obs_index] = act_index
                        parsed_fsc.update_function[int(node_s)][obs_index] = int(node_e)

        except:
            raise SyntaxError
        
        return parsed_fsc
        
    @classmethod
    def transform_act_labels(self, pomdp_act_labels):
        result_act_labels = []
        for obs_act_labels in pomdp_act_labels:
            res = []
            for label in obs_act_labels:
                r = str(label.pop())
                r = r.strip("()")
                res.append(r)
            result_act_labels.append(res)

        return result_act_labels
