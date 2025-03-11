#pragma once

/*
 * methods to compute***Probabilites were taken from TEMPEST (https://github.com/PrangerStefan/TempestSynthesis)
 */

#include <vector>

#include <storm/modelchecker/hints/ModelCheckerHint.h>
#include <storm/storage/SparseMatrix.h>
#include <storm/utility/solver.h>
#include <storm/solver/SolveGoal.h>

#include "SMGModelCheckingHelperReturnType.h"

namespace synthesis {

    template <typename ValueType>
    class SparseSmgRpatlHelper {
    public:

        static SMGSparseModelCheckingHelperReturnType<ValueType> computeUntilProbabilities(storm::Environment const& env, storm::solver::SolveGoal<ValueType>&& goal, storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::SparseMatrix<ValueType> const& backwardTransitions, storm::storage::BitVector const& phiStates, storm::storage::BitVector const& psiStates, bool qualitative, storm::storage::BitVector statesOfCoalition, bool produceScheduler, storm::modelchecker::ModelCheckerHint const& hint = storm::modelchecker::ModelCheckerHint());

        static SMGSparseModelCheckingHelperReturnType<ValueType> computeGloballyProbabilities(storm::Environment const& env, storm::solver::SolveGoal<ValueType>&& goal, storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::SparseMatrix<ValueType> const& backwardTransitions, storm::storage::BitVector const& psiStates, bool qualitative, storm::storage::BitVector statesOfCoalition, bool produceScheduler, storm::modelchecker::ModelCheckerHint const& hint = storm::modelchecker::ModelCheckerHint());

        static SMGSparseModelCheckingHelperReturnType<ValueType> computeNextProbabilities(storm::Environment const& env, storm::solver::SolveGoal<ValueType>&& goal, storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::SparseMatrix<ValueType> const& backwardTransitions, storm::storage::BitVector const& psiStates, bool qualitative, storm::storage::BitVector statesOfCoalition, bool produceScheduler, storm::modelchecker::ModelCheckerHint const& hint);

        static SMGSparseModelCheckingHelperReturnType<ValueType> computeBoundedGloballyProbabilities(storm::Environment const& env, storm::solver::SolveGoal<ValueType>&& goal, storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::SparseMatrix<ValueType> const& backwardTransitions, storm::storage::BitVector const& psiStates, bool qualitative, storm::storage::BitVector statesOfCoalition, bool produceScheduler, storm::modelchecker::ModelCheckerHint const& hint, uint64_t lowerBound, uint64_t upperBound);

        static SMGSparseModelCheckingHelperReturnType<ValueType> computeBoundedUntilProbabilities(storm::Environment const& env, storm::solver::SolveGoal<ValueType>&& goal, storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::SparseMatrix<ValueType> const& backwardTransitions, storm::storage::BitVector const& phiStates, storm::storage::BitVector const& psiStates, bool qualitative, storm::storage::BitVector statesOfCoalition, bool produceScheduler, storm::modelchecker::ModelCheckerHint const& hint, uint64_t lowerBound, uint64_t upperBound, bool computeBoundedGlobally = false);

        static SMGSparseModelCheckingHelperReturnType<ValueType> computeReachabilityRewards(storm::Environment const& env, storm::solver::SolveGoal<ValueType>&& goal, storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::SparseMatrix<ValueType> const& backwardTransitions, storm::models::sparse::StandardRewardModel<ValueType> const& rewardModel, storm::storage::BitVector const& targetStates, bool qualitative, storm::storage::BitVector statesOfCoalition, bool produceScheduler, storm::modelchecker::ModelCheckerHint const& hint = storm::modelchecker::ModelCheckerHint());

    private:

        static SMGSparseModelCheckingHelperReturnType<ValueType> computeReachabilityRewardsHelper(storm::Environment const& env, storm::solver::SolveGoal<ValueType>&& goal,
                                                                                                storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::SparseMatrix<ValueType> const& backwardTransitions,
                                                                                                std::function<std::vector<ValueType>(uint_fast64_t, storm::storage::SparseMatrix<ValueType> const&, storm::storage::BitVector const&)> const& totalStateRewardVectorGetter,
                                                                                                storm::storage::BitVector const& targetStates, bool qualitative, storm::storage::BitVector statesOfCoalition, bool produceScheduler,
                                                                                                storm::modelchecker::ModelCheckerHint const& hint = storm::modelchecker::ModelCheckerHint());

        static storm::storage::Scheduler<ValueType> expandScheduler(storm::storage::Scheduler<ValueType> scheduler, storm::storage::BitVector psiStates, storm::storage::BitVector notPhiStates);

        static void expandChoiceValues(std::vector<uint_fast64_t> const& rowGroupIndices, storm::storage::BitVector const& relevantStates, std::vector<ValueType> const& constrainedChoiceValues, std::vector<ValueType>& choiceValues);

    };
}
