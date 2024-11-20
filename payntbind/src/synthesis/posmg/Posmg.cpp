#include "Posmg.h"

namespace synthesis {

    Posmg::Posmg(storm::storage::sparse::ModelComponents<double> const& components)
        : Smg<double>(components), observations(components.observabilityClasses.value())
    {
        calculateP0ObservationCount();
    }
    Posmg::Posmg(storm::storage::sparse::ModelComponents<double> &&components)
        : Smg<double>(std::move(components)), observations(components.observabilityClasses.value())
    {
        calculateP0ObservationCount();
    }

    std::vector<uint32_t> const &Posmg::getObservations() const
    {
        return observations;
    }

    uint32_t Posmg::getObservation(uint64_t state) const
    {
        return observations.at(state);
    }

    uint64_t Posmg::getP0ObservationCount() const
    {
        return p0ObservationCount;
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

    void Posmg::calculateP0ObservationCount()
    {
        // For now, optimizing player always has index 0.
        // If we need to optimize for another player or for more than one player,
        // we can for example add a parameter to this method or add a 'optimizingPlayer' property.
        uint64_t optimizingPlayer = 0;

        auto stateCount = this->getNumberOfStates();
        auto statePlayerIndications = this->getStatePlayerIndications();
        std::set<uint32_t> p0Observations;

        for (uint64_t state = 0; state < stateCount; state++)
        {
            if (statePlayerIndications[state] == optimizingPlayer)
            {
                auto observation = observations[state];
                p0Observations.insert(observation);
            }
        }

        p0ObservationCount = p0Observations.size();
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