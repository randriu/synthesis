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
        .def(py::init<synthesis::Posmg const&>(), py::arg("posmg"))
        .def("construct_mdp", &synthesis::PosmgManager::constructMdp)
        .def("get_observation_mapping", &synthesis::PosmgManager::getObservationMapping)
        .def("set_observation_memory_size", &synthesis::PosmgManager::setObservationMemorySize,
            py::arg("observation"), py::arg("memory_size"));
}
