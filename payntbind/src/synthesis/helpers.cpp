#include "synthesis.h"

#include <storm/logic/Formula.h>
#include <storm/logic/UntilFormula.h>
#include <storm/logic/OperatorFormula.h>
#include <storm/logic/EventuallyFormula.h>
#include <storm/logic/RewardOperatorFormula.h>
#include <storm/logic/ProbabilityOperatorFormula.h>
#include <storm/logic/FormulaContext.h>

#include <storm/utility/initialize.h>
#include <storm/environment/solver/NativeSolverEnvironment.h>
#include <storm/environment/solver/MinMaxSolverEnvironment.h>
#include <storm/storage/SparseMatrix.h>
#include <storm/models/sparse/Model.h>
#include <storm/models/sparse/Dtmc.h>
#include <storm/storage/sparse/ModelComponents.h>

namespace synthesis {

template<typename ValueType>
std::shared_ptr<storm::logic::Formula> transformUntilToEventually(
    storm::logic::Formula const& formula
) {
    auto const& of = formula.asOperatorFormula();
    bool is_reward = of.isRewardOperatorFormula();

    auto ef = std::make_shared<storm::logic::EventuallyFormula>(
        of.getSubformula().asUntilFormula().getRightSubformula().asSharedPointer(),
        !is_reward ? storm::logic::FormulaContext::Probability : storm::logic::FormulaContext::Reward);

    std::shared_ptr<storm::logic::Formula> modified_formula;
    if(!is_reward) {
        modified_formula = std::make_shared<storm::logic::ProbabilityOperatorFormula>(ef, of.getOperatorInformation());
    } else {
        modified_formula = std::make_shared<storm::logic::RewardOperatorFormula>(ef, of.asRewardOperatorFormula().getRewardModelName(), of.getOperatorInformation());
    }

    return modified_formula;
}

template<typename ValueType>
void removeRewardModel(storm::models::sparse::Model<ValueType> & model, std::string const& reward_name) {
    model.removeRewardModel(reward_name);
}

template<typename ValueType>
std::shared_ptr<storm::models::sparse::Dtmc<ValueType>> applyDiscountTransformationToDtmc(storm::models::sparse::Dtmc<ValueType> &model, double discount_factor) {
    storm::storage::sparse::ModelComponents<ValueType> components;

    auto dtmcNumberOfStates = model.getNumberOfStates();

    // labeling
    storm::models::sparse::StateLabeling stateLabeling(dtmcNumberOfStates+1);
    storm::storage::BitVector init_flags = model.getInitialStates();
    init_flags.resize(dtmcNumberOfStates+1, false);
    stateLabeling.addLabel("init", std::move(init_flags));
    storm::storage::BitVector discount_flag(dtmcNumberOfStates+1, false);
    discount_flag.set(dtmcNumberOfStates, true);
    stateLabeling.addLabel("discount_sink", std::move(discount_flag));
    components.stateLabeling = stateLabeling;

    // transition matrix
    storm::storage::SparseMatrix<ValueType> const& transitionMatrix = model.getTransitionMatrix();
    storm::storage::SparseMatrixBuilder<ValueType> builder;
    for (uint_fast64_t state = 0; state < dtmcNumberOfStates; state++) {
        // this function was created for cassandra models where we don't want to discount the first transition
        // maybe it's not needed? TODO
        if (state == 0) {
            for (auto entry: transitionMatrix.getRow(state)) {
                builder.addNextValue(state, entry.getColumn(), entry.getValue());
            }
            builder.addNextValue(state, dtmcNumberOfStates, 0);
        }
        else {
            for (auto entry: transitionMatrix.getRow(state)) {
                builder.addNextValue(state, entry.getColumn(), entry.getValue() * discount_factor);
            }
            builder.addNextValue(state, dtmcNumberOfStates, 1-discount_factor);
        }
    }
    for (uint_fast64_t state = 0; state < dtmcNumberOfStates; state++) {
        builder.addNextValue(dtmcNumberOfStates, state, 0);
    }
    builder.addNextValue(dtmcNumberOfStates, dtmcNumberOfStates, 1);
    components.transitionMatrix = builder.build();

    // reward model
    //components.rewardModels.emplace(this->reward_model_name, this->constructRewardModel());

    return std::make_shared<storm::models::sparse::Dtmc<ValueType>>(std::move(components));
}

}


void define_helpers(py::module& m) {

    m.def("set_loglevel_off", []() { storm::utility::setLogLevel(l3pp::LogLevel::OFF); }, "set loglevel for storm to off");

    m.def("set_precision_native", [](storm::NativeSolverEnvironment& nsenv, double value) {
        nsenv.setPrecision(storm::utility::convertNumber<storm::RationalNumber>(value));
    });
    m.def("set_precision_minmax", [](storm::MinMaxSolverEnvironment& nsenv, double value) {
        nsenv.setPrecision(storm::utility::convertNumber<storm::RationalNumber>(value));
    });

    m.def("transform_until_to_eventually", &synthesis::transformUntilToEventually<double>, py::arg("formula"));
    m.def("remove_reward_model", &synthesis::removeRewardModel<double>, py::arg("model"), py::arg("reward_name"));

    m.def("apply_discount_transformation_to_dtmc", &synthesis::applyDiscountTransformationToDtmc<double>, py::arg("model"), py::arg("discount_factor"));

    m.def("multiply_with_vector", [] (storm::storage::SparseMatrix<double> matrix,std::vector<double> vector) {
        std::vector<double> result(matrix.getRowCount());
        matrix.multiplyWithVector(vector, result);
        return result;
    }, py::arg("matrix"), py::arg("vector"));

}

