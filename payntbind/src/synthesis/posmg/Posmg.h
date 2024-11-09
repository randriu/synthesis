#pragma once

#include "storm/models/sparse/Smg.h"
#include "storm/models/sparse/Pomdp.h"
#include <storm/adapters/RationalFunctionAdapter.h>

namespace synthesis {

/**
 * @brief A class representing Partially observable multiplayer game
 * @todo make generic with template
 */
class Posmg : public storm::models::sparse::Smg<double> {
    public:
    /**
     * @brief Construct a new Posmg object from model components
     *
     * @param components Both statePlayerIndications and observabilityClasses have to be filled
     */
    Posmg(storm::storage::sparse::ModelComponents<double> const& components);
    Posmg(storm::storage::sparse::ModelComponents<double> &&components);

    /**
     * @brief Return a vector of observatinos
     *
     * @return std::vector<uint32_t> const&
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
     *
     * @return uint64_t
     */
    uint64_t getP0ObservationCount() const;

    /**
     * @brief Get the underlying MDP
     *
     * @return storm::models::sparse::Mdp<double>
     */
    storm::models::sparse::Mdp<double> getMdp();

    /**
     * @brief Get the underlying POMDP
     *
     * @return storm::models::sparse::Pomdp<double>
     */
    storm::models::sparse::Pomdp<double> getPomdp();

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
 * @brief Create and return a Posmg object from pomdp and state indications
 *
 * @param pomdp Model information from this pomdp will be used to create the game
 * @param statePlayerIndications Vector indicating which states belong to which player
 * @return Posmg
 */
Posmg createPosmg(storm::models::sparse::Pomdp<double> pomdp,
            std::vector<storm::storage::PlayerIndex> statePlayerIndications);

/**
 * @brief Create and return a Components object based on the provided model
 *
 * @param model Properites to create the ModelComponents are taken from this model.
 * @return storm::storage::sparse::ModelComponents<double>
 */
storm::storage::sparse::ModelComponents<double> createComponents(
        storm::models::sparse::NondeterministicModel<double> const& model);

} // namespace synthesis