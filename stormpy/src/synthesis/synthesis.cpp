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
            "prepare_dtmc",
            &storm::synthesis::CounterexampleGenerator<>::prepareDtmc,
            "Prepare a DTMC for CE construction.",
            py::arg("dtmc"), py::arg("quotient_state_map")
            )
        .def(
            "invoke_cegis_parallel_execution",
            &storm::synthesis::CounterexampleGenerator<>::invoke_cegis_parallel_execution,
            "Invoke Cegis Parallel Execution",
            py::arg("hole_name_l2"), py::arg("option_labels_l3"), py::arg("options_l3"),
            py::arg("quotient_mdp"), py::arg("default_actions"), py::arg("action_to_hole_options"),
            // 2.point parameters
            py::arg("family_property_indices"), py::arg("specification_constraints"),
            py::arg("specification_has_optimality"), py::arg("formulea"),
            // 3.point parameters
            py::arg("sketch_spec_optimality_minimizing"), py::arg("current_optimum"),
            py::arg("current_threshold"), py::arg("sketch_spec_optimality_epsilon"),
            py::arg("sketch_spec_optimality_reward"),
            // 4.point parameters
            py::arg("ce_generator")
        )
        .def(
            "construct_conflict",
            &storm::synthesis::CounterexampleGenerator<>::constructConflict,
            "Construct a conflict to a prepared DTMC wrt a single formula.",
            py::arg("formula_index"), py::arg("formula_bound"), py::arg("mdp_bounds")
        );
        /*.def_property_readonly(
            "stats",
            [](storm::synthesis::CounterexampleGenerator<> & counterexample) {
                return counterexample.stats();
            },
            "Read stats."
        );*/
}

