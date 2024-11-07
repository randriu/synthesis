import stormpy

class ModelBuilder:

    @classmethod
    def default_builder_options(cls, specification = None):
        # builder options
        if specification is not None:
            formulae = specification.stormpy_formulae()
            builder_options = stormpy.BuilderOptions(formulae)
        else:
            builder_options = stormpy.BuilderOptions()
        builder_options.set_build_state_valuations(True)
        builder_options.set_build_with_choice_origins(True)
        builder_options.set_build_all_labels(True)
        builder_options.set_build_choice_labels(True)
        builder_options.set_add_overlapping_guards_label(True)
        builder_options.set_build_observation_valuations(True)
        builder_options.set_build_all_reward_models(True)
        # builder_options.set_exploration_checks(True)
        return builder_options

    @classmethod
    def from_jani(cls, program, specification = None):
        builder_options = cls.default_builder_options(specification)
        builder_options.set_build_choice_labels(False)
        model = stormpy.build_sparse_model_with_options(program, builder_options)
        return model

    @classmethod
    def from_prism(cls, program, specification = None):
        assert program.model_type in [stormpy.storage.PrismModelType.MDP, stormpy.storage.PrismModelType.POMDP]
        builder_options = cls.default_builder_options(specification)
        model = stormpy.build_sparse_model_with_options(program, builder_options)
        return model

    @classmethod
    def from_drn(cls, drn_path):
        builder_options = stormpy.core.DirectEncodingParserOptions()
        builder_options.build_choice_labels = True
        return stormpy.build_model_from_drn(drn_path, builder_options)
