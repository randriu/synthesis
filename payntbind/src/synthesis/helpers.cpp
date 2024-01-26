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

    m.def("multiply_with_vector", [] (storm::storage::SparseMatrix<double> matrix,std::vector<double> vector) {
        std::vector<double> result(matrix.getRowCount());
        matrix.multiplyWithVector(vector, result);
        return result;
    }, py::arg("matrix"), py::arg("vector"));

}

