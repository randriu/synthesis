#pragma once

#include "storm/models/sparse/Mdp.h"
#include "storm/models/sparse/Pomdp.h"

namespace storm {
    namespace synthesis {

        template<typename ValueType>
        class PomdpManager {

        public:
            
            PomdpManager(storm::models::sparse::Pomdp<ValueType> const& pomdp);
            std::shared_ptr<storm::models::sparse::Mdp<ValueType>> constructMdp();
            void injectMemory(uint64_t observation);

        private:
            
            storm::models::sparse::Pomdp<ValueType> const& pomdp;

            // for each observation contains number of allocated memory states (initially 1)
            std::vector<uint64_t> observation_memory_size;
            
            /**
             * Rebuild the state space:
             * - compute total number of states (@num_states)
             * - associate prototype states with their duplicates (@state_duplicates)
             * - for each state, remember its prototype (@state_prototype)
             * - for each state, remember its memory (@state_memory)
             */ 
            void buildStateSpace();

            // get index of the @memory equivalent of the @prototype
            uint64_t translateState(uint64_t prototype, uint64_t memory);

            storm::models::sparse::StateLabeling buildStateLabeling();

            storm::storage::SparseMatrix<ValueType> buildTransitionMatrix();
            uint64_t createChoicesOfState(uint64_t state, storm::storage::SparseMatrixBuilder<ValueType> builder, uint64_t num_rows, std::vector<uint64_t> const& row_copies_needed);

            storm::models::sparse::StandardRewardModel<ValueType> buildRewardModel(storm::models::sparse::StandardRewardModel<ValueType> const& rewardModel);

            
            // number of states in an unfolded MDP
            uint64_t num_states;
            // for each prototype state contains a list of its duplicates
            std::vector<std::vector<uint64_t>> state_duplicates;
            // for each state contains its prototype state (reverse of state_duplicates)
            std::vector<uint64_t> state_prototype;
            // for each state contains its memory index
            std::vector<uint64_t> state_memory;

            // number of rows in an unfolded MDP
            uint64_t num_rows;
            // for each row contains index of the original row
            std::vector<uint64_t> row_prototype;            
            // for each row contains a memory update associated with it 
            std::vector<uint64_t> row_memory;         

            // MDP obtained after last injection (initially contains MDP-ized POMDP)
            std::shared_ptr<storm::models::sparse::Mdp<ValueType>> mdp;
            
        };
    }
}