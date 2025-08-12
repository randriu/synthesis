#include "componentTranslations.h"
#include "src/synthesis/posmg/Posmg.h"

#include <storm/adapters/RationalNumberAdapter.h>
#include <storm/models/sparse/Pomdp.h>
#include <storm/models/sparse/Smg.h>
#include <storm/utility/builder.h>
#include <storm/exceptions/NotSupportedException.h>
#include <storm/exceptions/InvalidModelException.h>

namespace synthesis {

template<typename ValueType>
storm::storage::sparse::ModelComponents<ValueType> componentsFromModel(
    storm::models::sparse::Model<ValueType> const& model
) {
    storm::storage::sparse::ModelComponents<ValueType> components;
    components.stateLabeling = model.getStateLabeling();
    components.stateValuations = model.getOptionalStateValuations();
    components.transitionMatrix = model.getTransitionMatrix();
    components.choiceLabeling = model.getOptionalChoiceLabeling();
    components.choiceOrigins = model.getOptionalChoiceOrigins();
    components.rewardModels = model.getRewardModels();
    if (model.getType() == storm::models::ModelType::Pomdp) {
        auto pomdp = static_cast<storm::models::sparse::Pomdp<ValueType> const&>(model);
        components.observabilityClasses = pomdp.getObservations();
        components.observationValuations = pomdp.getOptionalObservationValuations();
    }
    if (model.getType() == storm::models::ModelType::Smg) {
        auto smg = static_cast<storm::models::sparse::Smg<ValueType> const&>(model);
        components.statePlayerIndications = smg.getStatePlayerIndications();
        // skipping playerNameToIndexMap since Smg does not directly exposes those
    }
    if (auto posmg = dynamic_cast<Posmg<ValueType> const*>(&model)) {
        components.observabilityClasses = posmg->getObservations();
        // state player indications are already filled in the ModelType == Smg branch
    }
    return components;
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
    storm::models::sparse::Model<ValueType> const& model,
    std::vector<uint64_t> const& translated_to_original_state
) {
    STORM_LOG_THROW(model.getType() == storm::models::ModelType::Pomdp, storm::exceptions::InvalidModelException, "the model is not a POMDP");
    auto pomdp = static_cast<storm::models::sparse::Pomdp<ValueType> const&>(model);
    uint64_t translated_num_states = translated_to_original_state.size();
    std::vector<uint32_t> observation_classes(translated_num_states);
    for(uint64_t translated_state=0; translated_state<translated_num_states; translated_state++) {
        uint64_t state = translated_to_original_state[translated_state];
        if(state >= pomdp.getNumberOfStates()) {
            continue;
        }
        observation_classes[translated_state] = pomdp.getObservation(state);
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
    STORM_LOG_THROW(!reward_model.hasStateRewards() and !reward_model.hasTransitionRewards() and reward_model.hasStateActionRewards(),
        storm::exceptions::NotSupportedException, "expected state-action rewards");

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


template storm::storage::sparse::ModelComponents<double> componentsFromModel<double>(
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
    storm::models::sparse::Model<double> const& model,
    std::vector<uint64_t> const& translated_to_original_state);




template storm::storage::sparse::ModelComponents<storm::RationalNumber> componentsFromModel<storm::RationalNumber>(
    storm::models::sparse::Model<storm::RationalNumber> const& model);

template storm::models::sparse::StateLabeling translateStateLabeling<storm::RationalNumber>(
    storm::models::sparse::Model<storm::RationalNumber> const& model,
    std::vector<uint64_t> const& translated_to_original_state,
    uint64_t translated_initial_state);

template void translateTransitionMatrixRow<storm::RationalNumber>(
    storm::models::sparse::Model<storm::RationalNumber> const& model,
    storm::storage::SparseMatrixBuilder<storm::RationalNumber> & builder,
    std::vector<uint64_t> const& original_to_translated_state,
    std::vector<uint64_t> const& original_to_translated_choice,
    uint64_t choice);
template void translateTransitionMatrixRowGroup<storm::RationalNumber>(
    storm::models::sparse::Model<storm::RationalNumber> const& model,
    storm::storage::SparseMatrixBuilder<storm::RationalNumber> & builder,
    std::vector<uint64_t> const& original_to_translated_state,
    std::vector<uint64_t> const& original_to_translated_choice,
    uint64_t state);

template storm::models::sparse::ChoiceLabeling translateChoiceLabeling<storm::RationalNumber>(
    storm::models::sparse::Model<storm::RationalNumber> const& model,
    std::vector<uint64_t> const& translated_to_original_choice,
    storm::storage::BitVector const& translated_choice_mask);
template storm::models::sparse::StandardRewardModel<storm::RationalNumber> translateRewardModel(
    storm::models::sparse::StandardRewardModel<storm::RationalNumber> const& reward_model,
    std::vector<uint64_t> const& translated_to_original_choice,
    storm::storage::BitVector const& translated_choice_mask);
template std::unordered_map<std::string,storm::models::sparse::StandardRewardModel<storm::RationalNumber>> translateRewardModels(
    storm::models::sparse::Model<storm::RationalNumber> const& model,
    std::vector<uint64_t> const& translated_to_original_choice,
    storm::storage::BitVector const& translated_choice_mask);

template std::vector<uint32_t> translateObservabilityClasses<storm::RationalNumber>(
    storm::models::sparse::Model<storm::RationalNumber> const& model,
    std::vector<uint64_t> const& translated_to_original_state);
}
