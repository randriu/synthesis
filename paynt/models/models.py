import stormpy

import paynt.verification.property
import paynt.verification.property_result

import logging
logger = logging.getLogger(__name__)

class Mdp:

    @classmethod
    def assert_no_overlapping_guards(cls, model):
        if model.labeling.contains_label("overlap_guards"):
            assert model.labeling.get_states("overlap_guards").number_of_set_bits() == 0
    
    def __init__(self, model):
        # Mdp.assert_no_overlapping_guards(model)
        self.model = model
        if len(model.initial_states) > 1:
            logger.warning("WARNING: obtained model with multiple initial states")

    @property
    def states(self):
        return self.model.nr_states

    @property
    def is_deterministic(self):
        return self.model.nr_choices == self.model.nr_states

    @property
    def initial_state(self):
        return self.model.initial_states[0]

    def model_check_property(self, prop, alt=False):
        formula = prop.formula if not alt else prop.formula_alt
        result = paynt.verification.property.Property.model_check(self.model,formula)
        value = result.at(self.initial_state)
        return paynt.verification.property_result.PropertyResult(prop, result, value)

class SubMdp(Mdp):

    def __init__(self, model, quotient_state_map, quotient_choice_map):
        super().__init__(model)
        self.quotient_choice_map = quotient_choice_map
        self.quotient_state_map = quotient_state_map
