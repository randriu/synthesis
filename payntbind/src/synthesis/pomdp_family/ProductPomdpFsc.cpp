#include "ProductPomdpFsc.h"
#include "src/synthesis/translation/componentTranslations.h"

namespace synthesis {

    
    template<typename ValueType>
    ProductPomdpFsc<ValueType>::ProductPomdpFsc(
        storm::models::sparse::Model<ValueType> const& quotient,
        std::vector<uint32_t> state_to_obs_class,
        uint64_t num_actions,
        std::vector<uint64_t> choice_to_action
    ) : quotient(quotient), state_to_obs_class(state_to_obs_class),
        num_actions(num_actions), choice_to_action(choice_to_action) {
        
        this->state_translator = ItemKeyTranslator<uint64_t>();
        this->state_action_choices.resize(this->quotient.getNumberOfStates());
        auto const& row_group_indices = this->quotient.getTransitionMatrix().getRowGroupIndices();
        for(uint64_t state = 0; state < this->quotient.getNumberOfStates(); state++) {
            this->state_action_choices[state].resize(this->num_actions);
            for (uint64_t row = row_group_indices[state]; row < row_group_indices[state+1]; row++) {
                uint64_t action = this->choice_to_action[row];
                this->state_action_choices[state][action].insert(row);
            }
        }
    }

    template<typename ValueType>
    uint64_t ProductPomdpFsc<ValueType>::numberOfTranslatedStates() {
        return this->state_translator.numTranslations();
    }

    template<typename ValueType>
    uint64_t ProductPomdpFsc<ValueType>::numberOfTranslatedChoices() {
        return this->product_choice_to_choice.size();
    }

    template<typename ValueType>
    uint64_t ProductPomdpFsc<ValueType>::translateInitialState() {
        uint64_t initial_state = *(this->quotient.getInitialStates().begin());
        uint64_t initial_memory = 0;
        return this->state_translator.translate(initial_state,initial_memory);
    }
    
    
    template<typename ValueType>
    void ProductPomdpFsc<ValueType>::buildStateSpace(
        std::vector<std::vector<uint64_t>> action_function,
        std::vector<std::vector<uint64_t>> update_function
    ) {
        this->state_translator.resize(this->quotient.getNumberOfStates());
        auto translated_state = this->translateInitialState();
        while(true) {
            auto[state,memory] = this->state_translator.retrieve(translated_state);
            auto observation = this->state_to_obs_class[state];
            auto action = action_function[memory][observation];
            auto memory_dst = update_function[memory][observation];
            for(auto choice: this->state_action_choices[state][action]) {
                for(auto const &entry: this->quotient.getTransitionMatrix().getRow(choice)) {
                    auto state_dst = entry.getColumn();
                    this->state_translator.translate(state_dst,memory_dst);
                }
            }
            translated_state++;
            if(translated_state >= this->numberOfTranslatedStates()) {
                break;
            }
        }
        this->product_state_to_state = this->state_translator.translationToItem();
    }

    template<typename ValueType>
    storm::storage::SparseMatrix<ValueType> ProductPomdpFsc<ValueType>::buildTransitionMatrix(
        std::vector<std::vector<uint64_t>> action_function,
        std::vector<std::vector<uint64_t>> update_function
    ) {
        this->product_choice_to_choice.clear();
        storm::storage::SparseMatrixBuilder<ValueType> builder(0, 0, 0, false, true, 0);
        for(uint64_t translated_state = 0; translated_state < this->numberOfTranslatedStates(); translated_state++) {
            builder.newRowGroup(this->numberOfTranslatedChoices());
            auto[state,memory] = this->state_translator.retrieve(translated_state);
            auto observation = this->state_to_obs_class[state];
            auto action = action_function[memory][observation];
            auto memory_dst = update_function[memory][observation];
            for(auto choice: this->state_action_choices[state][action]) {
                auto product_choice = this->numberOfTranslatedChoices();
                this->product_choice_to_choice.push_back(choice);
                for(auto const &entry: this->quotient.getTransitionMatrix().getRow(choice)) {
                    auto translated_dst = this->state_translator.translate(entry.getColumn(),memory_dst);
                    builder.addNextValue(product_choice, translated_dst, entry.getValue());
                }
            }
        }

        return builder.build();
    }


    template<typename ValueType>
    void ProductPomdpFsc<ValueType>::applyFsc(
        std::vector<std::vector<uint64_t>> action_function,
        std::vector<std::vector<uint64_t>> update_function
    ) {
        this->buildStateSpace(action_function,update_function);
        storm::storage::sparse::ModelComponents<ValueType> components;
        auto translated_initial_state = this->translateInitialState();
        components.stateLabeling = synthesis::translateStateLabeling(
            this->quotient,this->state_translator.translationToItem(),translated_initial_state
        );
        
        components.transitionMatrix = this->buildTransitionMatrix(action_function,update_function);
        storm::storage::BitVector translated_choice_mask(this->numberOfTranslatedChoices(),true);
        components.choiceLabeling = synthesis::translateChoiceLabeling(this->quotient,this->product_choice_to_choice,translated_choice_mask);
        for (auto const& reward_model : this->quotient.getRewardModels()) {
            auto new_reward_model = synthesis::translateRewardModel(reward_model.second,this->product_choice_to_choice,translated_choice_mask);
            components.rewardModels.emplace(reward_model.first, new_reward_model);
        }

        this->clearMemory();
        this->product = std::make_shared<storm::models::sparse::Mdp<ValueType>>(std::move(components));
    }


    template<typename ValueType>
    void ProductPomdpFsc<ValueType>::clearMemory() {
        this->state_translator.clear();
    }


    template class ProductPomdpFsc<double>;
}