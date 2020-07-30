#include <algorithm>

#include "research.h"

#include "storm/research/Counterexample.h"

// Define python bindings
void define_research(py::module& m) {

    // Counterexample generation
    py::class_<storm::research::Counterexample<>>(
        m, "SynthesisResearchCounterexample", "[synthesis research] Counterexample generation"
    )
        .def(
            py::init<
                uint_fast64_t,
                storm::logic::Formula const&,
                storm::models::sparse::Mdp<double> const&,
                storm::modelchecker::ExplicitQuantitativeCheckResult<double> const&
            >(),
            "Preprocess the quotiendt MDP.",
            py::arg("expanded_per_iter"), py::arg("formula"), py::arg("mdp"), py::arg("mdp_result")
        )
        .def(
            "construct",
            &storm::research::Counterexample<>::construct,
            "Construct a minimal counterexample to a given DTMC.",
            py::arg("dtmc"), py::arg("dtmc_result")
        )
        .def_property_readonly(
            "stats",
            [](storm::research::Counterexample<> & counterexample) {
                return counterexample.stats();
            },
            "Read stats."
        );  
}
