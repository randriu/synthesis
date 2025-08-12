#pragma once

#include <storm/models/sparse/Model.h>
#include <storm/environment/Environment.h>
#include <storm/utility/Stopwatch.h>
#include <storm/logic/GameFormula.h>

namespace synthesis {

    template<typename ValueType>
    class GameAbstractionSolver {

        /*
        - Player 1. States are states of the quotient model + a fresh target state. In each state s Player 1 has a
            choice of an action a, which leads to state (s,a) of Player 2. In their fresh target state, Player 1
            transitions to the fresh target state of Player 2.
        - Player 2. States are pairs (s,a), where s is the state of the quotient and a is the action selected in s by
            Player 1. In state (s,a), Player 2 chooses the color of a to be executed. In state (s,*) where s is the 
            target state of the quotient, Player 2 receives reward 1 and executes action available in this state. In
            their fresh target state, Player 2 loops back to the target state of Player 1.
        */

    public:
        
        /**
         * Create game abstraction solver.
         * @param quotient The quotient MDP. Sub-MDPs from the quotient will be used to construct sub-games.
         * @param quotient_num_action The total number of distinct actions in the quotient.
         * @param choice_to_action For each row of the quotient, the associated action.
         * @param formula Game formula to model check.
         * @param player1_maximizing Whether Player 1 maximizes.
         * @param target_label Label of the target states.
         * @param precision Game solving precision.
         */
        GameAbstractionSolver(
            storm::models::sparse::Model<ValueType> const& quotient,
            uint64_t quotient_num_actions,
            std::vector<uint64_t> const& choice_to_action,
            std::shared_ptr<storm::logic::Formula const> formula,
            bool player1_maximizing,
            std::string const& target_label,
            double precision
        );
        
        /**
         * Solve the game induced by the sub-MDP.
         * @param quotient_choice_mask Choices of the quotient that remained in the sub-MDP.
         */
        void solveSg(storm::storage::BitVector const& quotient_choice_mask);
        void solveSmg(storm::storage::BitVector const& quotient_choice_mask);

        /** For each state, the value of the game. */
        std::vector<double> solution_state_values;
        /** Value of the game in the initial state. */
        double solution_value;
        
        /**
         * For each state, an action selected by Player 1. State s contains quotient_num_actions if the action was not
         * set.
         */
        std::vector<uint64_t> solution_state_to_player1_action;
        /**
         * For each state, a choice selected by Player 1 & Player2. State s contains quotient_num_choices if the
         * choice was not set.
         */
        std::vector<uint64_t> solution_state_to_quotient_choice;

        // Profiling
        void enableProfiling(bool enable);
        void printProfiling();

    private:

        storm::models::sparse::Model<ValueType> const& quotient;
        uint64_t quotient_num_actions;
        std::vector<uint64_t> choice_to_action;
        std::shared_ptr<storm::logic::GameFormula const> game_formula;
        bool player1_maximizing;
        
        /** Identification of target states. */
        storm::storage::BitVector state_is_target;
        
        /** For each state of the quotient, a list of actions associated with its rows. */
        // std::vector<std::vector<uint64_t>> state_to_actions;
        /** For each choice of the quotient, its destinations. */
        std::vector<std::vector<uint64_t>> choice_to_destinations;

        /** Solver environment. */
        storm::Environment env;

        void setupSolverEnvironment(double precisions);
        storm::OptimizationDirection getOptimizationDirection(bool maximizing);

        // Profiling
        bool profiling_enabled = false;
        storm::utility::Stopwatch timer_total;
        storm::utility::Stopwatch timer_game_solving;
        
    };
}