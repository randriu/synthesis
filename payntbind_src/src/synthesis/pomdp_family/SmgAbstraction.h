#pragma once

#include <storm/models/sparse/Model.h>
#include <storm/models/sparse/Smg.h>

namespace synthesis {

/**
 * SMG abstraction for MDP sketch. States of Player 0 are the states of the quotient. In each state s, Player 0
 * has picks action a, which leads to state (s,a) of Player 1. In state (s,a), Player 1 chooses the color of a
 * to be executed.
 */
template<typename ValueType>
class SmgAbstraction {
public:

    /**
     * Create game abstraction for the sub-MDP.
     * @param quotient The quotient MDP. If the quotient is a POMDP, then @ref smg can be recast to a Posmg.
     * @param quotient_num_action The total number of distinct actions in the quotient.
     * @param choice_to_action For each row of the quotient, the associated action.
     * @param quotient_choice_mask Choices of the quotient that remained in the sub-MDP.
     */
    SmgAbstraction(
        storm::models::sparse::Model<ValueType> const& quotient,
        uint64_t quotient_num_actions,
        std::vector<uint64_t> const& choice_to_action,
        storm::storage::BitVector const& quotient_choice_mask
    );

    /** The game. */
    std::shared_ptr<storm::models::sparse::Smg<ValueType>> smg;
    /**
     * For each state s of the game, the corresponding (s,a) pair.
     * @note States of Player 0 are encoded as (s,num_actions).
     */
    std::vector<std::pair<uint64_t,uint64_t>> state_to_quotient_state_action;
    /**
     * For each choice of the game, the corresponding choice in the quotient.
     * @note Choice of Player 0 executing an action is mapped to its arbitrary variant.
     */
    std::vector<uint64_t> choice_to_quotient_choice;
};

}
