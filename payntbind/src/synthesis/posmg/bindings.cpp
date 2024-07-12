#include "../synthesis.h"

#include "Posmg.h"

void bindings_posmg(py::module &m) {
    py::class_<synthesis::Posmg, std::shared_ptr<synthesis::Posmg>>(m, "Posmg");
    //    .def(py::init<storm::storage::sparse::ModelComponents<double> const&>(), py::arg("components"))
    //    .def(py::init<storm::storage::sparse::ModelComponents<double> &&>(), py::arg("components"));

    m.def("create_posmg", &synthesis::createPosmg, py::arg("pomdp"), py::arg("state_player_indications"));
}