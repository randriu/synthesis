#pragma once

#include <storm/storage/BitVector.h>
#include <storm/adapters/RationalNumberAdapter.h>
#include <storm/models/sparse/Model.h>
#include <storm/models/sparse/StateLabeling.h>
#include <storm/models/sparse/ChoiceLabeling.h>

#include <vector>

namespace synthesis {

// label used for choices that do not have an explicit one
const std::string NO_ACTION_LABEL = "__no_label__";
// label used for a choice that executes a random selection of available choice
const std::string DONT_CARE_ACTION_LABEL = "__random__";

/**
 * Return for each state a list of its state destinations.
 */
template<typename ValueType>
std::vector<std::vector<uint64_t>> computeChoiceDestinations(storm::models::sparse::Model<ValueType> const& model);

/**
 * Add \p NO_ACTION_LABEL label to any choice that does not have any.
 */
template<typename ValueType>
void addMissingChoiceLabelsLabeling(
    storm::models::sparse::Model<ValueType> const& model,
    storm::models::sparse::ChoiceLabeling& choice_labeling
);

/**
 * Add \p NO_ACTION_LABEL label to any choice that does not have any.
 * @return an updated model or NULL if no change took place
 */
template<typename ValueType>
std::shared_ptr<storm::models::sparse::Model<ValueType>> addMissingChoiceLabelsModel(
    storm::models::sparse::Model<ValueType> const& model
);

/**
 * Assert that choice labeling is canonic, i.e. each choice has exactly one label and each has at most one choice with
 * any given label.
 * @param abort_on_fail if true, then an exception is thrown
 * @return whether canonicity holds
 */
bool assertChoiceLabelingIsCanonic(
    std::vector<uint64_t> const& row_groups,
    storm::models::sparse::ChoiceLabeling const& choice_labeling,
    bool throw_on_fail = true
);

/**
 * Remove labels that have zero associated choices.
 */
void removeUnusedLabels(storm::models::sparse::ChoiceLabeling & choice_labeling);

/**
 * Given a model with canonic choice labeling, return a list of action labels and a choice-to-action mapping.
 */
template<typename ValueType>
std::pair<std::vector<std::string>,std::vector<uint64_t>> extractActionLabels(
    storm::models::sparse::Model<ValueType> const& model
);

template<typename ValueType>
std::pair<std::shared_ptr<storm::models::sparse::Model<ValueType>>,std::vector<uint64_t>> enableAllActions(
    storm::models::sparse::Model<ValueType> const& model
);

/**
 * Given a model with canonic choice labeling, make sure that in each state in the set \p state_maks all actions
 * are available. If an action is not available in a state, add it to this state with the behavior of action having
 * the \c DONT_CARE_ACTION_LABEL, or the first existing action. The order of actions is the one obtained by
 * \c extractActionLabels.
 * @return the updated model and a choice-to-action mapping
 */
template<typename ValueType>
std::pair<std::shared_ptr<storm::models::sparse::Model<ValueType>>,std::vector<uint64_t>> enableAllActions(
    storm::models::sparse::Model<ValueType> const& model,
    storm::storage::BitVector const& state_mask
);

/**
 * Given a model with canonic choice labeling, remove an action from the given set \p state_mask of states.
 * @return an updated model or NULL if no change took place
 */
template<typename ValueType>
std::shared_ptr<storm::models::sparse::Model<ValueType>> removeAction(
    storm::models::sparse::Model<ValueType> const& model,
    std::string const& action_to_remove_label,
    storm::storage::BitVector const& state_mask
);

/**
 * For any absorbing state with an unlabeled action, explicitly add all available actions and subsequently remove
 * these unlabeled actions.
 * @return an updated model or NULL if no change took place
 */

template<typename ValueType>
std::shared_ptr<storm::models::sparse::Model<ValueType>> restoreActionsInAbsorbingStates(
    storm::models::sparse::Model<ValueType> const& model
);

/**
 * To every state in \p state_mask, add an explicit action that executes a random choice between available actions.
 */
template<typename ValueType>
std::shared_ptr<storm::models::sparse::Model<ValueType>> addDontCareAction(
    storm::models::sparse::Model<ValueType> const& model,
    storm::storage::BitVector const& state_mask
);

/**
 * Create a union model with a fresh initial state simulating a uniform choice.
 */
template<typename ValueType>
std::shared_ptr<storm::models::sparse::Model<ValueType>> createModelUnion(
    std::vector<std::shared_ptr<storm::models::sparse::Model<ValueType>>> const& models
);

}
