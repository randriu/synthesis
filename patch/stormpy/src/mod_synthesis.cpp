#include "common.h"

#include "synthesis/synthesis.h"

PYBIND11_MODULE(core, m) {
    m.doc() = "core";

#ifdef STORMPY_DISABLE_SIGNATURE_DOC
    py::options options;
    options.disable_function_signatures();
#endif

    define_synthesis(m);
}
