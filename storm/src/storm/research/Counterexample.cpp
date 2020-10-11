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

        /*bool SimpleValuationReferenceLess::operator()(storm::expressions::SimpleValuation const& a, storm::expressions::SimpleValuation const& b) const {
            static storm::expressions::SimpleValuationPointerLess pointer_less;
            auto ptr_a = const_cast<storm::expressions::SimpleValuation *>(&a);
            auto ptr_b = const_cast<storm::expressions::SimpleValuation *>(&b);
            return pointer_less(ptr_a, ptr_b);
        }*/

        // MdpStateInfo::MdpStateInfo (double bound, bool target) : bound(bound), target(target) {}

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
            this->formula = std::make_shared<storm::logic::ProbabilityOperatorFormula>(eventually_formula, of.getOperatorInformation());
            

            // Associate MDP states with satisfiability probabilities and being a target one
            storm::storage::sparse::StateValuations const& mdp_state_valuations = mdp.getStateValuations();
            StateType mdp_states = mdp_state_valuations.getNumberOfStates();
            for(StateType state = 0; state < mdp_states; state++) {
                // std:: cout << "> p " <<  mdp_state_valuations.toString(state) << std::endl << std::flush;

                // storm::storage::sparse::StateValuations::StateValuation const& key = mdp_state_valuations.getValuation(state);
                std::string const& key = mdp_state_valuations.toString(state,false);

                // this->mdp_bound.emplace(key, mdp_result[state]);
                // this->mdp_target.emplace(key, mdp_target_states[state]);
                this->mdp_info.emplace(key, std::make_pair(mdp_result[state], mdp_target_states[state]));
                // std::cout << "> (s) em " << mdp_state_valuations.toString(state,false)<< std::endl;

                
                // This compute wrong edges (and holes): why?
                /*
                std::set<std::string> state_holes;
                for(uint_fast64_t edge: choice_origins.getEdgeIndexSet(state)) {
                    auto search = this->edge2holes.find(edge);
                    if(search == this->edge2holes.end()) {
                        continue;
                    }
                    std::set<std::string> & holes = search->second;
                    state_holes.insert(holes.begin(), holes.end());
                }
                this->mdp_holes.emplace(key, state_holes);
                */
                /*std::cout << "> p " << key << " {";
                for(auto hole: state_holes) {
                    std::cout << hole << ",";
                }
                std::cout << "}" << std::endl;*/
            }

            this->mdp_preprocessing.stop();
            this->total.stop();
            
        }

        template <typename ValueType, typename StateType>
        storm::storage::FlatSet<std::string> Counterexample<ValueType,StateType>::constructViaHoles (
            storm::models::sparse::Dtmc<ValueType> const& dtmc,
            bool use_mdp_bounds
        ) {

            this->total.start();
            this->dtmc_preprocessing.start();

            // Introduce expanded state space with two sink states
            StateType initial_state = *(dtmc.getInitialStates().begin());
            StateType dtmc_states = dtmc.getNumberOfStates();
            StateType sink_state_false = dtmc_states;
            StateType sink_state_true = dtmc_states+1;
            storm::storage::SparseMatrix<ValueType> const& matrix_dtmc = dtmc.getTransitionMatrix();
            storm::storage::sparse::JaniChoiceOrigins & choice_origins = dtmc.getChoiceOrigins()->asJaniChoiceOrigins();

            // Associate DTMC states with
            // - the bound on satisfiability probabilities
            // - being the target state
            // - relevant holes
            std::vector<double> dtmc_bound(dtmc_states+2, 0);
            std::vector<bool> dtmc_target(dtmc_states+2, false);
            std::vector<std::set<std::string>> dtmc_holes(dtmc_states);
            storm::storage::sparse::StateValuations const& dtmc_state_valuations = dtmc.getStateValuations();
            double default_bound = this->formula_safety ? 0 : 1;
            for(StateType state = 0; state < dtmc_states; state++) {
                // storm::storage::sparse::StateValuations::StateValuation const& key =  dtmc_state_valuations.getValuation(state);
                std::string const& key = dtmc_state_valuations.toString(state,false);
                // std::cout << "> (s) lu " << dtmc_state_valuations.toString(state,false)<< std::endl;
                
                auto search = this->mdp_info.find(key);
                assert(search != this->mdp_info.end());
                auto info = search->second;
                // dtmc_bound[state] = info.first;
                dtmc_bound[state] = use_mdp_bounds ? info.first : default_bound;
                dtmc_target[state] = info.second;

                /*auto search_bound = this->mdp_bound.find(key);
                assert(search_bound != this->mdp_bound.end());
                double probability = search_bound->second;
                dtmc_bound[state] = probability;

                auto search_target = this->mdp_target.find(key);
                assert(search_target != this->mdp_target.end());
                bool target = search_target->second;
                dtmc_target[state] = target;*/

                // This is wrong
                /*auto search_holes = this->mdp_holes.find(key);
                assert(search_holes != this->mdp_holes.end());
                std::set<std::string> holes = search_holes->second;
                dtmc_holes[state] = holes;*/
                
                std::set<std::string> relevant_holes;
                for(auto edge: choice_origins.getEdgeIndexSet(state)) {
                    auto holes = this->edge2holes[edge];
                    relevant_holes.insert(holes.begin(),holes.end());
                }
                dtmc_holes[state] = relevant_holes;
                    
            }
            dtmc_bound[sink_state_false] = 0;
            dtmc_target[sink_state_false] = false;
            dtmc_bound[sink_state_true] = 1;
            dtmc_target[sink_state_true] = true;

            // Mark all holes as unregistered
            // maps hole to the round when was registered (0 = unregistered)
            std::map<std::string, uint_fast64_t> hole_registered;
            for(std::string hole: this->family_relevant_holes) {
                hole_registered.emplace(hole,0);
            }
            
            // Count the number of relevant holes in each state
            std::vector<uint_fast64_t> unregistered_holes_count(dtmc_states, 0);
            for(StateType state = 0; state < dtmc_states; state++) {
                unregistered_holes_count[state] = dtmc_holes[state].size();
            }

            // Establish state expansion order:
            // - explore the reachable state space by expanding only 'non-blocking' states (states with registered holes);
            // - if no non-blocking state remains, pick a blocking candidate with the least amount of unregistered holes
            // - register all holes in this blocking candidate, thus unblocking this state (and possibly many others)
            // - rinse and repeat
            
            // Prepare to explore
            // round increases by one when new holes of a blocking candidate are registered
            uint_fast64_t current_round = 0;
            // true if the state was reached during exploration (expanded+horizons)
            storm::storage::BitVector encountered_flag(dtmc_states, false);
            // non-blocking horizon
            std::stack<StateType> state_horizon;
            // horizon containing, for a current round, only blocking states
            std::vector<StateType> state_horizon_blocking;
            // blocking state containing currently the least number of holes
            bool blocking_candidate_set = false;
            StateType blocking_candidate;
            // states encountered/expanded during each round
            std::vector<std::vector<StateType>> round_encountered;
            std::vector<std::vector<StateType>> round_expanded;
            
            // Round 0: encounter initial state first (important)
            round_encountered.push_back(std::vector<StateType>());
            round_expanded.push_back(std::vector<StateType>());
            encountered_flag.set(initial_state);
            round_encountered[current_round].push_back(initial_state);
            if(unregistered_holes_count[initial_state] == 0) {
                // non-blocking
                state_horizon.push(initial_state);
            } else {
                // blocking
                state_horizon_blocking.push_back(initial_state);
                blocking_candidate_set = true;
                blocking_candidate = initial_state;
            }
            // encounter both sink states
            round_encountered[current_round].push_back(sink_state_false);
            round_encountered[current_round].push_back(sink_state_true);

            // Explore the state space
            while(true) {
                // Expand the non-blocking horizon
                while(!state_horizon.empty()) {
                    StateType state = state_horizon.top();
                    state_horizon.pop();
                    for(auto entry: matrix_dtmc.getRow(state)) {
                        StateType successor = entry.getColumn();
                        if(encountered_flag[successor]) {
                            // already encountered
                            continue;
                        }
                        // encounter this successor
                        encountered_flag.set(successor);
                        round_encountered[current_round].push_back(successor);
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
                    round_expanded[current_round].push_back(state);
                }

                // Non-blocking horizon exhausted
                if(!blocking_candidate_set) {
                    // Nothing more to expand
                    break;
                }
                
                // Start a new round
                current_round++;
                round_encountered.push_back(std::vector<StateType>());
                round_expanded.push_back(std::vector<StateType>());
                blocking_candidate_set = false;
                
                // Register all holes of this blocking state
                for(std::string hole: dtmc_holes[blocking_candidate]) {
                    hole_registered[hole] = current_round;
                }

                // Recompute number of unregistered holes in each state
                for(StateType state = 0; state < dtmc_states; state++) {
                    unregistered_holes_count[state] = 0;
                    for(std::string hole: dtmc_holes[state]) {
                        if(hole_registered.find(hole)->second == 0) {
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
            uint_fast64_t rounds_total = current_round;

            // Sanity check
            /*for(current_round = 0; current_round <= rounds_total; current_round++) {

                storm::storage::FlatSet<std::string> critical_holes_this_round;
                for(auto const& entry : hole_registered) {
                    if(entry.second > 0 && entry.second <= current_round) {
                        critical_holes_this_round.insert(entry.first);
                    }
                }
                
                storm::storage::FlatSet<uint_fast64_t> critical_edges_this_round;
                for(uint_fast64_t round = 0; round <= current_round; round++) {
                    for(StateType state: round_expanded[round]) {
                        auto edges = choice_origins.getEdgeIndexSet(state);
                        critical_edges_this_round.insert(edges.begin(), edges.end());
                    }    
                }
                storm::storage::FlatSet<std::string> critical_holes_this_round_2;
                for(auto edge: critical_edges_this_round) {
                    auto holes = this->edge2holes[edge];
                    critical_holes_this_round_2.insert(holes.begin(),holes.end());
                }
                
                std::cout << "> r" << current_round << std::endl;
                std::cout << "> h1: {";
                for(auto hole: critical_holes_this_round)
                    std::cout << hole << ",";
                std::cout << "}" << std::endl;
                std::cout << "> h2: {";
                for(auto hole: critical_holes_this_round_2)
                    std::cout << hole << ",";
                std::cout << "}" << std::endl;
                assert(critical_holes_this_round.size() == critical_holes_this_round_2.size());
            }*/
            
            // Create a new index map
            // storm::storage::BitVector encountered_flag(dtmc_states+2, false);
            std::vector<StateType> state2index(dtmc_states+2, 0);
            std::vector<StateType> index2state(dtmc_states+2, 0);
            std::vector<uint_fast64_t> encountered_per_round;
            uint_fast64_t encountered_order = 0;
            for(uint_fast64_t round = 0; round <= rounds_total; round++) {
                for(StateType state: round_encountered[round]) {
                    state2index[state] = encountered_order;
                    index2state[encountered_order] = state;
                    encountered_order++;
                }
                encountered_per_round.push_back(encountered_order);
            }
            
            // Construct matrices (new index)
            typedef std::vector<std::pair<StateType,ValueType>> row;
            typedef std::vector<row> rows;

            // Matrix of shorctuts = initial matrix of a subDTMC
            rows matrix;
            for(StateType index = 0; index < dtmc_states+2; index++) {
                row r;
                StateType state = index2state[index];
                double probability = dtmc_bound[state];
                r.emplace_back(state2index[sink_state_false], 1-probability);
                r.emplace_back(state2index[sink_state_true], probability);
                matrix.push_back(r);
            }

            // Original matrix (old index for rows, new index for columns)
            rows matrix_original;
            for(StateType state = 0; state < dtmc_states; state++) {
                row r;
                for(auto entry: matrix_dtmc.getRow(state)) {
                    r.emplace_back(state2index[entry.getColumn()], entry.getValue());
                }
                matrix_original.push_back(r);
            }
            
            // Construct prototype labeling for all states (new index):
            // copy the labeling, add two new states & associate target label with the true sink
            storm::models::sparse::StateLabeling labeling(dtmc_states+2);
            labeling.addLabel(this->target_label);
            for(StateType state = 0; state < dtmc_states; state++) {
                if(dtmc_target[state]) {
                    labeling.addLabelToState(this->target_label, state2index[state]);
                }
            }
            labeling.addLabelToState(this->target_label, state2index[sink_state_true]);
            storm::storage::BitVector encountered_index_flag(dtmc_states+2, false);
            this->dtmc_preprocessing.stop();

            // Iteratively construct and model check subDTMCs
            // std::cout << "> (s) model checking..." << std::endl;
            for(current_round = 0; current_round <= rounds_total; current_round++) {
                // std::cout << "> mc round: " << current_round << " / " << rounds_total << std::endl;

                // Expand the states expanded during the current round
                this->other.start();
                for(StateType state: round_expanded[current_round]) {
                    StateType index = state2index[state];
                    matrix[index] = std::move(matrix_original[state]);
                }
                this->other.stop();

                // Construct sub-matrix
                this->constructing.start();
                storm::storage::SparseMatrixBuilder<ValueType> transitionMatrixBuilder(0, 0, 0, false, false, 0);
                for(StateType index = 0; index < encountered_per_round[current_round]; index++) {
                    // StateType state = index2state[index];
                    encountered_index_flag.set(index);
                    for(auto entry: matrix[index]) {
                        transitionMatrixBuilder.addNextValue(index, entry.first, entry.second);
                    }
                }
                storm::storage::SparseMatrix<ValueType> sub_matrix = transitionMatrixBuilder.build();
                assert(sub_matrix.isProbabilistic());

                // Construct sub-labeling
                storm::models::sparse::StateLabeling sub_labeling = labeling.getSubLabeling(encountered_index_flag);
                
                // Construct sub-DTMC
                storm::storage::sparse::ModelComponents<ValueType> components(sub_matrix, sub_labeling);
                std::shared_ptr<storm::models::sparse::Model<ValueType>> sub_dtmc = storm::utility::builder::buildModelFromComponents(storm::models::ModelType::Dtmc, std::move(components));
                this->constructing.stop();
                
                // Model check
                this->model_checking.start();
                bool onlyInitialStatesRelevant = false;
                // storm::modelchecker::CheckTask<storm::logic::Formula, ValueType> task(this->formula, onlyInitialStatesRelevant);
                storm::modelchecker::CheckTask<storm::logic::Formula, ValueType> task(*(this->formula), onlyInitialStatesRelevant);
                std::unique_ptr<storm::modelchecker::CheckResult> result_ptr = storm::api::verifyWithSparseEngine<ValueType>(sub_dtmc, task);
                storm::modelchecker::ExplicitQualitativeCheckResult & result = result_ptr->asExplicitQualitativeCheckResult();
                bool satisfied = result[state2index[initial_state]];
                this->model_checking.stop();
                if(!satisfied) {
                    // CE obtained
                    // std::cout << "> (s): unsat" << std::endl;
                    break;
                }
            }
            // Check that a CE has been actually obtained
            assert(current_round <= rounds_total);
            this->subchains_checked = current_round+1;

            // Return a set of critical holes
            this->other.start();
            storm::storage::FlatSet<std::string> critical_holes;
            for(auto const& entry : hole_registered) {
                if(entry.second > 0 && entry.second <= current_round) {
                    critical_holes.insert(entry.first);
                }
            }
            
            // Double check using a  set of critical edges
            /*storm::storage::FlatSet<uint_fast64_t> critical_edges;
            for(uint_fast64_t round = 0; round <= current_round; round++) {
                for(StateType state: round_expanded[round]) {
                    auto edges = choice_origins.getEdgeIndexSet(state);
                    critical_edges.insert(edges.begin(), edges.end());
                }                
            }
            storm::storage::FlatSet<std::string> critical_holes_2;
            for(auto edge: critical_edges) {
                auto holes = this->edge2holes[edge];
                critical_holes_2.insert(holes.begin(),holes.end());
            }*/

            /*std::cout << "> h1: {";
            for(auto hole: critical_holes)
                std::cout << hole << ",";
            std::cout << "}" << std::endl;
            std::cout << "> h2: {";
            for(auto hole: critical_holes_2)
                std::cout << hole << ",";
            std::cout << "}" << std::endl;*/
            // assert(critical_holes.size() == critical_holes_2.size());
            
            this->other.stop();
            this->total.stop();

            return critical_holes;
        }

        template <typename ValueType, typename StateType>
        storm::storage::FlatSet<StateType> Counterexample<ValueType,StateType>::constructViaStates (
            storm::models::sparse::Dtmc<ValueType> const& dtmc,
            storm::modelchecker::ExplicitQuantitativeCheckResult<ValueType> const& dtmc_result,
            uint_fast64_t expanded_per_iter,
            uint_fast64_t subchains_checked_limit    
        ) {
            this->total.start();
            this->dtmc_preprocessing.start();

            // Identify target states
            /*std::shared_ptr<storm::models::sparse::Dtmc<ValueType>> dtmc_shared = std::make_shared<storm::models::sparse::Dtmc<ValueType>>(dtmc);
            bool onlyInitialStatesRelevant = false;
            storm::modelchecker::CheckTask<storm::logic::Formula, ValueType> task(*(this->target_states_predicate), onlyInitialStatesRelevant);
            std::unique_ptr<storm::modelchecker::CheckResult> result_ptr = storm::api::verifyWithSparseEngine<ValueType>(dtmc_shared, task);
            storm::modelchecker::ExplicitQualitativeCheckResult & dtmc_target = result_ptr->asExplicitQualitativeCheckResult();*/

            // Introduce expanded state space
            StateType initial_state = *(dtmc.getInitialStates().begin());
            assert(initial_state == 0);
            StateType dtmc_states = dtmc.getNumberOfStates();
            StateType sink_state_false = dtmc_states;
            StateType sink_state_true = dtmc_states+1;
            storm::storage::SparseMatrix<ValueType> const& matrix_dtmc = dtmc.getTransitionMatrix();

            // Associate DTMC states with satisfiability probabilities
            std::vector<double> dtmc_bound(dtmc_states+2, 0);
            std::vector<bool> dtmc_target(dtmc_states+2, false);
            storm::storage::sparse::StateValuations const& dtmc_state_valuations = dtmc.getStateValuations();
            for(StateType state = 0; state < dtmc_states; state++) {
                // storm::storage::sparse::StateValuations::StateValuation const& key =  dtmc_state_valuations.getValuation(state);
                std::string const& key = dtmc_state_valuations.toString(state,false);
                
                auto search = this->mdp_info.find(key);
                assert(search != this->mdp_info.end());
                auto info = search->second;
                dtmc_bound[state] = info.first;
                dtmc_target[state] = info.second;

                /*auto search_bound = this->mdp_bound.find(key);
                assert(search_bound != this->mdp_bound.end());
                double probability = search_bound->second;
                dtmc_bound[state] = probability;

                auto search_target = this->mdp_target.find(key);
                assert(search_target != this->mdp_target.end());
                bool target = search_target->second;
                dtmc_target[state] = target;*/

            }
            dtmc_bound[sink_state_false] = 0;
            dtmc_target[sink_state_false] = false;
            dtmc_bound[sink_state_true] = 1;
            dtmc_target[sink_state_true] = true;

            // Precompute encounter and expansion order: encountered = in subDTMC, expanded = has original transitions

            // Notation: state in DTMC, index in subDTMC 
            StateType encountered_states = 0;
            storm::storage::BitVector encountered_flag(dtmc_states+2, false);
            std::vector<StateType> index2state(dtmc_states+2, 0);
            std::vector<StateType> state2index(dtmc_states+2, 0);
            StateType expanded_states = 0;
            // storm::storage::BitVector expanded_flag(dtmc_states+2, false);
            std::vector<StateType> expanded_index2state(dtmc_states+2, 0);
            std::vector<StateType> expanded_state2index(dtmc_states+2, 0);
            std::vector<StateType> encountered_per_expansion(dtmc_states+2, 0);

            // Encounter initial state and two sink states
            for(StateType state: {initial_state, sink_state_false, sink_state_true}) {
                encountered_flag.set(state);
                index2state[encountered_states] = state;
                state2index[state] = encountered_states;
                encountered_states++;
            }
            encountered_per_expansion[expanded_states] = encountered_states;

            // Priority queue by the bound type: 
            std::vector<ValueType> const& vector_dtmc_bound = (dtmc_result.getValueVector());
            // auto cmp_dtmc_bound = [&] (StateType a, StateType b) { return (this->formula_safety ? vector_dtmc_bound[a] < vector_dtmc_bound[b] : vector_dtmc_bound[a] > vector_dtmc_bound[b]) || a > b; };
            auto cmp_dtmc_bound = [&] (StateType a, StateType b) { return (this->formula_safety ? vector_dtmc_bound[a] > vector_dtmc_bound[b] : vector_dtmc_bound[a] < vector_dtmc_bound[b]) || a > b; };
            // auto cmp_bfs = [&] (StateType a, StateType b) { return a > b; }; // breadth-first search
            auto cmp = cmp_dtmc_bound;
            std::priority_queue<StateType, std::vector<StateType>, decltype(cmp)> state_horizon(cmp);
            
            // Explore the state space starting from the initial state
            state_horizon.push(initial_state);
            while(!state_horizon.empty()) {
                StateType state = state_horizon.top();
                state_horizon.pop();
                for(auto entry: matrix_dtmc.getRow(state)) {
                    StateType successor = entry.getColumn();
                    if(!encountered_flag[successor]) {
                        encountered_flag.set(successor);
                        index2state[encountered_states] = successor;
                        state2index[successor] = encountered_states;
                        encountered_states++;
                        state_horizon.push(successor);
                    }
                }
                expanded_index2state[expanded_states] = state;
                expanded_state2index[state] = expanded_states;
                // expanded_flag.set(state);
                expanded_states++;
                encountered_per_expansion[expanded_states] = encountered_states;
            }

            // Construct matrices (new index)
            typedef std::vector<std::pair<StateType,ValueType>> row;
            typedef std::vector<row> rows;

            // Matrix of shorctuts = initial matrix of a subDTMC
            rows matrix;
            for(StateType index = 0; index < dtmc_states+2; index++) {
                row r;
                StateType state = index2state[index];
                double probability = dtmc_bound[state];
                r.emplace_back(state2index[sink_state_false], 1-probability);
                r.emplace_back(state2index[sink_state_true], probability);
                matrix.push_back(r);
            }

            // Original matrix (new index)
            rows matrix_original;
            for(StateType index = 0; index < dtmc_states+2; index++) {
                row r;
                StateType state = index2state[index];
                if(state == sink_state_false || state == sink_state_true) {
                    // blank row: it shound never be required
                } else {
                    for(auto entry: matrix_dtmc.getRow(state)) {
                        r.emplace_back(state2index[entry.getColumn()], entry.getValue());
                    }
                }
                matrix_original.push_back(r);
            }
            
            // Construct prototype labeling for all states (new index):
            // copy the labeling, add two new states & associate target label with the true sink
            storm::models::sparse::StateLabeling labeling(dtmc_states+2);
            labeling.addLabel(this->target_label);
            for(StateType state = 0; state < dtmc_states; state++) {
                if(dtmc_target[state]) {
                    labeling.addLabelToState(this->target_label, state2index[state]);
                }
            }
            labeling.addLabelToState(this->target_label, state2index[sink_state_true]);
            
            this->dtmc_preprocessing.stop();

            // Construct a state subspace with only initial state and two sink states
            this->other.start();
            encountered_flag.clear(); // which indices are encountered
            // expanded_flag.clear();  // which states are expanded (don't really need this)
            expanded_states = 0;
            for(StateType index = 0; index < encountered_per_expansion[expanded_states]; index++) {
                encountered_flag.set(index);
            }
            this->other.stop();

            // Iteratively construct and model check subDTMCs
            this->subchains_checked = 0;
            while(true) {
                // Expand the state horizon
                this->other.start();
                for(StateType expanded = 0; expanded < expanded_per_iter; expanded++) {
                    // Encounter new states
                    for(StateType index = encountered_per_expansion[expanded_states]; index < encountered_per_expansion[expanded_states+1]; index++) {
                        encountered_flag.set(index);
                    }
                    // Replace transitions with original ones
                    StateType state = expanded_index2state[expanded_states];
                    StateType encountered_index = state2index[state];
                    matrix[encountered_index] = std::move(matrix_original[encountered_index]);
                    // expanded_flag.set(expanded_index2state[expanded_states]);
                    expanded_states++;
                    if(expanded_states == dtmc_states) {
                        // This is definitely a critical subsystem
                        break;
                    }
                }
                this->other.stop();

                // Construct sub-matrix
                this->constructing.start();
                storm::storage::SparseMatrixBuilder<ValueType> transitionMatrixBuilder(0, 0, 0, false, false, 0);
                for(StateType index = 0; index < encountered_per_expansion[expanded_states]; index++) {
                    for(auto entry: matrix[index]) {
                        transitionMatrixBuilder.addNextValue(index, entry.first, entry.second);
                    }
                }
                storm::storage::SparseMatrix<ValueType> sub_matrix = transitionMatrixBuilder.build();

                // Construct sub-labeling
                storm::models::sparse::StateLabeling sub_labeling = labeling.getSubLabeling(encountered_flag);
                
                // Construct sub-DTMC
                storm::storage::sparse::ModelComponents<ValueType> components(sub_matrix, sub_labeling);
                std::shared_ptr<storm::models::sparse::Model<ValueType>> sub_dtmc = storm::utility::builder::buildModelFromComponents(storm::models::ModelType::Dtmc, std::move(components));
                this->constructing.stop();
                
                // Model check
                this->model_checking.start();
                bool onlyInitialStatesRelevant = false;
                // storm::modelchecker::CheckTask<storm::logic::Formula, ValueType> task(this->formula, onlyInitialStatesRelevant);
                storm::modelchecker::CheckTask<storm::logic::Formula, ValueType> task(*(this->formula), onlyInitialStatesRelevant);
                std::unique_ptr<storm::modelchecker::CheckResult> result_ptr = storm::api::verifyWithSparseEngine<ValueType>(sub_dtmc, task);
                storm::modelchecker::ExplicitQualitativeCheckResult & result = result_ptr->asExplicitQualitativeCheckResult();
                bool satisfied = result[state2index[initial_state]];
                this->subchains_checked++;
                this->model_checking.stop();
                if(!satisfied) {
                    break;
                }
                if(this->subchains_checked == subchains_checked_limit) {
                    // Too slow: return the most conservative critical subsystem
                    expanded_states = dtmc_states;
                    break;
                }
            }

            // Construct a set of critical edges = edges of each expanded state
            this->other.start();
            storm::storage::sparse::JaniChoiceOrigins & choice_origins = dtmc.getChoiceOrigins()->asJaniChoiceOrigins();
            storm::storage::FlatSet<StateType> critical_edges;
            std::set<StateType> critical_states;
            for(StateType index = 0; index < expanded_states; index++) {
                for(StateType edge: choice_origins.getEdgeIndexSet(expanded_index2state[index])) {
                    critical_edges.insert(edge);
                }
            }
            this->other.stop();
            this->total.stop();

            return critical_edges;
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

