from __future__ import annotations

from typing import Any

import stormpy
from paynt.parser.drn_parser import DrnParser
import paynt.specification.property


class ModelBuilder:

    @classmethod
    def default_builder_options(cls, specification: paynt.specification.property.Specification | None = None) -> Any:
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
    def from_jani(cls, program: Any, specification: paynt.specification.property.Specification | None = None, use_exact: bool = False) -> Any:
        builder_options = cls.default_builder_options(specification)
        builder_options.set_build_choice_labels(False)
        if use_exact:
            model = stormpy.build_sparse_exact_model_with_options(program, builder_options)
        else:
            model = stormpy.build_sparse_model_with_options(program, builder_options)
        return model

    @classmethod
    def from_prism(cls, program: Any, specification: paynt.specification.property.Specification | None = None, use_exact: bool = False) -> Any:
        assert program.model_type in [stormpy.storage.PrismModelType.MDP, stormpy.storage.PrismModelType.POMDP]
        builder_options = cls.default_builder_options(specification)
        if use_exact:
            model = stormpy.build_sparse_exact_model_with_options(program, builder_options)
        else:
            model = stormpy.build_sparse_model_with_options(program, builder_options)
        return model

    @classmethod
    def from_drn(cls, drn_path: str, use_exact: bool = False) -> Any:
        return DrnParser.parse_drn(drn_path, use_exact)
