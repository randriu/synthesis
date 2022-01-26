// author: Roman Andriushchenko

#include "storm-synthesis/synthesis/Counterexample.h"

#include <queue>
#include <deque>
#include "storm/storage/BitVector.h"

#include "storm/storage/sparse/JaniChoiceOrigins.h"
#include "storm/storage/sparse/StateValuations.h"

#include "storm/utility/builder.h"
#include "storm/storage/SparseMatrix.h"
#include "storm/storage/sparse/ModelComponents.h"
#include "storm/models/sparse/StateLabeling.h"

#include "storm/solver/OptimizationDirection.h"

#include "storm/api/verification.h"
#include "storm/logic/Bound.h"
#include "storm/modelchecker/CheckTask.h"

namespace storm {
    namespace synthesis {

        template <typename ValueType, typename StateType>
        std::shared_ptr<storm::modelchecker::ExplicitQualitativeCheckResult> CounterexampleGenerator<ValueType,StateType>::labelStates(
            storm::models::sparse::Mdp<ValueType> const& mdp,
            storm::logic::Formula const& label
        ) {
            std::shared_ptr<storm::models::sparse::Mdp<ValueType>> mdp_shared = std::make_shared<storm::models::sparse::Mdp<ValueType>>(mdp);
            bool onlyInitialStatesRelevant = false;
            storm::modelchecker::CheckTask<storm::logic::Formula, ValueType> task(label, onlyInitialStatesRelevant);
            std::unique_ptr<storm::modelchecker::CheckResult> result_ptr = storm::api::verifyWithSparseEngine<ValueType>(mdp_shared, task);
            std::shared_ptr<storm::modelchecker::ExplicitQualitativeCheckResult> mdp_target = std::make_shared<storm::modelchecker::ExplicitQualitativeCheckResult>(result_ptr->asExplicitQualitativeCheckResult());
            return mdp_target;
        }

        template <typename ValueType, typename StateType>
        CounterexampleGenerator<ValueType,StateType>::CounterexampleGenerator (
            storm::models::sparse::Mdp<ValueType> const& quotient_mdp,
            uint_fast64_t hole_count,
            std::vector<std::set<uint_fast64_t>> const& mdp_holes,
            std::vector<std::shared_ptr<storm::logic::Formula const>> const& formulae
            ) : quotient_mdp(quotient_mdp), hole_count(hole_count), mdp_holes(mdp_holes) {

            // create label formulae for our own labels
            std::shared_ptr<storm::logic::Formula const> const& target_label_formula = std::make_shared<storm::logic::AtomicLabelFormula>(this->target_label);
            std::shared_ptr<storm::logic::Formula const> const& until_label_formula = std::make_shared<storm::logic::AtomicLabelFormula>(this->until_label);

            // process all formulae
            for(auto formula: formulae) {

                // store formula type and optimality type
                assert(formula->isOperatorFormula());
                storm::logic::OperatorFormula const& of = formula->asOperatorFormula();
                
                assert(of.hasOptimalityType());
                storm::solver::OptimizationDirection ot = of.getOptimalityType();
                bool is_safety = ot == storm::solver::OptimizationDirection::Minimize;
                this->formula_safety.push_back(is_safety);

                bool is_reward = formula->isRewardOperatorFormula();
                this->formula_reward.push_back(is_reward);
                if(!is_reward) {
                    this->formula_reward_name.push_back("");
                } else {
                    this->formula_reward_name.push_back(formula->asRewardOperatorFormula().getRewardModelName());
                }

                // extract predicate for until and target states and identify such states
                storm::logic::Formula const& osf = of.getSubformula();
                if(!osf.isUntilFormula() && !osf.isEventuallyFormula()) {
                    throw storm::exceptions::NotImplementedException() << "Only until or reachability formulae supported.";
                }

                std::shared_ptr<storm::logic::Formula const> modified_subformula;
                if(osf.isUntilFormula()) {
                    storm::logic::UntilFormula const& uf = osf.asUntilFormula();
                    
                    auto mdp_until = this->labelStates(this->quotient_mdp,uf.getLeftSubformula());
                    this->mdp_untils.push_back(mdp_until);

                    auto mdp_target = this->labelStates(this->quotient_mdp, uf.getRightSubformula());
                    this->mdp_targets.push_back(mdp_target);

                    modified_subformula = std::make_shared<storm::logic::UntilFormula>(until_label_formula, target_label_formula);
                } else if(osf.isEventuallyFormula()) {
                    storm::logic::EventuallyFormula const& ef = osf.asEventuallyFormula();

                    this->mdp_untils.push_back(NULL);

                    auto mdp_target = this->labelStates(this->quotient_mdp,ef.getSubformula());
                    this->mdp_targets.push_back(mdp_target);

                    modified_subformula = std::make_shared<storm::logic::EventuallyFormula>(target_label_formula, ef.getContext());
                }

                // integrate formula into original context
                std::shared_ptr<storm::logic::Formula> modified_formula;
                if(!is_reward) {
                    modified_formula = std::make_shared<storm::logic::ProbabilityOperatorFormula>(modified_subformula, of.getOperatorInformation());
                } else {
                    modified_formula = std::make_shared<storm::logic::RewardOperatorFormula>(modified_subformula, this->formula_reward_name.back(), of.getOperatorInformation());
                }
                this->formula_modified.push_back(modified_formula);     
            }
        }

        template <typename ValueType, typename StateType>
        void CounterexampleGenerator<ValueType,StateType>::prepareDtmc(
            storm::models::sparse::Mdp<ValueType> const& dtmc,
            std::vector<uint_fast64_t> const& state_map
            ) {
            std::cout << "before anything..." << std::endl;

            // Clear up previous DTMC metadata
            this->hole_wave.clear();
            this->wave_states.clear();

            // Get DTMC info
            this->dtmc = std::make_shared<storm::models::sparse::Mdp<ValueType>>(dtmc);
            this->state_map = state_map;
            uint_fast64_t dtmc_states = this->dtmc->getNumberOfStates();
            StateType initial_state = *(this->dtmc->getInitialStates().begin());
            storm::storage::SparseMatrix<ValueType> const& transition_matrix = this->dtmc->getTransitionMatrix();

            std::cout << "before anything something......" << std::endl;

            // Mark all holes as unregistered
            for(uint_fast64_t index = 0; index < this->hole_count; index++) {
                this->hole_wave.push_back(0);
            }

            std::cout << "after mark all hole..." << std::endl;

            // Associate states of a DTMC with relevant holes and store their count
            std::vector<std::set<uint_fast64_t>> dtmc_holes(dtmc_states);
            std::cout << "dtmc states" << std::endl;
            std::vector<uint_fast64_t> unregistered_holes_count(dtmc_states, 0);
            std::cout << "dtmc unregistered hole count..." << std::endl;

            std::cout << "how many states -->:" << dtmc_states << std::endl;

            for(StateType state = 0; state < dtmc_states; state++) {
                std::cout << state << std::endl;
                dtmc_holes[state] = this->mdp_holes[state_map[state]];
                unregistered_holes_count[state] = dtmc_holes[state].size();
            }

            std::cout << "before prepare exploration space......" << std::endl;

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

            std::cout << "before exploration space......" << std::endl;

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
        }

        template <typename ValueType, typename StateType>
        bool CounterexampleGenerator<ValueType,StateType>::includesFce(
            std::unordered_map<int, int> hole_options,
            std::vector<std::vector<int>> options_l2) {

            for (auto const& hole : hole_options) {
                const int hole_index = hole.first;
                const int option = hole.second;

                std::vector<int> options_l1 = options_l2[hole_index];

                if (!(std::find(options_l1.begin(), options_l1.end(), option) != options_l1.end())) {
                    return false;
                }
            }
            return true;
       }

        template <typename ValueType, typename StateType>
        bool CounterexampleGenerator<ValueType,StateType>::improves_optimum(bool reward, ValueType result, int iteration,
            bool sketch_spec_optimality_minimizing, ValueType current_optimum) {
            if (!result_valid(reward, result)) {
                return false;
            }
            // self.optimum is None
            if (iteration == 0) {
                return true;
            }
            // sketch_spec_optimality_minimizing -> true
            if (sketch_spec_optimality_minimizing) {
                return result < current_optimum;
//                self.op = operator.lt
//                self.threshold = math.inf
            } else {
                return result > current_optimum;
//                self.op = operator.gt
//                self.threshold = -math.inf
            }
        }

        template <typename ValueType, typename StateType>
        bool CounterexampleGenerator<ValueType,StateType>::result_valid(bool reward, ValueType result) {
            return !reward || result != std::numeric_limits<double>::max();
        }

        template <typename ValueType, typename StateType>
        std::vector<bool> CounterexampleGenerator<ValueType,StateType>::invoke_cegis_parallel_execution(
            std::vector<std::vector<std::string>> hole_name_l2,
            std::vector<std::vector<std::vector<std::string>>> option_labels_l3,
            std::vector<std::vector<std::vector<int>>> options_l3,
            storm::models::sparse::Mdp<ValueType> quotient_mdp,
            storm::storage::BitVector default_actions,
            std::vector<std::unordered_map<int, int>> action_to_hole_options,
            // 2.point parameters...
            std::vector<int> family_property_indices,    // there is no need for each assignment has different family_property_indices (all assignments are in one family...)
            std::vector<int> specification_constraints,
            bool specification_has_optimality,
            std::shared_ptr<storm::logic::Formula const> const& formulae,
            // 3.point parameters
            bool sketch_spec_optimality_minimizing,
            double current_optimum,
            float current_threshold,
            float sketch_spec_optimality_epsilon,
            bool sketch_spec_optimality_reward,
            // 4.point parameters
            storm::synthesis::CounterexampleGenerator<>& ce_generator
            ) {
            // return type
            std::vector<bool> returnValue = {false, false};

            // I. for each assigment analyze...
            int assignment_index = 0;

            for (int assignment_index = 0; assignment_index < hole_name_l2.size(); assignment_index++) {
                // -------------------------------------
                // 1. build DTMC from quotient_mdp
                // -------------------------------------
                // a) select_actions method
                storm::storage::BitVector selected_actions = default_actions;

                for (int i = 0; i < quotient_mdp.getNumberOfChoices(); i++) {
                    if (selected_actions[i] != 0) {
                        continue;
                    }
                    std::unordered_map<int, int> hole_options = action_to_hole_options[i];

                    if (includesFce(hole_options, options_l3[assignment_index])) {
                        selected_actions.set(i);
                    }
                }
                // b) restrict_quotient method

                bool keep_unreachable_states = false;
                storm::transformer::SubsystemBuilderOptions subsystem_options = storm::transformer::SubsystemBuilderOptions();
                subsystem_options.buildStateMapping = true;
                subsystem_options.buildActionMapping = true;
                storm::storage::BitVector all_states(quotient_mdp.getNumberOfStates(), true);

                // DTMC builder...
                storm::transformer::SubsystemBuilderReturnType<ValueType> submodel_construction = storm::transformer::buildSubsystem(quotient_mdp, all_states, selected_actions, false, subsystem_options);

                std::shared_ptr<storm::models::sparse::Model<double, storm::models::sparse::StandardRewardModel<double>>> dtmc = submodel_construction.model;
                std::vector<uint_fast64_t> state_map = submodel_construction.newToOldStateIndexMapping;
                std::vector<uint64_t> choice_map = submodel_construction.newToOldActionIndexMapping;

                // -------------------------------------
                // 2. Model check all properties
                // -------------------------------------
                bool short_evaluation = false;
                // this encapsulate -> constraints_result = self.check_constraints(specification.constraints, property_indices, short_evaluation)
                std::vector<bool> result;
                bool constraints_result_all_sat = true;

                bool spec_optimality_result_improves = false;
                double model_check_result;

                if (!(short_evaluation && ! constraints_result_all_sat) && specification_has_optimality) {
                    // optimality_result = self.model_check_property(specification.optimality)
                    bool onlyInitialStatesRelevant = false;

                    storm::modelchecker::CheckTask<storm::logic::Formula, ValueType> task(*formulae, onlyInitialStatesRelevant);
                    std::unique_ptr<storm::modelchecker::CheckResult> result_ptr = storm::api::verifyWithSparseEngine<ValueType>(dtmc, task);
                    // result,value = self.model_check_formula(formula)
                    storm::modelchecker::ExplicitQuantitativeCheckResult<ValueType>& result = result_ptr->asExplicitQuantitativeCheckResult<ValueType>();

                    std::cout << result << std::endl;
                    // print initial state value
                    std::cout << result[0] << std::endl;
                    model_check_result = result[0];
                }
                // -------------------------------------
                // 3.point - Analyze model check results
                // -------------------------------------
                if (constraints_result_all_sat) {
                    if (!specification_has_optimality) {
                        // return True, True
                        return {true, true};
                    }
                    // bool reward, ValueType result, int iteration, bool sketch_spec_optimality_minimizing, ValueType current_optimum
                    if (improves_optimum(sketch_spec_optimality_reward, model_check_result, assignment_index, sketch_spec_optimality_minimizing, current_optimum)) {
                        current_optimum = model_check_result;
                        if (sketch_spec_optimality_minimizing) {
                            current_threshold = current_optimum * (1 - sketch_spec_optimality_epsilon);
                        } else {
                            current_threshold = current_optimum * (1 + sketch_spec_optimality_epsilon);
                        }
                        // improving -> true
                        returnValue[1] = true;
                    }
                }
                // -------------------------------------
                // 4.point - Prepare DTMC
                // -------------------------------------
                std::cout << "here.." << std::endl;
                ce_generator.prepareDtmc(dtmc, state_map);
                std::cout << "here..1" << std::endl;
                // -------------------------------------
                // 5.point - Generation of conflicts
                // -------------------------------------
            }
            return returnValue;
        }

        template <typename ValueType, typename StateType>
        void CounterexampleGenerator<ValueType,StateType>::prepareSubdtmc (
            uint_fast64_t formula_index,
            std::shared_ptr<storm::modelchecker::ExplicitQuantitativeCheckResult<ValueType> const> mdp_bounds,
            std::vector<std::vector<std::pair<StateType,ValueType>>> & matrix_subdtmc,
            storm::models::sparse::StateLabeling & labeling_subdtmc,
            std::unordered_map<std::string,storm::models::sparse::StandardRewardModel<ValueType>> & reward_models_subdtmc
            ) {

            // Typedefs for matrices
            // typedef std::vector<std::pair<StateType,ValueType>> row;
            // typedef std::vector<row> matrix;

            // Get DTMC info
            StateType dtmc_states = dtmc->getNumberOfStates();
            
            // Introduce expanded state space
            uint_fast64_t sink_state_false = dtmc_states;
            uint_fast64_t sink_state_true = dtmc_states+1;

            // Label target states of a DTMC
            std::shared_ptr<storm::modelchecker::ExplicitQualitativeCheckResult const> mdp_target = this->mdp_targets[formula_index];
            std::shared_ptr<storm::modelchecker::ExplicitQualitativeCheckResult const> mdp_until = this->mdp_untils[formula_index];
            labeling_subdtmc.addLabel(this->target_label);
            labeling_subdtmc.addLabel(this->until_label);
            for(StateType state = 0; state < dtmc_states; state++) {
                StateType mdp_state = this->state_map[state];
                if((*mdp_target)[mdp_state]) {
                    labeling_subdtmc.addLabelToState(this->target_label, state);
                }
                if(mdp_until != NULL && (*mdp_until)[mdp_state]) {
                    labeling_subdtmc.addLabelToState(this->until_label, state);
                }
            }
            // Associate true sink with the target label
            labeling_subdtmc.addLabelToState(this->target_label, sink_state_true);

            // Construct transition matrix (as well as the reward model) for the subdtmc
            if(!this->formula_reward[formula_index]) {
                // Probability formula: no reward models
                double default_bound = this->formula_safety[formula_index] ? 0 : 1;
                for(StateType state = 0; state < dtmc_states; state++) {
                    StateType mdp_state = this->state_map[state];
                    std::vector<std::pair<StateType,ValueType>> r;
                    double probability = mdp_bounds != NULL ? (*mdp_bounds)[mdp_state] : default_bound;
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
                    StateType mdp_state = this->state_map[state];
                    double reward = mdp_bounds != NULL ? (*mdp_bounds)[mdp_state] : default_reward;
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
        bool CounterexampleGenerator<ValueType,StateType>::expandAndCheck (
            uint_fast64_t index,
            ValueType formula_bound,
            std::vector<std::vector<std::pair<StateType,ValueType>>> & matrix_subdtmc,
            storm::models::sparse::StateLabeling const& labeling_subdtmc,
            std::unordered_map<std::string,storm::models::sparse::StandardRewardModel<ValueType>> & reward_models_subdtmc,
            std::vector<StateType> const& to_expand
        ) {
            
            // Get DTMC info
            uint_fast64_t dtmc_states = this->dtmc->getNumberOfStates();
            storm::storage::SparseMatrix<ValueType> const& transition_matrix = this->dtmc->getTransitionMatrix();
            StateType initial_state = *(this->dtmc->getInitialStates().begin());
            
            // Expand states from the new wave: 
            // - expand transition probabilities
            for(StateType state : to_expand) {
                matrix_subdtmc[state].clear();
                for(auto entry: transition_matrix.getRow(state)) {
                    matrix_subdtmc[state].emplace_back(entry.getColumn(), entry.getValue());
                }
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
            storm::modelchecker::ExplicitQuantitativeCheckResult<ValueType>& result = result_ptr->asExplicitQuantitativeCheckResult<ValueType>();
            bool satisfied;
            if(this->formula_safety[index]) {
                satisfied = result[initial_state] < formula_bound;
            } else {
                satisfied = result[initial_state] > formula_bound;
            }

            return satisfied;
        }

        template <typename ValueType, typename StateType>
        std::vector<uint_fast64_t> CounterexampleGenerator<ValueType,StateType>::constructConflict (
            uint_fast64_t formula_index,
            ValueType formula_bound,
            std::shared_ptr<storm::modelchecker::ExplicitQuantitativeCheckResult<ValueType> const> mdp_bounds
            ) {
            
            // Get DTMC info
            StateType dtmc_states = this->dtmc->getNumberOfStates();
            
            // Prepare to construct sub-DTMCs
            std::vector<std::vector<std::pair<StateType,ValueType>>> matrix_subdtmc;
            storm::models::sparse::StateLabeling labeling_subdtmc(dtmc_states+2);
            std::unordered_map<std::string, storm::models::sparse::StandardRewardModel<ValueType>> reward_models_subdtmc;
            this->prepareSubdtmc(
                formula_index, mdp_bounds, matrix_subdtmc, labeling_subdtmc, reward_models_subdtmc
            );

            // Explore subDTMCs wave by wave
            uint_fast64_t wave_last = this->wave_states.size()-1;
            uint_fast64_t wave = 0;
            while(true) {
                bool satisfied = this->expandAndCheck(
                    formula_index, formula_bound, matrix_subdtmc, labeling_subdtmc,
                    reward_models_subdtmc, this->wave_states[wave]
                );
                if(!satisfied) {
                    break;
                }
                if(wave == wave_last) {
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

            return critical_holes;
        }

         // Explicitly instantiate functions and classes.
        template class CounterexampleGenerator<double, uint_fast64_t>;

    } // namespace research
} // namespace storm
