// author: Roman Andriushchenko

#ifndef STORM_RESEARCH_COUNTEREXAMPLE_H
#define STORM_RESEARCH_COUNTEREXAMPLE_H

#include "storm/storage/jani/Model.h"
#include "storm/logic/Formula.h"
#include "storm/models/sparse/Mdp.h"
#include "storm/modelchecker/results/ExplicitQuantitativeCheckResult.h"

#include "storm/models/sparse/Dtmc.h"
#include "storm/utility/Stopwatch.h"

namespace storm {
    namespace research {

        /*class MdpStateInfo {
        public:
            double bound;
            bool target;

            MdpStateInfo(double bound, bool target);
        };*/

        template<typename ValueType = double, typename StateType = uint_fast64_t>
        class Counterexample {
        public:

            /*!
             * Preprocess the quotient MDP and its lower bound on the reachability probability before constructing counterexamples from various DTMCs.
             * @param program jani program mdp was made from
             * @param relevant_holes a set holes relevant in the family
             * @param formula Operator formula to check.
             * @param mdp The quotient MDP.
             * @param mdp_result Lower (safety) or upper (liveness) bound on the formula satisfiability for the quotient MDP.
             */
            Counterexample(
                storm::jani::Model const& program,
                storm::storage::FlatSet<std::string> const& family_relevant_holes,
                storm::logic::Formula const& formula,
                storm::models::sparse::Mdp<ValueType> const& mdp,
                storm::modelchecker::ExplicitQuantitativeCheckResult<ValueType> const& mdp_result
                );

            /*!
             * Construct a minimal counterexample to a given DTMC via state exploration.
             * @param dtmc A DTMC refuting the safety formula. It is assumed that the state space of the DTMC is topologically ordered.
             * @param dtmc Model checking result for this DTMC.
             * @param expanded_per_iter Number of states to expand before each model checking.
             * @param subchains_checked_limit Number of suchains to check before accelerating CE construction.
             * @return A set of critical edges.
             */
            storm::storage::FlatSet<StateType> constructViaStates(
                storm::models::sparse::Dtmc<ValueType> const& dtmc,
                storm::modelchecker::ExplicitQuantitativeCheckResult<ValueType> const& dtmc_result,
                uint_fast64_t expanded_per_iter,
                uint_fast64_t subchains_checked_limit
                );

            /*!
             * Construct a minimal counterexample to a given DTMC via hole exploration.
             * @param dtmc A DTMC refuting the safety formula. It is assumed that the state space of the DTMC is topologically ordered.
             * @param use_mdp_bounds If true, mdp bounds will be used for CE construction.
             * @return A set of critical holes.
             */
            storm::storage::FlatSet<std::string> constructViaHoles(
                storm::models::sparse::Dtmc<ValueType> const& dtmc,
                bool use_mdp_bounds
                );


            /*!
             * @return A profiling vector.
             */
            std::vector<double> stats();

        private:
            
            // A set of holes relevant in this family
            storm::storage::FlatSet<std::string> const& family_relevant_holes;
            // Maps edges to relevant holes
            std::map<uint_fast64_t, std::set<std::string>> edge2holes;

            // For each state valuation, a bound on the reachability probability and a flag whether this state is target one
            // std::map<std::string, ValueType> mdp_bound;
            // std::map<std::string, bool> mdp_target;
            std::map<std::string const, std::pair<ValueType,bool>> mdp_info;
            // std::map<storm::storage::sparse::StateValuations::StateValuation, std::pair<ValueType,bool>, storm::storage::sparse::StateValuations::StateValuationLess> mdp_info;
            
            // Formula type: safety (<,<=) or liveness (>,>=)
            bool formula_safety;
            // Target label for sub-dtmcs
            std::string target_label = "target";
            // Modified operator formula to apply to sub-dtmcs: P~?[F "target"]
            std::shared_ptr<storm::logic::Formula> formula;
            
            // Profiling
            storm::utility::Stopwatch total;
            storm::utility::Stopwatch mdp_preprocessing;
            storm::utility::Stopwatch dtmc_preprocessing;
            storm::utility::Stopwatch constructing;
            storm::utility::Stopwatch model_checking;
            storm::utility::Stopwatch other;

            // Number of checked subchains during the last construction
            uint_fast64_t subchains_checked;
        };

    } // namespace research
} // namespace storm

#endif  /* STORM_RESEARCH_COUNTEREXAMPLE_H */