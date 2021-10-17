#pragma once

#include "storm/models/sparse/Mdp.h"
#include "storm/models/sparse/Pomdp.h"
#include "storm-pomdp/storage/PomdpMemory.h"
#include "storm/models/sparse/StandardRewardModel.h"

namespace storm {
    namespace transformer {

        template<typename ValueType>
        class ExplicitPomdpMemoryUnfolder {

        public:
            
            ExplicitPomdpMemoryUnfolder(storm::models::sparse::Pomdp<ValueType> const& pomdp, storm::storage::PomdpMemory const& memory, bool addMemoryLabels = false, bool keepStateValuations = false);
            
            std::shared_ptr<storm::models::sparse::Mdp<ValueType>> transform();

            //+
            std::vector<uint64_t> state_to_state();
            std::vector<uint64_t> state_to_memory();
            // std::vector<uint64_t> action_map();
            // std::vector<uint64_t> memory_map();

        private:
            storm::storage::SparseMatrix<ValueType> transformTransitions();
            storm::models::sparse::StateLabeling transformStateLabeling() const;
            std::vector<uint32_t> transformObservabilityClasses(storm::storage::BitVector const& reachableStates) const;
            storm::models::sparse::StandardRewardModel<ValueType> transformRewardModel(storm::models::sparse::StandardRewardModel<ValueType> const& rewardModel, storm::storage::BitVector const& reachableStates) const;
            
            uint64_t getUnfoldingState(uint64_t modelState, uint64_t memoryState) const;
            uint64_t getModelState(uint64_t unfoldingState) const;
            uint64_t getMemoryState(uint64_t unfoldingState) const;
            
            uint32_t getUnfoldingObersvation(uint32_t modelObservation, uint64_t memoryState) const;
            uint32_t getModelObersvation(uint32_t unfoldingObservation) const;
            uint64_t getMemoryStateFromObservation(uint32_t unfoldingObservation) const;
            
            
            storm::models::sparse::Pomdp<ValueType> const& pomdp;
            storm::storage::PomdpMemory const& memory;

            bool addMemoryLabels;
            bool keepStateValuations;

            //+
            std::vector<uint64_t> product_to_pomdp_state;
            std::vector<uint64_t> product_to_pomdp_memory;
            std::vector<uint64_t> choice_action;
            std::vector<uint64_t> choice_memory;
        };
    }
}