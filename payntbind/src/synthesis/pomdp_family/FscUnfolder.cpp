#include "FscUnfolder.h"

#include "src/synthesis/translation/componentTranslations.h"

namespace synthesis {

    
    template<typename ValueType>
    FscUnfolder<ValueType>::FscUnfolder(
        storm::models::sparse::Model<ValueType> const& quotient,
        std::vector<uint32_t> const& state_to_obs_class,
        uint64_t num_actions,
        std::vector<uint64_t> const& choice_to_action
    ) : quotient(quotient), state_to_obs_class(state_to_obs_class),
        num_actions(num_actions), choice_to_action(choice_to_action) {
        
        this->state_translator = ItemKeyTranslator<std::tuple<uint64_t,uint64_t,bool>>();
        this->state_action_choices.resize(this->quotient.getNumberOfStates());
        std::vector<uint64_t> const& row_groups = this->quotient.getTransitionMatrix().getRowGroupIndices();
        for(uint64_t state = 0; state < this->quotient.getNumberOfStates(); ++state) {
            this->state_action_choices[state].resize(this->num_actions);
            for (uint64_t choice = row_groups[state]; choice < row_groups[state+1]; ++choice) {
                uint64_t action = this->choice_to_action[choice];
                this->state_action_choices[state][action].insert(choice);
            }
        }
    }

    template<typename ValueType>
    uint64_t FscUnfolder<ValueType>::invalidAction() {
        return this->num_actions;
    }

    template<typename ValueType>
    uint64_t FscUnfolder<ValueType>::invalidChoice() {
        return this->quotient.getNumberOfChoices();
    }

    template<typename ValueType>
    uint64_t FscUnfolder<ValueType>::numberOfTranslatedStates() {
        return this->state_translator.numTranslations();
    }

    template<typename ValueType>
    uint64_t FscUnfolder<ValueType>::numberOfTranslatedChoices() {
        return this->product_choice_to_choice.size();
    }

    template<typename ValueType>
    uint64_t FscUnfolder<ValueType>::translateInitialState() {
        uint64_t initial_state = *(this->quotient.getInitialStates().begin());
        uint64_t initial_memory = 0;
        return this->state_translator.translate(initial_state,std::make_tuple(initial_memory,invalidAction(),false));
    }
    
    
    template<typename ValueType>
    void FscUnfolder<ValueType>::buildStateSpace(
        std::vector<std::vector<std::map<uint64_t,double>>> action_function,
        std::vector<std::vector<std::map<uint64_t,double>>> update_function
    ) {
        this->state_translator.resize(this->quotient.getNumberOfStates());
        uint64_t translated_state = this->translateInitialState();
        while(true) {
            auto[state,memory_action_transitioned] = this->state_translator.retrieve(translated_state);
            auto[memory,action,transitioned] = memory_action_transitioned;
            uint64_t observation = this->state_to_obs_class[state];
            if(action == invalidAction() and not transitioned) {
                // random choice of an action
                for(auto [action,prob] : action_function[memory][observation]) {
                    this->state_translator.translate(state,std::make_tuple(memory,action,false));
                }
            } else if(action != invalidAction()) {
                // executing variants of the selected actions
                for(uint64_t choice: this->state_action_choices[state][action]) {
                    for(auto const &entry: this->quotient.getTransitionMatrix().getRow(choice)) {
                        uint64_t state_dst = entry.getColumn();
                        this->state_translator.translate(state_dst,std::make_tuple(memory,invalidAction(),true));
                    }
                }
            } else { // action == invalidAction() and transitioned
                // executing memory update
                for(auto [memory_dst,prob] : update_function[memory][observation]) {
                    this->state_translator.translate(state,std::make_tuple(memory_dst,invalidAction(),false));
                }
            }
            translated_state++;
            if(translated_state >= numberOfTranslatedStates()) {
                break;
            }
        }

        this->product_state_to_state = this->state_translator.translationToItem();
        this->product_state_to_state_memory_action_transitioned = this->state_translator.translationToItemKey();
    }

    template<typename ValueType>
    storm::storage::SparseMatrix<ValueType> FscUnfolder<ValueType>::buildTransitionMatrix(
        std::vector<std::vector<std::map<uint64_t,double>>> action_function,
        std::vector<std::vector<std::map<uint64_t,double>>> update_function
    ) {
        this->product_choice_to_choice.clear();
        storm::storage::SparseMatrixBuilder<ValueType> builder(0, 0, 0, false, true, 0);
        for(uint64_t translated_state = 0; translated_state < numberOfTranslatedStates(); ++translated_state) {
            builder.newRowGroup(numberOfTranslatedChoices());
            auto[state,memory_action_transitioned] = this->state_translator.retrieve(translated_state);
            auto[memory,action,transitioned] = memory_action_transitioned;
            uint64_t observation = this->state_to_obs_class[state];
            if(action == invalidAction() and not transitioned) {
                // random choice of an action
                uint64_t product_choice = numberOfTranslatedChoices();
                this->product_choice_to_choice.push_back(invalidChoice());
                for(auto [action,prob] : action_function[memory][observation]) {
                    uint64_t translated_dst = this->state_translator.translate(state,std::make_tuple(memory,action,false));
                    builder.addNextValue(product_choice, translated_dst, prob);
                }
            } else if(action != invalidAction()) {
                // executing variants of the selected actions
                for(uint64_t choice: this->state_action_choices[state][action]) {
                    uint64_t product_choice = numberOfTranslatedChoices();
                    this->product_choice_to_choice.push_back(choice);
                    for(auto const &entry: this->quotient.getTransitionMatrix().getRow(choice)) {
                        uint64_t state_dst = entry.getColumn();
                        uint64_t translated_dst = this->state_translator.translate(state_dst,std::make_tuple(memory,invalidAction(),true));
                        builder.addNextValue(product_choice, translated_dst, entry.getValue());
                    }
                }
            } else { // action == invalidAction() and transitioned
                // executing memory update
                uint64_t product_choice = numberOfTranslatedChoices();
                this->product_choice_to_choice.push_back(invalidChoice());
                for(auto [memory_dst,prob] : update_function[memory][observation]) {
                    uint64_t translated_dst = this->state_translator.translate(state,std::make_tuple(memory_dst,invalidAction(),false));
                    builder.addNextValue(product_choice, translated_dst, prob);
                }
            }
        }

        return builder.build();
    }


    template<typename ValueType>
    void FscUnfolder<ValueType>::applyFsc(
        std::vector<std::vector<std::map<uint64_t,double>>> action_function,
        std::vector<std::vector<std::map<uint64_t,double>>> update_function
    ) {
        this->buildStateSpace(action_function,update_function);
        storm::storage::sparse::ModelComponents<ValueType> components;
        auto translated_initial_state = this->translateInitialState();
        components.stateLabeling = synthesis::translateStateLabeling(
            this->quotient,this->state_translator.translationToItem(),translated_initial_state
        );
        
        components.transitionMatrix = this->buildTransitionMatrix(action_function,update_function);
        storm::storage::BitVector translated_choice_mask(numberOfTranslatedChoices(),true);
        auto quotient_num_choices = this->quotient.getNumberOfChoices();
        for(uint64_t translated_choice = 0; translated_choice<numberOfTranslatedChoices(); ++translated_choice) {
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
    void FscUnfolder<ValueType>::clearMemory() {
        this->state_translator.clear();
    }


    template class FscUnfolder<double>;
}