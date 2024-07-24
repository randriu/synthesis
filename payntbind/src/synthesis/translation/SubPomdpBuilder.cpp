#include "SubPomdpBuilder.h"

#include "src/synthesis/translation/componentTranslations.h"

#include <stack>

namespace synthesis {
    
    template<typename ValueType>
    SubPomdpBuilder<ValueType>::SubPomdpBuilder(storm::models::sparse::Pomdp<ValueType> const& pomdp): pomdp(pomdp) {
        // reserving 1 state and 1 choice to for the fresh initial state
        this->state_translator = ItemTranslator(this->pomdp.getNumberOfStates()+1);
        this->choice_translator = ItemTranslator(this->pomdp.getNumberOfChoices()+1);
    }

    template<typename ValueType>
    void SubPomdpBuilder<ValueType>::translateState(uint64_t state) {
        state_translator.translate(state);
        for(auto const& choice: pomdp.getTransitionMatrix().getRowGroupIndices(state)) {
            choice_translator.translate(choice);
        }
    }

    template<typename ValueType>
    void SubPomdpBuilder<ValueType>::collectReachableStates(uint64_t initial_state) {
        if(state_translator.hasTranslation(initial_state)) {
            return;
        }
        std::stack<uint64_t> state_stack;
        translateState(initial_state);
        state_stack.push(initial_state);
        auto const& tm = pomdp.getTransitionMatrix();
        while(!state_stack.empty()) {
            auto state = state_stack.top();
            state_stack.pop();
            for(auto const& entry: tm.getRowGroup(state)) {
                auto dst = entry.getColumn();
                if(not state_translator.hasTranslation(dst)) {
                    translateState(dst);
                    state_stack.push(dst);
                }
            }
        }
    }

    template<typename ValueType>
    std::shared_ptr<storm::models::sparse::Pomdp<ValueType>> SubPomdpBuilder<ValueType>::startFromBelief(
        std::map<uint64_t,ValueType> const& initial_belief
    ) {
        auto translated_initial_state = this->state_translator.translate(pomdp.getNumberOfStates());
        auto translated_initial_choice = this->choice_translator.translate(pomdp.getNumberOfChoices());
        for(auto const& [state,_]: initial_belief) {
            collectReachableStates(state);
        }

        storm::storage::sparse::ModelComponents<ValueType> components;
        components.stateLabeling = synthesis::translateStateLabeling(
            pomdp, state_translator.translationToItem(), translated_initial_state
        );

        storm::storage::BitVector translated_choice_mask(choice_translator.numTranslations(),true);

        auto translated_num_states = state_translator.numTranslations();
        auto translated_num_choices = choice_translator.numTranslations();
        storm::storage::SparseMatrixBuilder<ValueType> builder(
            translated_num_choices, translated_num_states, 0, true, true, translated_num_states
        );
        for(uint64_t translated_state = 0; translated_state < translated_num_states; ++translated_state) {
            if(translated_state == translated_initial_state) {
                builder.newRowGroup(builder.getLastRow());
                for(auto const& [dst,prob]: initial_belief) {
                    auto translated_dst = state_translator.translate(dst);
                    builder.addNextValue(translated_initial_choice, translated_dst, prob);
                }
                continue;
            }
            
            auto state = state_translator.retrieve(translated_state);
            builder.newRowGroup(builder.getLastRow()+1);
            synthesis::translateTransitionMatrixRowGroup(
                pomdp, builder, state_translator.itemToTranslation(), choice_translator.itemToTranslation(), state
            );
        }
        components.transitionMatrix =  builder.build();

        components.choiceLabeling = synthesis::translateChoiceLabeling(pomdp,choice_translator.translationToItem(),translated_choice_mask);
        components.rewardModels = synthesis::translateRewardModels(pomdp,choice_translator.translationToItem(),translated_choice_mask);

        // build state observations
        auto observability_classes = synthesis::translateObservabilityClasses(
            pomdp, state_translator.translationToItem()
        );
        // add fresh observation for the initial belief
        observability_classes[translated_initial_state] = pomdp.getNrObservations();
        components.observabilityClasses = observability_classes;

        state_sub_to_full = state_translator.translationToItem();

        clearMemory();
        return std::make_shared<storm::models::sparse::Pomdp<ValueType>>(std::move(components));
    }

    template<typename ValueType>
    void SubPomdpBuilder<ValueType>::clearMemory() {
        state_translator.clear();
        choice_translator.clear();
    }

    template class SubPomdpBuilder<double>;
}
