#include "../synthesis.h"

#include "SubPomdpBuilder.h"

void bindings_translation(py::module& m) {

    py::class_<synthesis::SubPomdpBuilder<double>, std::shared_ptr<synthesis::SubPomdpBuilder<double>>>(m, "SubPomdpBuilder")
        .def(py::init<storm::models::sparse::Pomdp<double> const&>())
        .def("start_from_belief", &synthesis::SubPomdpBuilder<double>::startFromBelief)
        .def_property_readonly("state_sub_to_full", [](synthesis::SubPomdpBuilder<double>& b) {return b.state_sub_to_full;} )
        ;
}

