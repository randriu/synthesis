#include "../synthesis.h"

#include "MemoryUnfolder.h"
#include <storm/adapters/RationalNumberAdapter.h>

void bindings_mdp_family(py::module& m) {

    m.def("constructUnfoldedModel", 
        &synthesis::constructUnfoldedModel<double>,
        "Construct an unfolded MDP from a given MDP and memory size.",
        py::arg("mdp"), py::arg("memory_size")
    );

    m.def("constructUnfoldedModelExact", 
        &synthesis::constructUnfoldedModel<storm::RationalNumber>,
        "Construct an unfolded MDP from a given MDP and memory size.",
        py::arg("mdp"), py::arg("memory_size")
    );

}
