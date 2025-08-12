/*
 * methods to compute***Probabilites were taken from TEMPEST (https://github.com/PrangerStefan/TempestSynthesis)
 */

#include "SparseSmgRpatlHelper.h"

#include <queue>
#include <cmath>
#include <cassert>

#include <storm/environment/solver/GameSolverEnvironment.h>
#include <storm/environment/Environment.h>
#include <storm/environment/solver/MinMaxSolverEnvironment.h>
#include <storm/utility/vector.h>
#include <storm/utility/graph.h>
#include <storm/storage/MaximalEndComponentDecomposition.h>
#include <storm/settings/SettingsManager.h>
#include <storm/settings/modules/ModelCheckerSettings.h>
#include <storm/exceptions/InvalidPropertyException.h>

#include "internal/GameViHelper.h"
#include "internal/Multiplier.h"
#include "GameMaximalEndComponentDecomposition.h"


namespace synthesis {

    struct QualitativeStateSetsReachabilityRewards {
        storm::storage::BitVector maybeStates;
        storm::storage::BitVector infinityStates;
        storm::storage::BitVector rewardZeroStates;
    };

    void setClippedStatesOfCoalition(storm::storage::BitVector *vector, storm::storage::BitVector relevantStates, storm::storage::BitVector statesOfCoalition) {
        auto clippedStatesCounter = 0;
        for(uint i = 0; i < relevantStates.size(); i++) {
            if(relevantStates.get(i)) {
                vector->set(clippedStatesCounter, statesOfCoalition[i]);
                clippedStatesCounter++;
            }
        }
    }

    bool epsilonGreaterOrEqual(double x, double y, double eps=1e-6) {
        return (x>=y) || (fabs(x - y) <= eps);
    }

    // extract scheduler from final (state and choice) values of value iteration
    // make sure agents leave MECs
    template <typename ValueType>
    std::unique_ptr<storm::storage::Scheduler<ValueType>> extractScheduler(storm::solver::SolveGoal<ValueType> const& goal, storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::BitVector const& statesOfCoalition,
                        std::vector<ValueType> const& constrainedChoiceValues, std::vector<ValueType> const& result, storm::storage::BitVector const& relevantStates) {

        bool maximize = !goal.minimize();
        uint64_t stateCount = transitionMatrix.getRowGroupCount();
        std::vector<uint64_t> optimalChoices(stateCount,0);
        storm::storage::BitVector optimalChoiceSet(stateCount);
        auto transposed_matrix = storm::storage::SparseMatrix<ValueType>(transitionMatrix.transpose(true));
        auto endComponentDecomposition = storm::storage::MaximalEndComponentDecomposition<ValueType>(transitionMatrix, transposed_matrix);

        for (auto const& mec : endComponentDecomposition) {
            std::vector<uint64_t> statesInMEC;
            std::queue<uint64_t> BFSqueue;
            // for each MEC compute which max value choices lead to an exit of the MEC
            for (auto const& stateActions : mec) {
                uint64_t const& state = stateActions.first;
                statesInMEC.push_back(state);
                uint64_t stateChoiceIndex = 0;
                for (uint64_t row = transitionMatrix.getRowGroupIndices()[state], endRow = transitionMatrix.getRowGroupIndices()[state + 1]; row < endRow; ++row) {
                    // check if the choice belongs to MEC, if not then this choice is the best exit choice for the MEC
                    // the states with such choices will be used as the initial states for backwards BFS
                    if ((!statesOfCoalition.get(state)) && (maximize ? epsilonGreaterOrEqual(constrainedChoiceValues[row], result[state]) : epsilonGreaterOrEqual(result[state], constrainedChoiceValues[row])) && (stateActions.second.find(row) == stateActions.second.end())) {
                        BFSqueue.push(state);
                        optimalChoices[state] = stateChoiceIndex;
                        optimalChoiceSet.set(state);
                        break;
                    } else if ((statesOfCoalition.get(state)) && (maximize ? epsilonGreaterOrEqual(result[state], constrainedChoiceValues[row]) : epsilonGreaterOrEqual(constrainedChoiceValues[row], result[state])) && (stateActions.second.find(row) == stateActions.second.end())) {
                        BFSqueue.push(state);
                        optimalChoices[state] = stateChoiceIndex;
                        optimalChoiceSet.set(state);
                        break;
                    }
                    stateChoiceIndex++;
                }
            }

            // perform BFS on the transposed matrix to identify actions that lead to an exit of MEC
            while (!BFSqueue.empty()) {
                auto currentState = BFSqueue.front();
                BFSqueue.pop();
                auto transposedRow = transposed_matrix.getRow(currentState);
                for (auto const &entry : transposedRow) {
                    auto preState = entry.getColumn();
                    auto preStateIt = std::find(statesInMEC.begin(), statesInMEC.end(), preState);
                    if ((preStateIt != statesInMEC.end()) && (!optimalChoiceSet.get(preState))) {
                        uint64_t stateChoiceIndex = 0;
                        bool choiceFound = false;
                        for (uint64_t row = transitionMatrix.getRowGroupIndices()[preState], endRow = transitionMatrix.getRowGroupIndices()[preState + 1]; row < endRow; ++row) {
                            if ((!statesOfCoalition.get(preState)) && (maximize ? epsilonGreaterOrEqual(constrainedChoiceValues[row], result[preState]) : epsilonGreaterOrEqual(result[preState], constrainedChoiceValues[row]))) {
                                for (auto const &preStateEntry : transitionMatrix.getRow(row)) {
                                    if (preStateEntry.getColumn() == currentState) {
                                        BFSqueue.push(preState);
                                        optimalChoices[preState] = stateChoiceIndex;
                                        optimalChoiceSet.set(preState);
                                        choiceFound = true;
                                        break;
                                    }
                                }
                            } else if ((statesOfCoalition.get(preState)) && (maximize ? epsilonGreaterOrEqual(result[preState], constrainedChoiceValues[row]) : epsilonGreaterOrEqual(constrainedChoiceValues[row], result[preState]))) {
                                for (auto const &preStateEntry : transitionMatrix.getRow(row)) {
                                    if (preStateEntry.getColumn() == currentState) {
                                        BFSqueue.push(preState);
                                        optimalChoices[preState] = stateChoiceIndex;
                                        optimalChoiceSet.set(preState);
                                        choiceFound = true;
                                        break;
                                    }
                                }
                            }
                            if (choiceFound) {
                                break;
                            }
                            stateChoiceIndex++;
                        }
                    }
                }
            }
        }

        // fill in the choices for states outside of MECs
        for (uint64_t state = 0; state < stateCount; state++) {
            if (optimalChoiceSet.get(state)) {
                continue;
            }
            if (!statesOfCoalition.get(state)) { // not sure why the statesOfCoalition bitvector is flipped
                uint64_t stateRowIndex = 0;
                for (auto choice : transitionMatrix.getRowGroupIndices(state)) {
                    if (maximize ? epsilonGreaterOrEqual(constrainedChoiceValues[choice], result[state]) : epsilonGreaterOrEqual(result[state], constrainedChoiceValues[choice])) {
                        optimalChoices[state] = stateRowIndex;
                        optimalChoiceSet.set(state);
                        break;
                    }
                    stateRowIndex++;
                }
            } else {
                uint64_t stateRowIndex = 0;
                for (auto choice : transitionMatrix.getRowGroupIndices(state)) {
                    if (maximize ? epsilonGreaterOrEqual(result[state], constrainedChoiceValues[choice]) : epsilonGreaterOrEqual(constrainedChoiceValues[choice], result[state])) {
                        optimalChoices[state] = stateRowIndex;
                        optimalChoiceSet.set(state);
                        break;
                    }
                    stateRowIndex++;
                }
            }
        }

        //double check if all states have a choice
        for (uint64_t state = 0; state < stateCount; state++) {
            if (!relevantStates.get(state)) {
                continue;
            }
            assert(optimalChoiceSet.get(state));
        }

        storm::storage::Scheduler<ValueType> tempScheduler(optimalChoices.size());
        for (uint64_t state = 0; state < optimalChoices.size(); ++state) {
            tempScheduler.setChoice(optimalChoices[state], state);
        }

        return std::make_unique<storm::storage::Scheduler<ValueType>>(tempScheduler);
    }

    template<typename ValueType>
    SMGSparseModelCheckingHelperReturnType<ValueType> SparseSmgRpatlHelper<ValueType>::computeUntilProbabilities(storm::Environment const& env, storm::solver::SolveGoal<ValueType>&& goal, storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::SparseMatrix<ValueType> const& backwardTransitions, storm::storage::BitVector const& phiStates, storm::storage::BitVector const& psiStates, bool qualitative, storm::storage::BitVector statesOfCoalition, bool produceScheduler, storm::modelchecker::ModelCheckerHint const& hint) {
        auto solverEnv = env;
        solverEnv.solver().minMax().setMethod(storm::solver::MinMaxMethod::ValueIteration, false);

        // Relevant states are those states which are phiStates and not PsiStates.
        storm::storage::BitVector relevantStates = phiStates & ~psiStates;

        // Initialize the x vector and solution vector result.
        std::vector<ValueType> x = std::vector<ValueType>(relevantStates.getNumberOfSetBits(), storm::utility::zero<ValueType>());
        std::vector<ValueType> result = std::vector<ValueType>(transitionMatrix.getRowGroupCount(), storm::utility::zero<ValueType>());
        std::vector<ValueType> b = transitionMatrix.getConstrainedRowGroupSumVector(relevantStates, psiStates);
        std::vector<ValueType> constrainedChoiceValues = std::vector<ValueType>(b.size(), storm::utility::zero<ValueType>());
        std::unique_ptr<storm::storage::Scheduler<ValueType>> scheduler;

        storm::storage::BitVector clippedStatesOfCoalition(relevantStates.getNumberOfSetBits());
        synthesis::setClippedStatesOfCoalition(&clippedStatesOfCoalition, relevantStates, statesOfCoalition);

        // Fill up the result vector with with 1s for psi states
        storm::utility::vector::setVectorValues(result, psiStates, storm::utility::one<ValueType>());

        if(!relevantStates.empty()) {
            // Reduce the matrix to relevant states.
            storm::storage::SparseMatrix<ValueType> submatrix = transitionMatrix.getSubmatrix(true, relevantStates, relevantStates, false);
            // Create GameViHelper for computations.
            synthesis::GameViHelper<ValueType> viHelper(submatrix, clippedStatesOfCoalition);
            if (produceScheduler) {
                viHelper.setProduceScheduler(true);
            }
            viHelper.performValueIteration(env, x, b, goal.direction(), constrainedChoiceValues);

            // Fill up the constrainedChoice Values to full size.
            viHelper.fillChoiceValuesVector(constrainedChoiceValues, relevantStates, transitionMatrix.getRowGroupIndices());

            // Fill up the result vector with the values of x for the relevant states, with 1s for psi states
            storm::utility::vector::setVectorValues(result, relevantStates, x);

            // if produceScheduler is true, produce scheduler based on the final values from value iteration
            if (produceScheduler) {
                scheduler = extractScheduler(goal, transitionMatrix, statesOfCoalition, constrainedChoiceValues, result, relevantStates);
            }
        }

        return SMGSparseModelCheckingHelperReturnType<ValueType>(std::move(result), std::move(relevantStates), std::move(scheduler), std::move(constrainedChoiceValues));
    }

    template<typename ValueType>
    storm::storage::Scheduler<ValueType> SparseSmgRpatlHelper<ValueType>::expandScheduler(storm::storage::Scheduler<ValueType> scheduler, storm::storage::BitVector psiStates, storm::storage::BitVector notPhiStates) {
        storm::storage::Scheduler<ValueType> completeScheduler(psiStates.size());
        uint_fast64_t maybeStatesCounter = 0;
        uint schedulerSize = psiStates.size();
        for(uint stateCounter = 0; stateCounter < schedulerSize; stateCounter++) {
            // psiStates already fulfill formulae so we can set an arbitrary action
            if(psiStates.get(stateCounter)) {
                completeScheduler.setChoice(0, stateCounter);
            // ~phiStates do not fulfill formulae so we can set an arbitrary action
            } else if(notPhiStates.get(stateCounter)) {
                completeScheduler.setChoice(0, stateCounter);
            } else {
                completeScheduler.setChoice(scheduler.getChoice(maybeStatesCounter), stateCounter);
                maybeStatesCounter++;
            }
        }
        return completeScheduler;
    }

    template<typename ValueType>
    SMGSparseModelCheckingHelperReturnType<ValueType> SparseSmgRpatlHelper<ValueType>::computeGloballyProbabilities(storm::Environment const& env, storm::solver::SolveGoal<ValueType>&& goal, storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::SparseMatrix<ValueType> const& backwardTransitions, storm::storage::BitVector const& psiStates, bool qualitative, storm::storage::BitVector statesOfCoalition, bool produceScheduler, storm::modelchecker::ModelCheckerHint const& hint) {
        // G psi = not(F(not psi)) = not(true U (not psi))
        // The psiStates are flipped, then the true U part is calculated, at the end the result is flipped again.
        storm::storage::BitVector notPsiStates = ~psiStates;
        statesOfCoalition.complement();

        auto result = computeUntilProbabilities(env, std::move(goal), transitionMatrix, backwardTransitions, storm::storage::BitVector(transitionMatrix.getRowGroupCount(), true), notPsiStates, qualitative, statesOfCoalition, produceScheduler, hint);
        for (auto& element : result.values) {
            element = storm::utility::one<ValueType>() - element;
        }
        for (auto& element : result.choiceValues) {
            element = storm::utility::one<ValueType>() - element;
        }
        return result;
    }

    template<typename ValueType>
    SMGSparseModelCheckingHelperReturnType<ValueType> SparseSmgRpatlHelper<ValueType>::computeNextProbabilities(storm::Environment const& env, storm::solver::SolveGoal<ValueType>&& goal, storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::SparseMatrix<ValueType> const& backwardTransitions, storm::storage::BitVector const& psiStates, bool qualitative, storm::storage::BitVector statesOfCoalition, bool produceScheduler, storm::modelchecker::ModelCheckerHint const& hint) {
        // Create vector result, bitvector allStates with a true for each state and a vector b for the probability for each state to get to a psi state, choiceValues is to store choices for shielding.
        std::vector<ValueType> result = std::vector<ValueType>(transitionMatrix.getRowGroupCount(), storm::utility::zero<ValueType>());
        storm::storage::BitVector allStates = storm::storage::BitVector(transitionMatrix.getRowGroupCount(), true);
        std::vector<ValueType> b = transitionMatrix.getConstrainedRowGroupSumVector(allStates, psiStates);
        std::vector<ValueType> choiceValues = std::vector<ValueType>(transitionMatrix.getRowCount(), storm::utility::zero<ValueType>());
        statesOfCoalition.complement();

        if (produceScheduler) {
            STORM_LOG_WARN("Next formula does not expect that produceScheduler is set to true.");
        }
        // Create a multiplier for reduction.
        auto multiplier = synthesis::MultiplierFactory<ValueType>().create(env, transitionMatrix);
        auto rowGroupIndices = transitionMatrix.getRowGroupIndices();
        rowGroupIndices.erase(rowGroupIndices.begin());
        multiplier->reduce(env, goal.direction(), rowGroupIndices, b, result, nullptr, &statesOfCoalition);
        return SMGSparseModelCheckingHelperReturnType<ValueType>(std::move(result), std::move(allStates), nullptr, std::move(choiceValues));
    }

    template<typename ValueType>
    SMGSparseModelCheckingHelperReturnType<ValueType> SparseSmgRpatlHelper<ValueType>::computeBoundedGloballyProbabilities(storm::Environment const& env, storm::solver::SolveGoal<ValueType>&& goal, storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::SparseMatrix<ValueType> const& backwardTransitions, storm::storage::BitVector const& psiStates, bool qualitative, storm::storage::BitVector statesOfCoalition, bool produceScheduler, storm::modelchecker::ModelCheckerHint const& hint,uint64_t lowerBound, uint64_t upperBound) {
        // G psi = not(F(not psi)) = not(true U (not psi))
        // The psiStates are flipped, then the true U part is calculated, at the end the result is flipped again.
        storm::storage::BitVector notPsiStates = ~psiStates;
        statesOfCoalition.complement();

        auto result = computeBoundedUntilProbabilities(env, std::move(goal), transitionMatrix, backwardTransitions, storm::storage::BitVector(transitionMatrix.getRowGroupCount(), true), notPsiStates, qualitative, statesOfCoalition, produceScheduler, hint, lowerBound, upperBound, true);
        for (auto& element : result.values) {
            element = storm::utility::one<ValueType>() - element;
        }
        for (auto& element : result.choiceValues) {
            element = storm::utility::one<ValueType>() - element;
        }
        return result;
    }

    template<typename ValueType>
    SMGSparseModelCheckingHelperReturnType<ValueType> SparseSmgRpatlHelper<ValueType>::computeBoundedUntilProbabilities(storm::Environment const& env, storm::solver::SolveGoal<ValueType>&& goal, storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::SparseMatrix<ValueType> const& backwardTransitions, storm::storage::BitVector const& phiStates, storm::storage::BitVector const& psiStates, bool qualitative, storm::storage::BitVector statesOfCoalition, bool produceScheduler, storm::modelchecker::ModelCheckerHint const& hint,uint64_t lowerBound, uint64_t upperBound, bool computeBoundedGlobally) {
        auto solverEnv = env;
        solverEnv.solver().minMax().setMethod(storm::solver::MinMaxMethod::ValueIteration, false);

        // boundedUntil formulas look like:
        // phi U [lowerBound, upperBound] psi
        // --
        // We solve this by look at psiStates, finding phiStates which have paths to psiStates in the given step bounds,
        // then we find all states which have a path to those phiStates in the given lower bound
        // (which states the paths pass before the lower bound does not matter).

        // First initialization of relevantStates between the step bounds.
        storm::storage::BitVector relevantStates = phiStates & ~psiStates;

        // Initializations.
        std::vector<ValueType> x = std::vector<ValueType>(relevantStates.getNumberOfSetBits(), storm::utility::zero<ValueType>());
        std::vector<ValueType> b = transitionMatrix.getConstrainedRowGroupSumVector(relevantStates, psiStates);
        std::vector<ValueType> result = std::vector<ValueType>(transitionMatrix.getRowGroupCount(), storm::utility::zero<ValueType>());
        std::vector<ValueType> constrainedChoiceValues = std::vector<ValueType>(transitionMatrix.getConstrainedRowGroupSumVector(relevantStates, psiStates).size(), storm::utility::zero<ValueType>());
        std::unique_ptr<storm::storage::Scheduler<ValueType>> scheduler;

        storm::storage::BitVector clippedStatesOfCoalition(relevantStates.getNumberOfSetBits());
        synthesis::setClippedStatesOfCoalition(&clippedStatesOfCoalition, relevantStates, statesOfCoalition);

        // If there are no relevantStates or the upperBound is 0, no computation is needed.
        if(!relevantStates.empty() && upperBound > 0) {
            // Reduce the matrix to relevant states. - relevant states are all states.
            storm::storage::SparseMatrix<ValueType> submatrix = transitionMatrix.getSubmatrix(true, relevantStates, relevantStates, false);
            // Create GameViHelper for computations.
            synthesis::GameViHelper<ValueType> viHelper(submatrix, clippedStatesOfCoalition);
            if (produceScheduler) {
                viHelper.setProduceScheduler(true);
            }
            // If the lowerBound = 0, value iteration is done until the upperBound.
            if(lowerBound == 0) {
                solverEnv.solver().game().setMaximalNumberOfIterations(upperBound);
                viHelper.performValueIteration(solverEnv, x, b, goal.direction(), constrainedChoiceValues);
            } else {
                // The lowerBound != 0, the first computation between the given bound steps is done.
                solverEnv.solver().game().setMaximalNumberOfIterations(upperBound - lowerBound);
                viHelper.performValueIteration(solverEnv, x, b, goal.direction(), constrainedChoiceValues);

                // Initialization of subResult, fill it with the result of the first computation and 1s for the psiStates in full range.
                std::vector<ValueType> subResult = std::vector<ValueType>(transitionMatrix.getRowGroupCount(), storm::utility::zero<ValueType>());
                storm::utility::vector::setVectorValues(subResult, relevantStates, x);
                storm::utility::vector::setVectorValues(subResult, psiStates, storm::utility::one<ValueType>());

                // The newPsiStates are those states which can reach the psiStates in the steps between the bounds - the !=0 values in subResult.
                storm::storage::BitVector newPsiStates(subResult.size(), false);
                storm::utility::vector::setNonzeroIndices(subResult, newPsiStates);

                // The relevantStates for the second part of the computation are all states.
                relevantStates = storm::storage::BitVector(phiStates.size(), true);
                submatrix = transitionMatrix.getSubmatrix(true, relevantStates, relevantStates, false);

                // Update the viHelper for the (full-size) submatrix and statesOfCoalition.
                viHelper.updateTransitionMatrix(submatrix);
                viHelper.updateStatesOfCoalition(statesOfCoalition);

                // Reset constrainedChoiceValues and b to 0-vector in the correct dimension.
                constrainedChoiceValues = std::vector<ValueType>(transitionMatrix.getConstrainedRowGroupSumVector(relevantStates, newPsiStates).size(), storm::utility::zero<ValueType>());
                b = std::vector<ValueType>(transitionMatrix.getConstrainedRowGroupSumVector(relevantStates, newPsiStates).size(), storm::utility::zero<ValueType>());

                // The second computation is done between step 0 and the lowerBound
                solverEnv.solver().game().setMaximalNumberOfIterations(lowerBound);
                viHelper.performValueIteration(solverEnv, subResult, b, goal.direction(), constrainedChoiceValues);

                x = subResult;
            }
            viHelper.fillChoiceValuesVector(constrainedChoiceValues, relevantStates, transitionMatrix.getRowGroupIndices());
            if (produceScheduler) {
                scheduler = std::make_unique<storm::storage::Scheduler<ValueType>>(expandScheduler(viHelper.extractScheduler(), relevantStates, ~relevantStates));
            }
            storm::utility::vector::setVectorValues(result, relevantStates, x);
        }
        // In bounded until and bounded eventually formula the psiStates have probability 1 to satisfy the formula,
        // because once reaching a state where psi holds those formulas are satisfied.
        // In bounded globally formulas we cannot set those states to 1 because it is possible to leave a set of safe states after reaching a psiState
        // and in globally the formula has to hold in every time step (between the bounds).
        // e.g. phiState -> phiState -> psiState -> unsafeState
        if(!computeBoundedGlobally){
            storm::utility::vector::setVectorValues(result, psiStates, storm::utility::one<ValueType>());
        }
        return SMGSparseModelCheckingHelperReturnType<ValueType>(std::move(result), std::move(relevantStates), std::move(scheduler), std::move(constrainedChoiceValues));
    }

    template<typename ValueType>
    SMGSparseModelCheckingHelperReturnType<ValueType> SparseSmgRpatlHelper<ValueType>::computeReachabilityRewards(storm::Environment const& env, storm::solver::SolveGoal<ValueType>&& goal, storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::SparseMatrix<ValueType> const& backwardTransitions, storm::models::sparse::StandardRewardModel<ValueType> const& rewardModel, storm::storage::BitVector const& targetStates, bool qualitative, storm::storage::BitVector statesOfCoalition, bool produceScheduler, storm::modelchecker::ModelCheckerHint const& hint) {
        STORM_LOG_THROW(!rewardModel.empty(), storm::exceptions::InvalidPropertyException, "Reward model for formula is empty. Skipping formula.");
        return computeReachabilityRewardsHelper(
            env, std::move(goal), transitionMatrix, backwardTransitions,
            [&rewardModel](uint_fast64_t rowCount, storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::BitVector const& maybeStates) {
                return rewardModel.getTotalRewardVector(rowCount, transitionMatrix, maybeStates);
            },
            targetStates, qualitative, statesOfCoalition, produceScheduler, hint);
    }

    // inspired by prism-games SMGSimple.java
    template<typename ValueType>
    void prob1step(storm::storage::BitVector const& subset, storm::storage::BitVector const& u, storm::storage::BitVector const& v,
                    storm::storage::SparseMatrix<ValueType> const& transitionMatrix,
                    bool forall1, storm::storage::BitVector const& statesOfCoalition,
                    storm::storage::BitVector& result)
    {
        bool b1, b2;
        bool forall;
        auto rowGroupIndices = transitionMatrix.getRowGroupIndices();

        for (uint64_t state = 0; state < transitionMatrix.getRowGroupCount(); state++) {
            if (subset.get(state)) {
                // statesOfCoalition.get(state) == true means it is player 2 state, else it is player 1 state
                forall = statesOfCoalition.get(state) ? !forall1 : forall1;
                b1 = forall;
                for (uint64_t choice = rowGroupIndices[state]; choice < rowGroupIndices[state + 1]; choice++) {
                    auto row = transitionMatrix.getRow(choice);
                    b2 = std::any_of(row.begin(), row.end(), [&v](auto const& entry) { return v.get(entry.getColumn()); }) &&
                         std::all_of(row.begin(), row.end(), [&u](auto const& entry) { return u.get(entry.getColumn()); });

                    if (forall)
                    {
                        if (!b2) {
                            b1 = false;
                            break;
                        }
                    }
                    else {
                        if (b2) {
                            b1 = true;
                            break;
                        }
                    }
                }
                result.set(state, b1);
            }
        }
    }

    // inspired by prism-games STPGModelChecker.java
    template<typename ValueType>
    storm::storage::BitVector prob1(storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::BitVector const& targetStates, bool min1, storm::storage::BitVector const& statesOfCoalition)
    {
        uint64_t stateCount = transitionMatrix.getRowGroupCount();

        storm::storage::BitVector u = storm::storage::BitVector(stateCount);
        storm::storage::BitVector v = storm::storage::BitVector(stateCount);
        storm::storage::BitVector soln = storm::storage::BitVector(stateCount);

        storm::storage::BitVector unknown = storm::storage::BitVector(stateCount, true);
        unknown &= ~targetStates;

        bool uDone, vDone;

        u.fill();
        uDone = false;
        while (!uDone) {
            v = targetStates;
            soln = targetStates;
            vDone = false;
            while (!vDone) {
                prob1step(unknown, u, v, transitionMatrix, min1, statesOfCoalition, soln);

                vDone = v == soln;
                v = soln;
            }

            uDone = u == v;
            u = v;
        }

        return u;
    }

    template<typename ValueType>
    QualitativeStateSetsReachabilityRewards computeQualitativeStateSetsReachabilityRewards(
        storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::BitVector const& targetStates,
        storm::solver::SolveGoal<ValueType> const& goal, storm::storage::BitVector const& statesOfCoalition
    ) {
        QualitativeStateSetsReachabilityRewards result;

        // if p1 wants to minimize rewards, he wants to maximize the probability to reach target states
        result.infinityStates = prob1(transitionMatrix, targetStates, !goal.minimize(), statesOfCoalition);
        // inifinity states are those, where even if maximizing, the probability of reaching target is <1
        result.infinityStates.complement();

        // TODO: compute all zero reward states (will be necessary to add zero reward getters parameters?)
        // this could reduce the state space for VI
        result.rewardZeroStates = targetStates;

        result.maybeStates = ~(result.rewardZeroStates | result.infinityStates);
        return result;
    }

    template<typename ValueType>
    std::vector<ValueType> replaceZerosWithEpsilon(std::vector<ValueType> v, ValueType epsilon)
    {
        std::vector<ValueType> vEps = v;
        for (auto& value : vEps) {
            if (value == storm::utility::zero<ValueType>()) {
                value = epsilon;
            }
        }

        return vEps;
    }

    // fill the choice values vector for every choice in original transition matrix. Result will be stored in choiceValues.
    // all choices leading from infinityStates or rewardZeroStates will have value 0
    // all choices leading from maybeStates to infinityStates will have value infinity
    // all other choices will have values from choiceValues vector
    template<typename ValueType>
    void fillChoiceValuesVectorRewards(std::vector<ValueType>& choiceValues, storm::storage::SparseMatrix<ValueType> const& transitionMatrix, QualitativeStateSetsReachabilityRewards const& qualitativeStateSets) {
        std::vector<ValueType> allChoices = std::vector<ValueType>(transitionMatrix.getRowCount());
        auto choiceIt = choiceValues.begin();
        uint64_t choice = 0;
        for (uint64_t state = 0; state < transitionMatrix.getRowGroupCount(); state ++) {
            if (qualitativeStateSets.maybeStates.get(state)) {
                // choice leads from maybe state
                uint64_t firstChoiceOfNextState = choice + transitionMatrix.getRowGroupSize(state);
                while (choice < firstChoiceOfNextState) {
                    auto row = transitionMatrix.getRow(choice);
                    if (std::any_of(row.begin(), row.end(), [&qualitativeStateSets](auto const& entry) { return qualitativeStateSets.infinityStates.get(entry.getColumn()); })) {
                        // choice leads to infinity state
                        allChoices[choice] = storm::utility::infinity<ValueType>();
                    }
                    else {
                        // choice leads to maybe or reward zero state
                        allChoices[choice] = *choiceIt;
                        choiceIt++;
                    }
                    choice++;
                }
            }
            else {
                // choice leads from infinity or reward zero state
                choice += transitionMatrix.getRowGroupSize(state);
            }
        }
        assert(choiceIt == choiceValues.end());

        choiceValues = allChoices;
    }

    // fill scheduler choices for infinity and reward zero states
    template<typename ValueType>
    void extendScheduler(storm::storage::Scheduler<ValueType>& scheduler, QualitativeStateSetsReachabilityRewards qualitativeStateSets,
                        storm::storage::SparseMatrix<ValueType> transitionMatrix, storm::storage::SparseMatrix<ValueType> backwardTransitions) {
        if (!scheduler.isChoiceSelected(qualitativeStateSets.rewardZeroStates)) {
            for (auto state : qualitativeStateSets.rewardZeroStates) {
                scheduler.setChoice(0, state);
            }
        }

        storm::utility::graph::computeSchedulerRewInf(qualitativeStateSets.infinityStates, transitionMatrix, backwardTransitions, scheduler);
    }

    template<typename ValueType>
    SMGSparseModelCheckingHelperReturnType<ValueType> SparseSmgRpatlHelper<ValueType>::computeReachabilityRewardsHelper(
                storm::Environment const& env, storm::solver::SolveGoal<ValueType>&& goal,
                storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::SparseMatrix<ValueType> const& backwardTransitions,
                std::function<std::vector<ValueType>(uint_fast64_t, storm::storage::SparseMatrix<ValueType> const&, storm::storage::BitVector const&)> const& totalStateRewardVectorGetter,
                storm::storage::BitVector const& targetStates, bool qualitative, storm::storage::BitVector statesOfCoalition, bool produceScheduler,
                storm::modelchecker::ModelCheckerHint const& hint) {
        std::vector<ValueType> result(transitionMatrix.getRowGroupCount(), storm::utility::zero<ValueType>());
        std::unique_ptr<storm::storage::Scheduler<ValueType>> scheduler = std::make_unique<storm::storage::Scheduler<ValueType>>(transitionMatrix.getRowGroupCount());
        std::vector<ValueType> choiceValues = std::vector<ValueType>(transitionMatrix.getRowCount(), storm::utility::zero<ValueType>());

        // Compute infinity, zero and maybe states
        QualitativeStateSetsReachabilityRewards qualitativeStateSets = computeQualitativeStateSetsReachabilityRewards(
            transitionMatrix, targetStates, goal, statesOfCoalition);

        storm::utility::vector::setVectorValues(result, qualitativeStateSets.infinityStates, storm::utility::infinity<ValueType>());

        // Check if the values of the maybe states are relevant for the SolveGoal
        bool maybeStatesNotRelevant = goal.hasRelevantValues() && goal.relevantValues().isDisjointFrom(qualitativeStateSets.maybeStates);

        if (qualitative || maybeStatesNotRelevant)
        {
            STORM_LOG_INFO("The rewards for the initial states were determined in a preprocessing step. No exact rewards were computed.");
            // Set the values for all maybe-states to 1 to indicate that their reward values
            // are neither 0 nor infinity.
            storm::utility::vector::setVectorValues(result, qualitativeStateSets.maybeStates, storm::utility::one<ValueType>());
        }
        else {
            storm::storage::BitVector relevantStates = qualitativeStateSets.maybeStates;

            if (!relevantStates.empty()) {
                // In this case we have to compute the reward values for the remaining states.

                // If the solve goal has relevant values, we need to adjust them.
                goal.restrictRelevantValues(relevantStates);

                // set up the GameViHelper
                storm::storage::SparseMatrix<ValueType> submatrix;
                std::vector<ValueType> b;
                storm::storage::BitVector selectedChoices = storm::storage::BitVector(transitionMatrix.getRowCount(), true);
                if (qualitativeStateSets.infinityStates.empty()) {
                    submatrix = transitionMatrix.getSubmatrix(true, relevantStates, relevantStates, false);
                    b = totalStateRewardVectorGetter(submatrix.getRowCount(), transitionMatrix, relevantStates);
                }
                else {
                    // Only choices of relevant states that lead to non-infinity states.
                    selectedChoices = transitionMatrix.getRowFilter(relevantStates, ~qualitativeStateSets.infinityStates);

                    submatrix = transitionMatrix.getSubmatrix(false, selectedChoices, relevantStates, false);
                    b = totalStateRewardVectorGetter(transitionMatrix.getRowCount(), transitionMatrix, storm::storage::BitVector(transitionMatrix.getRowGroupCount(), true));
                    storm::utility::vector::filterVectorInPlace(b, selectedChoices);
                }
                storm::storage::BitVector clippedStatesOfCoalition(relevantStates.getNumberOfSetBits());
                synthesis::setClippedStatesOfCoalition(&clippedStatesOfCoalition, relevantStates, statesOfCoalition);
                synthesis::GameViHelper<ValueType> viHelper(submatrix, clippedStatesOfCoalition);

                // prepare for value iteration
                auto solverEnv = env;
                solverEnv.solver().minMax().setMethod(storm::solver::MinMaxMethod::ValueIteration, false);
                std::vector<ValueType> x = std::vector<ValueType>(relevantStates.getNumberOfSetBits(), storm::utility::zero<ValueType>());
                std::vector<ValueType> constrainedChoiceValues = std::vector<ValueType>(b.size(), storm::utility::zero<ValueType>());

                // precomputation for zero reward end components
                // taken from prism-games (Automatic Verification of Competitive Stochastic Systems)

                // find maximum and minimum reward and check if all rewards are positive
                ValueType minimumReward = storm::utility::infinity<ValueType>();
                ValueType maximumReward = storm::utility::zero<ValueType>();
                bool allPositive = true;
                for (auto reward : b) {
                    if (reward > storm::utility::zero<ValueType>()) {
                        if (reward < minimumReward) {
                            minimumReward = reward;
                        }
                        if (reward > maximumReward) {
                            maximumReward = reward;
                        }
                    }
                    else {
                        allPositive = false;
                        if (reward < storm::utility::zero<ValueType>()) {
                            STORM_LOG_WARN("Some reward is negative. The computaion of negative rewards was not tested and might return wrong results or fail.");
                        }
                    }
                }

                if (!allPositive) {
                    // Compute rewards with epsilon instead of zero. This is used to get the over-approximation
                    // of the real result, which deals with the problem of staying in zero
                    // components for free when infinity should be gained.
                    ValueType epsilon = std::min(minimumReward, maximumReward * 0.01);

                    // the result of this over aproximation (stored in x) will be used as an initial value for the actual computation
                    viHelper.performValueIteration(solverEnv, x, replaceZerosWithEpsilon(b, epsilon), goal.direction(), constrainedChoiceValues);
                }

                if (produceScheduler) {
                    viHelper.setProduceScheduler(true);
                }
                viHelper.performValueIteration(solverEnv, x, b, goal.direction(), constrainedChoiceValues);

                storm::utility::vector::setVectorValues(result, relevantStates, x);

                fillChoiceValuesVectorRewards(constrainedChoiceValues, transitionMatrix, qualitativeStateSets);
                choiceValues = constrainedChoiceValues;

                // if produceScheduler is true, produce scheduler based on the final values from value iteration
                if (produceScheduler) {
                    scheduler = extractScheduler(goal, transitionMatrix, statesOfCoalition, choiceValues, result, relevantStates);
                }
            }
        }

        if (produceScheduler) {
            extendScheduler(*scheduler, qualitativeStateSets, transitionMatrix, backwardTransitions);
        }

        return SMGSparseModelCheckingHelperReturnType<ValueType>(std::move(result), std::move(qualitativeStateSets.maybeStates), std::move(scheduler), std::move(choiceValues));
    }

    template class SparseSmgRpatlHelper<double>;
}
