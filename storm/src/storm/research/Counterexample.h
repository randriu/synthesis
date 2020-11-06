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

            /**
             * Establish state expansion order (waves):
             * - explore the reachable state space wave by wave
             * - during each wave, expand only 'non-blocking' states (states with registered holes)
             * - if no non-blocking state remains, pick a blocking candidate with the least amount of unregistered holes
             * - register all holes in this blocking candidate, thus unblocking this state (and possibly many others)
             * - rinse and repeat
             * @param dtmc A DTMC.
             * @param hole_wave (output) For each hole, a wave when it was registered (0 = unregistered).
             * @param wave_states (output) For each wave, a set of states that were expanded.
             */
            void computeWaves(
                storm::models::sparse::Dtmc<ValueType> const& dtmc,
                std::map<std::string, uint_fast64_t> & hole_wave,
                std::vector<std::vector<StateType>> & wave_states
                );

            /**
             * Expand new wave and model check resulting rerouting of a DTMC.
             * @param dtmc A DTMC.
             * @param labeling Prototype labeling.
             * @param matrix_dtmc Original transition matrix.
             * @param matrix_subdtmc Rerouting of the transition matrix wrt. unexpanded states.
             * @param to_expand States expanded during this wave.
             * @return true if the rerouting still satisfies the formula
             */
            bool expandAndCheck(
                storm::models::sparse::Dtmc<ValueType> const& dtmc,
                storm::models::sparse::StateLabeling const& labeling,
                std::vector<std::vector<std::pair<StateType,ValueType>>> & matrix_dtmc,
                std::vector<std::vector<std::pair<StateType,ValueType>>> & matrix_subdtmc,
                std::vector<StateType> const& to_expand
                );

            /*!
             * Construct a minimal counterexample to a given DTMC via hole exploration.
             * @param dtmc A DTMC refuting the safety formula. It is assumed that the state space of the DTMC is topologically ordered.
             * @param use_mdp_bounds If true, mdp bounds will be used for CE construction.
             * @return A set of holes relevant in the CE.
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

            // For each state valuation, a bound on the reachability probability and a flag whether this a state is target one
            std::map<std::string const, std::pair<ValueType,bool>> mdp_info;
            // std::map<storm::storage::sparse::StateValuations::StateValuation, std::pair<ValueType,bool>, storm::storage::sparse::StateValuations::StateValuationLess> mdp_info;
            
            // Formula type: safety (<,<=) or liveness (>,>=)
            bool formula_safety;
            // Target label for sub-dtmcs
            std::string target_label = "__target__";
            // Modified operator formula to apply to sub-dtmcs: P~?[F "__target__"]
            std::shared_ptr<storm::logic::Formula> formula_modified;
            
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