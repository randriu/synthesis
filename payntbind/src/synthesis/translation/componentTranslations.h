#pragma once

#include <cstdint>
#include <vector>

#include <storm/storage/BitVector.h>
#include <storm/models/sparse/Model.h>
#include <storm/models/sparse/StateLabeling.h>
#include <storm/models/sparse/ChoiceLabeling.h>
#include <storm/models/sparse/StandardRewardModel.h>

namespace synthesis {

    template<typename ValueType>
    storm::models::sparse::StateLabeling translateStateLabeling(
        storm::models::sparse::Model<ValueType> const& model,
        std::vector<uint64_t> const& translated_to_original_state,
        uint64_t translated_initial_state
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

}