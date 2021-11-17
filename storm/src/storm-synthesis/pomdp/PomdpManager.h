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

            // inject 1 state to a selected observation
            void injectMemory(uint64_t observation);
            // set memory size to all observations
            void setMemorySize(uint64_t memory_size);

            // number of actions available at this observation
            std::vector<uint64_t> observation_actions;
            // for each row contains its index in its row group
            std::vector<uint64_t> prototype_row_index;
            
            // design space associated with this POMDP
            uint64_t num_holes;
            std::vector<std::vector<uint64_t>> action_holes;
            std::vector<std::vector<uint64_t>> memory_holes;
            std::vector<uint64_t> hole_options;

            std::vector<uint64_t> row_action_hole;
            std::vector<uint64_t> row_action_option;
            std::vector<uint64_t> row_memory_hole;
            std::vector<uint64_t> row_memory_option;

            // MDP obtained after last injection (initially contains MDP-ized POMDP)
            std::shared_ptr<storm::models::sparse::Mdp<ValueType>> mdp;            

        private:
            
            /**
             * Build the state space:
             * - compute total number of states (@num_states)
             * - associate prototype states with their duplicates (@prototype_duplicates)
             * - for each state, remember its prototype (@state_prototype)
             * - for each state, remember its memory (@state_memory)
             */ 
            void buildStateSpace();

            /**
             * Get index of the @memory equivalent of the @prototype.
             * If the prototype does not have the corresponding memory
             * equivalent, default to @memory=0.
             */
            uint64_t translateState(uint64_t prototype, uint64_t memory);

            // compute max memory size among all destinations of a prototype row
            uint64_t maxSuccessorMemorySize(uint64_t prototype_row);

            /**
             * Build the shape of the transition matrix:
             * - for each row store its prototype (@row_prototype)
             * - for each row store its memory index (@row_memory)
             * - deduce row groups of the resulting transition matrix (@row_groups)
             * - deduce the overall number of rows (@num_rows)
             */
            void buildTransitionMatrix();

            void buildTransitionMatrixSpurious();

            void resetDesignSpace();
            void buildDesignSpaceSpurious();

            storm::models::sparse::StateLabeling constructStateLabeling();
            storm::storage::SparseMatrix<ValueType> constructTransitionMatrix();
            storm::models::sparse::StandardRewardModel<ValueType> constructRewardModel(storm::models::sparse::StandardRewardModel<ValueType> const& reward_model);
            
            // original POMDP
            storm::models::sparse::Pomdp<ValueType> const& pomdp;
            // for each observation contains the number of allocated memory states (initially 1)
            std::vector<uint64_t> observation_memory_size;
            
            // number of states in an unfolded MDP
            uint64_t num_states;
            // for each prototype state contains a list of its duplicates (including itself)
            std::vector<std::vector<uint64_t>> prototype_duplicates;
            // for each state contains its prototype state (reverse of prototype_duplicates)
            std::vector<uint64_t> state_prototype;
            // for each state contains its memory index
            std::vector<uint64_t> state_memory;

            // for each observation contains the maximum memory size of a destination
            // across all rows of a prototype state having this observation
            std::vector<uint64_t> max_successor_memory_size;    

            // number of rows in an unfolded MDP
            uint64_t num_rows;
            // row groups of the resulting transition matrix
            std::vector<uint64_t> row_groups;
            // for each row contains index of the prototype row
            std::vector<uint64_t> row_prototype;
            // for each row contains a memory update associated with it 
            std::vector<uint64_t> row_memory;
        };
    }
}