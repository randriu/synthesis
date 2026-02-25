
import json

import stormpy

import logging
logger = logging.getLogger(__name__)

# TODO make this so that it works for POMDP observation valuations as well
def get_state_valuations(model):
    ''' Identify variable names and extract state valuation in the same order. '''
    assert model.has_state_valuations(), "model has no state valuations"
    # get name
    sv = model.state_valuations
    variable_names = None
    state_valuations = []
    for state in range(model.nr_states):
        valuation = json.loads(str(sv.get_json(state)))
        if variable_names is None:
            variable_names = list(valuation.keys())
        valuation = [valuation[var_name] for var_name in variable_names]
        state_valuations.append(valuation)

    return variable_names, state_valuations