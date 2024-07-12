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

} // namespace synthesis