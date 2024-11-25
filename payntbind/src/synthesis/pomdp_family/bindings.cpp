#include "../synthesis.h"

#include "ObservationEvaluator.h"
#include "FscUnfolder.h"
#include "GameAbstractionSolver.h"
#include "SmgAbstraction.h"

void bindings_pomdp_family(py::module& m) {

    py::class_<synthesis::ObservationEvaluator<double>>(m, "ObservationEvaluator")
        .def(py::init<storm::prism::Program &,storm::models::sparse::Model<double> const& >(), py::arg("prism"), py::arg("model"))
        .def_property_readonly("num_obs_expressions", [](synthesis::ObservationEvaluator<double>& e) {return e.num_obs_expressions;} )
        .def_property_readonly("obs_expr_label", [](synthesis::ObservationEvaluator<double>& e) {return e.obs_expr_label;} )
        .def_property_readonly("obs_expr_is_boolean", [](synthesis::ObservationEvaluator<double>& e) {return e.obs_expr_is_boolean;} )
        .def_property_readonly("num_obs_classes", [](synthesis::ObservationEvaluator<double>& e) {return e.num_obs_classes;} )
        .def_property_readonly("state_to_obs_class", [](synthesis::ObservationEvaluator<double>& e) {return e.state_to_obs_class;} )
        .def("obs_class_value", &synthesis::ObservationEvaluator<double>::observationClassValue, py::arg("obs_class"), py::arg("obs_expr"))
        .def("add_observations_to_submdp", &synthesis::ObservationEvaluator<double>::addObservationsToSubMdp, py::arg("mdp"), py::arg("state_sub_to_full"))
        ;

    py::class_<synthesis::FscUnfolder<double>>(m, "FscUnfolder")
        .def(
            py::init<storm::models::sparse::Model<double> const&,
            std::vector<uint32_t> const&,
            uint64_t,
            std::vector<uint64_t> const&>()
        )
        .def("apply_fsc", &synthesis::FscUnfolder<double>::applyFsc, py::arg("action_function"), py::arg("udate_function"))
        .def_property_readonly("product", [](synthesis::FscUnfolder<double>& m) {return m.product;} )
        .def_property_readonly("product_choice_to_choice", [](synthesis::FscUnfolder<double>& m) {return m.product_choice_to_choice;} )
        // .def_property_readonly("product_state_to_state", [](synthesis::FscUnfolder<double>& m) {return m.product_state_to_state;} )
        // .def_property_readonly("product_state_to_state_memory_action", [](synthesis::FscUnfolder<double>& m) {return m.product_state_to_state_memory_action;} )
        ;

    // m.def("randomize_action_variant", &synthesis::randomizeActionVariant<double>);
    py::class_<synthesis::GameAbstractionSolver<double>>(m, "GameAbstractionSolver")
        .def(
            py::init<
                storm::models::sparse::Model<double> const&,
                uint64_t,
                std::vector<uint64_t> const&,
                std::shared_ptr<storm::logic::Formula const>,
                bool,
                std::string const&,
                double
            >(),
            py::arg("quotient"), py::arg("num_actions"), py::arg("choice_to_action"), py::arg("formula"), py::arg("player1_maximizing"), py::arg("target_label"), py::arg("precision")
        )
        .def("solve_sg", &synthesis::GameAbstractionSolver<double>::solveSg)
        .def("solve_smg", &synthesis::GameAbstractionSolver<double>::solveSmg)
        .def_property_readonly("solution_state_values", [](synthesis::GameAbstractionSolver<double>& solver) {return solver.solution_state_values;})
        .def_property_readonly("solution_value", [](synthesis::GameAbstractionSolver<double>& solver) {return solver.solution_value;})
        .def_property_readonly("solution_state_to_player1_action", [](synthesis::GameAbstractionSolver<double>& solver) {return solver.solution_state_to_player1_action;})
        .def_property_readonly("solution_state_to_quotient_choice", [](synthesis::GameAbstractionSolver<double>& solver) {return solver.solution_state_to_quotient_choice;})
        .def("enable_profiling", &synthesis::GameAbstractionSolver<double>::enableProfiling)
        .def("print_profiling", &synthesis::GameAbstractionSolver<double>::printProfiling)
        ;

        py::class_<synthesis::SmgAbstraction<double>, std::shared_ptr<synthesis::SmgAbstraction<double>>>(m, "SmgAbstraction")
        .def(py::init<
            storm::models::sparse::Model<double> const&,
            uint64_t,
            std::vector<uint64_t> const&,
            storm::storage::BitVector const&
        >(), py::arg("model"), py::arg("num_actions"), py::arg("choice_to_action"), py::arg("choice_mask"))
        .def_readonly("smg", &synthesis::SmgAbstraction<double>::smg)
        .def_readonly("state_to_quotient_state_action", &synthesis::SmgAbstraction<double>::state_to_quotient_state_action)
        .def_readonly("choice_to_quotient_choice", &synthesis::SmgAbstraction<double>::choice_to_quotient_choice)
        ;
}
