#include "common.h"

#include "synthesis/synthesis.h"

PYBIND11_MODULE(synthesis, m) {
    m.doc() = "Synthesis extension of Stormpy.";

#ifdef STORMPY_DISABLE_SIGNATURE_DOC
    py::options options;
    options.disable_function_signatures();
#endif

    define_synthesis(m);
}
