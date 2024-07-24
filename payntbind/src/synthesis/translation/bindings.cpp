#include "../synthesis.h"
#include "SubPomdpBuilder.h"

#include "src/synthesis/translation/componentTranslations.h"

#include <storm/exceptions/InvalidModelException.h>
#include <storm/utility/builder.h>
#include <storm/transformer/SubsystemBuilder.h>

namespace synthesis {

/**
 * Add an explicit label to the choices that do not have any.
 */
template<typename ValueType>
std::shared_ptr<storm::models::sparse::Model<ValueType>> addMissingChoiceLabels(
    storm::models::sparse::Model<ValueType> const& model
) {
    STORM_LOG_THROW(model.hasChoiceLabeling(), storm::exceptions::InvalidModelException, "model does not have the choice labeling");

    storm::storage::sparse::ModelComponents<ValueType> components;
    components.stateLabeling = model.getStateLabeling();
    components.stateValuations = model.getOptionalStateValuations();
    components.transitionMatrix = model.getTransitionMatrix();
    components.choiceLabeling = model.getChoiceLabeling();
    components.choiceOrigins = model.getOptionalChoiceOrigins();
    components.rewardModels = model.getRewardModels();

    auto const& labeling = model.getChoiceLabeling();
    storm::storage::BitVector choices_without_label(model.getNumberOfChoices(),false);
    for(uint64_t choice = 0; choice < model.getNumberOfChoices(); ++choice) {
        if(labeling.getLabelsOfChoice(choice).empty()) {
            choices_without_label.set(choice,true);
        }
    }
    const std::string NO_ACTION_LABEL = "__no_label__";
    if(not choices_without_label.empty()) {
        components.choiceLabeling->addUniqueLabel(NO_ACTION_LABEL,choices_without_label);
    }
    if (model.getType() == storm::models::ModelType::Pomdp) {
        auto pomdp = static_cast<storm::models::sparse::Pomdp<ValueType> const&>(model);
        components.observabilityClasses = pomdp.getObservations();
        components.observationValuations = pomdp.getOptionalObservationValuations();
    }

    return storm::utility::builder::buildModelFromComponents<ValueType>(model.getType(),std::move(components));
}


/**
 * Given an MDP with canonic choice labeling, make sure that in each state from the provided \p state_maks all actions
 * are available. If an action is not available in a state, add it to this state with the behavior of the first
 * existing action.
 */
template<typename ValueType>
std::shared_ptr<storm::models::sparse::Model<ValueType>> enableAllActions(
    storm::models::sparse::Model<ValueType> const& model,
    storm::storage::BitVector const& state_mask
) {
    auto [action_labels,choice_to_action] = synthesis::extractActionLabels<ValueType>(model);
    uint64_t num_actions = action_labels.size();
    uint64_t num_states = model.getNumberOfStates();
    uint64_t num_choices = model.getNumberOfChoices();

    // for each action, find some choice that corresponds to this action
    std::vector<uint64_t> action_reference_choice(num_actions);
    for(uint64_t choice = 0; choice < num_choices; ++choice) {
        action_reference_choice[choice_to_action[choice]] = choice;
    }

    // for each state-action pair, find the corresponding choice
    // translate choices
    auto const& row_groups_old = model.getTransitionMatrix().getRowGroupIndices();
    std::vector<uint64_t> translated_to_original_choice;
    std::vector<uint64_t> translated_to_original_choice_label;
    std::vector<uint64_t> row_groups_new;
    for(uint64_t state = 0; state < num_states; ++state) {
        row_groups_new.push_back(translated_to_original_choice.size());
        if(not state_mask[state]) {
            for(uint64_t choice: model.getTransitionMatrix().getRowGroupIndices(state)) {
                translated_to_original_choice.push_back(choice);
                translated_to_original_choice_label.push_back(choice);
            }
        } else {
            std::vector<bool> action_exists(num_actions,false);
            for(uint64_t choice: model.getTransitionMatrix().getRowGroupIndices(state)) {
                uint64_t action = choice_to_action[choice];
                action_exists[action] = true;
                translated_to_original_choice.push_back(choice);
                translated_to_original_choice_label.push_back(choice);
            }
            for(uint64_t action = 0; action < num_actions; ++action) {
                if(action_exists[action]) {
                    continue;
                }
                uint64_t choice = row_groups_old[state];
                translated_to_original_choice.push_back(choice);
                translated_to_original_choice_label.push_back(action_reference_choice[action]);
            }
        }
    }
    row_groups_new.push_back(translated_to_original_choice.size());
    uint64_t num_translated_choices = translated_to_original_choice.size();

    // build components
    storm::storage::sparse::ModelComponents<ValueType> components;
    components.stateLabeling = model.getStateLabeling();
    components.stateValuations = model.getOptionalStateValuations();
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

    if (model.getType() == storm::models::ModelType::Pomdp) {
        auto pomdp = static_cast<storm::models::sparse::Pomdp<ValueType> const&>(model);
        components.observabilityClasses = pomdp.getObservations();
        components.observationValuations = pomdp.getOptionalObservationValuations();
    }

    return storm::utility::builder::buildModelFromComponents<ValueType,storm::models::sparse::StandardRewardModel<ValueType>>(model.getType(),std::move(components));
}

/**
 * Given an MDP with canonic choice labeling, remove an action from the given set \p state_mask of states.
 */
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
    uint64_t action_to_remove = num_actions;
    for(action_to_remove = 0; action_to_remove < num_actions; ++action_to_remove) {
        if(action_labels[action_to_remove] == action_to_remove_label) {
            break;
        }
    }

    storm::storage::BitVector choice_enabled(num_choices,true);
    for(uint64_t state: state_mask) {
        for(uint64_t choice: model.getTransitionMatrix().getRowGroupIndices(state)) {
            uint64_t action = choice_to_action[choice];
            if(action == action_to_remove) {
                choice_enabled.set(choice,false);
            }
        }
    }
    storm::storage::BitVector all_states(num_states,true);
    storm::transformer::SubsystemBuilderReturnType<ValueType> build_result = storm::transformer::buildSubsystem(model, all_states, choice_enabled);
    return build_result.model;
}

/**
 * Given an MDP, for any state in the set \p target_states, mark any unlabeled action, explicitly add all availabled
 * actions and subsequently removed unlabeled actions.
 */
template<typename ValueType>
std::shared_ptr<storm::models::sparse::Model<ValueType>> restoreActionsInTargetStates(
    storm::models::sparse::Model<ValueType> const& model,
    storm::storage::BitVector const& target_states
) {
    auto model_canonic = synthesis::addMissingChoiceLabels(model);
    auto model_target_enabled = synthesis::enableAllActions(*model_canonic, target_states);
    const std::string NO_ACTION_LABEL = "__no_label__";
    auto model_target_fixed = synthesis::removeAction(*model_target_enabled, NO_ACTION_LABEL, target_states);
    return model_target_fixed;
}

}

void bindings_translation(py::module& m) {

    m.def("addMissingChoiceLabels", &synthesis::addMissingChoiceLabels<double>);
    m.def("extractActionLabels", &synthesis::extractActionLabels<double>);
    m.def("enableAllActions", &synthesis::enableAllActions<double>);
    m.def("restoreActionsInTargetStates", &synthesis::restoreActionsInTargetStates<double>);

    py::class_<synthesis::SubPomdpBuilder<double>, std::shared_ptr<synthesis::SubPomdpBuilder<double>>>(m, "SubPomdpBuilder")
        .def(py::init<storm::models::sparse::Pomdp<double> const&>())
        .def("start_from_belief", &synthesis::SubPomdpBuilder<double>::startFromBelief)
        .def_property_readonly("state_sub_to_full", [](synthesis::SubPomdpBuilder<double>& b) {return b.state_sub_to_full;} )
        ;
}

