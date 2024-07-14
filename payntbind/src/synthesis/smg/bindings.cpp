#include "../synthesis.h"

#include <storm/api/verification.h>
#include <storm/api/storm.h>

#include "modelchecker/SparseSmgRpatlModelChecker.h"


namespace synthesis {

    template<typename ValueType>
    std::shared_ptr<storm::modelchecker::CheckResult> smgModelChecking (
        storm::models::sparse::Smg<ValueType> const& smg,
        std::shared_ptr<storm::logic::Formula const> formula,
        bool only_initial_states = false,
        bool set_produce_schedulers = true,
        storm::Environment const& env = storm::Environment() 
    ) {
        //prepare model checking task
        auto task = storm::api::createTask<ValueType>(formula, only_initial_states);
        task.setProduceSchedulers(set_produce_schedulers);

        // call model checker
        std::shared_ptr<storm::modelchecker::CheckResult> result;
        synthesis::SparseSmgRpatlModelChecker<storm::models::sparse::Smg<ValueType>> modelchecker(smg);
        if (modelchecker.canHandle(task)) {
            result = modelchecker.check(env, task);
        }
        return result;
    }

}

void bindings_smg(py::module& m) {

    m.def("smg_model_checking", &synthesis::smgModelChecking<double>, py::arg("smg"), py::arg("formula"), py::arg("only_initial_states") = false, py::arg("set_produce_schedulers") = true, py::arg("env") = storm::Environment() );

}

