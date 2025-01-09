#include "../synthesis.h"

#include "storm/storage/Scheduler.h"

namespace synthesis
{
    storm::storage::Scheduler<double> createScheduler(uint_fast64_t numberOfModelStates) {
        return storm::storage::Scheduler<double>(numberOfModelStates);
    }
}

void bindings_storage(py::module& m) {
    
    m.def("create_scheduler", &synthesis::createScheduler, py::arg("number_of_model_states"));
}