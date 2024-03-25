#include "BeliefMCExplorer.h"
#include <storm-pomdp/transformer/MakeStateSetObservationClosed.h>
#include <storm/modelchecker/results/ExplicitQuantitativeCheckResult.h>
#include <storm-pomdp/analysis/FormulaInformation.h>
#include <storm/utility/graph.h>
#include <storm/exceptions/NotSupportedException.h>
#include <storm/utility/SignalHandler.h>

namespace synthesis {
    
    template<typename PomdpModelType, typename BeliefValueType, typename BeliefMDPType>
    BeliefMCExplorer<PomdpModelType, BeliefValueType, BeliefMDPType>::BeliefMCExplorer(std::shared_ptr<PomdpModelType> pomdp)
    : inputPomdp(pomdp) {
        precision = 1e-12;
    }

    template<typename PomdpModelType, typename BeliefValueType, typename BeliefMDPType>
    double BeliefMCExplorer<PomdpModelType, BeliefValueType, BeliefMDPType>::checkAlphaVectors(storm::logic::Formula const& formula, AlphaVectorSet const& alphaVectorSet) {
        storm::Environment env;
        return checkAlphaVectors(formula, alphaVectorSet, env);
    }

    template<typename PomdpModelType, typename BeliefValueType, typename BeliefMDPType>
    double BeliefMCExplorer<PomdpModelType, BeliefValueType, BeliefMDPType>::checkAlphaVectors(storm::logic::Formula const& formula, AlphaVectorSet const& alphaVectorSet, storm::Environment const& env) {
        STORM_PRINT_AND_LOG("Start checking the MC induced by the alpha vector policy...\n")
        auto formulaInfo = storm::pomdp::analysis::getFormulaInformation(pomdp(), formula);
        std::optional<std::string> rewardModelName;
        std::set<uint32_t> targetObservations;
        if (formulaInfo.isNonNestedReachabilityProbability() || formulaInfo.isNonNestedExpectedRewardFormula()) {
            if (formulaInfo.getTargetStates().observationClosed) {
                targetObservations = formulaInfo.getTargetStates().observations;
            } else {
                storm::transformer::MakeStateSetObservationClosed<PomdpValueType> obsCloser(inputPomdp);
                std::tie(preprocessedPomdp, targetObservations) = obsCloser.transform(formulaInfo.getTargetStates().states);
            }
            if (formulaInfo.isNonNestedReachabilityProbability()) {
                if (!formulaInfo.getSinkStates().empty()) {
                    storm::storage::sparse::ModelComponents<PomdpValueType> components;
                    components.stateLabeling = pomdp().getStateLabeling();
                    components.rewardModels = pomdp().getRewardModels();
                    auto matrix = pomdp().getTransitionMatrix();
                    matrix.makeRowGroupsAbsorbing(formulaInfo.getSinkStates().states);
                    components.transitionMatrix = matrix;
                    components.observabilityClasses = pomdp().getObservations();
                    if(pomdp().hasChoiceLabeling()){
                        components.choiceLabeling = pomdp().getChoiceLabeling();
                    }
                    if(pomdp().hasObservationValuations()){
                        components.observationValuations = pomdp().getObservationValuations();
                    }
                    preprocessedPomdp = std::make_shared<PomdpModelType>(std::move(components), true);
                    auto reachableFromSinkStates = storm::utility::graph::getReachableStates(pomdp().getTransitionMatrix(), formulaInfo.getSinkStates().states, formulaInfo.getSinkStates().states, ~formulaInfo.getSinkStates().states);
                    reachableFromSinkStates &= ~formulaInfo.getSinkStates().states;
                    STORM_LOG_THROW(reachableFromSinkStates.empty(), storm::exceptions::NotSupportedException, "There are sink states that can reach non-sink states. This is currently not supported");
                }
            } else {
                // Expected reward formula!
                rewardModelName = formulaInfo.getRewardModelName();
            }
        } else {
            STORM_LOG_THROW(false, storm::exceptions::NotSupportedException, "Unsupported formula '" << formula << "'.");
        }

        // Compute bound using the underlying MDP and a simple policy
        auto underlyingMdp = std::make_shared<storm::models::sparse::Mdp<PomdpValueType>>(pomdp().getTransitionMatrix(), pomdp().getStateLabeling(), pomdp().getRewardModels());
        auto resultPtr = storm::api::verifyWithSparseEngine<PomdpValueType>(underlyingMdp, storm::api::createTask<PomdpValueType>(formula.asSharedPointer(), false));
        STORM_LOG_THROW(resultPtr, storm::exceptions::UnexpectedException, "No check result obtained.");
        STORM_LOG_THROW(resultPtr->isExplicitQuantitativeCheckResult(), storm::exceptions::UnexpectedException, "Unexpected Check result Type");
        std::vector<PomdpValueType> fullyObservableResult = std::move(resultPtr->template asExplicitQuantitativeCheckResult<PomdpValueType>().getValueVector());

        if(formulaInfo.minimize()){
            pomdpValueBounds.trivialPomdpValueBounds.lower.push_back(fullyObservableResult);
        } else {
            pomdpValueBounds.trivialPomdpValueBounds.upper.push_back(fullyObservableResult);
        }

        // For cut-offs, we need to provide values. To not skew result too much, we always take the first enabled action
        storm::storage::Scheduler<PomdpValueType> pomdpScheduler(pomdp().getNumberOfStates());
        for(uint64_t state = 0; state < pomdp().getNumberOfStates(); ++state) {
            pomdpScheduler.setChoice(0, state);
        }

        // Model check the DTMC resulting from the policy
        auto scheduledModel = underlyingMdp->applyScheduler(pomdpScheduler, false);
        resultPtr = storm::api::verifyWithSparseEngine<PomdpValueType>(scheduledModel, storm::api::createTask<PomdpValueType>(formula.asSharedPointer(), false));
        STORM_LOG_THROW(resultPtr, storm::exceptions::UnexpectedException, "No check result obtained.");
        STORM_LOG_THROW(resultPtr->isExplicitQuantitativeCheckResult(), storm::exceptions::UnexpectedException, "Unexpected Check result Type");
        auto cutoffVec = resultPtr->template asExplicitQuantitativeCheckResult<PomdpValueType>().getValueVector();
        if(formulaInfo.minimize()){
            pomdpValueBounds.trivialPomdpValueBounds.upper.push_back(cutoffVec);
        } else {
            pomdpValueBounds.trivialPomdpValueBounds.lower.push_back(cutoffVec);
        }

        auto manager = std::make_shared<BeliefManagerType>(pomdp(), storm::utility::convertNumber<BeliefValueType>(precision), BeliefManagerType::TriangulationMode::Static);
        if (rewardModelName) {
            manager->setRewardModel(rewardModelName);
        }

        auto explorer = std::make_shared<ExplorerType>(manager, pomdpValueBounds.trivialPomdpValueBounds);
        exploreMC(targetObservations, formulaInfo.minimize(), rewardModelName.has_value(), manager, explorer, cutoffVec, alphaVectorSet, env);

        STORM_LOG_ASSERT(explorer->hasComputedValues(), "Values for MC were not computed");

        return explorer->getComputedValueAtInitialState();
    }



    template<typename PomdpModelType, typename BeliefValueType, typename BeliefMDPType>
    bool BeliefMCExplorer<PomdpModelType, BeliefValueType, BeliefMDPType>::exploreMC(const std::set<uint32_t> &targetObservations, bool min, bool computeRewards, std::shared_ptr<BeliefManagerType> &beliefManager, std::shared_ptr<ExplorerType> &beliefExplorer, std::vector<typename PomdpModelType::ValueType> const &cutoffVec, AlphaVectorSet const& alphaVectorSet, storm::Environment const& env){
        if (computeRewards) {
            beliefExplorer->startNewExploration(storm::utility::zero<BeliefMDPType>());
        } else {
            beliefExplorer->startNewExploration(storm::utility::one<BeliefMDPType>(), storm::utility::zero<BeliefMDPType>());
        }

        uint64_t sizeThreshold = 1000000;

        //TODO use timelimit
        bool fixPoint = true;
        bool timeLimitExceeded = false;
        bool stopExploration = false;
        //TODO stopping criterion
        while (beliefExplorer->hasUnexploredState()) {
            if (false) {
                STORM_LOG_INFO("Exploration time limit exceeded.");
                timeLimitExceeded = true;
            }

            uint64_t currId = beliefExplorer->exploreNextState();

            if (timeLimitExceeded) {
                fixPoint = false;
            }
            if (targetObservations.count(beliefManager->getBeliefObservation(currId)) != 0) {
                beliefExplorer->setCurrentStateIsTarget();
                beliefExplorer->addSelfloopTransition();
                beliefExplorer->addChoiceLabelToCurrentState(0, "loop");
            } else {
                if (timeLimitExceeded || beliefExplorer->getCurrentNumberOfMdpStates() >= sizeThreshold /*&& !statistics.beliefMdpDetectedToBeFinite*/) {
                    stopExploration = true;
                    beliefExplorer->setCurrentStateIsTruncated();
                }
                if(!stopExploration) {
                    // determine the best action from the alpha vectors
                    auto chosenLocalActionIndex = getBestActionInBelief(currId, beliefManager, beliefExplorer, alphaVectorSet);
                    // if action is not in the model, treat it as a self loop action
                    if(chosenLocalActionIndex >= beliefManager->getBeliefNumberOfChoices(currId)){
                        beliefExplorer->addSelfloopTransition();
                        beliefExplorer->addChoiceLabelToCurrentState(0, "loop");
                    }
                    else {
                        // Add successor transitions for the chosen action
                        auto truncationProbability = storm::utility::zero<typename PomdpModelType::ValueType>();
                        auto truncationValueBound = storm::utility::zero<typename PomdpModelType::ValueType>();
                        auto successors = beliefManager->expand(currId, chosenLocalActionIndex);
                        for (auto const &successor : successors) {
                            bool added = beliefExplorer->addTransitionToBelief(0, successor.first, successor.second, stopExploration);
                            if (!added) {
                                STORM_LOG_ASSERT(stopExploration, "Didn't add a transition although exploration shouldn't be stopped.");
                                // We did not explore this successor state. Get a bound on the "missing" value
                                truncationProbability += successor.second;
                                truncationValueBound += successor.second * (min ? beliefExplorer->computeUpperValueBoundAtBelief(successor.first)
                                                                                : beliefExplorer->computeLowerValueBoundAtBelief(successor.first));
                            }
                        }
                        if (computeRewards) {
                            // The truncationValueBound will be added on top of the reward introduced by the current belief state.
                            beliefExplorer->addRewardToCurrentState(0, beliefManager->getBeliefActionReward(currId, chosenLocalActionIndex) + truncationValueBound);
                        }
                    }
                } else {
                    //When we stop, we apply simple cut-offs
                    auto cutOffValue = beliefManager->getWeightedSum(currId, cutoffVec);
                    if (computeRewards) {
                        beliefExplorer->addTransitionsToExtraStates(0, storm::utility::one<PomdpValueType>());
                        beliefExplorer->addRewardToCurrentState(0, cutOffValue);
                    } else {
                        beliefExplorer->addTransitionsToExtraStates(0, cutOffValue,storm::utility::one<PomdpValueType>() - cutOffValue);
                    }
                    if(pomdp().hasChoiceLabeling()){
                        beliefExplorer->addChoiceLabelToCurrentState(0, "cutoff");
                    }
                }
            }
            if (storm::utility::resources::isTerminate()) {
                break;
            }
        }

        if (storm::utility::resources::isTerminate()) {
            return false;
        }

        beliefExplorer->finishExploration();
        STORM_PRINT_AND_LOG("Finished exploring Alpha Vector Policy induced Markov chain.\n Start analysis...\n");

        beliefExplorer->computeValuesOfExploredMdp(env, min ? storm::solver::OptimizationDirection::Minimize : storm::solver::OptimizationDirection::Maximize);
        // don't overwrite statistics of a previous, successful computation
        return fixPoint;
    }



    template<typename PomdpModelType, typename BeliefValueType, typename BeliefMDPType>
    uint64_t BeliefMCExplorer<PomdpModelType, BeliefValueType, BeliefMDPType>::getBestActionInBelief(uint64_t beliefId, std::shared_ptr<BeliefManagerType> &beliefManager, std::shared_ptr<ExplorerType> &beliefExplorer, AlphaVectorSet const& alphaVectorSet) {
        uint64_t bestAlphaIndex = 0;
        double bestAlphaValue = 0;
        for (uint64_t alphaIndex = 0; alphaIndex < alphaVectorSet.alphaVectors.size(); alphaIndex++ ) {
            if (alphaIndex == 0) {
                auto belief = beliefManager->getBeliefAsMap(beliefId);
                for (auto const &pointEntry : belief) {
                    bestAlphaValue += alphaVectorSet.alphaVectors.at(alphaIndex).at(pointEntry.first) * pointEntry.second;
                }
            } else {
                double alphaValue = 0;
                auto belief = beliefManager->getBeliefAsMap(beliefId);
                for (auto const &pointEntry : belief) {
                    alphaValue += alphaVectorSet.alphaVectors.at(alphaIndex).at(pointEntry.first) * pointEntry.second;
                }

                if (alphaValue > bestAlphaValue) {
                    bestAlphaValue = alphaValue;
                    bestAlphaIndex = alphaIndex;
                }
            }
        }
        return alphaVectorSet.alphaVectorActions.at(bestAlphaIndex);
    }



    template<typename PomdpModelType, typename BeliefValueType, typename BeliefMDPType>
    PomdpModelType const& BeliefMCExplorer<PomdpModelType, BeliefValueType, BeliefMDPType>::pomdp() const {
        if (preprocessedPomdp) {
            return *preprocessedPomdp;
        } else {
            return *inputPomdp;
        }
    }


    template class BeliefMCExplorer<storm::models::sparse::Pomdp<double>>;
}