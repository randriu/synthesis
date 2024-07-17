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
    std::vector<uint32_t> observations;
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