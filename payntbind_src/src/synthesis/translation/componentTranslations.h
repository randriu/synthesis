#pragma once

#include <storm/storage/BitVector.h>
#include <storm/adapters/RationalNumberAdapter.h>
#include <storm/models/sparse/Model.h>
#include <storm/models/sparse/StateLabeling.h>
#include <storm/models/sparse/ChoiceLabeling.h>
#include <storm/models/sparse/StandardRewardModel.h>

#include <vector>

namespace synthesis {

/**
 * Copy components from existing model.
 */
template<typename ValueType>
storm::storage::sparse::ModelComponents<ValueType> componentsFromModel(
    storm::models::sparse::Model<ValueType> const& model
);

template<typename ValueType>
storm::models::sparse::StateLabeling translateStateLabeling(
    storm::models::sparse::Model<ValueType> const& model,
    std::vector<uint64_t> const& translated_to_original_state,
    uint64_t translated_initial_state
);

template<typename ValueType>
std::vector<uint32_t> translateObservabilityClasses(
    storm::models::sparse::Model<ValueType> const& model,
    std::vector<uint64_t> const& translated_to_original_state
);

template<typename ValueType>
storm::models::sparse::ChoiceLabeling translateChoiceLabeling(
    storm::models::sparse::Model<ValueType> const& model,
    std::vector<uint64_t> const& translated_to_original_choice,
    storm::storage::BitVector const& translated_choice_mask
);

template<typename ValueType>
storm::models::sparse::StandardRewardModel<ValueType> translateRewardModel(
    storm::models::sparse::StandardRewardModel<ValueType> const& reward_model,
    std::vector<uint64_t> const& translated_to_original_choice,
    storm::storage::BitVector const& translated_choice_mask
);
template<typename ValueType>
std::unordered_map<std::string,storm::models::sparse::StandardRewardModel<ValueType>> translateRewardModels(
    storm::models::sparse::Model<ValueType> const& model,
    std::vector<uint64_t> const& translated_to_original_choice,
    storm::storage::BitVector const& translated_choice_mask
);

template<typename ValueType>
void translateTransitionMatrixRow(
    storm::models::sparse::Model<ValueType> const& model,
    storm::storage::SparseMatrixBuilder<ValueType> & builder,
    std::vector<uint64_t> const& original_to_translated_state,
    std::vector<uint64_t> const& original_to_translated_choice,
    uint64_t choice
);
template<typename ValueType>
void translateTransitionMatrixRowGroup(
    storm::models::sparse::Model<ValueType> const& model,
    storm::storage::SparseMatrixBuilder<ValueType> & builder,
    std::vector<uint64_t> const& original_to_translated_state,
    std::vector<uint64_t> const& original_to_translated_choice,
    uint64_t state
);

}
