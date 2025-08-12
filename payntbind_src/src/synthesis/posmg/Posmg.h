#pragma once

#include <storm/models/sparse/StandardRewardModel.h>
#include <storm/models/sparse/Smg.h>
#include <storm/models/sparse/Pomdp.h>
#include <storm/adapters/RationalFunctionAdapter.h>

namespace synthesis {

/**
 * @brief A class representing partially observable stochastic multiplayer game.
 */
template<class ValueType, typename RewardModelType = storm::models::sparse::StandardRewardModel<ValueType>>
class Posmg : public storm::models::sparse::Smg<ValueType,RewardModelType> {
    public:
    /**
     * @brief Construct a new Posmg object from model components
     *
     * @param components Both statePlayerIndications and observabilityClasses have to be filled
     */
    Posmg(storm::storage::sparse::ModelComponents<ValueType,RewardModelType> const& components);
    Posmg(storm::storage::sparse::ModelComponents<ValueType,RewardModelType>&& components);

    /**
     * @brief Return a vector of observatinos
     */
    std::vector<uint32_t> const &getObservations() const;

    /**
     * @brief Return the observation of a given state
     *
     * @param state Specifies the state
     * @return uint32_t Return the observation of a given state
     */
    uint32_t getObservation(uint64_t state) const;

    /**
     * @brief Return number of observations corresponding to player 0 states.
     */
    uint64_t getP0ObservationCount() const;

    /**
     * @brief Get the underlying MDP
     */
    storm::models::sparse::Mdp<ValueType,RewardModelType> getMdp();

    /**
     * @brief Get the underlying POMDP
     */
    storm::models::sparse::Pomdp<ValueType,RewardModelType> getPomdp();

    private:
    /**
     * @brief Calculate number of player 0 observations and store it in p0ObservationCount
     */
    void calculateP0ObservationCount();

    /** Vector of observations. Observation (value) at index i is the observation of state i */
    std::vector<uint32_t> observations;

    /** Number of observations corresponding to player 0 states */
    uint64_t p0ObservationCount;
};

/**
 * @brief Create a POSMG from a POMDP and state indications.
 * @param pomdp Base POMDP
 * @param statePlayerIndications Vector indicating which states belong to which player
 */
template<typename ValueType,typename RewardModelType = storm::models::sparse::StandardRewardModel<ValueType>>
Posmg<ValueType,RewardModelType> posmgFromPomdp(
    storm::models::sparse::Pomdp<ValueType,RewardModelType> pomdp,
    std::vector<storm::storage::PlayerIndex> statePlayerIndications);

/**
 * @brief Create a POSMG from an SMG and observability classes.
 * @param smg Base SMG
 * @param observabilityClasses for each state an observability class
 */
template<typename ValueType,typename RewardModelType = storm::models::sparse::StandardRewardModel<ValueType>>
Posmg<ValueType,RewardModelType> posmgFromSmg(
    storm::models::sparse::Smg<ValueType,RewardModelType> smg,
    std::optional<std::vector<uint32_t>> observabilityClasses);

} // namespace synthesis