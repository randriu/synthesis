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
        
        std::vector<ValueType> action_rewards(translated_to_original_choice.size());
        for(auto translated_choice: translated_choice_mask) {
            auto choice = translated_to_original_choice[translated_choice];
            auto reward = reward_model.getStateActionReward(choice);
            action_rewards[translated_choice] = reward;
        }
        return storm::models::sparse::StandardRewardModel<ValueType>(std::move(state_rewards), std::move(action_rewards));
    }


 
    template storm::models::sparse::StateLabeling translateStateLabeling<double>(
        storm::models::sparse::Model<double> const& model,
        std::vector<uint64_t> const& translated_to_original_state,
        uint64_t translated_initial_state);
    template storm::models::sparse::ChoiceLabeling translateChoiceLabeling<double>(
        storm::models::sparse::Model<double> const& model,
        std::vector<uint64_t> const& translated_to_original_choice,
        storm::storage::BitVector const& translated_choice_mask);
    template storm::models::sparse::StandardRewardModel<double> translateRewardModel(
        storm::models::sparse::StandardRewardModel<double> const& reward_model,
        std::vector<uint64_t> const& translated_to_original_choice,
        storm::storage::BitVector const& translated_choice_mask);

}