#include "../synthesis.h"

#include "PomdpManager.h"
#include "PomdpManagerAposteriori.h"
#include <storm/adapters/RationalNumberAdapter.h>
#include <string>

template<typename ValueType>
void bindings_pomdp_vt(py::module& m, std::string const& vtSuffix) {

    py::class_<synthesis::PomdpManager<ValueType>>(m, (vtSuffix + "PomdpManager").c_str(), "POMDP manager")
        .def(py::init<storm::models::sparse::Pomdp<ValueType> const&>(), "Constructor.", py::arg("pomdp"))
        .def("set_observation_memory_size", &synthesis::PomdpManager<ValueType>::setObservationMemorySize, "Set memory size to a selected observation.", py::arg("observation"), py::arg("memory_size"))
        .def("set_global_memory_size", &synthesis::PomdpManager<ValueType>::setGlobalMemorySize, "Set memory size to all observations.", py::arg("memory_size"))
        .def("construct_mdp", &synthesis::PomdpManager<ValueType>::constructMdp, "Unfold memory model (a priori memory update) into the POMDP.")
        .def_property_readonly("state_prototype", [](synthesis::PomdpManager<ValueType>& manager) {return manager.state_prototype;})
        .def_property_readonly("state_memory", [](synthesis::PomdpManager<ValueType>& manager) {return manager.state_memory;})
        .def_property_readonly("observation_memory_size", [](synthesis::PomdpManager<ValueType>& manager) {return manager.observation_memory_size;})
        .def_property_readonly("observation_actions", [](synthesis::PomdpManager<ValueType>& manager) {return manager.observation_actions;})
        .def_property_readonly("observation_successors", [](synthesis::PomdpManager<ValueType>& manager) {return manager.observation_successors;})
        .def_property_readonly("max_successor_memory_size", [](synthesis::PomdpManager<ValueType>& manager) {return manager.max_successor_memory_size;})
        .def_property_readonly("num_holes", [](synthesis::PomdpManager<ValueType>& manager) {return manager.num_holes;})
        .def_property_readonly("action_holes", [](synthesis::PomdpManager<ValueType>& manager) {return manager.action_holes;})
        .def_property_readonly("memory_holes", [](synthesis::PomdpManager<ValueType>& manager) {return manager.memory_holes;})
        .def_property_readonly("hole_options", [](synthesis::PomdpManager<ValueType>& manager) {return manager.hole_options;})
        .def_property_readonly("row_action_hole", [](synthesis::PomdpManager<ValueType>& manager) {return manager.row_action_hole;})
        .def_property_readonly("row_action_option", [](synthesis::PomdpManager<ValueType>& manager) {return manager.row_action_option;})
        .def_property_readonly("row_memory_hole", [](synthesis::PomdpManager<ValueType>& manager) {return manager.row_memory_hole;})
        .def_property_readonly("row_memory_option", [](synthesis::PomdpManager<ValueType>& manager) {return manager.row_memory_option;})
        ;

    py::class_<synthesis::PomdpManagerAposteriori<ValueType>>(m, (vtSuffix + "PomdpManagerAposteriori").c_str(), "POMDP manager (a posteriori)")
        .def(py::init<storm::models::sparse::Pomdp<ValueType> const&>(), "Constructor.")
        .def("set_observation_memory_size", &synthesis::PomdpManagerAposteriori<ValueType>::setObservationMemorySize)
        .def("set_global_memory_size", &synthesis::PomdpManagerAposteriori<ValueType>::setGlobalMemorySize)
        .def("construct_mdp", &synthesis::PomdpManagerAposteriori<ValueType>::constructMdp)
        .def_property_readonly("state_prototype", [](synthesis::PomdpManagerAposteriori<ValueType>& manager) {return manager.state_prototype;})
        .def_property_readonly("state_memory", [](synthesis::PomdpManagerAposteriori<ValueType>& manager) {return manager.state_memory;})
        .def_property_readonly("coloring", [](synthesis::PomdpManagerAposteriori<ValueType>& manager) {return manager.coloring;})
        .def_property_readonly("hole_num_options", [](synthesis::PomdpManagerAposteriori<ValueType>& manager) {return manager.hole_num_options;})
        .def_property_readonly("action_holes", [](synthesis::PomdpManagerAposteriori<ValueType>& manager) {return manager.action_holes;})
        .def_property_readonly("update_holes", [](synthesis::PomdpManagerAposteriori<ValueType>& manager) {return manager.update_holes;})
        ;

}

void bindings_pomdp(py::module& m) {
    bindings_pomdp_vt<double>(m, "");
    bindings_pomdp_vt<storm::RationalNumber>(m, "Exact");
}
