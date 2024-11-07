#include "choiceTransformation.h"

#include "src/synthesis/translation/componentTranslations.h"

#include <storm/exceptions/InvalidModelException.h>
#include <storm/exceptions/UnexpectedException.h>
#include <storm/exceptions/InvalidArgumentException.h>
#include <storm/models/sparse/Pomdp.h>
#include <storm/utility/builder.h>
#include <storm/transformer/SubsystemBuilder.h>

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
    return storm::utility::builder::buildModelFromComponents<ValueType>(model.getType(),std::move(components));
}

bool assertChoiceLabelingIsCanonic(
    std::vector<uint64_t> const& row_groups,
    storm::models::sparse::ChoiceLabeling const& choice_labeling,
    bool throw_on_fail
) {
    std::set<std::string> state_labels;
    for(uint64_t state = 0; state < row_groups.size()-1; ++state) {
        for(uint64_t choice = row_groups[state]; choice < row_groups[state+1]; ++choice) {
            auto const& labels = choice_labeling.getLabelsOfChoice(choice);
            if(labels.size() != 1) {
                if(throw_on_fail) {
                    STORM_LOG_THROW(false, storm::exceptions::InvalidModelException, "expected exactly 1 label for choice " << choice);
                } else {
                    return false;
                }
            }
            std::string const& label = *(labels.begin());
            if(state_labels.find(label) != state_labels.end()) {
                if(throw_on_fail) {
                    STORM_LOG_THROW(false, storm::exceptions::InvalidModelException, "label " << label << " is used twice for choices in state " << state);
                } else {
                    return false;
                }
            }
            state_labels.insert(label);
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
    std::set<std::string> action_labels_set;
    for(uint64_t choice = 0; choice < model.getNumberOfChoices(); ++choice) {
        for(std::string const& label: choice_labeling.getLabelsOfChoice(choice)) {
            action_labels_set.insert(label);
        }
    }

    // sort action labels to ensure order determinism
    std::vector<std::string> action_labels;
    for(std::string const& label: action_labels_set) {
        action_labels.push_back(label);
    }
    std::sort(action_labels.begin(),action_labels.end());

    // map action labels to actions
    std::map<std::string,uint64_t> action_label_to_action;
    for(uint64_t action = 0; action < action_labels.size(); ++action) {
        action_label_to_action[action_labels[action]] = action;
    }

    assertChoiceLabelingIsCanonic(model.getTransitionMatrix().getRowGroupIndices(), choice_labeling, false);
    std::vector<uint64_t> choice_to_action(model.getNumberOfChoices());
    for(uint64_t choice = 0; choice < model.getNumberOfChoices(); ++choice) {
        auto const& labels = choice_labeling.getLabelsOfChoice(choice);
        std::string const& label = *(labels.begin());
        uint64_t action = action_label_to_action[label];
        choice_to_action[choice] = action;
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
    storm::storage::BitVector action_exists(num_actions,false);
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
        action_exists.clear();
        uint64_t fallback_choice = row_groups_old[state];
        for(uint64_t choice: model.getTransitionMatrix().getRowGroupIndices(state)) {
            uint64_t action = choice_to_action[choice];
            if(action == dont_care_action) {
                fallback_choice = choice;
            }
            action_exists.set(action,true);
            translated_to_original_choice.push_back(choice);
            translated_to_original_choice_label.push_back(choice);
            translated_to_true_action.push_back(action);
        }
        // add missing actions
        for(uint64_t action: ~action_exists) {
            translated_to_original_choice.push_back(fallback_choice);
            translated_to_original_choice_label.push_back(action_reference_choice[action]);
            translated_to_true_action.push_back(choice_to_action[fallback_choice]);
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
    storm::models::sparse::Model<ValueType> const& model
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
    for(uint64_t state = 0; state < num_states; ++state) {
        row_groups_new.push_back(translated_to_original_choice.size());
        // copy existing choices
        for(uint64_t choice: model.getTransitionMatrix().getRowGroupIndices(state)) {
            translated_to_original_choice.push_back(choice);
        }
        // add don't care action
        translated_to_original_choice.push_back(num_choices);
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
        // copy existing choices
        std::map<uint64_t,ValueType> dont_care_transitions;
        uint64_t new_translated_choice = row_groups_new[state+1]-1;
        uint64_t state_num_choices = new_translated_choice-row_groups_new[state];
        for(uint64_t translated_choice = row_groups_new[state]; translated_choice < new_translated_choice; ++translated_choice) {
            uint64_t choice = translated_to_original_choice[translated_choice];
            for(auto entry: model.getTransitionMatrix().getRow(choice)) {
                uint64_t dst = entry.getColumn();
                ValueType prob = entry.getValue();
                builder.addNextValue(translated_choice, dst, prob);
                dont_care_transitions[dst] += prob/state_num_choices;
            }
        }
        // add don't care action
        for(auto [dst,prob]: dont_care_transitions) {
            builder.addNextValue(new_translated_choice,dst,prob);
        }
    }
    components.transitionMatrix =  builder.build();
    auto rewardModels = synthesis::translateRewardModels(model,translated_to_original_choice,translated_choice_mask);
    for(auto & [name,reward_model]: rewardModels) {
        std::vector<ValueType> & choice_reward = reward_model.getStateActionRewardVector();
        for(uint64_t state = 0; state < num_states; ++state) {
            ValueType reward_sum = 0;
            uint64_t new_translated_choice = row_groups_new[state+1]-1;
            uint64_t state_num_choices = new_translated_choice-row_groups_new[state];
            for(uint64_t translated_choice = row_groups_new[state]; translated_choice < new_translated_choice; ++translated_choice) {
                reward_sum += choice_reward[translated_choice];
            }
            choice_reward[new_translated_choice] = reward_sum / state_num_choices;
        }
    }
    components.rewardModels = rewardModels;
    return storm::utility::builder::buildModelFromComponents<ValueType,storm::models::sparse::StandardRewardModel<ValueType>>(model.getType(),std::move(components));
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
    storm::models::sparse::Model<double> const& model);

}
