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

    Posmg createPosmg(storm::models::sparse::Pomdp<double> pomdp,
                      std::vector<storm::storage::PlayerIndex> statePlayerIndications)
    {
        // Model components
        storm::storage::sparse::ModelComponents<double> components(
            std::move(pomdp.getTransitionMatrix()),
            std::move(pomdp.getStateLabeling()),
            std::move(pomdp.getRewardModels())
        );
        if (pomdp.hasChoiceLabeling())
        {
            components.choiceLabeling = pomdp.getChoiceLabeling();
        }
        if (pomdp.hasStateValuations())
        {
            components.stateValuations = pomdp.getStateValuations();
        }
        if (pomdp.hasChoiceOrigins())
        {
            components.choiceOrigins = pomdp.getChoiceOrigins();
        }

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

} // namespace synthesis