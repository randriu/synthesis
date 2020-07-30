// author: Roman Andriushchenko

#ifndef STORM_RESEARCH_COUNTEREXAMPLE_H
#define	STORM_RESEARCH_COUNTEREXAMPLE_H

#include "storm/logic/Formula.h"
#include "storm/logic/OperatorFormula.h"
#include "storm/models/sparse/Mdp.h"
#include "storm/modelchecker/results/ExplicitQuantitativeCheckResult.h"
#include "storm/models/sparse/Dtmc.h"

#include "storm/utility/Stopwatch.h"
#include "storm/storage/BoostTypes.h"
#include "storm/storage/SparseMatrix.h"

namespace storm {
    namespace research {

        template<typename ValueType = double, typename StateType = uint_fast64_t>
        class Counterexample {
        public:

            /*!
             * Preprocess the quotient MDP and its lower bound on the reachability
             * probability before constructing counterexamples from various DTMCs.
             * @param expanded_per_iter Number of states to expand before each model checking.
             * @param formula Operator formula to check.
             * @param mdp The quotient MDP.
             * @param mdp_result Lower (safety) or upper (liveness) bound on the formula satisfiability for the quotient MDP.
             */
            Counterexample(
                uint_fast64_t expanded_per_iter,
                storm::logic::Formula const& formula,
                storm::models::sparse::Mdp<ValueType> const& mdp,
                storm::modelchecker::ExplicitQuantitativeCheckResult<ValueType> const& mdp_result
                );

            /*!
             * Construct a minimal counterexample to a given DTMC.
             * @param dtmc A DTMC refuting the safety formula. It is assumed that the state space of the DTMC is topologically ordered.
             * @return A set of critical states.
             */
            storm::storage::FlatSet<StateType> construct(
                storm::models::sparse::Dtmc<ValueType> const& dtmc,
                storm::modelchecker::ExplicitQuantitativeCheckResult<ValueType> const& dtmc_result
                );

            /*!
             * @return A profiling vector.
             */
            std::vector<double> stats();

        private:
            // Number of states to expand before model checking
            uint_fast64_t expanded_per_iter;
            
            // Operator formula to check.
            storm::logic::Formula const& formula;
            // Formula type: safety (<,<=) or liveness (>,>=)
            bool formula_safety;
            // Lower (safety) or upper (liveness) bound on the formula satisfiability for the quotient MDP.
            std::map<storm::storage::sparse::StateValuations::StateValuation, ValueType, storm::storage::sparse::StateValuations::StateValuationLess> mdp_bound;
            // Target label.
            std::string target_label;

            // Profiling
            storm::utility::Stopwatch total;
            storm::utility::Stopwatch mdp_preprocessing;
            storm::utility::Stopwatch dtmc_preprocessing;
            storm::utility::Stopwatch constructing;
            storm::utility::Stopwatch model_checking;
            storm::utility::Stopwatch other;
        };

    } // namespace research
} // namespace storm

#endif	/* STORM_RESEARCH_COUNTEREXAMPLE_H */
