// author: Roman Andriushchenko
// git check

#include "storm-counterexamples/synthesis/Counterexample.h"

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

namespace storm {
    namespace synthesis {

        template<typename ValueType, typename StateType>
        std::pair<std::shared_ptr<storm::models::sparse::Model<ValueType>>,std::vector<StateType>> DtmcFromMdp (
            storm::models::sparse::Mdp<ValueType> const& mdp,
            storm::storage::FlatSet<uint_fast64_t> const& selected_edge_indices
            ) {

            // MDP info
            uint_fast64_t mdp_states = mdp.getNumberOfStates();
            StateType mdp_initial_state = *(mdp.getInitialStates().begin());
            storm::storage::SparseMatrix<ValueType> const& mdp_matrix = mdp.getTransitionMatrix();
            storm::storage::sparse::JaniChoiceOrigins & mdp_choice_origins = mdp.getChoiceOrigins()->asJaniChoiceOrigins();
            std::vector<uint_fast64_t> const& action_group_indices = mdp_matrix.getRowGroupIndices();

            // Reachable subspace structures
            // establish DTMC state to MDP state/action mapping
            storm::storage::BitVector mdp_state_reachable(mdp_states, false);
            std::queue<StateType> mdp_horizon;
            std::vector<StateType> mdp2dtmc_state(mdp_states);
            uint_fast64_t dtmc_states = 0; // state reached => added to DTMC
            std::vector<StateType> dtmc2mdp_state;
            std::vector<uint_fast64_t> dtmc2mdp_action;

            // Initiate BFS from the initial state
            mdp_state_reachable.set(mdp_initial_state);
            mdp_horizon.push(mdp_initial_state);
            mdp2dtmc_state[mdp_initial_state] = dtmc_states;
              dtmc2mdp_state.push_back(mdp_initial_state);
              dtmc2mdp_action.push_back(0);
              dtmc_states++;
            while(!mdp_horizon.empty()) {
                StateType mdp_state = mdp_horizon.front();
                mdp_horizon.pop();
                StateType dtmc_state = mdp2dtmc_state[mdp_state];
                
                // Identify exactly one action of interest
                bool action_identified = false;
                uint_fast64_t action_of_interest;
                for (
                    uint_fast64_t action = action_group_indices[mdp_state];
                    action < action_group_indices[mdp_state+1];
                    action++
                ) {
                    bool action_suitable = true;
                    for(auto edge_index: mdp_choice_origins.getEdgeIndexSet(action)) {
                        if(selected_edge_indices.find(edge_index) == selected_edge_indices.end()) {
                            action_suitable = false;
                            break;
                        }
                    }
                    if(action_suitable) {
                        action_identified = true;
                        action_of_interest = action;
                        break;
                    }
                }
                assert(action_identified);

                // Expand via the action of interest
                dtmc2mdp_action[dtmc_state] = action_of_interest;
                for(auto entry: mdp_matrix.getRow(action_of_interest)) {
                    StateType mdp_successor = entry.getColumn();
                    if(!mdp_state_reachable[mdp_successor]) {
                        // new state reached
                        mdp_state_reachable.set(mdp_successor);
                        mdp_horizon.push(mdp_successor);
                        mdp2dtmc_state[mdp_successor] = dtmc_states;
                          dtmc2mdp_state.push_back(mdp_successor);
                          dtmc2mdp_action.push_back(0);
                          dtmc_states++;
                    }
                }
            }

            // Build DTMC components:
            // - matrix
            storm::storage::SparseMatrixBuilder<ValueType> matrix_builder(0, 0, 0, false, false, 0);
            for(StateType dtmc_state = 0; dtmc_state < dtmc_states; dtmc_state++) {
                uint_fast64_t mdp_action = dtmc2mdp_action[dtmc_state];
                for(auto entry: mdp_matrix.getRow(mdp_action)) {
                    StateType mdp_successor = entry.getColumn();
                    StateType dtmc_successor = mdp2dtmc_state[mdp_successor];
                    matrix_builder.addNextValue(dtmc_state, dtmc_successor, entry.getValue());
                }
            }
            storm::storage::SparseMatrix<ValueType> dtmc_matrix = matrix_builder.build();
            assert(dtmc_matrix.isProbabilistic());

            // - labeling
            storm::models::sparse::StateLabeling dtmc_labeling(dtmc_states);
            storm::models::sparse::StateLabeling const& mdp_labeling = mdp.getStateLabeling();
            for(auto & label: mdp_labeling.getLabels()) {
                dtmc_labeling.addLabel(label);
            }
            for(StateType state = 0; state < dtmc_states; state++) {
                StateType mdp_state = dtmc2mdp_state[state];
                for(auto & label: mdp_labeling.getLabelsOfState(mdp_state)) {
                    dtmc_labeling.addLabelToState(label,state);
                }
            }

            // - reward models
            std::unordered_map<std::string,storm::models::sparse::StandardRewardModel<ValueType>> dtmc_reward_models;
            for(auto const& kv: mdp.getRewardModels()) {
                std::string reward_name = kv.first;
                storm::models::sparse::StandardRewardModel<ValueType> const& mdp_reward = kv.second;
                assert(mdp_reward.hasStateRewards() || mdp_reward.hasStateActionRewards());
                std::vector<ValueType> dtmc_state_rewards(dtmc_states);
                for(StateType dtmc_state = 0; dtmc_state < dtmc_states; dtmc_state++) {
                    if(mdp_reward.hasStateRewards()) {
                        uint_fast64_t mdp_state = dtmc2mdp_state[dtmc_state];
                        dtmc_state_rewards[dtmc_state] = mdp_reward.getStateReward(mdp_state);
                    } else {
                        uint_fast64_t mdp_action = dtmc2mdp_action[dtmc_state];
                        dtmc_state_rewards[dtmc_state] = mdp_reward.getStateActionReward(mdp_action);
                    }
                }
                storm::models::sparse::StandardRewardModel<ValueType> dtmc_reward(dtmc_state_rewards, boost::none, boost::none);
                dtmc_reward_models.emplace(reward_name,dtmc_reward);
            }

            // Build the DTMC
            storm::storage::sparse::ModelComponents<ValueType> components(dtmc_matrix, dtmc_labeling, dtmc_reward_models);
            std::shared_ptr<storm::models::sparse::Model<ValueType>> dtmc = storm::utility::builder::buildModelFromComponents(storm::models::ModelType::Dtmc, std::move(components));

            return std::make_pair(dtmc,dtmc2mdp_state);
        }

        template <typename ValueType, typename StateType>
        Counterexample<ValueType,StateType>::Counterexample (
            storm::models::sparse::Mdp<ValueType> const& quotient_mdp,
            uint_fast64_t hole_count,
            std::vector<std::set<uint_fast64_t>> const& mdp_holes,
            std::vector<std::shared_ptr<storm::logic::Formula const>> const& formulae,
            std::vector<std::shared_ptr<storm::modelchecker::ExplicitQuantitativeCheckResult<ValueType> const>> const& mdp_bounds
            ) : quotient_mdp(quotient_mdp), hole_count(hole_count), mdp_holes(mdp_holes), mdp_bounds(mdp_bounds) {
            
            this->total.start();
            this->preparing_mdp.start();

            // Process formulae
            this->formulae_count = formulae.size();
            this->formula_safety = std::vector<bool>();
            this->formula_reward = std::vector<bool>();
            this->formula_reward_name = std::vector<std::string>();
            this->formula_modified = std::vector<std::shared_ptr<storm::logic::Formula>>();
            this->mdp_targets = std::vector<std::shared_ptr<storm::modelchecker::ExplicitQualitativeCheckResult const>>();
            for(uint_fast64_t index = 0; index < this->formulae_count; index++) {

                auto formula = formulae[index];

                // Check formula type
                assert(formula->isOperatorFormula());
                storm::logic::OperatorFormula const& of = formula->asOperatorFormula();
                assert(of.hasBound());
                storm::logic::ComparisonType ct = of.getComparisonType();
                bool is_safety = ct == storm::logic::ComparisonType::Less || ct == storm::logic::ComparisonType::LessEqual;
                this->formula_safety.push_back(is_safety);

                bool is_reward = formula->isRewardOperatorFormula();
                this->formula_reward.push_back(is_reward);
                if(is_reward) {
                    storm::logic::RewardOperatorFormula rf = formula->asRewardOperatorFormula();
                    this->formula_reward_name.push_back(rf.getRewardModelName());
                } else {
                    this->formula_reward_name.push_back("");
                }

                // Extract predicate for target states and identify such states
                storm::logic::EventuallyFormula const& ef = of.getSubformula().asEventuallyFormula();
                storm::logic::Formula const& target_states_predicate = ef.getSubformula();
                std::shared_ptr<storm::models::sparse::Mdp<ValueType>> mdp_shared = std::make_shared<storm::models::sparse::Mdp<ValueType>>(this->quotient_mdp);
                bool onlyInitialStatesRelevant = false;
                storm::modelchecker::CheckTask<storm::logic::Formula, ValueType> task(target_states_predicate, onlyInitialStatesRelevant);
                std::unique_ptr<storm::modelchecker::CheckResult> result_ptr = storm::api::verifyWithSparseEngine<ValueType>(mdp_shared, task);
                std::shared_ptr<storm::modelchecker::ExplicitQualitativeCheckResult> mdp_target = std::make_shared<storm::modelchecker::ExplicitQualitativeCheckResult>(result_ptr->asExplicitQualitativeCheckResult());
                this->mdp_targets.push_back(mdp_target);

                // Replace target states predicate in the formula with our own label
                std::shared_ptr<storm::logic::Formula const> const& label_formula = std::make_shared<storm::logic::AtomicLabelFormula>(this->target_label);
                std::shared_ptr<storm::logic::Formula const> const& eventually_formula = std::make_shared<storm::logic::EventuallyFormula>(label_formula, ef.getContext());
                if(!is_reward) {
                    this->formula_modified.push_back(std::make_shared<storm::logic::ProbabilityOperatorFormula>(eventually_formula, of.getOperatorInformation()));
                } else {
                    this->formula_modified.push_back(std::make_shared<storm::logic::RewardOperatorFormula>(eventually_formula, this->formula_reward_name[index], of.getOperatorInformation()));
                }
            }
            this->preparing_mdp.stop();

            this->total.stop();
        }

        template <typename ValueType, typename StateType>
        void Counterexample<ValueType,StateType>::replaceFormulaThreshold(
                uint_fast64_t formula_index,
                ValueType formula_threshold,
                std::shared_ptr<storm::modelchecker::ExplicitQuantitativeCheckResult<ValueType> const> mdp_bound
            ) {
            assert(formula_index < this->formulae_count);
            this->mdp_bounds[formula_index] = mdp_bound;
            storm::logic::OperatorFormula & of = this->formula_modified[formula_index]->asOperatorFormula();
            storm::expressions::ExpressionManager const& em = of.getThreshold().getManager();
            storm::expressions::Expression threshold_expression = em.rational(formula_threshold);
            of.setThreshold(threshold_expression);
        }

        template <typename ValueType, typename StateType>
        void Counterexample<ValueType,StateType>::prepareDtmc(
            storm::models::sparse::Dtmc<ValueType> const& dtmc,
            std::vector<uint_fast64_t> const& state_map
            ) {
            this->total.start();
            this->preparing_dtmc.start();

            // Clear up previous DTMC metadata
            this->hole_wave.clear();
            this->wave_states.clear();

            // Get DTMC info
            this->dtmc = std::make_shared<storm::models::sparse::Dtmc<ValueType>>(dtmc);
            this->state_map = state_map;
            uint_fast64_t dtmc_states = this->dtmc->getNumberOfStates();
            StateType initial_state = *(this->dtmc->getInitialStates().begin());
            storm::storage::SparseMatrix<ValueType> const& transition_matrix = this->dtmc->getTransitionMatrix();

            // Mark all holes as unregistered
            for(uint_fast64_t index = 0; index < this->hole_count; index++) {
                this->hole_wave.push_back(0);
            }

            // Associate states of a DTMC with relevant holes and store their count
            std::vector<std::set<uint_fast64_t>> dtmc_holes(dtmc_states);
            std::vector<uint_fast64_t> unregistered_holes_count(dtmc_states, 0);
            for(StateType state = 0; state < dtmc_states; state++) {
                dtmc_holes[state] = this->mdp_holes[state_map[state]];
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
            this->wave_states.push_back(std::vector<StateType>());
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
                    this->wave_states.back().push_back(state);

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
                this->wave_states.push_back(std::vector<StateType>());
                blocking_candidate_set = false;
                
                // Register all unregistered holes of this blocking state
                for(uint_fast64_t hole: dtmc_holes[blocking_candidate]) {
                    if(this->hole_wave[hole] == 0) {
                        hole_wave[hole] = current_wave;
                    }
                }

                // Recompute number of unregistered holes in each state
                for(StateType state = 0; state < dtmc_states; state++) {
                    unregistered_holes_count[state] = 0;
                    for(uint_fast64_t hole: dtmc_holes[state]) {
                        if(this->hole_wave[hole] == 0) {
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

            this->preparing_dtmc.stop();
            this->total.stop();
        }

        template <typename ValueType, typename StateType>
        void Counterexample<ValueType,StateType>::prepareSubdtmc (
            uint_fast64_t formula_index,
            bool use_mdp_bounds,
            std::vector<std::vector<std::pair<StateType,ValueType>>> & matrix_dtmc,
            std::vector<std::vector<std::pair<StateType,ValueType>>> & matrix_subdtmc,
            storm::models::sparse::StateLabeling & labeling_subdtmc,
            std::unordered_map<std::string,storm::models::sparse::StandardRewardModel<ValueType>> & reward_models_subdtmc
            ) {

            // Typedef for matrices
            // typedef std::vector<std::pair<StateType,ValueType>> row;
            // typedef std::vector<row> matrix;

            // Get DTMC info
            StateType dtmc_states = dtmc->getNumberOfStates();
            
            storm::storage::SparseMatrix<ValueType> const& transition_matrix = dtmc->getTransitionMatrix();
            
            // Introduce expanded state space
            uint_fast64_t sink_state_false = dtmc_states;
            uint_fast64_t sink_state_true = dtmc_states+1;

            // Construct a copy of the original matrix
            for(StateType state = 0; state < dtmc_states; state++) {
                std::vector<std::pair<StateType,ValueType>> r;
                for(auto entry: transition_matrix.getRow(state)) {
                    r.emplace_back(entry.getColumn(), entry.getValue());
                }
                matrix_dtmc.push_back(r);
            }

            // Associate states of a DTMC with
            // - the bound on satisfiability probabilities
            // - being the target state
            std::vector<double> dtmc_bound(dtmc_states);
            labeling_subdtmc.addLabel(this->target_label);
            std::shared_ptr<storm::modelchecker::ExplicitQuantitativeCheckResult<ValueType> const> mdp_bound = this->mdp_bounds[formula_index];
            std::shared_ptr<storm::modelchecker::ExplicitQualitativeCheckResult const> mdp_target = this->mdp_targets[formula_index];
            for(StateType state = 0; state < dtmc_states; state++) {
                StateType mdp_state = this->state_map[state];
                double bound = (*mdp_bound)[mdp_state];
                bool target = (*mdp_target)[mdp_state];

                dtmc_bound[state] = bound;
                if(target) {
                    labeling_subdtmc.addLabelToState(this->target_label, state);
                }
            }
            // Associate true sink with the target label
            labeling_subdtmc.addLabelToState(this->target_label, sink_state_true);

            // Construct transition matrix (as well as the reward model) for the subdtmc
            if(!this->formula_reward[formula_index]) {
                // Probability formula: no reward models
                double default_bound = this->formula_safety[formula_index] ? 0 : 1;
                for(StateType state = 0; state < dtmc_states; state++) {
                    std::vector<std::pair<StateType,ValueType>> r;
                    double probability = use_mdp_bounds ? dtmc_bound[state] : default_bound;
                    r.emplace_back(sink_state_false, 1-probability);
                    r.emplace_back(sink_state_true, probability);
                    matrix_subdtmc.push_back(r);
                }
            } else {
                // Reward formula: one reward model
                assert(this->formula_safety[formula_index]);
                assert(dtmc->hasRewardModel(this->formula_reward_name[formula_index]));
                storm::models::sparse::StandardRewardModel<ValueType> const& reward_model_dtmc = dtmc->getRewardModel(this->formula_reward_name[formula_index]);
                assert(reward_model_dtmc.hasOnlyStateRewards());

                std::vector<ValueType> state_rewards_subdtmc(dtmc_states+2);
                double default_reward = 0;
                for(StateType state = 0; state < dtmc_states; state++) {
                    double reward = use_mdp_bounds ? dtmc_bound[state] : default_reward;
                    state_rewards_subdtmc[state] = reward;

                    std::vector<std::pair<StateType,ValueType>> r;
                    r.emplace_back(sink_state_true, 1);
                    matrix_subdtmc.push_back(r);
                }
                storm::models::sparse::StandardRewardModel<ValueType> reward_model_subdtmc(state_rewards_subdtmc, boost::none, boost::none);
                reward_models_subdtmc.emplace(this->formula_reward_name[formula_index], reward_model_subdtmc);
            }

            // Add self-loops to sink states
            for(StateType state = sink_state_false; state <= sink_state_true; state++) {
                std::vector<std::pair<StateType,ValueType>> r;
                r.emplace_back(state, 1);
                matrix_subdtmc.push_back(r);
            }
        }

        template <typename ValueType, typename StateType>
        bool Counterexample<ValueType,StateType>::expandAndCheck (
            uint_fast64_t index,
            std::vector<std::vector<std::pair<StateType,ValueType>>> & matrix_dtmc,
            std::vector<std::vector<std::pair<StateType,ValueType>>> & matrix_subdtmc,
            storm::models::sparse::StateLabeling const& labeling_subdtmc,
            std::unordered_map<std::string,storm::models::sparse::StandardRewardModel<ValueType>> & reward_models_subdtmc,
            std::vector<StateType> const& to_expand
        ) {

            // Get DTMC info
            uint_fast64_t dtmc_states = this->dtmc->getNumberOfStates();
            StateType initial_state = *(this->dtmc->getInitialStates().begin());
            
            // Expand states from the new wave: 
            // - expand transition probabilities
            for(StateType state : to_expand) {
                matrix_subdtmc[state] = std::move(matrix_dtmc[state]);
            }
            if(this->formula_reward[index]) {
                // - expand state rewards
                storm::models::sparse::StandardRewardModel<ValueType> const& reward_model_dtmc = dtmc->getRewardModel(this->formula_reward_name[index]);
                storm::models::sparse::StandardRewardModel<ValueType> & reward_model_subdtmc = (reward_models_subdtmc.find(this->formula_reward_name[index]))->second;
                for(StateType state : to_expand) {
                    reward_model_subdtmc.setStateReward(state, reward_model_dtmc.getStateReward(state));
                }
            }

            // Construct sub-DTMC
            storm::storage::SparseMatrixBuilder<ValueType> transitionMatrixBuilder(0, 0, 0, false, false, 0);
            for(StateType state = 0; state < dtmc_states+2; state++) {
                for(auto row_entry: matrix_subdtmc[state]) {
                    transitionMatrixBuilder.addNextValue(state, row_entry.first, row_entry.second);
                }
            }
            storm::storage::SparseMatrix<ValueType> sub_matrix = transitionMatrixBuilder.build();
            assert(sub_matrix.isProbabilistic());
            storm::storage::sparse::ModelComponents<ValueType> components(sub_matrix, labeling_subdtmc, reward_models_subdtmc);
            std::shared_ptr<storm::models::sparse::Model<ValueType>> subdtmc = storm::utility::builder::buildModelFromComponents(storm::models::ModelType::Dtmc, std::move(components));
            
            // Model check
            bool onlyInitialStatesRelevant = false;
            storm::modelchecker::CheckTask<storm::logic::Formula, ValueType> task(*(this->formula_modified[index]), onlyInitialStatesRelevant);
            std::unique_ptr<storm::modelchecker::CheckResult> result_ptr = storm::api::verifyWithSparseEngine<ValueType>(subdtmc, task);
            storm::modelchecker::ExplicitQualitativeCheckResult & result = result_ptr->asExplicitQualitativeCheckResult();
            bool satisfied = result[initial_state];

            return satisfied;
        }

        template <typename ValueType, typename StateType>
        std::vector<uint_fast64_t> Counterexample<ValueType,StateType>::constructCounterexample (
            uint_fast64_t formula_index, bool use_mdp_bounds
            ) {
            this->total.start();

            // Get DTMC info
            StateType dtmc_states = this->dtmc->getNumberOfStates();

            this->preparing_subdtmc.start();
            // Prepare to construct sub-DTMCs
            std::vector<std::vector<std::pair<StateType,ValueType>>> matrix_dtmc;
            std::vector<std::vector<std::pair<StateType,ValueType>>> matrix_subdtmc;
            storm::models::sparse::StateLabeling labeling_subdtmc(dtmc_states+2);
            std::unordered_map<std::string, storm::models::sparse::StandardRewardModel<ValueType>> reward_models_subdtmc;
            this->prepareSubdtmc(
                formula_index, use_mdp_bounds, matrix_dtmc,
                matrix_subdtmc, labeling_subdtmc, reward_models_subdtmc
            );
            this->preparing_subdtmc.stop();

            this->constructing_counterexample.start();
            // Explore subDTMCs wave by wave
            uint_fast64_t wave_last = this->wave_states.size()-1;
            uint_fast64_t wave = 0;
            while(true) {
                assert(wave <= wave_last);
                bool satisfied = this->expandAndCheck(
                    formula_index, matrix_dtmc, matrix_subdtmc, labeling_subdtmc,
                    reward_models_subdtmc, this->wave_states[wave]
                );
                if(!satisfied) {
                    break;
                }
                wave++;
            }

            // Return a set of critical holes
            std::vector<uint_fast64_t> critical_holes;
            for(uint_fast64_t hole = 0; hole < this->hole_count; hole++) {
                uint_fast64_t wave_registered = this->hole_wave[hole];
                if(wave_registered > 0 && wave_registered <= wave) {
                    critical_holes.push_back(hole);
                }
            }
            this->constructing_counterexample.stop();

            this->total.stop();

            return critical_holes;
        }

        template <typename ValueType, typename StateType>
        std::vector<double> Counterexample<ValueType,StateType>::stats (
        ) {
            std::vector<double> time_stats;
            double time_total = this->total.getTimeInMilliseconds();
            time_stats.push_back(time_total);

            time_stats.push_back(this->preparing_mdp.getTimeInMilliseconds() / time_total);
            time_stats.push_back(this->preparing_dtmc.getTimeInMilliseconds() / time_total);
            time_stats.push_back(this->preparing_subdtmc.getTimeInMilliseconds() / time_total);
            time_stats.push_back(this->constructing_counterexample.getTimeInMilliseconds() / time_total);
            
            return time_stats;
        }

         // Explicitly instantiate functions and classes.
        template class Counterexample<double, uint_fast64_t>;
        template std::pair<std::shared_ptr<storm::models::sparse::Model<double>>,std::vector<uint_fast64_t>> DtmcFromMdp<double, uint_fast64_t>(storm::models::sparse::Mdp<double> const&, storm::storage::FlatSet<uint_fast64_t> const&);

    } // namespace research
} // namespace storm
