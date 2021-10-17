// author: Roman Andriushchenko

#ifndef STORM_SYNTHESIS_COUNTEREXAMPLE_H
#define STORM_SYNTHESIS_COUNTEREXAMPLE_H

#include "storm/storage/jani/Model.h"
#include "storm/logic/Formula.h"
#include "storm/models/sparse/Mdp.h"
#include "storm/modelchecker/results/ExplicitQuantitativeCheckResult.h"
#include "storm/modelchecker/results/ExplicitQualitativeCheckResult.h"

#include "storm/models/sparse/Dtmc.h"
#include "storm/utility/Stopwatch.h"

namespace storm {
    namespace synthesis {

        /*!
         * Construct a DTMC by exploring a reachable state space of an MDP 
         * through selected edges All reward models are automatically reduced
         * to their state variants.
         * @param mdp An MDP.
         * @param selected_edge_indices Allowed edges in the resulting DTMC.
         * @return A DTMC with a DTMC-MDP state mapping.
         */
        template<typename ValueType = double, typename StateType = uint_fast64_t>
        std::pair<std::shared_ptr<storm::models::sparse::Model<ValueType>>,std::vector<StateType>> DtmcFromMdp(
            storm::models::sparse::Mdp<ValueType> const& mdp,
            storm::storage::FlatSet<uint_fast64_t> const& selected_edge_indices
            );

        template<typename ValueType = double, typename StateType = uint_fast64_t>
        class Counterexample {
        public:

            /*!
             * Preprocess the quotient MDP and its bound on the reachability
             * probability before constructing counterexamples from various
             * sub-MDPs (DTMCs).
             * @param quotient_mdp The quotient MDP.
             * @param hole_count Total number of holes.
             * @param mdp_holes A list of indices of significant holes for each
             *   state of the quotient MDP.
             * @param formula Operator formulae to check, can be both
             *   probabilistic and reward-based.
             * @param mdp_bound Lower (safety) or upper (liveness) bounds on
             *   the formulae satisfiability for the quotient MDP.
             */
            Counterexample(
                storm::models::sparse::Mdp<ValueType> const& quotient_mdp,
                uint_fast64_t hole_count,
                std::vector<std::set<uint_fast64_t>> const& mdp_holes,
                std::vector<std::shared_ptr<storm::logic::Formula const>> const& formulae,
                std::vector<std::shared_ptr<storm::modelchecker::ExplicitQuantitativeCheckResult<ValueType> const>> const& mdp_bounds
                );

            /*!
             * Replace a formula threshold and the corresponding mdp bound for
             * the formula with the given index.
             * @note This function is used for updating the violation formula.
             */
            void replaceFormulaThreshold(
                uint_fast64_t formula_index,
                ValueType formula_threshold,
                std::shared_ptr<storm::modelchecker::ExplicitQuantitativeCheckResult<ValueType> const> mdp_bound
            );

            /*!
             * Preprocess the DTMC by establishing the state expansion order (waves):
             * - explore the reachable state space wave by wave
             * - during each wave, expand only 'non-blocking' states (states with registered holes)
             * - if no non-blocking state remains, pick a blocking candidate with the least amount of unregistered holes
             * - register all holes in this blocking candidate, thus unblocking this state (and possibly many others)
             * - rinse and repeat
             * @param dtmc A DTMC.
             * @param state_map DTMC-MDP state mapping.
             */
            void prepareDtmc(
                storm::models::sparse::Dtmc<ValueType> const& dtmc,
                std::vector<uint_fast64_t> const& state_map
                );
            
            /*!
             * Construct a counterexample to a prepared DTMC and a formula with
             * the given index.
             * @param formula_index Formula index.
             * @param use_mdp_bounds If true, MDP bounds will be used for CE construction.
             * @return A list of holes relevant in the CE.
             */
            std::vector<uint_fast64_t> constructCounterexample(
                uint_fast64_t formula_index, bool use_mdp_bounds = true
                );
            
            /*!
             * @return A profiling vector.
             */
            std::vector<double> stats();

        protected:

            /**
             * Prepare data structures for sub-DTMC construction.
             * @param index Formula index
             * @param use_mdp_bounds If false, trivial bounds are used.
             * @param matrix_dtmc (output) Copy of the transition matrix of the DTMC.
             * @param matrix_subdtmc (output) Matrix of shortcuts.
             * @param labeling_subdtdmc (output) Labeling marking target states.
             * @param reward_model_subdtmc (output) If the reward property is
             *   investigated, this map will contain exactly one reward model
             *   for the initial sub-DTMC.
             */
            void prepareSubdtmc(
                uint_fast64_t index,
                bool use_mdp_bounds,
                std::vector<std::vector<std::pair<StateType,ValueType>>> & matrix_dtmc,
                std::vector<std::vector<std::pair<StateType,ValueType>>> & matrix_subdtmc,
                storm::models::sparse::StateLabeling & labeling_subdtmc,
                std::unordered_map<std::string,storm::models::sparse::StandardRewardModel<ValueType>> & reward_models_subdtmc
                );

            /**
             * Expand new wave and model check resulting rerouting of a DTMC.
             * @param dtmc A DTMC.
             * @param labeling Prototype labeling.
             * @param matrix_dtmc Original transition matrix.
             * @param matrix_subdtmc Rerouting of the transition matrix wrt. unexpanded states.
             * @param reward_models_subdtmc Reward models for the initial sub-DTMC.
             * @param to_expand States expanded during this wave.
             * @return true if the rerouting still satisfies the formula
             */
            bool expandAndCheck(
                uint_fast64_t index,
                std::vector<std::vector<std::pair<StateType,ValueType>>> & matrix_dtmc,
                std::vector<std::vector<std::pair<StateType,ValueType>>> & matrix_subdtmc,
                storm::models::sparse::StateLabeling const& labeling_subdtmc,
                std::unordered_map<std::string,storm::models::sparse::StandardRewardModel<ValueType>> & reward_models_subdtmc,
                std::vector<StateType> const& to_expand
                );

            // Quotient MDP
            storm::models::sparse::Mdp<ValueType> const& quotient_mdp;
            // Number of significant holes
            uint_fast64_t hole_count;
            // Significant holes in MDP states
            std::vector<std::set<uint_fast64_t>> mdp_holes;
            
            // Target label for sub-dtmcs
            const std::string target_label = "__target__";

            // Total number of formulae
            uint_fast64_t formulae_count;
            // Formula bounds: safety (<,<=) or liveness (>,>=)
            std::vector<bool> formula_safety;
            // Formula types: probability (false) or reward-based (true)
            std::vector<bool> formula_reward;
            // Reward model names for reward formulae
            std::vector<std::string> formula_reward_name;
            // Modified operator formulae to apply to sub-dtmcs: P~?[F "__target__"]
            std::vector<std::shared_ptr<storm::logic::Formula>> formula_modified;
            // Bounds from MDP model checking
            std::vector<std::shared_ptr<storm::modelchecker::ExplicitQuantitativeCheckResult<ValueType> const>> mdp_bounds;
            // Flags for target states
            std::vector<std::shared_ptr<storm::modelchecker::ExplicitQualitativeCheckResult const>> mdp_targets;
            
            // Transition matrix of a DTMC under investigation
            std::shared_ptr<storm::models::sparse::Dtmc<ValueType>> dtmc;
            // DTMC to MDP state mapping
            std::vector<uint_fast64_t> state_map;
            // For each hole, a wave when it was registered (0 = unregistered).
            std::vector<uint_fast64_t> hole_wave;
            // // For each wave, a set of states that were expanded.
            std::vector<std::vector<StateType>> wave_states;
             

            // Profiling
            storm::utility::Stopwatch total;

            storm::utility::Stopwatch preparing_mdp;
            storm::utility::Stopwatch preparing_dtmc;
            storm::utility::Stopwatch preparing_subdtmc;
            storm::utility::Stopwatch constructing_counterexample;

        };

    } // namespace research
} // namespace storm

#endif  /* STORM_SYNTHESIS_COUNTEREXAMPLE_H */
