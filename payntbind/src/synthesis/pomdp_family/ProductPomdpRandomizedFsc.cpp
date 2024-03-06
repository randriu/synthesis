#include "ProductPomdpRandomizedFsc.h"

#include "src/synthesis/translation/componentTranslations.h"

namespace synthesis {

    
    template<typename ValueType>
    ProductPomdpRandomizedFsc<ValueType>::ProductPomdpRandomizedFsc(
        storm::models::sparse::Model<ValueType> const& quotient,
        std::vector<uint32_t> state_to_obs_class,
        uint64_t num_actions,
        std::vector<uint64_t> choice_to_action
    ) : quotient(quotient), state_to_obs_class(state_to_obs_class),
        num_actions(num_actions), choice_to_action(choice_to_action) {
        
        this->state_translator = ItemKeyTranslator<std::pair<uint64_t,uint64_t>>();
        this->state_action_choices.resize(this->quotient.getNumberOfStates());
        auto const& row_group_indices = this->quotient.getTransitionMatrix().getRowGroupIndices();
        for(uint64_t state = 0; state < this->quotient.getNumberOfStates(); ++state) {
            this->state_action_choices[state].resize(this->num_actions);
            for (uint64_t row = row_group_indices[state]; row < row_group_indices[state+1]; row++) {
                uint64_t action = this->choice_to_action[row];
                this->state_action_choices[state][action].insert(row);
            }
        }
    }

    template<typename ValueType>
    uint64_t ProductPomdpRandomizedFsc<ValueType>::numberOfTranslatedStates() {
        return this->state_translator.numTranslations();
    }

    template<typename ValueType>
    uint64_t ProductPomdpRandomizedFsc<ValueType>::numberOfTranslatedChoices() {
        return this->product_choice_to_choice.size();
    }

    template<typename ValueType>
    uint64_t ProductPomdpRandomizedFsc<ValueType>::translateInitialState() {
        uint64_t initial_state = *(this->quotient.getInitialStates().begin());
        uint64_t initial_memory = 0;
        uint64_t initial_action = this->num_actions;
        return this->state_translator.translate(initial_state,std::make_pair(initial_memory,initial_action));
    }
    
    
    template<typename ValueType>
    void ProductPomdpRandomizedFsc<ValueType>::buildStateSpace(
        std::vector<std::vector<std::map<uint64_t,double>>> action_function,
        std::vector<std::vector<uint64_t>> update_function
    ) {
        this->state_translator.resize(this->quotient.getNumberOfStates());
        auto translated_state = this->translateInitialState();
        while(true) {
            auto[state,memory_action] = this->state_translator.retrieve(translated_state);
            auto[memory,action] = memory_action;
            auto observation = this->state_to_obs_class[state];
            if(action == this->num_actions) {
                for(auto [action,prob] : action_function[memory][observation]) {
                    this->state_translator.translate(state,std::make_pair(memory,action));
                }
            } else {
                auto memory_dst = update_function[memory][observation];
                for(auto choice: this->state_action_choices[state][action]) {
                    for(auto const &entry: this->quotient.getTransitionMatrix().getRow(choice)) {
                        auto state_dst = entry.getColumn();
                        this->state_translator.translate(state_dst,std::make_pair(memory_dst,this->num_actions));
                    }
                }
            }
            translated_state++;
            if(translated_state >= this->numberOfTranslatedStates()) {
                break;
            }
        }

        this->product_state_to_state = this->state_translator.translationToItem();
        this->product_state_to_state_memory_action = this->state_translator.translationToItemKey();
    }

    template<typename ValueType>
    storm::storage::SparseMatrix<ValueType> ProductPomdpRandomizedFsc<ValueType>::buildTransitionMatrix(
        std::vector<std::vector<std::map<uint64_t,double>>> action_function,
        std::vector<std::vector<uint64_t>> update_function
    ) {
        this->product_choice_to_choice.clear();
        auto quotient_num_choices = this->quotient.getNumberOfChoices();
        storm::storage::SparseMatrixBuilder<ValueType> builder(0, 0, 0, false, true, 0);
        for(uint64_t translated_state = 0; translated_state < this->numberOfTranslatedStates(); ++translated_state) {
            builder.newRowGroup(this->numberOfTranslatedChoices());
            auto[state,memory_action] = this->state_translator.retrieve(translated_state);
            auto[memory,action] = memory_action;
            auto observation = this->state_to_obs_class[state];
            if(action == this->num_actions) {
                // 1 choice where we stochastically pick an action
                auto product_choice = this->numberOfTranslatedChoices();
                this->product_choice_to_choice.push_back(quotient_num_choices);
                for(auto [action,prob] : action_function[memory][observation]) {
                    auto translated_dst = this->state_translator.translate(state,std::make_pair(memory,action));
                    builder.addNextValue(product_choice, translated_dst, prob);
                }
            } else {
                auto memory_dst = update_function[memory][observation];
                for(auto choice: this->state_action_choices[state][action]) {
                    auto product_choice = this->numberOfTranslatedChoices();
                    this->product_choice_to_choice.push_back(choice);
                    for(auto const &entry: this->quotient.getTransitionMatrix().getRow(choice)) {
                        auto translated_dst = this->state_translator.translate(entry.getColumn(),std::make_pair(memory_dst,this->num_actions));
                        builder.addNextValue(product_choice, translated_dst, entry.getValue());
                    }
                }
            }
        }

        return builder.build();
    }


    template<typename ValueType>
    void ProductPomdpRandomizedFsc<ValueType>::applyFsc(
        std::vector<std::vector<std::map<uint64_t,double>>> action_function,
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
        auto quotient_num_choices = this->quotient.getNumberOfChoices();
        for(uint64_t translated_choice = 0; translated_choice<this->numberOfTranslatedChoices(); ++translated_choice) {
            if(this->product_choice_to_choice[translated_choice]==quotient_num_choices) {
                translated_choice_mask.set(translated_choice,false);
            }
        }
        components.choiceLabeling = synthesis::translateChoiceLabeling(this->quotient,this->product_choice_to_choice,translated_choice_mask);
        for (auto const& reward_model : this->quotient.getRewardModels()) {
            auto new_reward_model = synthesis::translateRewardModel(reward_model.second,this->product_choice_to_choice,translated_choice_mask);
            components.rewardModels.emplace(reward_model.first, new_reward_model);
        }

        this->clearMemory();
        this->product = std::make_shared<storm::models::sparse::Mdp<ValueType>>(std::move(components));
    }


    template<typename ValueType>
    void ProductPomdpRandomizedFsc<ValueType>::clearMemory() {
        this->state_translator.clear();
    }


    template class ProductPomdpRandomizedFsc<double>;
}