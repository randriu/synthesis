#include "../synthesis.h"
#include "SubPomdpBuilder.h"

#include "src/synthesis/translation/componentTranslations.h"
#include "src/synthesis/translation/choiceTransformation.h"

#include <storm/exceptions/InvalidModelException.h>
#include <storm/utility/builder.h>
#include <storm/transformer/SubsystemBuilder.h>

void bindings_translation(py::module& m) {

    m.def("computeChoiceDestinations", &synthesis::computeChoiceDestinations<double>);
    m.def("addMissingChoiceLabels", &synthesis::addMissingChoiceLabelsModel<double>);
    m.def("assertChoiceLabelingIsCanonic", &synthesis::assertChoiceLabelingIsCanonic);
    m.def("extractActionLabels", &synthesis::extractActionLabels<double>);
    m.def("enableAllActions", py::overload_cast<storm::models::sparse::Model<double> const&>(&synthesis::enableAllActions<double>));
    m.def("restoreActionsInAbsorbingStates", &synthesis::restoreActionsInAbsorbingStates<double>);

    py::class_<synthesis::SubPomdpBuilder<double>, std::shared_ptr<synthesis::SubPomdpBuilder<double>>>(m, "SubPomdpBuilder")
        .def(py::init<storm::models::sparse::Pomdp<double> const&>())
        .def("start_from_belief", &synthesis::SubPomdpBuilder<double>::startFromBelief)
        .def_property_readonly("state_sub_to_full", [](synthesis::SubPomdpBuilder<double>& b) {return b.state_sub_to_full;} )
        ;
}

