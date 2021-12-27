#include "synthesis.h"

#include "storm-synthesis/synthesis/Counterexample.h"

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
            "set_mdp_bounds",
            &storm::synthesis::CounterexampleGenerator<>::setMdpBounds,
            "Set MDP bounds before analyzing DTMCs in the subfamily.",
            py::arg("mdp_bounds")
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
            py::arg("formula_index"), py::arg("formula_bound"), py::arg("use_bounds")
        );
        /*.def_property_readonly(
            "stats",
            [](storm::synthesis::CounterexampleGenerator<> & counterexample) {
                return counterexample.stats();
            },
            "Read stats."
        );*/
}

