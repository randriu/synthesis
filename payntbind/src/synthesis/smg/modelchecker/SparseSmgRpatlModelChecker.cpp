/**
 * The code below was taken from TEMPEST (https://github.com/PrangerStefan/TempestSynthesis) and adapted to the latest
 * Storm version.
 */

#include "SparseSmgRpatlModelChecker.h"

#include <vector>
#include <memory>
#include <algorithm>

#include <storm/utility/FilteredRewardModel.h>
#include <storm/modelchecker/results/ExplicitQualitativeCheckResult.h>
#include <storm/modelchecker/results/ExplicitQuantitativeCheckResult.h>
#include <storm/modelchecker/helper/utility/SetInformationFromCheckTask.h>
#include <storm/logic/PlayerCoalition.h>
#include <storm/environment/solver/MultiplierEnvironment.h>
#include <storm/exceptions/InvalidPropertyException.h>
#include <storm/exceptions/InvalidArgumentException.h>
#include <storm/modelchecker/results/ExplicitParetoCurveCheckResult.h>
#include <storm/logic/FragmentSpecification.h>

#include "helper/SparseSmgRpatlHelper.h"
#include "helper/SparseNondeterministicGameInfiniteHorizonHelper.h"

namespace synthesis {


    storm::logic::FragmentSpecification rpatl() {
        storm::logic::FragmentSpecification rpatl = storm::logic::propositional();

        rpatl.setGameFormulasAllowed(true);
        rpatl.setRewardOperatorsAllowed(true);
        rpatl.setLongRunAverageRewardFormulasAllowed(true);
        rpatl.setLongRunAverageOperatorsAllowed(true);

        rpatl.setProbabilityOperatorsAllowed(true);
        rpatl.setReachabilityProbabilityFormulasAllowed(true);
        rpatl.setUntilFormulasAllowed(true);
        rpatl.setGloballyFormulasAllowed(true);
        rpatl.setNextFormulasAllowed(true);
        rpatl.setBoundedUntilFormulasAllowed(true);
        rpatl.setStepBoundedUntilFormulasAllowed(true);
        rpatl.setTimeBoundedUntilFormulasAllowed(true);

        return rpatl;
    }

    template<typename SparseSmgModelType>
    SparseSmgRpatlModelChecker<SparseSmgModelType>::SparseSmgRpatlModelChecker(SparseSmgModelType const& model) : storm::modelchecker::SparsePropositionalModelChecker<SparseSmgModelType>(model) {
        // Intentionally left empty.
    }

    template<typename SparseSmgModelType>
    bool SparseSmgRpatlModelChecker<SparseSmgModelType>::canHandleStatic(storm::modelchecker::CheckTask<storm::logic::Formula, ValueType> const& checkTask, bool* requiresSingleInitialState) {
        storm::logic::Formula const& formula = checkTask.getFormula();
        return formula.isInFragment(synthesis::rpatl());
    }

    template<typename SparseSmgModelType>
    bool SparseSmgRpatlModelChecker<SparseSmgModelType>::canHandle(storm::modelchecker::CheckTask<storm::logic::Formula, ValueType> const& checkTask) const {
        bool requiresSingleInitialState = false;
        if (canHandleStatic(checkTask, &requiresSingleInitialState)) {
            return !requiresSingleInitialState || this->getModel().getInitialStates().getNumberOfSetBits() == 1;
        } else {
            return false;
        }
    }

    #ifndef DISABLE_SMG

    template<typename SparseSmgModelType>
    std::unique_ptr<storm::modelchecker::CheckResult> SparseSmgRpatlModelChecker<SparseSmgModelType>::checkGameFormula(storm::Environment const& env, storm::modelchecker::CheckTask<storm::logic::GameFormula, ValueType> const& checkTask) {
        storm::Environment solverEnv = env;

        storm::logic::GameFormula const& gameFormula = checkTask.getFormula();
        storm::logic::Formula const& subFormula = gameFormula.getSubformula();

        statesOfCoalition = this->getModel().computeStatesOfCoalition(gameFormula.getCoalition());
        STORM_LOG_INFO("Found " << statesOfCoalition.getNumberOfSetBits() << " states in coalition.");
        statesOfCoalition.complement();

        if (subFormula.isRewardOperatorFormula()) {
            return this->checkRewardOperatorFormula(solverEnv, checkTask.substituteFormula(subFormula.asRewardOperatorFormula()));
        } else if (subFormula.isLongRunAverageOperatorFormula()) {
            return this->checkLongRunAverageOperatorFormula(solverEnv, checkTask.substituteFormula(subFormula.asLongRunAverageOperatorFormula()));
        } else if (subFormula.isProbabilityOperatorFormula()) {
            return this->checkProbabilityOperatorFormula(solverEnv, checkTask.substituteFormula(subFormula.asProbabilityOperatorFormula()));
        }
        STORM_LOG_THROW(false, storm::exceptions::NotImplementedException, "Cannot check this property (yet).");
    }

    template<typename ModelType>
    std::unique_ptr<storm::modelchecker::CheckResult> SparseSmgRpatlModelChecker<ModelType>::checkProbabilityOperatorFormula(storm::Environment const& env, storm::modelchecker::CheckTask<storm::logic::ProbabilityOperatorFormula, ValueType> const& checkTask) {
        storm::logic::ProbabilityOperatorFormula const& stateFormula = checkTask.getFormula();
        std::unique_ptr<storm::modelchecker::CheckResult> result = this->computeProbabilities(env, checkTask.substituteFormula(stateFormula.getSubformula()));

        if (checkTask.isBoundSet()) {
            STORM_LOG_THROW(result->isQuantitative(), storm::exceptions::InvalidOperationException, "Unable to perform comparison operation on non-quantitative result.");
            return result->asQuantitativeCheckResult<ValueType>().compareAgainstBound(checkTask.getBoundComparisonType(), checkTask.getBoundThreshold());
        } else {
            return result;
        }
    }

    template<typename ModelType>
    std::unique_ptr<storm::modelchecker::CheckResult> SparseSmgRpatlModelChecker<ModelType>::checkRewardOperatorFormula(storm::Environment const& env, storm::modelchecker::CheckTask<storm::logic::RewardOperatorFormula, ValueType> const& checkTask) {
        storm::logic::RewardOperatorFormula const& formula = checkTask.getFormula();
        std::unique_ptr<storm::modelchecker::CheckResult> result = this->computeRewards(env, checkTask.substituteFormula(formula.getSubformula()));
        return result;
    }

    template<typename ModelType>
    std::unique_ptr<storm::modelchecker::CheckResult> SparseSmgRpatlModelChecker<ModelType>::checkLongRunAverageOperatorFormula(storm::Environment const& env, storm::modelchecker::CheckTask<storm::logic::LongRunAverageOperatorFormula, ValueType> const& checkTask) {
        storm::logic::LongRunAverageOperatorFormula const& formula = checkTask.getFormula();
        std::unique_ptr<storm::modelchecker::CheckResult> result = this->computeLongRunAverageProbabilities(env, checkTask.substituteFormula(formula.getSubformula().asStateFormula()));
        return result;
    }

    template<typename ModelType>
    std::unique_ptr<storm::modelchecker::CheckResult> SparseSmgRpatlModelChecker<ModelType>::computeProbabilities(storm::Environment const& env, storm::modelchecker::CheckTask<storm::logic::Formula, ValueType> const& checkTask) {
        storm::logic::Formula const& formula = checkTask.getFormula();
        if (formula.isReachabilityProbabilityFormula()) {
            return this->computeReachabilityProbabilities(env, checkTask.substituteFormula(formula.asReachabilityProbabilityFormula()));
        } else if (formula.isUntilFormula()) {
            return this->computeUntilProbabilities(env, checkTask.substituteFormula(formula.asUntilFormula()));
        } else if (formula.isGloballyFormula()) {
            return this->computeGloballyProbabilities(env, checkTask.substituteFormula(formula.asGloballyFormula()));
        } else if (formula.isNextFormula()) {
            return this->computeNextProbabilities(env, checkTask.substituteFormula(formula.asNextFormula()));
        } else if (formula.isBoundedUntilFormula()) {
            return this->computeBoundedUntilProbabilities(env, checkTask.substituteFormula(formula.asBoundedUntilFormula()));
        }
        STORM_LOG_THROW(false, storm::exceptions::InvalidArgumentException, "The given formula '" << formula << "' is invalid.");
    }

    template<typename ModelType>
    std::unique_ptr<storm::modelchecker::CheckResult> SparseSmgRpatlModelChecker<ModelType>::computeRewards(storm::Environment const& env, storm::modelchecker::CheckTask<storm::logic::Formula, ValueType> const& checkTask) {
        storm::logic::Formula const& rewardFormula = checkTask.getFormula();
        if (rewardFormula.isLongRunAverageRewardFormula()) {
            return this->computeLongRunAverageRewards(env, checkTask.substituteFormula(rewardFormula.asLongRunAverageRewardFormula()));
        }
        STORM_LOG_THROW(false, storm::exceptions::InvalidArgumentException, "The given formula '" << rewardFormula << "' cannot (yet) be handled.");
    }

    template<typename ModelType>
    std::unique_ptr<storm::modelchecker::CheckResult> SparseSmgRpatlModelChecker<ModelType>::computeUntilProbabilities(storm::Environment const& env, storm::modelchecker::CheckTask<storm::logic::UntilFormula, ValueType> const& checkTask) {
        // Currently we only support computation of reachability probabilities, i.e. the left subformula will always be 'true' (for now).
        storm::logic::UntilFormula const& pathFormula = checkTask.getFormula();
        STORM_LOG_THROW(checkTask.isOptimizationDirectionSet(), storm::exceptions::InvalidPropertyException, "Formula needs to specify whether minimal or maximal values are to be computed on nondeterministic model.");
        std::unique_ptr<storm::modelchecker::CheckResult> leftResultPointer = this->check(env, pathFormula.getLeftSubformula());
        std::unique_ptr<storm::modelchecker::CheckResult> rightResultPointer = this->check(env, pathFormula.getRightSubformula());
        storm::modelchecker::ExplicitQualitativeCheckResult const& leftResult = leftResultPointer->asExplicitQualitativeCheckResult();
        storm::modelchecker::ExplicitQualitativeCheckResult const& rightResult = rightResultPointer->asExplicitQualitativeCheckResult();

        auto ret = synthesis::SparseSmgRpatlHelper<ValueType>::computeUntilProbabilities(env, storm::solver::SolveGoal<ValueType>(this->getModel(), checkTask), this->getModel().getTransitionMatrix(), this->getModel().getBackwardTransitions(), leftResult.getTruthValuesVector(), rightResult.getTruthValuesVector(), checkTask.isQualitativeSet(), statesOfCoalition, checkTask.isProduceSchedulersSet(), checkTask.getHint());
        std::unique_ptr<storm::modelchecker::CheckResult> result(new storm::modelchecker::ExplicitQuantitativeCheckResult<ValueType>(std::move(ret.values)));
        if (checkTask.isProduceSchedulersSet() && ret.scheduler) {
            result->asExplicitQuantitativeCheckResult<ValueType>().setScheduler(std::move(ret.scheduler));
        }
        return result;
    }

    template<typename ModelType>
    std::unique_ptr<storm::modelchecker::CheckResult> SparseSmgRpatlModelChecker<ModelType>::computeGloballyProbabilities(storm::Environment const& env, storm::modelchecker::CheckTask<storm::logic::GloballyFormula, ValueType> const& checkTask) {
        storm::logic::GloballyFormula const& pathFormula = checkTask.getFormula();
        std::unique_ptr<storm::modelchecker::CheckResult> subResultPointer = this->check(env, pathFormula.getSubformula());
        storm::modelchecker::ExplicitQualitativeCheckResult const& subResult = subResultPointer->asExplicitQualitativeCheckResult();

        auto ret = synthesis::SparseSmgRpatlHelper<ValueType>::computeGloballyProbabilities(env, storm::solver::SolveGoal<ValueType>(this->getModel(), checkTask), this->getModel().getTransitionMatrix(), this->getModel().getBackwardTransitions(), subResult.getTruthValuesVector(), checkTask.isQualitativeSet(), statesOfCoalition, checkTask.isProduceSchedulersSet(), checkTask.getHint());
        std::unique_ptr<storm::modelchecker::CheckResult> result(new storm::modelchecker::ExplicitQuantitativeCheckResult<ValueType>(std::move(ret.values)));
        if (checkTask.isProduceSchedulersSet() && ret.scheduler) {
            result->asExplicitQuantitativeCheckResult<ValueType>().setScheduler(std::move(ret.scheduler));
        }
        return result;
    }

    template<typename ModelType>
    std::unique_ptr<storm::modelchecker::CheckResult> SparseSmgRpatlModelChecker<ModelType>::computeNextProbabilities(storm::Environment const& env, storm::modelchecker::CheckTask<storm::logic::NextFormula, ValueType> const& checkTask) {
        storm::logic::NextFormula const& pathFormula = checkTask.getFormula();
        STORM_LOG_THROW(checkTask.isOptimizationDirectionSet(), storm::exceptions::InvalidPropertyException, "Formula needs to specify whether minimal or maximal values are to be computed on nondeterministic model.");
        std::unique_ptr<storm::modelchecker::CheckResult> subResultPointer = this->check(env, pathFormula.getSubformula());
        storm::modelchecker::ExplicitQualitativeCheckResult const& subResult = subResultPointer->asExplicitQualitativeCheckResult();

        auto ret = synthesis::SparseSmgRpatlHelper<ValueType>::computeNextProbabilities(env, storm::solver::SolveGoal<ValueType>(this->getModel(), checkTask), this->getModel().getTransitionMatrix(), this->getModel().getBackwardTransitions(), subResult.getTruthValuesVector(), checkTask.isQualitativeSet(), ~statesOfCoalition, checkTask.isProduceSchedulersSet(), checkTask.getHint());
        std::unique_ptr<storm::modelchecker::CheckResult> result(new storm::modelchecker::ExplicitQuantitativeCheckResult<ValueType>(std::move(ret.values)));
        return result;
    }

    template<typename ModelType>
    std::unique_ptr<storm::modelchecker::CheckResult> SparseSmgRpatlModelChecker<ModelType>::computeBoundedUntilProbabilities(storm::Environment const& env, storm::modelchecker::CheckTask<storm::logic::BoundedUntilFormula, ValueType> const& checkTask) {
        storm::logic::BoundedUntilFormula const& pathFormula = checkTask.getFormula();
        STORM_LOG_THROW(checkTask.isOptimizationDirectionSet(), storm::exceptions::InvalidPropertyException, "Formula needs to specify whether minimal or maximal values are to be computed on nondeterministic model.");
        // checks for bounds
        STORM_LOG_THROW(pathFormula.hasUpperBound(), storm::exceptions::InvalidPropertyException, "Formula needs to have (a single) upper step bound.");
        STORM_LOG_THROW(pathFormula.hasIntegerLowerBound(), storm::exceptions::InvalidPropertyException, "Formula lower step bound must be discrete.");
        STORM_LOG_THROW(pathFormula.hasIntegerUpperBound(), storm::exceptions::InvalidPropertyException, "Formula upper step bound must be discrete.");

        std::unique_ptr<storm::modelchecker::CheckResult> leftResultPointer = this->check(env, pathFormula.getLeftSubformula());
        std::unique_ptr<storm::modelchecker::CheckResult> rightResultPointer = this->check(env, pathFormula.getRightSubformula());
        storm::modelchecker::ExplicitQualitativeCheckResult const& leftResult = leftResultPointer->asExplicitQualitativeCheckResult();
        storm::modelchecker::ExplicitQualitativeCheckResult const& rightResult = rightResultPointer->asExplicitQualitativeCheckResult();

        auto ret = synthesis::SparseSmgRpatlHelper<ValueType>::computeBoundedUntilProbabilities(env, storm::solver::SolveGoal<ValueType>(this->getModel(), checkTask), this->getModel().getTransitionMatrix(), this->getModel().getBackwardTransitions(), leftResult.getTruthValuesVector(), rightResult.getTruthValuesVector(), checkTask.isQualitativeSet(), statesOfCoalition, checkTask.isProduceSchedulersSet(), checkTask.getHint(), pathFormula.getNonStrictLowerBound<uint64_t>(), pathFormula.getNonStrictUpperBound<uint64_t>());
        std::unique_ptr<storm::modelchecker::CheckResult> result(new storm::modelchecker::ExplicitQuantitativeCheckResult<ValueType>(std::move(ret.values)));
        return result;
    }

    template<typename SparseSmgModelType>
    std::unique_ptr<storm::modelchecker::CheckResult> SparseSmgRpatlModelChecker<SparseSmgModelType>::computeLongRunAverageProbabilities(storm::Environment const& env, storm::modelchecker::CheckTask<storm::logic::StateFormula, ValueType> const& checkTask) {
        STORM_LOG_THROW(false, storm::exceptions::NotImplementedException, "NYI");
    }

    template<typename SparseSmgModelType>
    std::unique_ptr<storm::modelchecker::CheckResult> SparseSmgRpatlModelChecker<SparseSmgModelType>::computeLongRunAverageRewards(storm::Environment const& env, storm::modelchecker::CheckTask<storm::logic::LongRunAverageRewardFormula, ValueType> const& checkTask) {
        auto rewardModel = storm::utility::createFilteredRewardModel(this->getModel(), checkTask);
        synthesis::SparseNondeterministicGameInfiniteHorizonHelper<ValueType> helper(this->getModel().getTransitionMatrix(), statesOfCoalition);
        storm::modelchecker::helper::setInformationFromCheckTaskNondeterministic(helper, checkTask, this->getModel());
        auto values = helper.computeLongRunAverageRewards(env, rewardModel.get());

        std::unique_ptr<storm::modelchecker::CheckResult> result(new storm::modelchecker::ExplicitQuantitativeCheckResult<ValueType>(std::move(values)));
        if (checkTask.isProduceSchedulersSet()) {
            result->asExplicitQuantitativeCheckResult<ValueType>().setScheduler(std::make_unique<storm::storage::Scheduler<ValueType>>(helper.extractScheduler()));
        }
        return result;
    }

    #endif //DISABLE_SMG

    template class SparseSmgRpatlModelChecker<storm::models::sparse::Smg<double>>;

}
