#include "componentTranslations.h"

#include <storm/exceptions/NotSupportedException.h>
#include <storm/exceptions/InvalidModelException.h>

namespace synthesis {

    template<typename ValueType>
    std::pair<std::vector<std::string>,std::vector<uint64_t>> extractActionLabels(
        storm::models::sparse::Model<ValueType> const& model
    ) {
        // collect action labels
        STORM_LOG_THROW(model.hasChoiceLabeling(), storm::exceptions::InvalidModelException,
            "model does not have the choice labeling");
        storm::models::sparse::ChoiceLabeling const& choice_labeling = model.getChoiceLabeling();
        std::vector<std::string> action_labels;
        std::map<std::string,uint64_t> action_label_index;
        std::set<std::string> action_labels_set;
        for(uint64_t choice = 0; choice < model.getNumberOfChoices(); ++choice) {
            for(std::string const& label: choice_labeling.getLabelsOfChoice(choice)) {
                action_labels_set.insert(label);
            }
        }
        for(std::string const& label: action_labels_set) {
            action_label_index[label] = action_labels.size();
            action_labels.push_back(label);
        }
        auto num_choices = model.getNumberOfChoices();

        // assert that each choice has exactly one label
        std::vector<uint64_t> choice_to_action(num_choices);
        for(uint64_t choice = 0; choice < model.getNumberOfChoices(); ++choice) {
            auto const& labels = choice_labeling.getLabelsOfChoice(choice);
            STORM_LOG_THROW(labels.size()==1, storm::exceptions::InvalidModelException,
                "expected exactly 1 label for choice " << choice);
            std::string const& label = *(labels.begin());
            uint64_t action = action_label_index[label];
            choice_to_action[choice] = action;
        }
        return std::make_pair(action_labels,choice_to_action);
    }


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
        uint64_t translated_num_states = translated_to_original_state.size();
        std::vector<uint32_t> observation_classes(translated_num_states);
        for(uint64_t translated_state=0; translated_state<translated_num_states; translated_state++) {
            uint64_t state = translated_to_original_state[translated_state];
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
        uint64_t translated_num_choices = translated_to_original_choice.size();
        storm::models::sparse::ChoiceLabeling translated_labeling(translated_num_choices);
        for(uint64_t translated_choice: translated_choice_mask) {
            uint64_t choice = translated_to_original_choice[translated_choice];
            if(choice >= model.getNumberOfChoices()) {
                continue;
            }
            for (std::string const& label : model.getChoiceLabeling().getLabelsOfChoice(choice)) {
                if(not translated_labeling.containsLabel(label)) {
                    translated_labeling.addLabel(label);
                }
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
        STORM_LOG_THROW(!reward_model.hasStateRewards(), storm::exceptions::NotSupportedException,
            "state rewards are currently not supported.");
        STORM_LOG_THROW(!reward_model.hasTransitionRewards(), storm::exceptions::NotSupportedException,
            "transition rewards are currently not supported.");
        
        uint64_t num_choices = reward_model.getStateActionRewardVector().size();
        std::vector<ValueType> action_rewards(translated_to_original_choice.size());
        for(uint64_t translated_choice: translated_choice_mask) {
            uint64_t choice = translated_to_original_choice[translated_choice];
            if(choice >= num_choices) {
                continue;
            }
            action_rewards[translated_choice] = reward_model.getStateActionReward(choice);
        }
        return storm::models::sparse::StandardRewardModel<ValueType>(std::move(state_rewards), std::move(action_rewards));
    }
    template<typename ValueType>
    std::unordered_map<std::string,storm::models::sparse::StandardRewardModel<ValueType>> translateRewardModels(
        storm::models::sparse::Model<ValueType> const& model,
        std::vector<uint64_t> const& translated_to_original_choice,
        storm::storage::BitVector const& translated_choice_mask
    ) {
        std::unordered_map<std::string,storm::models::sparse::StandardRewardModel<ValueType>> reward_models;
        for(auto const& reward_model : model.getRewardModels()) {
            auto new_reward_model = translateRewardModel(reward_model.second,translated_to_original_choice,translated_choice_mask);
            reward_models.emplace(reward_model.first, new_reward_model);
        }
        return reward_models;
    }

    template<typename ValueType>
    void translateTransitionMatrixRow(
        storm::models::sparse::Model<ValueType> const& model,
        storm::storage::SparseMatrixBuilder<ValueType> & builder,
        std::vector<uint64_t> const& original_to_translated_state,
        std::vector<uint64_t> const& original_to_translated_choice,
        uint64_t choice
    ) {
        uint64_t translated_choice = original_to_translated_choice[choice];
        for(auto entry: model.getTransitionMatrix().getRow(choice)) {
            uint64_t translated_dst = original_to_translated_state[entry.getColumn()];
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
        for(uint64_t const& choice: model.getTransitionMatrix().getRowGroupIndices(state)) {
            synthesis::translateTransitionMatrixRow(
                model, builder, original_to_translated_state, original_to_translated_choice, choice
            );
        }
    }


    template std::pair<std::vector<std::string>,std::vector<uint64_t>> extractActionLabels<double>(
        storm::models::sparse::Model<double> const& model);

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
    template std::unordered_map<std::string,storm::models::sparse::StandardRewardModel<double>> translateRewardModels(
        storm::models::sparse::Model<double> const& model,
        std::vector<uint64_t> const& translated_to_original_choice,
        storm::storage::BitVector const& translated_choice_mask);

    template std::vector<uint32_t> translateObservabilityClasses<double>(
        storm::models::sparse::Pomdp<double> const& model,
        std::vector<uint64_t> const& translated_to_original_state);
    
}
