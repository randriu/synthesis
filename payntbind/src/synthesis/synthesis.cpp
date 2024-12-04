#include "synthesis.h"

void define_synthesis(py::module& m) {
    define_helpers(m);

    bindings_translation(m);
    bindings_pomdp(m);
    bindings_decpomdp(m);
    bindings_counterexamples(m);
    bindings_pomdp_family(m);

    bindings_coloring(m);

    #ifndef DISABLE_SMG
    bindings_smg(m);
    bindings_posmg(m);
    #endif // DISABLE_SMG
}