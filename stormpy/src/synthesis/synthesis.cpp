#include "synthesis.h"

#include "storm-synthesis/synthesis/Counterexample.h"

#include "storm/modelchecker/CheckTask.h"
#include "storm/environment/Environment.h"
#include "storm/api/verification.h"
#include "storm/modelchecker/hints/ExplicitModelCheckerHint.h"



template<typename ValueType>
std::shared_ptr<storm::modelchecker::CheckResult> modelCheckWithHint(
    std::shared_ptr<storm::models::sparse::Model<ValueType>> model,
    storm::modelchecker::CheckTask<storm::logic::Formula, ValueType> & task,
    storm::Environment const& env,
    std::vector<ValueType> hint_values
) {
    storm::modelchecker::ExplicitModelCheckerHint<ValueType> hint;
    hint.setComputeOnlyMaybeStates(false);
    hint.setResultHint(boost::make_optional(hint_values));
    task.setHint(std::make_shared<storm::modelchecker::ExplicitModelCheckerHint<ValueType>>(hint));
    return storm::api::verifyWithSparseEngine<ValueType>(env, model, task);
}

// Define python bindings
void define_synthesis(py::module& m) {

    // Counterexample generation
    py::class_<storm::synthesis::CounterexampleGenerator<>>(
        m, "CounterexampleGenerator", "Counterexample generation"
    )
        .def(
            py::init<
                storm::models::sparse::Mdp<double> const&,
                uint_fast64_t,
                std::vector<std::set<uint_fast64_t>> const&,
                std::vector<std::shared_ptr<storm::logic::Formula const>> const&
            >(),
            "Preprocess the quotient MDP.",
            py::arg("quotient_mdp"), py::arg("hole_count"), py::arg("mdp_holes"), py::arg("formulae")
            )
        .def(
            "prepare_dtmc",
            &storm::synthesis::CounterexampleGenerator<>::prepareDtmc,
            "Prepare a DTMC for CE construction.",
            py::arg("dtmc"), py::arg("quotient_state_map")
            )
        .def(
            "construct_conflict",
            &storm::synthesis::CounterexampleGenerator<>::constructConflict,
            "Construct a conflict to a prepared DTMC wrt a single formula.",
            py::arg("formula_index"), py::arg("formula_bound"), py::arg("mdp_bounds"), py::arg("mdp_quotient_state_map")
            )
        .def(
            "print_profiling",
            &storm::synthesis::CounterexampleGenerator<>::printProfiling,
            "Print profiling stats."
            )
        
        /*.def_property_readonly(
            "stats",
            [](storm::synthesis::CounterexampleGenerator<> & counterexample) {
                return counterexample.stats();
            },
            "Read stats."
        );*/
        ;

    m.def("model_check_with_hint", &modelCheckWithHint<double>, "Perform model checking using the sparse engine", py::arg("model"), py::arg("task"), py::arg("environment"), py::arg("hint_values"));
    
}

