#include "Posmg.h"

#include "src/synthesis/translation/componentTranslations.h"

namespace synthesis {

template<typename ValueType, typename RewardModelType>
Posmg<ValueType,RewardModelType>::Posmg(storm::storage::sparse::ModelComponents<ValueType,RewardModelType> const& components)
    : storm::models::sparse::Smg<ValueType,RewardModelType>(components), observations(components.observabilityClasses.value())
{
    calculateP0ObservationCount();
}
template<typename ValueType, typename RewardModelType>
Posmg<ValueType,RewardModelType>::Posmg(storm::storage::sparse::ModelComponents<ValueType,RewardModelType> &&components)
    : storm::models::sparse::Smg<ValueType,RewardModelType>(std::move(components)), observations(components.observabilityClasses.value())
{
    calculateP0ObservationCount();
}

template<typename ValueType, typename RewardModelType>
std::vector<uint32_t> const &Posmg<ValueType,RewardModelType>::getObservations() const
{
    return observations;
}

template<typename ValueType, typename RewardModelType>
uint32_t Posmg<ValueType,RewardModelType>::getObservation(uint64_t state) const
{
    return observations.at(state);
}

template<typename ValueType, typename RewardModelType>
uint64_t Posmg<ValueType,RewardModelType>::getP0ObservationCount() const
{
    return p0ObservationCount;
}

template<typename ValueType, typename RewardModelType>
storm::models::sparse::Mdp<ValueType,RewardModelType> Posmg<ValueType,RewardModelType>::getMdp()
{
    auto components = synthesis::componentsFromModel(*this);
    return storm::models::sparse::Mdp<ValueType,RewardModelType>(std::move(components));
}

template<typename ValueType, typename RewardModelType>
storm::models::sparse::Pomdp<ValueType,RewardModelType> Posmg<ValueType,RewardModelType>::getPomdp()
{
    auto components = synthesis::componentsFromModel(*this);
    components.observabilityClasses = this->observations;
    return storm::models::sparse::Pomdp<ValueType,RewardModelType>(std::move(components));
}

template<typename ValueType, typename RewardModelType>
void Posmg<ValueType,RewardModelType>::calculateP0ObservationCount()
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

template class Posmg<double>;


template<typename ValueType, typename RewardModelType>
Posmg<ValueType,RewardModelType> posmgFromPomdp(
    storm::models::sparse::Pomdp<ValueType,RewardModelType> pomdp,
    std::vector<storm::storage::PlayerIndex> statePlayerIndications) {
    auto components = synthesis::componentsFromModel<ValueType>(pomdp);
    components.statePlayerIndications = statePlayerIndications;
    return Posmg<ValueType,RewardModelType>(components);
}

template<typename ValueType, typename RewardModelType>
Posmg<ValueType,RewardModelType> posmgFromSmg(
    storm::models::sparse::Smg<ValueType,RewardModelType> smg,
    std::optional<std::vector<uint32_t>> observabilityClasses) {
    auto components = synthesis::componentsFromModel<ValueType>(smg);
    components.observabilityClasses = observabilityClasses;
    return Posmg<ValueType,RewardModelType>(components);
}

template Posmg<double> posmgFromPomdp<double>(
    storm::models::sparse::Pomdp<double> pomdp,
    std::vector<storm::storage::PlayerIndex> statePlayerIndications);
template Posmg<double> posmgFromSmg<double>(
    storm::models::sparse::Smg<double>,
    std::optional<std::vector<uint32_t>> observabilityClasses);

} // namespace synthesis