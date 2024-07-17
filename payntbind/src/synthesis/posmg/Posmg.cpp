#include "Posmg.h"

namespace synthesis {

    Posmg::Posmg(storm::storage::sparse::ModelComponents<double> const& components)
        : Smg<double>(components), observations(components.observabilityClasses.value())
    {

    }
    Posmg::Posmg(storm::storage::sparse::ModelComponents<double> &&components)
        : Smg<double>(std::move(components)), observations(components.observabilityClasses.value())
    {

    }

    storm::models::sparse::Mdp<double> Posmg::getMdp()
    {
        auto components = createComponents(*this);

        return storm::models::sparse::Mdp<double>(std::move(components));
    }

    storm::models::sparse::Pomdp<double> Posmg::getPomdp()
    {
        auto components = createComponents(*this);
        components.observabilityClasses = this->observations;

        return storm::models::sparse::Pomdp<double>(std::move(components));
    }

    Posmg createPosmg(storm::models::sparse::Pomdp<double> pomdp,
                      std::vector<storm::storage::PlayerIndex> statePlayerIndications)
    {
        auto components = createComponents(pomdp);

        // Smg components
        components.statePlayerIndications = statePlayerIndications;
        // todo playerNameToIndexMap ??

        // Pomdp components
        components.observabilityClasses = pomdp.getObservations();
        if (pomdp.hasObservationValuations())
        {
            components.observationValuations = pomdp.getObservationValuations();
        }

        return Posmg(components);
    }

    storm::storage::sparse::ModelComponents<double> createComponents(
            storm::models::sparse::NondeterministicModel<double> const& model)
    {
        storm::storage::sparse::ModelComponents<double> components(
            model.getTransitionMatrix(),
            model.getStateLabeling(),
            model.getRewardModels()
        );
        if (model.hasChoiceLabeling()) {
            components.choiceLabeling = model.getChoiceLabeling();
        }
        if (model.hasStateValuations()) {
            components.stateValuations = model.getStateValuations();
        }
        if (model.hasChoiceOrigins()) {
            components.choiceOrigins = model.getChoiceOrigins();
        }

        return components;
    }

} // namespace synthesis