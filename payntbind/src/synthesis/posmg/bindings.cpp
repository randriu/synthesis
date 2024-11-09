#include "../synthesis.h"

#include "Posmg.h"
#include "PosmgManager.h"
#include "storm/models/sparse/Smg.h"

void bindings_posmg(py::module &m) {
    py::class_<synthesis::Posmg, std::shared_ptr<synthesis::Posmg>, storm::models::sparse::Smg<double>>(m, "Posmg")
    //    .def(py::init<storm::storage::sparse::ModelComponents<double> const&>(), py::arg("components"))
    //    .def(py::init<storm::storage::sparse::ModelComponents<double> &&>(), py::arg("components"));
        .def("get_observations", &synthesis::Posmg::getObservations)
        .def("get_p0_observation_count", &synthesis::Posmg::getP0ObservationCount)
        .def("get_mdp", &synthesis::Posmg::getMdp)
        .def("get_pomdp", &synthesis::Posmg::getPomdp)
        // this binding (calculation) is done in stormpy for mdp, but posmg doesn't inherit from mdp, so it is also copied here
        .def("get_nr_available_actions", [](synthesis::Posmg const& posmg, uint64_t stateIndex)
            { return posmg.getNondeterministicChoiceIndices()[stateIndex+1] - posmg.getNondeterministicChoiceIndices()[stateIndex] ; },
             py::arg("state"))
        // same as ^
        .def("get_choice_index", [](synthesis::Posmg const& posmg, uint64_t state, uint64_t actOff)
            { return posmg.getNondeterministicChoiceIndices()[state]+actOff; },
             py::arg("state"), py::arg("action_offset"), "gets the choice index for the offset action from the given state.");


    m.def("create_posmg", &synthesis::createPosmg, py::arg("pomdp"), py::arg("state_player_indications"));

    py::class_<synthesis::PosmgManager, std::shared_ptr<synthesis::PosmgManager>>(m, "PosmgManager")
        .def(py::init<synthesis::Posmg const&, uint64_t>(), py::arg("posmg"), py::arg("optimizing_player"))
        .def("construct_mdp", &synthesis::PosmgManager::constructMdp)
        .def("get_observation_mapping", &synthesis::PosmgManager::getObservationMapping)
        .def("set_observation_memory_size", &synthesis::PosmgManager::setObservationMemorySize,
            py::arg("observation"), py::arg("memory_size"))
        .def("get_state_player_indications", &synthesis::PosmgManager::getStatePlayerIndications)
        .def("get_action_count", &synthesis::PosmgManager::getActionCount, py::arg("state"))
        .def_property_readonly("state_prototype", [](synthesis::PosmgManager& manager) {return manager.statePrototype;})
        .def_property_readonly("state_memory", [](synthesis::PosmgManager& manager) {return manager.stateMemory;})
        .def_property_readonly("observation_memory_size", [](synthesis::PosmgManager& manager) {return manager.optPlayerObservationMemorySize;})
        .def_property_readonly("observation_actions", [](synthesis::PosmgManager& manager) {return manager.optPlayerObservationActions;})
        .def_property_readonly("observation_successors", [](synthesis::PosmgManager& manager) {return manager.succesors;})
        .def_property_readonly("max_successor_memory_size", [](synthesis::PosmgManager& manager) {return manager.maxSuccesorDuplicateCount;})
        .def_property_readonly("num_holes", [](synthesis::PosmgManager& manager) {return manager.holeCount;})
        .def_property_readonly("action_holes", [](synthesis::PosmgManager& manager) {return manager.actionHoles;})
        .def_property_readonly("memory_holes", [](synthesis::PosmgManager& manager) {return manager.memoryHoles;})
        .def_property_readonly("hole_options", [](synthesis::PosmgManager& manager) {return manager.holeOptionCount;})
        .def_property_readonly("row_action_hole", [](synthesis::PosmgManager& manager) {return manager.rowActionHole;})
        .def_property_readonly("row_action_option", [](synthesis::PosmgManager& manager) {return manager.rowActionOption;})
        .def_property_readonly("row_memory_hole", [](synthesis::PosmgManager& manager) {return manager.rowMemoryHole;})
        .def_property_readonly("row_memory_option", [](synthesis::PosmgManager& manager) {return manager.rowMemoryOption;})
        ;

}
