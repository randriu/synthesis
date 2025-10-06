#include "choiceTransformation.h"

#include "src/synthesis/translation/componentTranslations.h"
#include "src/synthesis/posmg/Posmg.h"

#include <storm/adapters/RationalNumberAdapter.h>
#include <storm/exceptions/InvalidArgumentException.h>
#include <storm/exceptions/InvalidModelException.h>
#include <storm/exceptions/NotSupportedException.h>
#include <storm/exceptions/UnexpectedException.h>
#include <storm/models/sparse/Pomdp.h>
#include <storm/transformer/SubsystemBuilder.h>
#include <storm/utility/builder.h>


namespace synthesis {

template<typename ValueType>
std::vector<std::vector<uint64_t>> computeChoiceDestinations(storm::models::sparse::Model<ValueType> const& model) {
    uint64_t num_choices = model.getNumberOfChoices();
    std::vector<std::vector<uint64_t>> choice_destinations(num_choices);
    for(uint64_t choice = 0; choice < num_choices; ++choice) {
        for(auto const& entry: model.getTransitionMatrix().getRow(choice)) {
            choice_destinations[choice].push_back(entry.getColumn());
        }
    }
    return choice_destinations;
}

template<typename ValueType>
void addMissingChoiceLabelsLabeling(
    storm::models::sparse::Model<ValueType> const& model,
    storm::models::sparse::ChoiceLabeling& choice_labeling
) {
    storm::storage::BitVector choice_has_no_label(model.getNumberOfChoices(),false);
    for(uint64_t choice = 0; choice < model.getNumberOfChoices(); ++choice) {
        if(choice_labeling.getLabelsOfChoice(choice).size() == 0) {
            choice_has_no_label.set(choice,true);
        }
    }
    if(choice_has_no_label.empty()) {
        return;
    }
    STORM_LOG_THROW(not choice_labeling.containsLabel(NO_ACTION_LABEL), storm::exceptions::InvalidModelException, "model already has the '" << NO_ACTION_LABEL << "' label");
    choice_labeling.addLabel(NO_ACTION_LABEL, choice_has_no_label);
}

template<typename ValueType>
std::shared_ptr<storm::models::sparse::Model<ValueType>> addMissingChoiceLabelsModel(
    storm::models::sparse::Model<ValueType> const& model
) {
    storm::storage::sparse::ModelComponents<ValueType> components = componentsFromModel(model);
    addMissingChoiceLabelsLabeling(model,components.choiceLabeling.value());
    if(not components.choiceLabeling.value().containsLabel(NO_ACTION_LABEL)) {
        return NULL;
    }

    if (dynamic_cast<Posmg<ValueType> const*>(&model))
    {
        return std::make_shared<Posmg<ValueType>>(std::move(components));
    }
    else
    {
        return storm::utility::builder::buildModelFromComponents<ValueType>(model.getType(),std::move(components));
    }
}

bool assertChoiceLabelingIsCanonic(
    std::vector<uint64_t> const& row_groups,
    storm::models::sparse::ChoiceLabeling const& choice_labeling,
    bool throw_on_fail
) {
    // collect action labels
    std::set<std::string> action_labels_set = choice_labeling.getLabels();
    std::vector<std::string> action_labels;
    action_labels.assign(action_labels_set.begin(), action_labels_set.end());
    uint64_t num_actions = action_labels.size();

    // associate choices with actions, check uniqueness for a choice
    std::vector<uint64_t> choice_to_action(row_groups.back(), num_actions);
    for(uint64_t action = 0; action < action_labels.size(); ++action) {
        std::string const& action_label = action_labels[action];
        for(uint64_t choice: choice_labeling.getChoices(action_label)) {
            if(choice_to_action[choice] != num_actions) {
                if(throw_on_fail) {
                    STORM_LOG_THROW(false, storm::exceptions::InvalidModelException, "multiple labels for choice " << choice);
                } else {
                    return false;
                }
            }
            choice_to_action[choice] = action;
        }
    }

    // check existence for a choice
    for(uint64_t action: choice_to_action) {
        if(action == num_actions) {
            if(throw_on_fail) {
                STORM_LOG_THROW(false, storm::exceptions::InvalidModelException, "a choice has no labels");
            } else {
                return false;
            }
        }
    }

    // check uniqueness for a state
    storm::storage::BitVector state_labels(num_actions, false);
    for(uint64_t state = 0; state < row_groups.size()-1; ++state) {
        for(uint64_t choice = row_groups[state]; choice < row_groups[state+1]; ++choice) {
            uint64_t action = choice_to_action[choice];
            if(state_labels[action]) {
                if(throw_on_fail) {
                    STORM_LOG_THROW(false, storm::exceptions::InvalidModelException, "a label is used twice for choices in state " << state);
                } else {
                    return false;
                }
            }
            state_labels.set(action,true);
        }
        state_labels.clear();
    }
    return true;
}

bool isChoiceLabelingCanonic(
    std::vector<uint64_t> const& row_groups,
    storm::models::sparse::ChoiceLabeling const& choice_labeling
) {
    std::set<std::string> state_labels;
    for(uint64_t state = 0; state < row_groups.size()-1; ++state) {
        for(uint64_t choice = row_groups[state]; choice < row_groups[state+1]; ++choice) {
            auto const& labels = choice_labeling.getLabelsOfChoice(choice);
            if(labels.size() != 1) {
                return false;
            }
            std::string const& label = *(labels.begin());
            if(state_labels.find(label) != state_labels.end()) {
                return false;
            }
            state_labels.insert(label);
        }
        state_labels.clear();
    }
    return true;
}

void removeUnusedLabels(storm::models::sparse::ChoiceLabeling & choice_labeling) {
    for(auto const& label: choice_labeling.getLabels()) {
        if(choice_labeling.getChoices(label).empty()) {
            choice_labeling.removeLabel(label);
        }
    }
}


template<typename ValueType>
std::pair<std::vector<std::string>,std::vector<uint64_t>> extractActionLabels(
    storm::models::sparse::Model<ValueType> const& model
) {
    // collect action labels
    storm::models::sparse::ChoiceLabeling const& choice_labeling = model.getChoiceLabeling();
    std::set<std::string> action_labels_set = choice_labeling.getLabels();
    std::vector<std::string> action_labels;
    action_labels.assign(action_labels_set.begin(), action_labels_set.end());
    // sort action labels to ensure order determinism (why did we think this was necessary?)
    std::sort(action_labels.begin(),action_labels.end());

    assertChoiceLabelingIsCanonic(model.getTransitionMatrix().getRowGroupIndices(), choice_labeling, false);

    std::vector<uint64_t> choice_to_action(model.getNumberOfChoices());
    for(uint64_t action = 0; action < action_labels.size(); ++action) {
        std::string const& action_label = action_labels[action];
        for(uint64_t choice: choice_labeling.getChoices(action_label)) {
            choice_to_action[choice] = action;
        }
    }

    return std::make_pair(action_labels,choice_to_action);
}

template<typename ValueType>
std::pair<std::shared_ptr<storm::models::sparse::Model<ValueType>>,std::vector<uint64_t>> enableAllActions(
    storm::models::sparse::Model<ValueType> const& model
) {
    return enableAllActions(model,storm::storage::BitVector(model.getNumberOfStates(),true));
}

template<typename ValueType>
std::pair<std::shared_ptr<storm::models::sparse::Model<ValueType>>,std::vector<uint64_t>> enableAllActions(
    storm::models::sparse::Model<ValueType> const& model,
    storm::storage::BitVector const& state_mask
) {
    auto [action_labels,choice_to_action] = synthesis::extractActionLabels<ValueType>(model);
    uint64_t num_actions = action_labels.size();
    uint64_t num_states = model.getNumberOfStates();
    uint64_t num_choices = model.getNumberOfChoices();

    uint64_t dont_care_action = num_actions;
    for(uint64_t action = 0; action < num_actions; ++action) {
        if(action_labels[action] == DONT_CARE_ACTION_LABEL) {
            dont_care_action = action;
            break;
        }
    }

    // for each action, find any choice that corresponds to this action
    // we compute this to easily build the new choice labeling
    std::vector<uint64_t> action_reference_choice(num_actions);
    for(uint64_t choice = 0; choice < num_choices; ++choice) {
        action_reference_choice[choice_to_action[choice]] = choice;
    }
    std::vector<uint64_t> translated_to_true_action;

    // for each state-action pair, find the corresponding choice
    // translate choices
    auto const& row_groups_old = model.getTransitionMatrix().getRowGroupIndices();
    std::vector<uint64_t> translated_to_original_choice;
    std::vector<uint64_t> translated_to_original_choice_label;
    std::vector<uint64_t> row_groups_new;
    std::vector<uint64_t> action_to_choice(num_actions);
    for(uint64_t state = 0; state < num_states; ++state) {
        row_groups_new.push_back(translated_to_original_choice.size());
        if(not state_mask[state]) {
            // keep choices
            for(uint64_t choice: model.getTransitionMatrix().getRowGroupIndices(state)) {
                translated_to_original_choice.push_back(choice);
                translated_to_original_choice_label.push_back(choice);
                translated_to_true_action.push_back(choice_to_action[choice]);
            }
            continue;
        }
        // identify existing actions, identify the fallback choice
        uint64_t fallback_choice = row_groups_old[state];
        std::fill(action_to_choice.begin(),action_to_choice.end(),num_choices);
        for(uint64_t choice: model.getTransitionMatrix().getRowGroupIndices(state)) {
            uint64_t action = choice_to_action[choice];
            if(action == dont_care_action) {
                fallback_choice = choice;
            }
            action_to_choice[action] = choice;
        }
        uint64_t fallback_action = choice_to_action[fallback_choice];
        // add new choices in the order of actions
        for(uint64_t action = 0; action < num_actions; ++action) {
            uint64_t choice = action_to_choice[action];
            if(choice < num_choices) {
                translated_to_original_choice.push_back(choice);
                translated_to_true_action.push_back(action);
            } else {
                translated_to_original_choice.push_back(fallback_choice);
                translated_to_true_action.push_back(fallback_action);
            }
            translated_to_original_choice_label.push_back(action_reference_choice[action]);
        }
    }
    row_groups_new.push_back(translated_to_original_choice.size());
    uint64_t num_translated_choices = translated_to_original_choice.size();

    // build components
    storm::storage::sparse::ModelComponents<ValueType> components = componentsFromModel(model);
    components.choiceOrigins.reset();
    storm::storage::BitVector translated_choice_mask(num_translated_choices,true);
    components.choiceLabeling = synthesis::translateChoiceLabeling<ValueType>(model,translated_to_original_choice_label,translated_choice_mask);
    storm::storage::SparseMatrixBuilder<ValueType> builder(num_translated_choices, num_states, 0, true, true, num_states);
    for(uint64_t state = 0; state < num_states; ++state) {
        builder.newRowGroup(row_groups_new[state]);
        for(uint64_t translated_choice = row_groups_new[state]; translated_choice < row_groups_new[state+1]; ++translated_choice) {
            uint64_t choice = translated_to_original_choice[translated_choice];
            for(auto entry: model.getTransitionMatrix().getRow(choice)) {
                builder.addNextValue(translated_choice, entry.getColumn(), entry.getValue());
            }
        }
    }
    components.transitionMatrix =  builder.build();
    components.rewardModels = synthesis::translateRewardModels(model,translated_to_original_choice,translated_choice_mask);
    auto new_model = storm::utility::builder::buildModelFromComponents<ValueType,storm::models::sparse::StandardRewardModel<ValueType>>(model.getType(),std::move(components));
    return std::make_pair(new_model,translated_to_true_action);
}


template<typename ValueType>
std::shared_ptr<storm::models::sparse::Model<ValueType>> removeAction(
    storm::models::sparse::Model<ValueType> const& model,
    std::string const& action_to_remove_label,
    storm::storage::BitVector const& state_mask
) {
    auto [action_labels,choice_to_action] = synthesis::extractActionLabels<ValueType>(model);
    uint64_t num_actions = action_labels.size();
    uint64_t num_states = model.getNumberOfStates();
    uint64_t num_choices = model.getNumberOfChoices();
    // identify action to remove
    uint64_t action_to_remove = num_actions;
    for(action_to_remove = 0; action_to_remove < num_actions; ++action_to_remove) {
        if(action_labels[action_to_remove] == action_to_remove_label) {
            break;
        }
    }
    if(action_to_remove == num_actions) {
        return NULL;
    }

    // identify choices to remove
    storm::storage::BitVector choice_enabled(num_choices,true);
    for(uint64_t state: state_mask) {
        for(uint64_t choice: model.getTransitionMatrix().getRowGroupIndices(state)) {
            if(choice_to_action[choice] == action_to_remove) {
                choice_enabled.set(choice,false);
            }
        }
    }
    if(choice_enabled.full()) {
        return NULL;
    }

    // construct the corresponding sub-MDP
    storm::storage::BitVector all_states(num_states,true);
    storm::storage::sparse::ModelComponents<ValueType> components = componentsFromModel(model);
    if((model.getChoiceLabeling().getChoices(action_to_remove_label) & choice_enabled).empty()) {
        components.choiceLabeling.value().removeLabel(action_to_remove_label);
    }
    std::shared_ptr<storm::models::sparse::Model<ValueType>> mdp = storm::utility::builder::buildModelFromComponents<ValueType>(storm::models::ModelType::Mdp,std::move(components));
    storm::transformer::SubsystemBuilderReturnType<ValueType> build_result = storm::transformer::buildSubsystem(*mdp, all_states, choice_enabled);
    std::shared_ptr<storm::models::sparse::Model<ValueType>> submdp = build_result.model;
    if (model.getType() != storm::models::ModelType::Pomdp) {
        return submdp;
    }
    components = componentsFromModel(*submdp);
    components.observabilityClasses = translateObservabilityClasses(model,build_result.newToOldStateIndexMapping);
    return storm::utility::builder::buildModelFromComponents<ValueType>(model.getType(),std::move(components));
}


template<typename ValueType>
std::shared_ptr<storm::models::sparse::Model<ValueType>> restoreActionsInAbsorbingStates(
    storm::models::sparse::Model<ValueType> const& model
) {
    auto model_canonic = addMissingChoiceLabelsModel(model);
    if(model_canonic == NULL) {
        return NULL;
    }
    assertChoiceLabelingIsCanonic(model_canonic->getTransitionMatrix().getRowGroupIndices(), model_canonic->getChoiceLabeling());
    storm::storage::BitVector const& no_action_label_choices = model_canonic->getChoiceLabeling().getChoices(NO_ACTION_LABEL);
    storm::storage::BitVector absorbing_states(model.getNumberOfStates(),true);
    for(uint64_t state = 0; state < model.getNumberOfStates(); ++state) {
        for(uint64_t choice: model_canonic->getTransitionMatrix().getRowGroupIndices(state)) {
            if(not no_action_label_choices[choice]) {
                absorbing_states.set(state,false);
                break;
            }
            for(auto const& entry: model_canonic->getTransitionMatrix().getRow(choice)) {
                if(entry.getColumn() != state) {
                    absorbing_states.set(state,false);
                    break;
                }
            }
            if(not absorbing_states[state]) {
                break;
            }
        }
    }
    if(absorbing_states.empty()) {
        return NULL;
    }
    auto [model_absorbing_enabled,translated_to_true_action] = synthesis::enableAllActions(*model_canonic, absorbing_states);
    return synthesis::removeAction(*model_absorbing_enabled, NO_ACTION_LABEL, absorbing_states);
}

template<typename ValueType>
std::shared_ptr<storm::models::sparse::Model<ValueType>> addDontCareAction(
    storm::models::sparse::Model<ValueType> const& model,
    storm::storage::BitVector const& state_mask
) {
    auto [action_labels,choice_to_action] = synthesis::extractActionLabels<ValueType>(model);
    auto it = std::find(action_labels.begin(),action_labels.end(),DONT_CARE_ACTION_LABEL);
    STORM_LOG_THROW(it == action_labels.end(), storm::exceptions::UnexpectedException,
        "label " << DONT_CARE_ACTION_LABEL << " is already defined");
    uint64_t num_actions = action_labels.size();
    uint64_t num_states = model.getNumberOfStates();
    uint64_t num_choices = model.getNumberOfChoices();

    // for each action, find any choice that corresponds to this action
    // we compute this to easily build choice labeling later
    std::vector<uint64_t> action_reference_choice(num_actions);
    for(uint64_t choice = 0; choice < num_choices; ++choice) {
        action_reference_choice[choice_to_action[choice]] = choice;
    }

    // translate choices
    std::vector<uint64_t> translated_to_original_choice;
    std::vector<uint64_t> row_groups_new;
    std::vector<uint64_t> const& row_groups = model.getTransitionMatrix().getRowGroupIndices();
    for(uint64_t state = 0; state < num_states; ++state) {
        row_groups_new.push_back(translated_to_original_choice.size());
        // copy existing choices
        for(uint64_t choice = row_groups[state]; choice < row_groups[state+1]; ++choice) {
            translated_to_original_choice.push_back(choice);
        }
        if(state_mask[state]) {
            // add don't care action
            translated_to_original_choice.push_back(num_choices);
        }
    }
    row_groups_new.push_back(translated_to_original_choice.size());
    uint64_t num_translated_choices = translated_to_original_choice.size();
    storm::storage::BitVector translated_choice_mask(num_translated_choices,false);
    for(uint64_t translated_choice = 0; translated_choice < num_translated_choices; ++translated_choice) {
        translated_choice_mask.set(translated_choice, translated_to_original_choice[translated_choice] < num_choices);
    }

    // build components
    storm::storage::sparse::ModelComponents<ValueType> components = componentsFromModel(model);
    components.choiceOrigins.reset();
    auto choiceLabeling = synthesis::translateChoiceLabeling<ValueType>(model,translated_to_original_choice,translated_choice_mask);
    choiceLabeling.addLabel(DONT_CARE_ACTION_LABEL, ~translated_choice_mask);
    components.choiceLabeling = choiceLabeling;
    storm::storage::SparseMatrixBuilder<ValueType> builder(num_translated_choices, num_states, 0, true, true, num_states);
    for(uint64_t state = 0; state < num_states; ++state) {
        builder.newRowGroup(row_groups_new[state]);
        uint64_t state_num_choices = row_groups[state+1]-row_groups[state]; // the original number of choices
        // copy existing choices
        std::map<uint64_t,ValueType> dont_care_transitions;
        uint64_t translated_choice = row_groups_new[state];
        for(uint64_t choice = row_groups[state]; choice < row_groups[state+1]; ++choice) {
            for(auto entry: model.getTransitionMatrix().getRow(choice)) {
                uint64_t dst = entry.getColumn();
                ValueType prob = entry.getValue();
                builder.addNextValue(translated_choice, dst, prob);
                // it seems like we have no choice but to add explicit cast to unsigned long since gmp does not
                // support convrsion of unsigned long long to mpq_class which caused problems on ARM
                if constexpr (std::is_same_v<ValueType, mpq_class>) {
                    dont_care_transitions[dst] += prob / static_cast<unsigned long>(state_num_choices);
                } else {
                    dont_care_transitions[dst] += prob / state_num_choices;
                }
            }
            ++translated_choice;
        }
        if(state_mask[state]) {
            // add don't care action
            for(auto [dst,prob]: dont_care_transitions) {
                builder.addNextValue(translated_choice,dst,prob);
            }
        }
    }
    components.transitionMatrix =  builder.build();
    auto rewardModels = synthesis::translateRewardModels(model,translated_to_original_choice,translated_choice_mask);
    for(auto & [name,reward_model]: rewardModels) {
        std::vector<ValueType> & choice_reward = reward_model.getStateActionRewardVector();
        for(uint64_t state = 0; state < num_states; ++state) {
            if(not state_mask[state]) {
                continue;
            }
            ValueType reward_sum = 0;
            uint64_t dont_care_translated_choice = row_groups_new[state+1]-1;
            uint64_t state_num_choices = dont_care_translated_choice-row_groups_new[state];
            for(uint64_t translated_choice = row_groups_new[state]; translated_choice < dont_care_translated_choice; ++translated_choice) {
                reward_sum += choice_reward[translated_choice];
            }
            // it seems like we have no choice but to add explicit cast to unsigned long since gmp does not
            // support convrsion of unsigned long long to mpq_class which caused problems on ARM
            if constexpr (std::is_same_v<ValueType, mpq_class>) {
                choice_reward[dont_care_translated_choice] = reward_sum / static_cast<unsigned long>(state_num_choices);
            } else {
                choice_reward[dont_care_translated_choice] = reward_sum / state_num_choices;
            }
        }
    }
    components.rewardModels = rewardModels;
    return storm::utility::builder::buildModelFromComponents<ValueType,storm::models::sparse::StandardRewardModel<ValueType>>(model.getType(),std::move(components));
}



template<typename ValueType>
std::shared_ptr<storm::models::sparse::Model<ValueType>> createModelUnion(
    std::vector<std::shared_ptr<storm::models::sparse::Model<ValueType>>> const& models
) {
    uint64_t num_models = models.size();
    STORM_LOG_THROW(num_models > 0, storm::exceptions::InvalidArgumentException, "the list of models is empty");

    uint64_t union_initial_state = 0;
    uint64_t union_num_states = 1;
    uint64_t union_num_choices = 1;
    std::vector<uint64_t> state_offset;
    std::vector<uint64_t> choice_offset;
    for(uint64_t model_index = 0; model_index < num_models; ++model_index) {
        state_offset.push_back(union_num_states);
        choice_offset.push_back(union_num_choices);
        auto model = models[model_index];
        union_num_states += model->getNumberOfStates();
        union_num_choices += model->getNumberOfChoices();
    }

    storm::storage::sparse::ModelComponents<ValueType> components;
    storm::models::sparse::StateLabeling union_state_labeling(union_num_states);
    union_state_labeling.addLabel("init");
    union_state_labeling.addLabelToState("init",union_initial_state);
    for(uint64_t model_index = 0; model_index < num_models; ++model_index) {
        auto model = models[model_index];
        storm::models::sparse::StateLabeling const& state_labeling = model->getStateLabeling();
        for (auto const& label : state_labeling.getLabels()) {
            if(not union_state_labeling.containsLabel(label)) {
                union_state_labeling.addLabel(label);
            }
        }
        for(uint64_t state = 0; state < model->getNumberOfStates(); ++state) {
            uint64_t union_state = state_offset[model_index] + state;
            for(std::string const& label: state_labeling.getLabelsOfState(state)) {
                if(label == "init") {
                    continue;
                }
                union_state_labeling.addLabelToState(label,union_state);
            }
        }
    }
    components.stateLabeling = union_state_labeling;

    if(models[0]->getType() == storm::models::ModelType::Pomdp) {
        std::vector<uint32_t> state_observation(union_num_states);
        uint64_t num_observations = 0;
        for(uint64_t model_index = 0; model_index < num_models; ++model_index) {
            auto model = models[model_index];
            auto pomdp = static_cast<storm::models::sparse::Pomdp<ValueType> const&>(*model);
            if(pomdp.getNrObservations() > num_observations) {
                num_observations = pomdp.getNrObservations();
            }
            for(uint64_t state = 0; state < pomdp.getNumberOfStates(); ++state) {
                uint64_t union_state = state_offset[model_index] + state;
                state_observation[union_state] = pomdp.getObservation(state);
            }
        }
        state_observation[union_initial_state] = num_observations;
        components.observabilityClasses = state_observation;
    }

    // skipping state and observation valuations

    storm::models::sparse::ChoiceLabeling union_choice_labeling(union_num_choices);
    union_choice_labeling.addLabel(NO_ACTION_LABEL);
    union_choice_labeling.addLabelToChoice(NO_ACTION_LABEL,0);
    storm::storage::SparseMatrixBuilder<ValueType> builder(
        union_num_choices, union_num_states, 0, false, true, union_num_states
    );
    ValueType belief_uniform_prob = 1.0/num_models;
    builder.newRowGroup(union_initial_state);
    for(uint64_t model_index = 0; model_index < num_models; ++model_index) {
        auto model = models[model_index];
        uint64_t initial_state = state_offset[model_index] + *(model->getInitialStates().begin());
        builder.addNextValue(union_initial_state, initial_state, belief_uniform_prob);
    }
    for(uint64_t model_index = 0; model_index < num_models; ++model_index) {
        auto model = models[model_index];
        storm::models::sparse::ChoiceLabeling const& choice_labeling = model->getChoiceLabeling();
        for (auto const& label : choice_labeling.getLabels()) {
            if(not union_choice_labeling.containsLabel(label)) {
                union_choice_labeling.addLabel(label);
            }
        }

        auto const& row_groups = model->getTransitionMatrix().getRowGroupIndices();
        for(uint64_t state = 0; state < model->getNumberOfStates(); ++state) {
            builder.newRowGroup(choice_offset[model_index]+row_groups[state]);
            for(uint64_t choice = row_groups[state]; choice < row_groups[state+1]; ++choice) {
                uint64_t union_choice = choice_offset[model_index]+choice;
                for(auto entry: model->getTransitionMatrix().getRow(choice)) {
                    builder.addNextValue(union_choice, state_offset[model_index]+entry.getColumn(), entry.getValue());
                }
                for(std::string const& label: choice_labeling.getLabelsOfChoice(choice)) {
                    union_choice_labeling.addLabelToChoice(label,union_choice);
                }
            }
        }
    }
    components.transitionMatrix =  builder.build();
    components.choiceLabeling = union_choice_labeling;
    // skipping choice origins

    std::map<std::string,std::vector<ValueType>> reward_models;
    for(uint64_t model_index = 0; model_index < num_models; ++model_index) {
        auto model = models[model_index];
        for(auto const& [reward_name,reward_model] : model->getRewardModels()) {
            STORM_LOG_THROW(!reward_model.hasStateRewards() and !reward_model.hasTransitionRewards() and reward_model.hasStateActionRewards(),
                storm::exceptions::NotSupportedException, "expected state-action rewards");
            if(reward_models.count(reward_name) == 0) {
                reward_models.emplace(reward_name,std::vector<ValueType>(union_num_choices,0));
            }

            for(uint64_t choice = 0; choice < model->getNumberOfChoices(); ++choice) {
                uint64_t union_choice = choice_offset[model_index] + choice;
                reward_models[reward_name][union_choice] = reward_model.getStateActionReward(choice);
            }
        }
    }

    for(auto &[reward_name,action_rewards]: reward_models) {
        std::optional<std::vector<ValueType>> state_rewards;
        components.rewardModels.emplace(
            reward_name, storm::models::sparse::StandardRewardModel<ValueType>(std::move(state_rewards), std::move(action_rewards))
        );
    }

    return storm::utility::builder::buildModelFromComponents<ValueType>(models[0]->getType(),std::move(components));
}


template std::vector<std::vector<uint64_t>> computeChoiceDestinations<double>(
    storm::models::sparse::Model<double> const& model);
template std::pair<std::vector<std::string>,std::vector<uint64_t>> extractActionLabels<double>(
    storm::models::sparse::Model<double> const& model);
template void addMissingChoiceLabelsLabeling<double>(
    storm::models::sparse::Model<double> const& model,
    storm::models::sparse::ChoiceLabeling& choice_labeling);
template std::shared_ptr<storm::models::sparse::Model<double>> addMissingChoiceLabelsModel<double>(
    storm::models::sparse::Model<double> const& model);
template std::pair<std::shared_ptr<storm::models::sparse::Model<double>>,std::vector<uint64_t>> enableAllActions(
    storm::models::sparse::Model<double> const& model);
template std::pair<std::shared_ptr<storm::models::sparse::Model<double>>,std::vector<uint64_t>> enableAllActions<double>(
    storm::models::sparse::Model<double> const& model,
    storm::storage::BitVector const& state_mask);
template std::shared_ptr<storm::models::sparse::Model<double>> removeAction<double>(
    storm::models::sparse::Model<double> const& model,
    std::string const& action_to_remove_label,
    storm::storage::BitVector const& state_mask);
template std::shared_ptr<storm::models::sparse::Model<double>> restoreActionsInAbsorbingStates<double>(
    storm::models::sparse::Model<double> const& model);
template std::shared_ptr<storm::models::sparse::Model<double>> addDontCareAction<double>(
    storm::models::sparse::Model<double> const& model,
    storm::storage::BitVector const& state_mask);
template std::shared_ptr<storm::models::sparse::Model<double>> createModelUnion(
    std::vector<std::shared_ptr<storm::models::sparse::Model<double>>> const&
);

template std::vector<std::vector<uint64_t>> computeChoiceDestinations<storm::RationalNumber>(
    storm::models::sparse::Model<storm::RationalNumber> const& model);
template std::pair<std::vector<std::string>,std::vector<uint64_t>> extractActionLabels<storm::RationalNumber>(
    storm::models::sparse::Model<storm::RationalNumber> const& model);
template void addMissingChoiceLabelsLabeling<storm::RationalNumber>(
    storm::models::sparse::Model<storm::RationalNumber> const& model,
    storm::models::sparse::ChoiceLabeling& choice_labeling);
template std::shared_ptr<storm::models::sparse::Model<storm::RationalNumber>> addMissingChoiceLabelsModel<storm::RationalNumber>(
    storm::models::sparse::Model<storm::RationalNumber> const& model);
template std::pair<std::shared_ptr<storm::models::sparse::Model<storm::RationalNumber>>,std::vector<uint64_t>> enableAllActions(
    storm::models::sparse::Model<storm::RationalNumber> const& model);
template std::pair<std::shared_ptr<storm::models::sparse::Model<storm::RationalNumber>>,std::vector<uint64_t>> enableAllActions<storm::RationalNumber>(
    storm::models::sparse::Model<storm::RationalNumber> const& model,
    storm::storage::BitVector const& state_mask);
template std::shared_ptr<storm::models::sparse::Model<storm::RationalNumber>> removeAction<storm::RationalNumber>(
    storm::models::sparse::Model<storm::RationalNumber> const& model,
    std::string const& action_to_remove_label,
    storm::storage::BitVector const& state_mask);
template std::shared_ptr<storm::models::sparse::Model<storm::RationalNumber>> restoreActionsInAbsorbingStates<storm::RationalNumber>(
    storm::models::sparse::Model<storm::RationalNumber> const& model);
template std::shared_ptr<storm::models::sparse::Model<storm::RationalNumber>> addDontCareAction<storm::RationalNumber>(
    storm::models::sparse::Model<storm::RationalNumber> const& model,
    storm::storage::BitVector const& state_mask);
template std::shared_ptr<storm::models::sparse::Model<storm::RationalNumber>> createModelUnion(
    std::vector<std::shared_ptr<storm::models::sparse::Model<storm::RationalNumber>>> const&
);

}
