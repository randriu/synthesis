#include "../synthesis.h"

#include <storm/api/verification.h>
#include <storm/api/storm.h>

#include "modelchecker/SparseSmgRpatlModelChecker.h"


namespace synthesis {

    template<typename ValueType>
    std::shared_ptr<storm::modelchecker::CheckResult> modelCheckSmg (
        storm::models::sparse::Smg<ValueType> const& smg,
        std::shared_ptr<storm::logic::Formula const> formula,
        bool only_initial_states = false,
        bool set_produce_schedulers = true,
        storm::Environment const& env = storm::Environment()
    ) {
        auto task = storm::api::createTask<ValueType>(formula, only_initial_states);
        task.setProduceSchedulers(set_produce_schedulers);
        std::shared_ptr<storm::modelchecker::CheckResult> result;
        synthesis::SparseSmgRpatlModelChecker<storm::models::sparse::Smg<ValueType>> modelchecker(smg);
        if (modelchecker.canHandle(task)) {
            result = modelchecker.check(env, task);
        }
        return result;
    }

    template std::shared_ptr<storm::modelchecker::CheckResult> modelCheckSmg (
        storm::models::sparse::Smg<double> const& smg,
        std::shared_ptr<storm::logic::Formula const> formula,
        bool only_initial_states = false,
        bool set_produce_schedulers = true,
        storm::Environment const& env = storm::Environment()
    );
}
