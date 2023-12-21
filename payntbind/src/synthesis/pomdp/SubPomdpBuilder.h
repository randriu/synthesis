#pragma once

#include "storm/models/sparse/Pomdp.h"
#include "storm/logic/Formula.h"

namespace synthesis {

    class SubPomdpBuilder {

    public:

        /**
         * Prepare sub-POMDP construction wrt a given canonic POMDP. New
         * sub-POMDP will be model checked using property
         * R[reward_name]=? [F target_label].
         */
        SubPomdpBuilder(
            storm::models::sparse::Pomdp<double> const& pomdp,
            std::string const& reward_name,
            std::string const& target_label
        );

        /**
         * If <1 discount factor is set, each action will redirect 1-df probability to the (target) sink state.
         */
        void setDiscountFactor(double discount_factor) {
            this->discount_factor = discount_factor;
        }

        /**
         * Set which observations to keep in the restricted sub-POMDP. All states reachable from the initial belief
         * having relevant observation will be included in the sub-POMDP.
         */
        void setRelevantObservations(
            storm::storage::BitVector const& relevant_observations,
            std::map<uint64_t,double> const& initial_belief
        );

        /** Set which states to keep in the restricted sub-POMDP. */
        void setRelevantStates(storm::storage::BitVector const& relevant_states);

        /**
         * Construct a POMDP restriction containing the following states:
         * - fresh initial state to simulate initial distribution
         * - fresh sink state (labeled as target)
         * - relevant states
         * - frontier states having single action going to sink state with probability 1 and reward 0
         * @param initial_belief initial probability distribution
         */
        std::shared_ptr<storm::models::sparse::Pomdp<double>> restrictPomdp(
            std::map<uint64_t,double> const& initial_belief
        );

        // observations relevant for the current restriction
        storm::storage::BitVector relevant_observations;
        // states relevant for the current restriction
        storm::storage::BitVector relevant_states;
        // irrelevant states reachable from the relevant ones in one step
        storm::storage::BitVector frontier_states;

        // for each state of a sub-POMDP its index in the full POMDP; fresh states (initial & sink) are associated
        // with a number of states in the POMDP
        std::vector<uint64_t> state_sub_to_full;
        // for each state of a full POMDP its index in the sub-POMDP; unreachable states are associated with
        // a number of states in the sub-POMDP
        std::vector<uint64_t> state_full_to_sub;
        // nondeterminstic choice indices of the sub-POMDP
        std::vector<uint64_t> subpomdp_row_groups;

    private:

        // original POMDP
        storm::models::sparse::Pomdp<double> const& pomdp;
        // name of the investigated reward
        std::string const reward_name;
        // label assigned to target states
        std::string const target_label;
        // for each state, a list of immediate successors (excluding state itself)
        std::vector<std::set<uint64_t>> reachable_successors;
        // discount factor to be applied to the transformed POMDP
        double discount_factor = 1;

        // number of states in the sub-POMDP
        uint64_t num_states_subpomdp;
        // number of rows in the sub-POMDP
        uint64_t num_rows_subpomdp;

        // index of the new initial state
        const uint64_t initial_state = 0;
        // index of the new sink state
        const uint64_t sink_state = 1;
        // label associated with initial distribution as well as shortcut actions
        const std::string empty_label = "";
        
        // upon setting vector of relevant states, identify frontier states
        void collectFrontierStates();
        // create sub-to-full and full-to-sub state maps
        void constructStates();

        storm::storage::SparseMatrix<double> constructTransitionMatrix(
            std::map<uint64_t,double> const& initial_belief
        );
        storm::models::sparse::StateLabeling constructStateLabeling();
        storm::models::sparse::ChoiceLabeling constructChoiceLabeling();
        std::vector<uint32_t> constructObservabilityClasses();
        storm::models::sparse::StandardRewardModel<double> constructRewardModel();
    

    };
}