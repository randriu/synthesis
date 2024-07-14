/* 
 * code in this file was taken from TEMPEST (https://github.com/PrangerStefan/TempestSynthesis)
 */

#include <list>
#include <numeric>

#include <storm/storage/StronglyConnectedComponentDecomposition.h>

#include "GameMaximalEndComponentDecomposition.h"

namespace synthesis {

    template<typename ValueType>
    GameMaximalEndComponentDecomposition<ValueType>::GameMaximalEndComponentDecomposition() : Decomposition() {
        // Intentionally left empty.
    }

    template<typename ValueType>
    template<typename RewardModelType>
    GameMaximalEndComponentDecomposition<ValueType>::GameMaximalEndComponentDecomposition(storm::models::sparse::NondeterministicModel<ValueType, RewardModelType> const& model) {
        singleMEC(model.getTransitionMatrix(), model.getBackwardTransitions());
        //performGameMaximalEndComponentDecomposition(model.getTransitionMatrix(), model.getBackwardTransitions());
    }

    template<typename ValueType>
    GameMaximalEndComponentDecomposition<ValueType>::GameMaximalEndComponentDecomposition(storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::SparseMatrix<ValueType> const& backwardTransitions) {
        singleMEC(transitionMatrix, backwardTransitions);
        //performGameMaximalEndComponentDecomposition(transitionMatrix, backwardTransitions);
    }

    template<typename ValueType>
    GameMaximalEndComponentDecomposition<ValueType>::GameMaximalEndComponentDecomposition(storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::SparseMatrix<ValueType> const& backwardTransitions, storm::storage::BitVector const& states) {
    }

    template<typename ValueType>
    GameMaximalEndComponentDecomposition<ValueType>::GameMaximalEndComponentDecomposition(storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::SparseMatrix<ValueType> const& backwardTransitions, storm::storage::BitVector const& states, storm::storage::BitVector const& choices) {
    }

    template<typename ValueType>
    GameMaximalEndComponentDecomposition<ValueType>::GameMaximalEndComponentDecomposition(storm::models::sparse::NondeterministicModel<ValueType> const& model, storm::storage::BitVector const& states) {
    }

    template<typename ValueType>
    GameMaximalEndComponentDecomposition<ValueType>::GameMaximalEndComponentDecomposition(GameMaximalEndComponentDecomposition const& other) : Decomposition(other) {
        // Intentionally left empty.
    }

    template<typename ValueType>
    GameMaximalEndComponentDecomposition<ValueType>& GameMaximalEndComponentDecomposition<ValueType>::operator=(GameMaximalEndComponentDecomposition const& other) {
        Decomposition::operator=(other);
        return *this;
    }

    template<typename ValueType>
    GameMaximalEndComponentDecomposition<ValueType>::GameMaximalEndComponentDecomposition(GameMaximalEndComponentDecomposition&& other) : Decomposition(std::move(other)) {
        // Intentionally left empty.
    }

    template<typename ValueType>
    GameMaximalEndComponentDecomposition<ValueType>& GameMaximalEndComponentDecomposition<ValueType>::operator=(GameMaximalEndComponentDecomposition&& other) {
        Decomposition::operator=(std::move(other));
        return *this;
    }

    template <typename ValueType>
    void GameMaximalEndComponentDecomposition<ValueType>::performGameMaximalEndComponentDecomposition(storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::SparseMatrix<ValueType> backwardTransitions, storm::storage::BitVector const* states, storm::storage::BitVector const* choices) {
        // Get some data for convenient access.
        uint_fast64_t numberOfStates = transitionMatrix.getRowGroupCount();
        std::vector<uint_fast64_t> const& nondeterministicChoiceIndices = transitionMatrix.getRowGroupIndices();

        // Initialize the maximal end component list to be the full state space.
        std::list<storm::storage::StateBlock> endComponentStateSets;
        if (states) {
            endComponentStateSets.emplace_back(states->begin(), states->end(), true);
        } else {
            std::vector<storm::storage::sparse::state_type> allStates;
            allStates.resize(transitionMatrix.getRowGroupCount());
            std::iota(allStates.begin(), allStates.end(), 0);
            endComponentStateSets.emplace_back(allStates.begin(), allStates.end(), true);
        }
        storm::storage::BitVector statesToCheck(numberOfStates);
        storm::storage::BitVector includedChoices;
        if (choices) {
            includedChoices = *choices;
        } else if (states) {
            includedChoices = storm::storage::BitVector(transitionMatrix.getRowCount());
            for (auto state : *states) {
                for (uint_fast64_t choice = nondeterministicChoiceIndices[state]; choice < nondeterministicChoiceIndices[state + 1]; ++choice) {
                    includedChoices.set(choice, true);
                }
            }
        } else {
            includedChoices = storm::storage::BitVector(transitionMatrix.getRowCount(), true);
        }
        storm::storage::BitVector currMecAsBitVector(transitionMatrix.getRowGroupCount());

        for (std::list<storm::storage::StateBlock>::const_iterator mecIterator = endComponentStateSets.begin(); mecIterator != endComponentStateSets.end();) {
            storm::storage::StateBlock const& mec = *mecIterator;
            currMecAsBitVector.clear();
            currMecAsBitVector.set(mec.begin(), mec.end(), true);
            // Keep track of whether the MEC changed during this iteration.
            bool mecChanged = false;

            // Get an SCC decomposition of the current MEC candidate.

            storm::storage::StronglyConnectedComponentDecomposition<ValueType> sccs(transitionMatrix, storm::storage::StronglyConnectedComponentDecompositionOptions().subsystem(currMecAsBitVector).choices(includedChoices).dropNaiveSccs());
            for(auto const& sc: sccs) {
                STORM_LOG_DEBUG("SCC size: " << sc.size());
            }

            // We need to do another iteration in case we have either more than once SCC or the SCC is smaller than
            // the MEC canditate itself.
            mecChanged |= sccs.size() != 1 || (sccs.size() > 0 && sccs[0].size() < mec.size());

            // Check for each of the SCCs whether all actions for each state do not leave the SCC. // TODO there is certainly a better way to do that...
            for (auto& scc : sccs) {
                statesToCheck.set(scc.begin(), scc.end());

                while (!statesToCheck.empty()) {
                    storm::storage::BitVector statesToRemove(numberOfStates);

                    for (auto state : statesToCheck) {
                        bool keepStateInMEC = true;

                        for (uint_fast64_t choice = nondeterministicChoiceIndices[state]; choice < nondeterministicChoiceIndices[state + 1]; ++choice) {

                            // If the choice is not part of our subsystem, skip it.
                            if (choices && !choices->get(choice)) {
                                continue;
                            }

                            // If the choice is not included any more, skip it.
                            //if (!includedChoices.get(choice)) {
                            //    continue;
                            //}

                            bool choiceContainedInMEC = true;
                            for (auto const& entry : transitionMatrix.getRow(choice)) {
                                if (storm::utility::isZero(entry.getValue())) {
                                    continue;
                                }

                                if (!scc.containsState(entry.getColumn())) {
                                    //includedChoices.set(choice, false);
                                    choiceContainedInMEC = false;
                                    break;
                                }
                            }

                            //TODO If there is at least one choice whose successor states are fully contained in the MEC, we can leave the state in the MEC.
                            if (!choiceContainedInMEC) {
                                keepStateInMEC = false;
                                break;
                            }
                        }
                        if (!keepStateInMEC) {
                            statesToRemove.set(state, true);
                        }

                    }

                    // Now erase the states that have no option to stay inside the MEC with all successors.
                    mecChanged |= !statesToRemove.empty();
                    for (uint_fast64_t state : statesToRemove) {
                        scc.erase(state);
                    }

                    // Now check which states should be reconsidered, because successors of them were removed.
                    statesToCheck.clear();
                    for (auto state : statesToRemove) {
                        for (auto const& entry : backwardTransitions.getRow(state)) {
                            if (scc.containsState(entry.getColumn())) {
                                statesToCheck.set(entry.getColumn());
                            }
                        }
                    }
                }
            }

            // If the MEC changed, we delete it from the list of MECs and append the possible new MEC candidates to
            // the list instead.
            if (mecChanged) {
                for (storm::storage::StronglyConnectedComponent& scc : sccs) {
                    if (!scc.empty()) {
                        endComponentStateSets.push_back(std::move(scc));
                    }
                }

                std::list<storm::storage::StateBlock>::const_iterator eraseIterator(mecIterator);
                ++mecIterator;
                endComponentStateSets.erase(eraseIterator);
            } else {
                // Otherwise, we proceed with the next MEC candidate.
                ++mecIterator;
            }

        } // End of loop over all MEC candidates.

        // Now that we computed the underlying state sets of the MECs, we need to properly identify the choices
        // contained in the MEC and store them as actual MECs.
        this->blocks.reserve(endComponentStateSets.size());
        for (auto const& mecStateSet : endComponentStateSets) {
            storm::storage::MaximalEndComponent newMec;

            for (auto state : mecStateSet) {
                storm::storage::MaximalEndComponent::set_type containedChoices;
                for (uint_fast64_t choice = nondeterministicChoiceIndices[state]; choice < nondeterministicChoiceIndices[state + 1]; ++choice) {
                    // Skip the choice if it is not part of our subsystem.
                    if (choices && !choices->get(choice)) {
                        continue;
                    }

                    if (includedChoices.get(choice)) {
                        containedChoices.insert(choice);
                    }
                }

                STORM_LOG_ASSERT(!containedChoices.empty(), "The contained choices of any state in an MEC must be non-empty.");
                newMec.addState(state, std::move(containedChoices));
            }

            this->blocks.emplace_back(std::move(newMec));
        }

        STORM_LOG_DEBUG("MEC decomposition found " << this->size() << " GMEC(s).");
    }

    template <typename ValueType>
    void GameMaximalEndComponentDecomposition<ValueType>::singleMEC(storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::SparseMatrix<ValueType> backwardTransitions, storm::storage::BitVector const* states, storm::storage::BitVector const* choices) {
        storm::storage::MaximalEndComponent singleMec;

        std::vector<uint_fast64_t> const& nondeterministicChoiceIndices = transitionMatrix.getRowGroupIndices();

        std::list<storm::storage::StateBlock> endComponentStateSets;
        std::vector<storm::storage::sparse::state_type> allStates;
        allStates.resize(transitionMatrix.getRowGroupCount());
        std::iota(allStates.begin(), allStates.end(), 0);
        endComponentStateSets.emplace_back(allStates.begin(), allStates.end(), true);

        storm::storage::BitVector includedChoices = storm::storage::BitVector(transitionMatrix.getRowCount(), true);
        this->blocks.reserve(endComponentStateSets.size());
        for (auto const& mecStateSet : endComponentStateSets) {
            storm::storage::MaximalEndComponent newMec;

            for (auto state : mecStateSet) {
                storm::storage::MaximalEndComponent::set_type containedChoices;
                for (uint_fast64_t choice = nondeterministicChoiceIndices[state]; choice < nondeterministicChoiceIndices[state + 1]; ++choice) {
                    // Skip the choice if it is not part of our subsystem.
                    if (choices && !choices->get(choice)) {
                        continue;
                    }

                    if (includedChoices.get(choice)) {
                        containedChoices.insert(choice);
                    }
                }

                STORM_LOG_ASSERT(!containedChoices.empty(), "The contained choices of any state in an MEC must be non-empty.");
                newMec.addState(state, std::move(containedChoices));
            }

            this->blocks.emplace_back(std::move(newMec));
        }

        STORM_LOG_DEBUG("Whole state space is one single MEC");

    }

    // Explicitly instantiate the MEC decomposition.
    template class GameMaximalEndComponentDecomposition<double>;
    // template GameMaximalEndComponentDecomposition<double>::GameMaximalEndComponentDecomposition(storm::models::sparse::NondeterministicModel<double> const& model);
}
