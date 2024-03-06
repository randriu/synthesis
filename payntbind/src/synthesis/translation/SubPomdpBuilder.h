#pragma once

#include "src/synthesis/translation/ItemTranslator.h"

#include <storm/models/sparse/Pomdp.h>

namespace synthesis {

    template<typename ValueType>
    class SubPomdpBuilder {

    public:

        /** Prepare sub-POMDP construction wrt a given canonic POMDP. */
        SubPomdpBuilder(storm::models::sparse::Pomdp<ValueType> const& pomdp);

        /**
         * Construct a POMDP that starts in a fresh state in which a given initial belief is simulated. The new initial
         * state is marked with a fresh observation and observation valuations are not preserved, otherwise the
         * sub-POMDP is unchanged.
         * @param initial_belief initial probability distribution
         */
        std::shared_ptr<storm::models::sparse::Pomdp<ValueType>> startFromBelief(
            std::map<uint64_t,ValueType> const& initial_belief
        );

        /**
         * Sub-POMDP-to-POMDP state mapping. Fresh states have an invalid value
         * equal to the number of states in the POMDP.
         */
        std::vector<uint64_t> state_sub_to_full;

    private:

        /** The original POMDP. */
        storm::models::sparse::Pomdp<ValueType> const& pomdp;
        /** POMDP-to-sub-POMDP state translator. */
        ItemTranslator state_translator;
        /** POMDP-to-sub-POMDP choice translator. */
        ItemTranslator choice_translator;

        /**
         * Update \p state_translator and \p choice_translator to include translation of the state and its choices,
         * respectively.
         */
        void translateState(uint64_t state);
        /** Translate states reachable from the given initial state. */
        void collectReachableStates(uint64_t initial_state);
        
        void clearMemory();

    };
}