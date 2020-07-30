// author: Roman Andriushchenko

#include "storm/research/Counterexample.h"

#include "storm/storage/sparse/StateValuations.h"
#include "storm/models/sparse/StateLabeling.h"
#include "storm/storage/SparseMatrix.h"
#include "storm/storage/sparse/ModelComponents.h"

#include "storm/modelchecker/results/ExplicitQualitativeCheckResult.h"
#include "storm/utility/builder.h"

#include "storm/modelchecker/CheckTask.h"
#include "storm/api/verification.h"

#include <queue>
#include <typeinfo>
#include <boost/optional.hpp>

#include "storm/utility/Stopwatch.h"
#include "storm/logic/CloneVisitor.h"
#include "storm/logic/ComparisonType.h"
#include "storm/logic/Bound.h"

#include "storm/storage/sparse/JaniChoiceOrigins.h"
#include "storm/storage/BitVector.h"

namespace storm {
    namespace research {

        /*bool SimpleValuationReferenceLess::operator()(storm::expressions::SimpleValuation const& a, storm::expressions::SimpleValuation const& b) const {
            static storm::expressions::SimpleValuationPointerLess pointer_less;
            auto ptr_a = const_cast<storm::expressions::SimpleValuation *>(&a);
            auto ptr_b = const_cast<storm::expressions::SimpleValuation *>(&b);
            return pointer_less(ptr_a, ptr_b);
        }*/

        template <typename ValueType, typename StateType>
        Counterexample<ValueType,StateType>::Counterexample (
            uint_fast64_t expanded_per_iter,
            storm::logic::Formula const& formula,
            storm::models::sparse::Mdp<ValueType> const& mdp,
            storm::modelchecker::ExplicitQuantitativeCheckResult<ValueType> const& mdp_result
        ) : expanded_per_iter(expanded_per_iter), formula(formula) {
            this->total.start();
            this->mdp_preprocessing.start();

            assert(this->formula.isOperatorFormula());
            storm::logic::OperatorFormula const& of = this->formula.asOperatorFormula();
            assert(of.hasBound());
            storm::logic::ComparisonType ct = of.getComparisonType();
            this->formula_safety = ct == storm::logic::ComparisonType::Less || ct == storm::logic::ComparisonType::LessEqual;

            // Associate MDP states with satisfiability probabilities
            storm::storage::sparse::StateValuations const& mdp_state_valuations = mdp.getStateValuations();
            StateType mdp_states = mdp_state_valuations.getNumberOfStates();
            for(StateType state = 0; state < mdp_states; state++) {
                storm::storage::sparse::StateValuations::StateValuation const& valuation = mdp_state_valuations.getValuation(state);
                double probability = mdp_result[state];
                this->mdp_bound.emplace(valuation, probability);
            }

             // Identify the target label
            storm::models::sparse::StateLabeling labeling = mdp.getStateLabeling();
            std::set<std::string> reserved_labels {"init", "deadlock", "overlap_guards", "out_of_bounds"};
            std::set<std::string> labels = labeling.getLabels();
            std::set<std::string> non_reserved;
            std::set_difference(
                labels.begin(), labels.end(),
                reserved_labels.begin(), reserved_labels.end(),
                std::inserter(non_reserved, non_reserved.begin())
            );
            assert(non_reserved.size() == 1);
            this->target_label = *(non_reserved.begin());

            this->mdp_preprocessing.stop();
            this->total.stop();
        }

        template <typename ValueType, typename StateType>
        storm::storage::FlatSet<StateType> Counterexample<ValueType,StateType>::construct (
            storm::models::sparse::Dtmc<ValueType> const& dtmc,
            storm::modelchecker::ExplicitQuantitativeCheckResult<ValueType> const& dtmc_result
        ) {
            this->total.start();
            this->dtmc_preprocessing.start();

            // Introduce expanded state space
            StateType initial_state = *(dtmc.getInitialStates().begin());
            assert(initial_state == 0);
            StateType dtmc_states = dtmc.getNumberOfStates();
            StateType sink_state_false = dtmc_states;
            StateType sink_state_true = dtmc_states+1;
            storm::storage::SparseMatrix<ValueType> const& matrix_dtmc = dtmc.getTransitionMatrix();

            // Associate DTMC states with satisfiability probabilities
            std::vector<double> dtmc_bound(dtmc_states+2, 0);
            storm::storage::sparse::StateValuations const& dtmc_state_valuations = dtmc.getStateValuations();
            for(StateType state = 0; state < dtmc_states; state++) {
                storm::storage::sparse::StateValuations::StateValuation const& valuation =  dtmc_state_valuations.getValuation(state);
                double probability = this->mdp_bound[valuation];
                dtmc_bound[state] = probability;
            }
            dtmc_bound[sink_state_false] = 0;
            dtmc_bound[sink_state_true] = 1;

            // Precompute encounter and expansion order: encountered = in subDTMC, expanded = has original transitions

            // Notation: state in DTMC, index in subDTMC 
            StateType encountered_states = 0;
            storm::storage::BitVector encountered_flag(dtmc_states+2, false);
            std::vector<StateType> encountered_index2state(dtmc_states+2, 0);
            std::vector<StateType> encountered_state2index(dtmc_states+2, 0);
            StateType expanded_states = 0;
            // storm::storage::BitVector expanded_flag(dtmc_states+2, false);
            std::vector<StateType> expanded_index2state(dtmc_states+2, 0);
            std::vector<StateType> expanded_state2index(dtmc_states+2, 0);
            std::vector<StateType> encountered_per_expanded(dtmc_states+2, 0);

            // Encounter initial state and two sink states
            for(StateType state: {initial_state, sink_state_false, sink_state_true}) {
                encountered_flag.set(state);
                encountered_index2state[encountered_states] = state;
                encountered_state2index[state] = encountered_states;
                encountered_states++;
            }
            encountered_per_expanded[expanded_states] = encountered_states;

            // Priority queue by the bound type: 
            std::vector<ValueType> const& vector_dtmc_bound = (dtmc_result.getValueVector());
            auto cmp_dtmc_bound = [&] (StateType a, StateType b) { return (this->formula_safety ? vector_dtmc_bound[a] < vector_dtmc_bound[b] : vector_dtmc_bound[a] > vector_dtmc_bound[b]) || a > b; };
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
                        encountered_index2state[encountered_states] = successor;
                        encountered_state2index[successor] = encountered_states;
                        encountered_states++;
                        state_horizon.push(successor);
                    }
                }
                expanded_index2state[expanded_states] = state;
                expanded_state2index[state] = expanded_states;
                // expanded_flag.set(state);
                expanded_states++;
                encountered_per_expanded[expanded_states] = encountered_states;
            }

            // Construct matrices (new index)
            typedef std::vector<std::pair<StateType,ValueType>> row;
            typedef std::vector<row> rows;

            // Matrix of shorctuts = initial matrix of a subDTMC
            rows matrix;
            for(StateType index = 0; index < dtmc_states+2; index++) {
                row r;
                StateType state = encountered_index2state[index];
                double probability = dtmc_bound[state];
                r.emplace_back(encountered_state2index[sink_state_false], 1-probability);
                r.emplace_back(encountered_state2index[sink_state_true], probability);
                matrix.push_back(r);
            }

            // Original matrix (new index)
            rows matrix_original;
            for(StateType index = 0; index < dtmc_states+2; index++) {
                row r;
                StateType state = encountered_index2state[index];
                if(state == sink_state_false || state == sink_state_true) {
                    // blank row: it shound never be required
                } else {
                    for(auto entry: matrix_dtmc.getRow(state)) {
                        r.emplace_back(encountered_state2index[entry.getColumn()], entry.getValue());
                    }
                }
                matrix_original.push_back(r);
            }
            
            // Construct prototype labeling for all states (new index):
            // copy the labeling, add two new states & associate target label with the true sink
            storm::models::sparse::StateLabeling labeling_old = dtmc.getStateLabeling();
            storm::models::sparse::StateLabeling labeling(dtmc_states+2);
            for(auto label: labeling_old.getLabels()) {
                labeling.addLabel(label);
            }
            for(StateType index = 0; index < dtmc_states+2; index++) {
                StateType state = encountered_index2state[index];
                if(state == sink_state_false || state == sink_state_true) {
                    continue;
                }
                for(auto label: labeling_old.getLabelsOfState(state)) {
                    labeling.addLabelToState(label, index);
                }
            }
            labeling.addLabelToState(this->target_label, encountered_state2index[sink_state_true]);
            
            // std::vector<StateType> index_encountered(dtmc_states+2, 0);
            this->dtmc_preprocessing.stop();

            // Construct a state subspace with only initial state and two sink states
            this->other.start();
            encountered_flag.clear(); // which indices are encountered
            // expanded_flag.clear();  // which states are expanded
            expanded_states = 0;
            for(StateType index = 0; index < encountered_per_expanded[expanded_states]; index++) {
                encountered_flag.set(index);
            }
            this->other.stop();

            // Iteratively construct and model check subDTMCs
            while(true) {
                // Expand the state horizon
                this->other.start();
                for(StateType expanded = 0; expanded < this->expanded_per_iter; expanded++) {
                    // Encounter new states
                    for(StateType index = encountered_per_expanded[expanded_states]; index < encountered_per_expanded[expanded_states+1]; index++) {
                        encountered_flag.set(index);
                    }
                    // Replace transitions with original ones
                    StateType state = expanded_index2state[expanded_states];
                    StateType encountered_index = encountered_state2index[state];
                    matrix[encountered_index] = std::move(matrix_original[encountered_index]);
                    // expanded_flag.set(expanded_index2state[expanded_states]);
                    expanded_states++;
                    if(expanded_states == dtmc_states) {
                        break;
                    }
                }
                this->other.stop();

                // Construct sub-matrix
                this->constructing.start();
                storm::storage::SparseMatrixBuilder<ValueType> transitionMatrixBuilder(0, 0, 0, false, false, 0);
                for(StateType index = 0; index < encountered_per_expanded[expanded_states]; index++) {
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
                storm::modelchecker::CheckTask<storm::logic::Formula, ValueType> task(this->formula, onlyInitialStatesRelevant);
                std::unique_ptr<storm::modelchecker::CheckResult> result_ptr = storm::api::verifyWithSparseEngine<ValueType>(sub_dtmc, task);
                storm::modelchecker::ExplicitQualitativeCheckResult & result = result_ptr->asExplicitQualitativeCheckResult();
                bool satisfied = result[encountered_state2index[initial_state]];
                this->model_checking.stop();
                if(!satisfied) {
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
            return time_stats;
        }
        
        // Explicitly instantiate the class.
        template class Counterexample<double, uint_fast64_t>;

    } // namespace research
} // namespace storm


                