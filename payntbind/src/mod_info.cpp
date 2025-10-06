#include "common.h"
#include "storm-version-info/storm-version.h"

PYBIND11_MODULE(_info, m) {
    m.doc() = "Storm information";

#ifdef STORMPY_DISABLE_SIGNATURE_DOC
    py::options options;
    options.disable_function_signatures();
#endif

}
