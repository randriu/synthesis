import stormpy

import paynt.verification.property
import paynt.verification.property_result

import logging
logger = logging.getLogger(__name__)

class Mdp:

    # options for the construction of chains
    builder_options = None

    @classmethod
    def initialize(cls, specification):
        # builder options
        formulae = specification.stormpy_formulae()
        cls.builder_options = stormpy.BuilderOptions(formulae)
        cls.builder_options.set_build_with_choice_origins(True)
        cls.builder_options.set_build_state_valuations(True)
        cls.builder_options.set_add_overlapping_guards_label()
        cls.builder_options.set_build_observation_valuations(True)
        cls.builder_options.set_build_all_labels(True)
        # cls.builder_options.set_exploration_checks(True)

    @classmethod
    def assert_no_overlapping_guards(cls, model):
        if model.labeling.contains_label("overlap_guards"):
            assert model.labeling.get_states("overlap_guards").number_of_set_bits() == 0
    
    @classmethod
    def from_prism(cls, prism):
        assert prism.model_type in [stormpy.storage.PrismModelType.MDP, stormpy.storage.PrismModelType.POMDP]
        # TODO why do we disable choice labels here?
        Mdp.builder_options.set_build_choice_labels(True)
        model = stormpy.build_sparse_model_with_options(prism, Mdp.builder_options)
        Mdp.builder_options.set_build_choice_labels(False)
        # Mdp.assert_no_overlapping_guards(model)
        return model

    def __init__(self, model):
        # Mdp.assert_no_overlapping_guards(model)
        if len(model.initial_states) > 1:
            logger.warning("WARNING: obtained model with multiple initial states")
        self.model = model

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
