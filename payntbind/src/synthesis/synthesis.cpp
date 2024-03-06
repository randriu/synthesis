#include "synthesis.h"

void define_synthesis(py::module& m) {
    define_helpers(m);

    bindings_translation(m);
    bindings_pomdp(m);
    bindings_decpomdp(m);
    bindings_counterexamples(m);
    bindings_pomdp_family(m);

    bindings_coloring(m);
}

