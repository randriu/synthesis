#pragma once

/**
 * The code below was taken from TEMPEST (https://github.com/PrangerStefan/TempestSynthesis) and adapted to the latest
 * Storm version.
 */

#include <map>
#include <functional>

#include <storm/modelchecker/propositional/SparsePropositionalModelChecker.h>
#include <storm/models/sparse/Smg.h>
#include <storm/storage/BitVector.h>

namespace synthesis {

    template<class SparseSmgModelType>
    class SparseSmgRpatlModelChecker : public storm::modelchecker::SparsePropositionalModelChecker<SparseSmgModelType> {
    public:

        typedef typename SparseSmgModelType::ValueType ValueType;
        typedef typename SparseSmgModelType::RewardModelType RewardModelType;

        explicit SparseSmgRpatlModelChecker(SparseSmgModelType const& model);

        /*!
            * Returns false, if this task can certainly not be handled by this model checker (independent of the concrete model).
            * @param requiresSingleInitialState if not nullptr, this flag is set to true iff checking this formula requires a model with a single initial state
            */
        static bool canHandleStatic(storm::modelchecker::CheckTask<storm::logic::Formula, ValueType> const& checkTask, bool* requiresSingleInitialState = nullptr);

        // The implemented methods of the AbstractModelChecker interface.
        bool canHandle(storm::modelchecker::CheckTask<storm::logic::Formula, ValueType> const& checkTask) const override;

        #ifndef DISABLE_SMG
        std::unique_ptr<storm::modelchecker::CheckResult> checkGameFormula(storm::Environment const& env, storm::modelchecker::CheckTask<storm::logic::GameFormula, ValueType> const& checkTask) override;
        std::unique_ptr<storm::modelchecker::CheckResult> checkProbabilityOperatorFormula(storm::Environment const& env, storm::modelchecker::CheckTask<storm::logic::ProbabilityOperatorFormula, ValueType> const& checkTask) override;
        std::unique_ptr<storm::modelchecker::CheckResult> checkRewardOperatorFormula(storm::Environment const& env, storm::modelchecker::CheckTask<storm::logic::RewardOperatorFormula, ValueType> const& checkTask) override;
        std::unique_ptr<storm::modelchecker::CheckResult> checkLongRunAverageOperatorFormula(storm::Environment const& env, storm::modelchecker::CheckTask<storm::logic::LongRunAverageOperatorFormula, ValueType> const& checkTask) override;

        std::unique_ptr<storm::modelchecker::CheckResult> computeProbabilities(storm::Environment const& env, storm::modelchecker::CheckTask<storm::logic::Formula, ValueType> const& checkTask) override;
        std::unique_ptr<storm::modelchecker::CheckResult> computeRewards(storm::Environment const& env, storm::modelchecker::CheckTask<storm::logic::Formula, ValueType> const& checkTask) override;

        std::unique_ptr<storm::modelchecker::CheckResult> computeUntilProbabilities(storm::Environment const& env, storm::modelchecker::CheckTask<storm::logic::UntilFormula, ValueType> const& checkTask) override;
        std::unique_ptr<storm::modelchecker::CheckResult> computeGloballyProbabilities(storm::Environment const& env, storm::modelchecker::CheckTask<storm::logic::GloballyFormula, ValueType> const& checkTask) override;
        std::unique_ptr<storm::modelchecker::CheckResult> computeNextProbabilities(storm::Environment const& env, storm::modelchecker::CheckTask<storm::logic::NextFormula, ValueType> const& checkTask) override;
        std::unique_ptr<storm::modelchecker::CheckResult> computeBoundedUntilProbabilities(storm::Environment const& env, storm::modelchecker::CheckTask<storm::logic::BoundedUntilFormula, ValueType> const& checkTask) override;

        std::unique_ptr<storm::modelchecker::CheckResult> computeLongRunAverageProbabilities(storm::Environment const& env, storm::modelchecker::CheckTask<storm::logic::StateFormula, ValueType> const& checkTask) override;
        std::unique_ptr<storm::modelchecker::CheckResult> computeLongRunAverageRewards(storm::Environment const& env, storm::modelchecker::CheckTask<storm::logic::LongRunAverageRewardFormula, ValueType> const& checkTask) override;

        #endif // DISABLE_SMG

    private:
        storm::storage::BitVector statesOfCoalition;
    };
}

