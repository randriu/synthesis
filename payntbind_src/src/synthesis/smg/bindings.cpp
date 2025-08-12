#include "../synthesis.h"

#include "smgModelChecker.h"

void bindings_smg(py::module& m) {
    m.def("model_check_smg", &synthesis::modelCheckSmg<double>, py::arg("smg"), py::arg("formula"), py::arg("only_initial_states") = false, py::arg("set_produce_schedulers") = true, py::arg("env") = storm::Environment() );
}
