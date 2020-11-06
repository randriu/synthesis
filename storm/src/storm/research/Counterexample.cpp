// author: Roman Andriushchenko

#include "storm/research/Counterexample.h"

#include <queue>
#include <deque>
#include "storm/storage/BitVector.h"

#include "storm/storage/sparse/JaniChoiceOrigins.h"
#include "storm/storage/sparse/StateValuations.h"

#include "storm/utility/builder.h"
#include "storm/storage/SparseMatrix.h"
#include "storm/storage/sparse/ModelComponents.h"
#include "storm/models/sparse/StateLabeling.h"

#include "storm/api/verification.h"
#include "storm/logic/ComparisonType.h"
#include "storm/logic/Bound.h"
#include "storm/modelchecker/CheckTask.h"
#include "storm/modelchecker/results/ExplicitQualitativeCheckResult.h"

namespace storm {
    namespace research {

        template <typename ValueType, typename StateType>
        Counterexample<ValueType,StateType>::Counterexample (
            storm::jani::Model const& program,
            storm::storage::FlatSet<std::string> const& family_relevant_holes,
            storm::logic::Formula const& formula,
            storm::models::sparse::Mdp<ValueType> const& mdp,
            storm::modelchecker::ExplicitQuantitativeCheckResult<ValueType> const& mdp_result
        ) : family_relevant_holes(family_relevant_holes) {
            
            this->total.start();
            this->mdp_preprocessing.start();

            // storm::storage::sparse::JaniChoiceOrigins & choice_origins = mdp.getChoiceOrigins()->asJaniChoiceOrigins();

            // Map edges to holes
            for(uint_fast64_t automaton_index = 0; automaton_index < program.getNumberOfAutomata(); automaton_index++) {
                storm::jani::Automaton const& automaton = program.getAutomaton(automaton_index);
                for(uint_fast64_t edge_index = 0; edge_index < automaton.getNumberOfEdges(); edge_index++) {
                    storm::jani::Edge const& edge = automaton.getEdge(edge_index);
                    std::set<storm::expressions::Variable> variables;

                    // Read variables
                    auto guard_vars = edge.getGuard().getVariables();
                    variables.insert(guard_vars.begin(), guard_vars.end());
                    for(auto destination: edge.getDestinations()) {
                        auto prob_vars = destination.getProbability().getVariables();
                        variables.insert(prob_vars.begin(), prob_vars.end());
                        for(auto assignment: destination.getOrderedAssignments()) {
                            auto ass_vars = assignment.getAssignedExpression().getVariables();
                            variables.insert(ass_vars.begin(), ass_vars.end());
                        }
                    }

                    // Filter relevant variables, store only names
                    std::set<std::string> holes;
                    for(auto var: variables) {
                        if(this->family_relevant_holes.find(var.getName()) != this->family_relevant_holes.end()) {
                            holes.insert(var.getName());
                        }
                    }
                    if(holes.size() > 0) {
                        uint_fast64_t index = program.encodeAutomatonAndEdgeIndices(automaton_index, edge_index);
                        this->edge2holes.emplace(index,holes);
                    }
                }
            }

            // Check formula type
            assert(formula.isOperatorFormula());
            storm::logic::OperatorFormula const& of = formula.asOperatorFormula();
            assert(of.hasBound());
            storm::logic::ComparisonType ct = of.getComparisonType();
            this->formula_safety = ct == storm::logic::ComparisonType::Less || ct == storm::logic::ComparisonType::LessEqual;

            // Extract predicate for target states and identify these states
            storm::logic::EventuallyFormula const& ef = of.getSubformula().asEventuallyFormula();
            storm::logic::Formula const& target_states_predicate = ef.getSubformula();
            std::shared_ptr<storm::models::sparse::Mdp<ValueType>> mdp_shared = std::make_shared<storm::models::sparse::Mdp<ValueType>>(mdp);
            bool onlyInitialStatesRelevant = false;
            storm::modelchecker::CheckTask<storm::logic::Formula, ValueType> task(target_states_predicate, onlyInitialStatesRelevant);
            std::unique_ptr<storm::modelchecker::CheckResult> result_ptr = storm::api::verifyWithSparseEngine<ValueType>(mdp_shared, task);
            storm::modelchecker::ExplicitQualitativeCheckResult & mdp_target_states = result_ptr->asExplicitQualitativeCheckResult();

            // Replace target states predicate in the formula with our own label
            std::shared_ptr<storm::logic::Formula const> const& label_formula = std::make_shared<storm::logic::AtomicLabelFormula>(this->target_label);
            std::shared_ptr<storm::logic::Formula const> const& eventually_formula = std::make_shared<storm::logic::EventuallyFormula>(label_formula, ef.getContext());
            this->formula_modified = std::make_shared<storm::logic::ProbabilityOperatorFormula>(eventually_formula, of.getOperatorInformation());

            // Associate MDP states with satisfiability probabilities and being a target one
            storm::storage::sparse::StateValuations const& mdp_state_valuations = mdp.getStateValuations();
            StateType mdp_states = mdp_state_valuations.getNumberOfStates();
            for(StateType state = 0; state < mdp_states; state++) {
                std::string const& key = mdp_state_valuations.toString(state,false);
                this->mdp_info.emplace(key, std::make_pair(mdp_result[state], mdp_target_states[state]));
            }

            this->mdp_preprocessing.stop();
            this->total.stop();
        }

        template <typename ValueType, typename StateType>
        void Counterexample<ValueType,StateType>::computeWaves(
            storm::models::sparse::Dtmc<ValueType> const& dtmc,
            std::map<std::string, uint_fast64_t> & hole_wave,
            std::vector<std::vector<StateType>> & wave_states
            ) {
            
            // Get DTMC info
            uint_fast64_t dtmc_states = dtmc.getNumberOfStates();
            StateType initial_state = *(dtmc.getInitialStates().begin());
            storm::storage::SparseMatrix<ValueType> const& transition_matrix = dtmc.getTransitionMatrix();

            // Associate states of a DTMC with relevant holes
            storm::storage::sparse::JaniChoiceOrigins & choice_origins = dtmc.getChoiceOrigins()->asJaniChoiceOrigins();
            std::vector<std::set<std::string>> dtmc_holes(dtmc_states);
            for(StateType state = 0; state < dtmc_states; state++) {
                std::set<std::string> relevant_holes;
                for(auto edge: choice_origins.getEdgeIndexSet(state)) {
                    auto holes = this->edge2holes[edge];
                    relevant_holes.insert(holes.begin(),holes.end());
                }
                dtmc_holes[state] = relevant_holes;
            }

            // Mark all holes as unregistered
            // maps hole to the wave when it was registered (0 = unregistered)
            for(std::string hole: this->family_relevant_holes) {
                hole_wave.emplace(hole,0);
            }
            
            // Count the number of relevant holes in each state
            std::vector<uint_fast64_t> unregistered_holes_count(dtmc_states, 0);
            for(StateType state = 0; state < dtmc_states; state++) {
                unregistered_holes_count[state] = dtmc_holes[state].size();
            }

            // Prepare to explore
            // wave increases by one when new holes of a blocking candidate are registered
            uint_fast64_t current_wave = 0;
            // true if the state was reached during exploration (expanded states + both horizons)
            storm::storage::BitVector reachable_flag(dtmc_states, false);
            // non-blocking horizon
            std::stack<StateType> state_horizon;
            // horizon containing, for a current wave, only blocking states
            std::vector<StateType> state_horizon_blocking;
            // blocking state containing currently the least number of unregistered holes + flag if the value was set
            bool blocking_candidate_set = false;
            StateType blocking_candidate;
            
            // Round 0: encounter initial state first (important)
            wave_states.push_back(std::vector<StateType>());
            reachable_flag.set(initial_state);
            if(unregistered_holes_count[initial_state] == 0) {
                // non-blocking
                state_horizon.push(initial_state);
            } else {
                // blocking
                state_horizon_blocking.push_back(initial_state);
                blocking_candidate_set = true;
                blocking_candidate = initial_state;
            }

            // Explore the state space
            while(true) {
                // Expand the non-blocking horizon
                while(!state_horizon.empty()) {
                    StateType state = state_horizon.top();
                    state_horizon.pop();
                    wave_states.back().push_back(state);
                    // Reach successors
                    for(auto entry: transition_matrix.getRow(state)) {
                        StateType successor = entry.getColumn();
                        if(reachable_flag[successor]) {
                            // already reached
                            continue;
                        }
                        // new state reached
                        reachable_flag.set(successor);
                        if(unregistered_holes_count[successor] == 0) {
                            // non-blocking
                            state_horizon.push(successor);
                        } else {
                            // blocking
                            state_horizon_blocking.push_back(successor);
                            if(!blocking_candidate_set || unregistered_holes_count[successor] < unregistered_holes_count[blocking_candidate]) {
                                // new blocking candidate
                                blocking_candidate_set = true;
                                blocking_candidate = successor;
                            }
                        }
                    }
                }

                // Non-blocking horizon exhausted
                if(!blocking_candidate_set) {
                    // Nothing more to expand
                    break;
                }
                
                // Start a new wave
                current_wave++;
                wave_states.push_back(std::vector<StateType>());
                blocking_candidate_set = false;
                
                // Register all unregistered holes of this blocking state
                for(std::string hole: dtmc_holes[blocking_candidate]) {
                    if(hole_wave[hole] == 0) {
                        hole_wave[hole] = current_wave;
                    }
                }

                // Recompute number of unregistered holes in each state
                for(StateType state = 0; state < dtmc_states; state++) {
                    unregistered_holes_count[state] = 0;
                    for(std::string hole: dtmc_holes[state]) {
                        if(hole_wave[hole] == 0) {
                            unregistered_holes_count[state]++;
                        }
                    }
                }
                
                // Unblock the states from the blocking horizon
                std::vector<StateType> old_blocking_horizon;
                old_blocking_horizon.swap(state_horizon_blocking);
                for(StateType state: old_blocking_horizon) {
                    if(unregistered_holes_count[state] == 0) {
                        // state unblocked
                        state_horizon.push(state);
                    } else {
                        // still blocking
                        state_horizon_blocking.push_back(state);
                        if(!blocking_candidate_set || unregistered_holes_count[state] < unregistered_holes_count[blocking_candidate]) {
                            // new blocking candidate
                            blocking_candidate_set = true;
                            blocking_candidate = state;
                        }
                    }
                }
            }
        }

        template <typename ValueType, typename StateType>
        bool Counterexample<ValueType,StateType>::expandAndCheck (
            storm::models::sparse::Dtmc<ValueType> const& dtmc,
                storm::models::sparse::StateLabeling const& labeling,
                std::vector<std::vector<std::pair<StateType,ValueType>>> & matrix_dtmc,
                std::vector<std::vector<std::pair<StateType,ValueType>>> & matrix_subdtmc,
                std::vector<StateType> const& to_expand
        ) {
            this->other.start();

            // Get DTMC info
            uint_fast64_t dtmc_states = dtmc.getNumberOfStates();
            StateType initial_state = *(dtmc.getInitialStates().begin());
            // Expand states from the new wave
            for(StateType state : to_expand) {
                matrix_subdtmc[state] = std::move(matrix_dtmc[state]);
            }
            this->other.stop();

            // Construct sub-DTMC
            this->constructing.start();
            storm::storage::SparseMatrixBuilder<ValueType> transitionMatrixBuilder(0, 0, 0, false, false, 0);
            for(StateType state = 0; state < dtmc_states+2; state++) {
                for(auto row_entry: matrix_subdtmc[state]) {
                    transitionMatrixBuilder.addNextValue(state, row_entry.first, row_entry.second);
                }
            }
            storm::storage::SparseMatrix<ValueType> sub_matrix = transitionMatrixBuilder.build();
            assert(sub_matrix.isProbabilistic());
            storm::storage::sparse::ModelComponents<ValueType> components(sub_matrix, labeling);
            std::shared_ptr<storm::models::sparse::Model<ValueType>> sub_dtmc = storm::utility::builder::buildModelFromComponents(storm::models::ModelType::Dtmc, std::move(components));
            this->constructing.stop();
            
            // Model check
            this->model_checking.start();
            bool onlyInitialStatesRelevant = false;
            // storm::modelchecker::CheckTask<storm::logic::Formula, ValueType> task(this->formula_modified, onlyInitialStatesRelevant);
            storm::modelchecker::CheckTask<storm::logic::Formula, ValueType> task(*(this->formula_modified), onlyInitialStatesRelevant);
            std::unique_ptr<storm::modelchecker::CheckResult> result_ptr = storm::api::verifyWithSparseEngine<ValueType>(sub_dtmc, task);
            storm::modelchecker::ExplicitQualitativeCheckResult & result = result_ptr->asExplicitQualitativeCheckResult();
            bool satisfied = result[initial_state];
            this->model_checking.stop();

            return satisfied;
        }

        template <typename ValueType, typename StateType>
        storm::storage::FlatSet<std::string> Counterexample<ValueType,StateType>::constructViaHoles (
            storm::models::sparse::Dtmc<ValueType> const& dtmc,
            bool use_mdp_bounds
        ) {
            this->total.start();
            this->dtmc_preprocessing.start();

            // Get DTMC info
            StateType dtmc_states = dtmc.getNumberOfStates();
            storm::storage::SparseMatrix<ValueType> const& transition_matrix = dtmc.getTransitionMatrix();
            
            // Introduce expanded state space with two sink states
            StateType sink_state_false = dtmc_states;
            StateType sink_state_true = dtmc_states+1;

            // Typedef for matrices
            typedef std::vector<std::pair<StateType,ValueType>> row;
            typedef std::vector<row> matrix;

            // Construct copy of the original matrix
            matrix matrix_dtmc;
            for(StateType state = 0; state < dtmc_states; state++) {
                row r;
                for(auto entry: transition_matrix.getRow(state)) {
                    r.emplace_back(entry.getColumn(), entry.getValue());
                }
                matrix_dtmc.push_back(r);
            }

            // Matrix of shortcuts = initial matrix of the subDTMC
            matrix matrix_subdtmc;

            // Associate states of a DTMC with
            // - the bound on satisfiability probabilities
            // - being the target state
            storm::storage::sparse::StateValuations const& dtmc_state_valuations = dtmc.getStateValuations();
            double default_bound = this->formula_safety ? 0 : 1;
            storm::models::sparse::StateLabeling labeling(dtmc_states+2);
            labeling.addLabel(this->target_label);
            for(StateType state = 0; state < dtmc_states; state++) {
                std::string const& key = dtmc_state_valuations.toString(state,false);
                auto search = this->mdp_info.find(key);
                assert(search != this->mdp_info.end());
                auto info = search->second;
                double bound = info.first;
                bool is_target = info.second;
                
                // use bound to construct the matrix of shortcuts
                row r;
                double probability = use_mdp_bounds ? bound : default_bound;
                r.emplace_back(sink_state_false, 1-probability);
                r.emplace_back(sink_state_true, probability);
                matrix_subdtmc.push_back(r);

                // use target state info to construct labeling
                if(is_target) {
                    labeling.addLabelToState(this->target_label, state);
                }
            }

            // Add self-loops to sink states
            for(StateType state = sink_state_false; state <= sink_state_true; state++) {
                row r;
                r.emplace_back(state, 1);
                matrix_subdtmc.push_back(r);
            }
            // Associate true sink with the target label
            labeling.addLabelToState(this->target_label, sink_state_true);

            // Compute waves
            std::map<std::string, uint_fast64_t> hole_wave;
            std::vector<std::vector<StateType>> wave_states;
            computeWaves(dtmc, hole_wave, wave_states);
            this->dtmc_preprocessing.stop();

            // Explore subDTMCs wave by wave
            uint_fast64_t waves_total = wave_states.size()-1;
            uint_fast64_t wave = 0;
            while(true) {
                assert(wave <= waves_total);
                bool satisfied = this->expandAndCheck(
                    dtmc,labeling, matrix_dtmc,matrix_subdtmc, wave_states[wave]
                );
                if(!satisfied) {
                    break;
                }
                wave++;
            }
            this->subchains_checked = wave+1;

            // Return a set of critical holes
            this->other.start();
            storm::storage::FlatSet<std::string> critical_holes;
            for(auto const& entry : hole_wave) {
                uint_fast64_t wave_registered = entry.second;
                if(wave_registered > 0 && wave_registered <= wave) {
                    critical_holes.insert(entry.first);
                }
            }
            
            this->other.stop();
            this->total.stop();

            return critical_holes;
        }

        

        template <typename ValueType, typename StateType>
        std::vector<double> Counterexample<ValueType,StateType>::stats (
        ) {
            std::vector<double> time_stats;
            double time_total = this->total.getTimeInMilliseconds();
            time_stats.push_back(time_total);
            time_stats.push_back(this->mdp_preprocessing.getTimeInMilliseconds() / time_total);
            time_stats.push_back(this->dtmc_preprocessing.getTimeInMilliseconds() / time_total);
            time_stats.push_back(this->constructing.getTimeInMilliseconds() / time_total);
            time_stats.push_back(this->model_checking.getTimeInMilliseconds() / time_total);
            time_stats.push_back(this->other.getTimeInMilliseconds() / time_total);
            time_stats.push_back(this->subchains_checked);
            return time_stats;
        }

         // Explicitly instantiate the class.
        template class Counterexample<double, uint_fast64_t>;

    } // namespace research
} // namespace storm
