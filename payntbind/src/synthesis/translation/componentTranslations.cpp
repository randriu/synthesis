#include "componentTranslations.h"

#include <storm/exceptions/NotSupportedException.h>

namespace synthesis {

    template<typename ValueType>
    storm::models::sparse::StateLabeling translateStateLabeling(
        storm::models::sparse::Model<ValueType> const& model,
        std::vector<uint64_t> const& translated_to_original_state,
        uint64_t translated_initial_state
    ) {
        auto translated_num_states = translated_to_original_state.size();
        storm::models::sparse::StateLabeling translated_labeling(translated_num_states);
        for (auto const& label : model.getStateLabeling().getLabels()) {
            translated_labeling.addLabel(label, storm::storage::BitVector(translated_num_states,false));
        }
        for(uint64_t translated_state=0; translated_state<translated_num_states; translated_state++) {
            auto state = translated_to_original_state[translated_state];
            if(state >= model.getNumberOfStates()) {
                continue;
            }
            for (auto const& label : model.getStateLabeling().getLabelsOfState(state)) {
                if(label=="init") {
                    continue;
                }
                translated_labeling.addLabelToState(label,translated_state);
            }
        }
        translated_labeling.addLabelToState("init",translated_initial_state);
        return translated_labeling;
    }

    template<typename ValueType>
    std::vector<uint32_t> translateObservabilityClasses(
        storm::models::sparse::Pomdp<ValueType> const& model,
        std::vector<uint64_t> const& translated_to_original_state
    ) {
        auto translated_num_states = translated_to_original_state.size();
        std::vector<uint32_t> observation_classes(translated_num_states);
        for(uint64_t translated_state=0; translated_state<translated_num_states; translated_state++) {
            auto state = translated_to_original_state[translated_state];
            if(state >= model.getNumberOfStates()) {
                continue;
            }
            observation_classes[translated_state] = model.getObservation(state);
        }
        return observation_classes;
    }


    template<typename ValueType>
    storm::models::sparse::ChoiceLabeling translateChoiceLabeling(
        storm::models::sparse::Model<ValueType> const& model,
        std::vector<uint64_t> const& translated_to_original_choice,
        storm::storage::BitVector const& translated_choice_mask
    ) {
        auto translated_num_choices = translated_to_original_choice.size();
        storm::models::sparse::ChoiceLabeling translated_labeling(translated_num_choices);
        for (auto const& label : model.getChoiceLabeling().getLabels()) {
            translated_labeling.addLabel(label, storm::storage::BitVector(translated_num_choices,false));
        }
        for(auto translated_choice: translated_choice_mask) {
            auto choice = translated_to_original_choice[translated_choice];
            if(choice >= model.getNumberOfChoices()) {
                continue;
            }
            for (auto const& label : model.getChoiceLabeling().getLabelsOfChoice(choice)) {
                translated_labeling.addLabelToChoice(label,translated_choice);
            }
        }
        return translated_labeling;
    }

    template<typename ValueType>
    storm::models::sparse::StandardRewardModel<ValueType> translateRewardModel(
        storm::models::sparse::StandardRewardModel<ValueType> const& reward_model,
        std::vector<uint64_t> const& translated_to_original_choice,
        storm::storage::BitVector const& translated_choice_mask
    ) {
        std::optional<std::vector<ValueType>> state_rewards;
        STORM_LOG_THROW(!reward_model.hasStateRewards(), storm::exceptions::NotSupportedException, "state rewards are currently not supported.");
        STORM_LOG_THROW(!reward_model.hasTransitionRewards(), storm::exceptions::NotSupportedException, "transition rewards are currently not supported.");
        
        auto num_choices = reward_model.getStateActionRewardVector().size();
        std::vector<ValueType> action_rewards(translated_to_original_choice.size());
        for(auto translated_choice: translated_choice_mask) {
            auto choice = translated_to_original_choice[translated_choice];
            if(choice >= num_choices) {
                continue;
            }
            auto reward = reward_model.getStateActionReward(choice);
            action_rewards[translated_choice] = reward;
        }
        return storm::models::sparse::StandardRewardModel<ValueType>(std::move(state_rewards), std::move(action_rewards));
    }

    template<typename ValueType>
    void translateTransitionMatrixRow(
        storm::models::sparse::Model<ValueType> const& model,
        storm::storage::SparseMatrixBuilder<ValueType> & builder,
        std::vector<uint64_t> const& original_to_translated_state,
        std::vector<uint64_t> const& original_to_translated_choice,
        uint64_t choice
    ) {
        auto translated_choice = original_to_translated_choice[choice];
        for(auto entry: model.getTransitionMatrix().getRow(choice)) {
            auto translated_dst = original_to_translated_state[entry.getColumn()];
            builder.addNextValue(translated_choice, translated_dst, entry.getValue());
        }
    }

    template<typename ValueType>
    void translateTransitionMatrixRowGroup(
        storm::models::sparse::Model<ValueType> const& model,
        storm::storage::SparseMatrixBuilder<ValueType> & builder,
        std::vector<uint64_t> const& original_to_translated_state,
        std::vector<uint64_t> const& original_to_translated_choice,
        uint64_t state
    ) {
        for(auto const& choice: model.getTransitionMatrix().getRowGroupIndices(state)) {
            synthesis::translateTransitionMatrixRow(
                model, builder, original_to_translated_state, original_to_translated_choice, choice
            );
        }
    }


    template storm::models::sparse::StateLabeling translateStateLabeling<double>(
        storm::models::sparse::Model<double> const& model,
        std::vector<uint64_t> const& translated_to_original_state,
        uint64_t translated_initial_state);
    
    template void translateTransitionMatrixRow<double>(
        storm::models::sparse::Model<double> const& model,
        storm::storage::SparseMatrixBuilder<double> & builder,
        std::vector<uint64_t> const& original_to_translated_state,
        std::vector<uint64_t> const& original_to_translated_choice,
        uint64_t choice);
    template void translateTransitionMatrixRowGroup<double>(
        storm::models::sparse::Model<double> const& model,
        storm::storage::SparseMatrixBuilder<double> & builder,
        std::vector<uint64_t> const& original_to_translated_state,
        std::vector<uint64_t> const& original_to_translated_choice,
        uint64_t state);
    
    template storm::models::sparse::ChoiceLabeling translateChoiceLabeling<double>(
        storm::models::sparse::Model<double> const& model,
        std::vector<uint64_t> const& translated_to_original_choice,
        storm::storage::BitVector const& translated_choice_mask);
    template storm::models::sparse::StandardRewardModel<double> translateRewardModel(
        storm::models::sparse::StandardRewardModel<double> const& reward_model,
        std::vector<uint64_t> const& translated_to_original_choice,
        storm::storage::BitVector const& translated_choice_mask);

    template std::vector<uint32_t> translateObservabilityClasses<double>(
        storm::models::sparse::Pomdp<double> const& model,
        std::vector<uint64_t> const& translated_to_original_state);
    
}
