#include "../synthesis.h"

#include "PomdpManager.h"
#include "PomdpManagerAposteriori.h"
#include "SubPomdpBuilder.h"

void bindings_pomdp(py::module& m) {

    py::class_<synthesis::PomdpManager<double>>(m, "PomdpManager", "POMDP manager")
        .def(py::init<storm::models::sparse::Pomdp<double> const&>(), "Constructor.", py::arg("pomdp"))
        .def("set_observation_memory_size", &synthesis::PomdpManager<double>::setObservationMemorySize, "Set memory size to a selected observation.", py::arg("observation"), py::arg("memory_size"))
        .def("set_global_memory_size", &synthesis::PomdpManager<double>::setGlobalMemorySize, "Set memory size to all observations.", py::arg("memory_size"))
        .def("construct_mdp", &synthesis::PomdpManager<double>::constructMdp, "Unfold memory model (a priori memory update) into the POMDP.")
        .def_property_readonly("state_prototype", [](synthesis::PomdpManager<double>& manager) {return manager.state_prototype;})
        .def_property_readonly("state_memory", [](synthesis::PomdpManager<double>& manager) {return manager.state_memory;})
        .def_property_readonly("observation_memory_size", [](synthesis::PomdpManager<double>& manager) {return manager.observation_memory_size;})
        .def_property_readonly("observation_actions", [](synthesis::PomdpManager<double>& manager) {return manager.observation_actions;})
        .def_property_readonly("observation_successors", [](synthesis::PomdpManager<double>& manager) {return manager.observation_successors;})
        .def_property_readonly("max_successor_memory_size", [](synthesis::PomdpManager<double>& manager) {return manager.max_successor_memory_size;})
        .def_property_readonly("num_holes", [](synthesis::PomdpManager<double>& manager) {return manager.num_holes;})
        .def_property_readonly("action_holes", [](synthesis::PomdpManager<double>& manager) {return manager.action_holes;})
        .def_property_readonly("memory_holes", [](synthesis::PomdpManager<double>& manager) {return manager.memory_holes;})
        .def_property_readonly("hole_options", [](synthesis::PomdpManager<double>& manager) {return manager.hole_options;})
        .def_property_readonly("row_action_hole", [](synthesis::PomdpManager<double>& manager) {return manager.row_action_hole;})
        .def_property_readonly("row_action_option", [](synthesis::PomdpManager<double>& manager) {return manager.row_action_option;})
        .def_property_readonly("row_memory_hole", [](synthesis::PomdpManager<double>& manager) {return manager.row_memory_hole;})
        .def_property_readonly("row_memory_option", [](synthesis::PomdpManager<double>& manager) {return manager.row_memory_option;})
        ;

    py::class_<synthesis::PomdpManagerAposteriori<double>>(m, "PomdpManagerAposteriori", "POMDP manager (a posteriori)")
        .def(py::init<storm::models::sparse::Pomdp<double> const&>(), "Constructor.")
        .def("set_observation_memory_size", &synthesis::PomdpManagerAposteriori<double>::setObservationMemorySize)
        .def("set_global_memory_size", &synthesis::PomdpManagerAposteriori<double>::setGlobalMemorySize)
        .def("construct_mdp", &synthesis::PomdpManagerAposteriori<double>::constructMdp)
        .def_property_readonly("state_prototype", [](synthesis::PomdpManagerAposteriori<double>& manager) {return manager.state_prototype;})
        .def_property_readonly("state_memory", [](synthesis::PomdpManagerAposteriori<double>& manager) {return manager.state_memory;})
        .def_property_readonly("coloring", [](synthesis::PomdpManagerAposteriori<double>& manager) {return manager.coloring;})
        .def_property_readonly("hole_num_options", [](synthesis::PomdpManagerAposteriori<double>& manager) {return manager.hole_num_options;})
        .def_property_readonly("action_holes", [](synthesis::PomdpManagerAposteriori<double>& manager) {return manager.action_holes;})
        .def_property_readonly("update_holes", [](synthesis::PomdpManagerAposteriori<double>& manager) {return manager.update_holes;})
        ;

    py::class_<synthesis::SubPomdpBuilder, std::shared_ptr<synthesis::SubPomdpBuilder>>(m, "SubPomdpBuilder")
        .def(py::init<storm::models::sparse::Pomdp<double> const&, std::string const&, std::string const&>())
        .def("set_discount_factor", &synthesis::SubPomdpBuilder::setDiscountFactor)
        .def("set_relevant_observations", &synthesis::SubPomdpBuilder::setRelevantObservations)
        .def_property_readonly("relevant_states", [](synthesis::SubPomdpBuilder& builder) {return builder.relevant_states;})
        .def_property_readonly("frontier_states", [](synthesis::SubPomdpBuilder& builder) {return builder.frontier_states;})
        .def("restrict_pomdp", &synthesis::SubPomdpBuilder::restrictPomdp)
        .def_property_readonly("state_sub_to_full", [](synthesis::SubPomdpBuilder& builder) {return builder.state_sub_to_full;})
        .def_property_readonly("state_full_to_sub", [](synthesis::SubPomdpBuilder& builder) {return builder.state_full_to_sub;})
        ;
}

