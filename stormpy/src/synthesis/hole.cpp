#include "synthesis.h"

#include "storm-synthesis/synthesis/Hole.h"

// Define python bindings
void define_hole(py::module& m) {

    py::class_<storm::synthesis::Hole>(
        m, "Hole", "Representation of Hole object used in python"
    )
        .def(
            py::init<
                std::string,
                std::vector<int>,
                std::vector<int>
            >(),
            "Constructor.",
            py::arg("name"), py::arg("option_labels"),
            py::arg("options"));
}

