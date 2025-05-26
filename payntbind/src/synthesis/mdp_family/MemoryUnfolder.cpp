#include "MemoryUnfolder.h"

#include "src/synthesis/translation/componentTranslations.h"
#include "storm/exceptions/NotSupportedException.h"

namespace synthesis {

    template<typename ValueType>
    MemoryUnfolder<ValueType>::MemoryUnfolder(
        storm::models::sparse::Mdp<ValueType> const& mdp
    ) : mdp(mdp) {}

    template<typename ValueType>
    std::shared_ptr<storm::models::sparse::Mdp<ValueType>> MemoryUnfolder<ValueType>::constructUnfoldedModel(
        uint64_t memory_size
    ) {
        
        uint64_t num_states = 0;

        storm::storage::sparse::ModelComponents<ValueType> components;

        // compute state space
        for (uint64_t prototype = 0; prototype < this->mdp.getNumberOfStates(); prototype++) {
            for (uint64_t memory = 0; memory < memory_size; memory++) {
                this->statePrototype.push_back(prototype);
                this->stateMemory.push_back(memory);
                num_states++;
            }
        }

        // compute transition matrix
        storm::storage::SparseMatrixBuilder<ValueType> builder(
        this->mdp.getTransitionMatrix().getRowCount()*memory_size*memory_size, num_states, 0, true, true,num_states
        );
        uint64_t num_rows = 0;
        auto const& row_group_indices = this->mdp.getTransitionMatrix().getRowGroupIndices();
        for(uint64_t state = 0; state < num_states; state++) {
            builder.newRowGroup(num_rows);
            auto prototype_state = this->statePrototype[state];
            auto memory = this->stateMemory[state];
            for (
                uint64_t prototype_row = row_group_indices[prototype_state];
                prototype_row < row_group_indices[prototype_state + 1];
                prototype_row++
            ) {
                for (uint64_t dst_mem = 0; dst_mem < memory_size; dst_mem++) {
                    for (auto const& entry : this->mdp.getTransitionMatrix().getRow(prototype_row)) {
                        builder.addNextValue(num_rows, entry.getColumn()*memory_size+dst_mem, entry.getValue());
                    }
                    this->choiceMap.push_back(prototype_row);
                    num_rows++;
                }
            }
        }
        auto transition_matrix = builder.build();
        components.transitionMatrix = transition_matrix;

        // construct state labeling
        storm::models::sparse::StateLabeling labeling(num_states);
        for (auto const& label : this->mdp.getStateLabeling().getLabels()) {
            storm::storage::BitVector label_flags(num_states, false);
            
            if (label == "init") {
                // init label is only assigned to states with the initial memory state
                for (auto const& prototype : this->mdp.getStateLabeling().getStates(label)) {
                    for (uint64_t state = 0; state < num_states; state++) {
                        if (this->statePrototype[state] == prototype && this->stateMemory[state] == 0) {
                            label_flags.set(state);
                            break; // only one state can have the init label
                        }
                    }
                }
            } else {
                for (auto const& prototype : this->mdp.getStateLabeling().getStates(label)) {
                    for (uint64_t state = 0; state < num_states; state++) {
                        if (this->statePrototype[state] == prototype) {
                            label_flags.set(state);
                        }
                    }
                }
            }
            labeling.addLabel(label, std::move(label_flags));
        }
        components.stateLabeling = labeling;

        // construct reward models
        for (auto const& reward_model : this->mdp.getRewardModels()) {

            std::optional<std::vector<ValueType>> state_rewards, action_rewards;
            STORM_LOG_THROW(!reward_model.second.hasStateRewards(), storm::exceptions::NotSupportedException, "state rewards are currently not supported.");
            STORM_LOG_THROW(!reward_model.second.hasTransitionRewards(), storm::exceptions::NotSupportedException, "transition rewards are currently not supported.");
            if(not reward_model.second.hasStateActionRewards()) {
                STORM_LOG_WARN("Reward model exists but has no state-action value vector associated with it.");
            } else {
                action_rewards = std::vector<ValueType>();
                for(uint64_t row = 0; row < num_rows; row++) {
                    auto prototype = this->choiceMap[row];
                    auto reward = reward_model.second.getStateActionReward(prototype);
                    action_rewards->push_back(reward);
                }
            }

            auto constructed_reward_model = storm::models::sparse::StandardRewardModel<ValueType>(
                std::move(state_rewards), std::move(action_rewards)
            );

            components.rewardModels.emplace(reward_model.first, constructed_reward_model);
        }

        // create choice labeling
        storm::models::sparse::ChoiceLabeling choice_labeling(num_rows);
        // add labels first
        for (auto const& label : this->mdp.getChoiceLabeling().getLabels()) {
            for (uint64_t memory = 0; memory < memory_size; memory++) {
                std::string label_memory = label + "_mem_" + std::to_string(memory);
                choice_labeling.addLabel(label_memory, storm::storage::BitVector(num_rows, false));
            }
        }
        for (uint64_t choice = 0; choice < num_rows; choice++) {
            auto original_choice = this->choiceMap[choice];
            auto choice_mem = choice % memory_size;
            for (auto const& label : this->mdp.getChoiceLabeling().getLabelsOfChoice(original_choice)) {
                std::string label_memory = label + "_mem_" + std::to_string(choice_mem);
                choice_labeling.addLabelToChoice(label_memory, choice);
            }
        }
        components.choiceLabeling = choice_labeling;

        this->unfoldedMdp = std::make_shared<storm::models::sparse::Mdp<ValueType>>(std::move(components));

        return this->unfoldedMdp;
    }


    template class MemoryUnfolder<storm::RationalNumber>;
    template class MemoryUnfolder<double>;

}