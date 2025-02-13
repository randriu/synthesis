#include "../synthesis.h"
#include "SubPomdpBuilder.h"

#include "src/synthesis/translation/componentTranslations.h"
#include "src/synthesis/translation/choiceTransformation.h"
#include <storm/adapters/RationalNumberAdapter.h>

template <typename ValueType>
void bindings_translation_vt(py::module& m, std::string const& vtSuffix) {

    m.def(("computeChoiceDestinations" + vtSuffix).c_str(), &synthesis::computeChoiceDestinations<ValueType>);
    m.def(("addMissingChoiceLabels" + vtSuffix).c_str(), &synthesis::addMissingChoiceLabelsModel<ValueType>);
    m.def(("assertChoiceLabelingIsCanonic" + vtSuffix).c_str(), &synthesis::assertChoiceLabelingIsCanonic);
    m.def(("extractActionLabels" + vtSuffix).c_str(), &synthesis::extractActionLabels<ValueType>);
    m.def(("enableAllActions" + vtSuffix).c_str(), py::overload_cast<storm::models::sparse::Model<ValueType> const&>(&synthesis::enableAllActions<ValueType>));
    m.def(("restoreActionsInAbsorbingStates" + vtSuffix).c_str(), &synthesis::restoreActionsInAbsorbingStates<ValueType>);
    m.def(("addDontCareAction" + vtSuffix).c_str(), &synthesis::addDontCareAction<ValueType>);
    m.def(("createModelUnion" + vtSuffix).c_str(), &synthesis::createModelUnion<ValueType>);

    py::class_<synthesis::SubPomdpBuilder<ValueType>, std::shared_ptr<synthesis::SubPomdpBuilder<ValueType>>>(m, ("SubPomdpBuilder" + vtSuffix).c_str())
        .def(py::init<storm::models::sparse::Pomdp<ValueType> const&>())
        .def("start_from_belief", &synthesis::SubPomdpBuilder<ValueType>::startFromBelief)
        .def_property_readonly("state_sub_to_full", [](synthesis::SubPomdpBuilder<ValueType>& b) {return b.state_sub_to_full;} )
        ;
}

void bindings_translation(py::module& m) {
    bindings_translation_vt<double>(m, "");
    bindings_translation_vt<storm::RationalNumber>(m, "Exact");
}
