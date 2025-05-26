#include "MemoryUnfolder.h"

#include "src/synthesis/translation/componentTranslations.h"
#include "storm/exceptions/NotSupportedException.h"

namespace synthesis {

    template<typename ValueType>
    storm::models::sparse::Mdp<ValueType> constructUnfoldedModel(
        storm::models::sparse::Mdp<ValueType> const& mdp,
        uint64_t memory_size
    ) {
        
        uint64_t num_states = 0;
        std::vector<uint64_t> state_prototype;
        std::vector<uint64_t> state_memory;

        storm::storage::sparse::ModelComponents<ValueType> components;

        // compute state space
        for (uint64_t prototype = 0; prototype < mdp.getNumberOfStates(); prototype++) {
            for (uint64_t memory = 0; memory < memory_size; memory++) {
                state_prototype.push_back(prototype);
                state_memory.push_back(memory);
                num_states++;
            }
        }

        // compute transition matrix
        storm::storage::SparseMatrixBuilder<ValueType> builder(
        mdp.getTransitionMatrix().getRowCount()*memory_size*memory_size, num_states, 0, true, true,num_states
        );
        uint64_t num_rows = 0;
        for(uint64_t state = 0; state < num_states; state++) {
            builder.newRowGroup(num_rows);
            auto prototype_state = state_prototype[state];
            auto memory = state_memory[state];
            auto const& row_group_indices = mdp.getTransitionMatrix().getRowGroupIndices();
            for (
                uint64_t prototype_row = row_group_indices[prototype_state];
                prototype_row < row_group_indices[prototype_state + 1];
                prototype_row++
            ) {
                for (uint64_t dst_mem = 0; dst_mem < memory_size; dst_mem++) {
                    for (auto const& entry : mdp.getTransitionMatrix().getRow(prototype_row)) {
                        builder.addNextValue(num_rows, entry.getColumn()*memory_size+dst_mem, entry.getValue());
                    }
                    num_rows++;
                }
            }
        }
        auto transition_matrix = builder.build();
        components.transitionMatrix = transition_matrix;

        // construct state labeling
        storm::models::sparse::StateLabeling labeling(num_states);
        for (auto const& label : mdp.getStateLabeling().getLabels()) {
            storm::storage::BitVector label_flags(num_states, false);
            
            if (label == "init") {
                // init label is only assigned to states with the initial memory state
                for (auto const& prototype : mdp.getStateLabeling().getStates(label)) {
                    for (uint64_t state = 0; state < num_states; state++) {
                        if (state_prototype[state] == prototype && state_memory[state] == 0) {
                            label_flags.set(state);
                            break; // only one state can have the init label
                        }
                    }
                }
            } else {
                for (auto const& prototype : mdp.getStateLabeling().getStates(label)) {
                    for (uint64_t state = 0; state < num_states; state++) {
                        if (state_prototype[state] == prototype) {
                            label_flags.set(state);
                        }
                    }
                }
            }
            labeling.addLabel(label, std::move(label_flags));
        }
        components.stateLabeling = labeling;

        // construct reward models
        for (auto const& reward_model : mdp.getRewardModels()) {
            
            std::optional<std::vector<ValueType>> state_rewards, action_rewards;
            STORM_LOG_THROW(!reward_model.second.hasStateRewards(), storm::exceptions::NotSupportedException, "state rewards are currently not supported.");
            STORM_LOG_THROW(!reward_model.second.hasTransitionRewards(), storm::exceptions::NotSupportedException, "transition rewards are currently not supported.");
            if(not reward_model.second.hasStateActionRewards()) {
                STORM_LOG_WARN("Reward model exists but has no state-action value vector associated with it.");
            } else {
                action_rewards = std::vector<ValueType>();
                for(uint64_t row = 0; row < num_rows; row++) {
                    auto prototype = row / (memory_size*memory_size);
                    auto reward = reward_model.second.getStateActionReward(prototype);
                    action_rewards->push_back(reward);
                }
            }

            auto constructed_reward_model = storm::models::sparse::StandardRewardModel<ValueType>(
                std::move(state_rewards), std::move(action_rewards)
            );

            components.rewardModels.emplace(reward_model.first, constructed_reward_model);
        }

        auto unfoldedMdp = storm::models::sparse::Mdp<ValueType>(std::move(components)
        );

        return unfoldedMdp;
    }


    template
    storm::models::sparse::Mdp<double> constructUnfoldedModel(
        storm::models::sparse::Mdp<double> const& mdp,
        uint64_t memory_size
    );

    template
    storm::models::sparse::Mdp<storm::RationalNumber> constructUnfoldedModel(
        storm::models::sparse::Mdp<storm::RationalNumber> const& mdp,
        uint64_t memory_size
    );

}