#include "ObservationEvaluator.h"

#include <storm/exceptions/InvalidTypeException.h>
#include <storm/exceptions/NotSupportedException.h>
#include <storm/storage/expressions/ExpressionEvaluator.h>
#include <storm-pomdp/transformer/MakePOMDPCanonic.h>

namespace synthesis {

    template<typename ValueType>
    ObservationEvaluator<ValueType>::ObservationEvaluator(
        storm::prism::Program & prism,
        storm::models::sparse::Model<ValueType> const& model
    ) {
        // substitute constants and simplify formulas in the program
        prism = prism.substituteConstantsFormulas(true,true);

        // identify names and types of observation labels
        this->num_obs_expressions = prism.getNumberOfObservationLabels();
        this->obs_expr_label.resize(this->num_obs_expressions);
        this->obs_expr_is_boolean.resize(this->num_obs_expressions);

        for(uint32_t o = 0; o < this->num_obs_expressions; o++) {
            auto const& obs_label = prism.getObservationLabels()[o];
            obs_expr_label[o] = obs_label.getName();
            auto const& obs_expr = obs_label.getStatePredicateExpression();
            STORM_LOG_THROW(obs_expr.hasBooleanType() or obs_expr.hasIntegerType(), storm::exceptions::InvalidTypeException,
                "expected boolean or integer observation expression");
            this->obs_expr_is_boolean[o] = obs_expr.hasBooleanType();
        }

        // evaluate observation expression for each state valuation
        storm::expressions::ExpressionEvaluator<double> evaluator(prism.getManager());
        auto const& state_valuations = model.getStateValuations();
        // associate each evaluation with the unique observation class
        this->state_to_obs_class.resize(model.getNumberOfStates());
        this->num_obs_classes = 0;
        for(uint64_t state = 0; state < model.getNumberOfStates(); state++) {

            // collect state valuation into evaluator
            for(auto it = state_valuations.at(state).begin(); it != state_valuations.at(state).end(); ++it) {
                // we pass Jani variables to the evaluator, but it seems to work, perhaps it works with variable names
                auto const& var = it.getVariable();
                if(it.isBoolean()) {
                    evaluator.setBooleanValue(var, it.getBooleanValue());
                } else if(it.isInteger()) {
                    evaluator.setIntegerValue(var, it.getIntegerValue());
                } else {
                    // this is a rational variable: we skip it in a hope that this variable encodes reward value
                    // which is not relevant for the observation
                    // evaluator.setRationalValue(var, it.getRationalValue());
                }
            }
            
            // evaluate observation expressions and assign class
            storm::storage::BitVector evaluation(OBS_EXPR_VALUE_SIZE*num_obs_expressions);
            for (uint32_t o = 0; o < num_obs_expressions; o++) {
                evaluation.setFromInt(
                    OBS_EXPR_VALUE_SIZE*o,
                    OBS_EXPR_VALUE_SIZE,
                    evaluator.asInt(prism.getObservationLabels()[o].getStatePredicateExpression())
                );
            }
            auto result = this->obs_evaluation_to_class.insert(std::make_pair(evaluation,this->num_obs_classes));
            if(not result.second) {
                // existing evaluation
                this->state_to_obs_class[state] = result.first->second;
            } else {
                // new evaluation
                this->state_to_obs_class[state] = this->num_obs_classes;
                this->obs_class_to_evaluation.push_back(evaluation);
                this->num_obs_classes++;
            }
        }
    }

    template<typename ValueType>
    uint32_t ObservationEvaluator<ValueType>::observationClassValue(uint32_t obs_class, uint32_t obs_expr) {
        return this->obs_class_to_evaluation[obs_class].getAsInt(OBS_EXPR_VALUE_SIZE*obs_expr,OBS_EXPR_VALUE_SIZE);
    }

    template<typename ValueType>
    std::shared_ptr<storm::models::sparse::Pomdp<ValueType>> ObservationEvaluator<ValueType>::addObservationsToSubMdp(
        storm::models::sparse::Mdp<ValueType> const& sub_mdp,
        std::vector<uint64_t> state_sub_to_full
    ) {

        storm::storage::sparse::ModelComponents<ValueType> components;
        components.transitionMatrix = sub_mdp.getTransitionMatrix();
        components.stateLabeling = sub_mdp.getStateLabeling();
        components.rewardModels = sub_mdp.getRewardModels();
        components.choiceLabeling = sub_mdp.getChoiceLabeling();
        
        std::vector<uint32_t> observability_classes(sub_mdp.getNumberOfStates());
        for(uint64_t state = 0; state < sub_mdp.getNumberOfStates(); state++) {
            observability_classes[state] = this->state_to_obs_class[state_sub_to_full[state]];
        }
        components.observabilityClasses = observability_classes;

        auto pomdp = storm::models::sparse::Pomdp<ValueType>(std::move(components));
        auto pomdp_canonic = storm::transformer::MakePOMDPCanonic<ValueType>(pomdp).transform();
        return pomdp_canonic;
        // return std::make_shared<storm::models::sparse::Pomdp<ValueType>>(std::move(components));
    }

    
    template class ObservationEvaluator<double>;
}
