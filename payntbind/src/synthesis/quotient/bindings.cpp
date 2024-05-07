#include "../synthesis.h"

#include "JaniChoices.h"
#include "Family.h"
#include "Coloring.h"

#include <storm/models/sparse/Mdp.h>
#include <storm/storage/BitVector.h>
#include <storm/models/sparse/Mdp.h>
#include <storm/storage/sparse/JaniChoiceOrigins.h>

#include <storm/storage/Scheduler.h>

#include <queue>

namespace synthesis {

template<typename ValueType>
std::pair<storm::storage::BitVector,std::vector<std::vector<std::pair<uint64_t,uint64_t>>>> janiMapChoicesToHoleAssignments(
    storm::models::sparse::Mdp<ValueType> const& mdp,
    Family const& family,
    std::map<uint64_t,std::vector<std::pair<uint64_t,uint64_t>>> edge_to_hole_assignment
) {

    uint64_t num_choices = mdp.getNumberOfChoices();
    storm::storage::BitVector choice_is_valid(num_choices,true);
    std::vector<std::vector<std::pair<uint64_t,uint64_t>>> choice_to_hole_assignment(num_choices);
    for(uint64_t choice = 0; choice < num_choices; ++choice) {
        std::vector<bool> hole_set(family.numHoles(),false);
        std::vector<uint64_t> hole_option(family.numHoles());
        bool valid_choice = true;
        for(auto const& edge: mdp.getChoiceOrigins()->asJaniChoiceOrigins().getEdgeIndexSet(choice)) {
            auto hole_assignment = edge_to_hole_assignment.find(edge);
            if(hole_assignment == edge_to_hole_assignment.end()) {
                continue;
            }
            for(auto const& [hole,option]: hole_assignment->second) {
                if(not hole_set[hole]) {
                    hole_option[hole] = option;
                    hole_set[hole] = true;
                } else if(hole_option[hole] != option) {
                    valid_choice = false;
                    break;
                }
            }
            if(not valid_choice) {
                break;
            }
        }
        if(not valid_choice) {
            choice_is_valid.set(choice,false);
            continue;
        }
        for(uint64_t hole = 0; hole < family.numHoles(); ++hole) {
            if(not hole_set[hole]) {
                continue;
            }
            choice_to_hole_assignment[choice].push_back(std::make_pair(hole,hole_option[hole]));
        }
    }
    return std::make_pair(choice_is_valid,choice_to_hole_assignment);
}


template<typename ValueType>
std::vector<std::vector<uint64_t>> computeChoiceDestinations(storm::models::sparse::Mdp<ValueType> const& mdp) {
    uint64_t num_choices = mdp.getNumberOfChoices();
    std::vector<std::vector<uint64_t>> choice_destinations(num_choices);
    for(uint64_t choice = 0; choice < num_choices; ++choice) {
        for(auto const& entry: mdp.getTransitionMatrix().getRow(choice)) {
            choice_destinations[choice].push_back(entry.getColumn());
        }
    }
    return choice_destinations;
}

template<typename ValueType>
std::vector<uint64_t> schedulerToStateToGlobalChoice(
    storm::storage::Scheduler<ValueType> const& scheduler, storm::models::sparse::Mdp<ValueType> const& sub_mdp,
    std::vector<uint64_t> choice_to_global_choice
) {
    uint64_t num_states = sub_mdp.getNumberOfStates();
    std::vector<uint64_t> state_to_choice(num_states);
    auto const& nci = sub_mdp.getNondeterministicChoiceIndices();
    for(uint64_t state=0; state<num_states; ++state) {
        uint64_t choice = nci[state] + scheduler.getChoice(state).getDeterministicChoice();
        uint64_t choice_global = choice_to_global_choice[choice];
        state_to_choice[state] = choice_global;
    }
    return state_to_choice;
}

std::map<uint64_t,double> computeInconsistentHoleVariance(
    Family const& family,
    std::vector<uint64_t> const& row_groups, std::vector<uint64_t> const& choice_to_global_choice, std::vector<double> const& choice_to_value,
    Coloring const& coloring, std::map<uint64_t,std::vector<uint64_t>> const& hole_to_inconsistent_options,
    std::vector<double> const& state_to_expected_visits
) {

    auto num_holes = family.numHoles();
    std::vector<BitVector> hole_to_inconsistent_options_mask(num_holes);
    for(uint64_t hole=0; hole<num_holes; ++hole) {
        hole_to_inconsistent_options_mask[hole] = BitVector(family.holeNumOptionsTotal(hole));
    }
    BitVector inconsistent_holes(num_holes);
    for(auto const& [hole,options]: hole_to_inconsistent_options) {
        inconsistent_holes.set(hole);
        for(auto option: options) {
            hole_to_inconsistent_options_mask[hole].set(option);
        }
    }

    std::vector<double> hole_difference_avg(num_holes,0);
    std::vector<uint64_t> hole_states_affected(num_holes,0);
    auto const& choice_to_assignment = coloring.getChoiceToAssignment();
    
    std::vector<bool> hole_set(num_holes);
    std::vector<double> hole_min(num_holes);
    std::vector<double> hole_max(num_holes);
        
    auto num_states = row_groups.size()-1;
    for(uint64_t state=0; state<num_states; ++state) {

        for(uint64_t choice=row_groups[state]; choice<row_groups[state+1]; ++choice) {
            auto value = choice_to_value[choice];
            auto choice_global = choice_to_global_choice[choice];
            
            for(auto const& [hole,option]: choice_to_assignment[choice_global]) {
                if(not  hole_to_inconsistent_options_mask[hole][option]) {
                    continue;
                }

                if(not hole_set[hole]) {
                    hole_min[hole] = value;
                    hole_max[hole] = value;
                    hole_set[hole] = true;
                } else {
                    if(value < hole_min[hole]) {
                        hole_min[hole] = value;
                    }
                    if(value > hole_max[hole]) {
                        hole_max[hole] = value;
                    }
                }
            }
        }

        for(auto hole: inconsistent_holes) {
            if(not hole_set[hole]) {
                continue;
            }
            double difference = (hole_max[hole]-hole_min[hole])*state_to_expected_visits[state];
            hole_states_affected[hole] += 1;
            hole_difference_avg[hole] += (difference-hole_difference_avg[hole]) / hole_states_affected[hole];
        }
        std::fill(hole_set.begin(), hole_set.end(), false);
    }

    std::map<uint64_t,double> inconsistent_hole_variance;
    for(auto hole: inconsistent_holes) {
        inconsistent_hole_variance[hole] = hole_difference_avg[hole];
    }

    return inconsistent_hole_variance;
}



/*storm::storage::BitVector keepReachableChoices(
    storm::storage::BitVector enabled_choices, uint64_t initial_state,
    std::vector<uint64_t> const& row_groups, std::vector<std::vector<uint64_t>> const& choice_destinations
) {

    uint64_t num_states = row_groups.size()-1;
    uint64_t num_choices = enabled_choices.size();

    storm::storage::BitVector reachable_choices(num_choices,false);
    storm::storage::BitVector state_visited(num_states,false);

    std::queue<uint64_t> state_queue;
    state_visited.set(initial_state,true);
    state_queue.push(initial_state);
    while(not state_queue.empty()) {
        auto state = state_queue.front();
        state_queue.pop();
        for(uint64_t choice = row_groups[state]; choice < row_groups[state+1]; ++choice) {
            if(not enabled_choices[choice]) {
                continue;
            }
            reachable_choices.set(choice,true);
            for(auto dst: choice_destinations[choice]) {
                if(not state_visited[dst]) {
                    state_visited.set(dst,true);
                    state_queue.push(dst);
                }
            }
        }
    }
    return reachable_choices;
}*/

// RA: I don't even understand why this needs to be optimized, but it does
storm::storage::BitVector policyToChoicesForFamily(
    std::vector<uint64_t> const& policy_choices,
    storm::storage::BitVector const& family_choices
) {
    storm::storage::BitVector choices(family_choices.size(),false);
    for(auto choice : policy_choices) {
        choices.set(choice,true);
    }
    return choices & family_choices;
}


//----------------xshevc01----------------
/**
 * Finds all predecessors of each state
 * 
 * @param quotient_mdp The quotient MDP
 * 
 * @return The predecessors of each state
*/
template<typename ValueType>
std::vector<std::set<uint64_t>> findAllPredecessors(
    storm::models::sparse::Mdp<ValueType> const& quotient_mdp
){
    auto num_states = quotient_mdp.getNumberOfStates();
    auto const& row_groups = quotient_mdp.getNondeterministicChoiceIndices();
    std::vector<std::set<uint64_t>> predecessors(num_states);
    for(uint64_t state=0; state<num_states; ++state) {
        for(uint64_t choice=row_groups[state]; choice<row_groups[state+1]; ++choice) {
            for(auto const& entry: quotient_mdp.getTransitionMatrix().getRow(choice)) {
                uint64_t entry_state = entry.getColumn();
                predecessors[entry_state].insert(state);
            }
        }
    }
    return predecessors;
}

/**
 * Maps choices to corresponding states
 * 
 * @param quotient_mdp The quotient MDP
 * 
 * @return Mapping from choices to states
*/
template<typename ValueType>
std::vector<uint64_t> mapChoicesToStates(
    storm::models::sparse::Mdp<ValueType> const& quotient_mdp
){
    auto num_states = quotient_mdp.getNumberOfStates();
    auto num_choices = quotient_mdp.getNumberOfChoices();
    auto const& row_groups = quotient_mdp.getNondeterministicChoiceIndices();
    std::vector<uint64_t> choices_to_states(num_choices);
    std::vector<std::set<uint64_t>> leading_choices(num_states);
    for(uint64_t state=0; state<num_states; ++state) {
        for(uint64_t choice=row_groups[state]; choice<row_groups[state+1]; ++choice) {
            choices_to_states[choice] = state;
        }
    }
    return choices_to_states;
}


/**
 * Among all compatible choices, for not affected states leaves only scheduler's choice
 * and for affected states does not change anything
 * 
 * @param quotient_choice_map The mapping of choices to quotient choices
 * @param quotient_state_map The mapping of states to quotient states
 * @param quotient_mdp The parent MDP
 * @param states_affected The bit vector of affected states
 * @param parent_state_choice The choices of the parent's scheduler
 * @param compatible_choices The choices that are compatible with the family
 * 
 * @return The final bit vector of choices for the family
*/
template<typename ValueType>
storm::storage::BitVector affectedStatesToMask(
    std::vector<uint64_t>const& quotient_choice_map,
    std::vector<uint64_t>const& quotient_state_map,
    storm::models::sparse::Mdp<ValueType> const& quotient_mdp,
    storm::storage::BitVector const& states_affected,
    std::vector<int>& parent_state_choice,
    storm::storage::BitVector& compatible_choices
) {
    auto const& row_groups = quotient_mdp.getNondeterministicChoiceIndices();
    uint64_t num_states = quotient_mdp.getNumberOfStates();
    storm::storage::BitVector mask(compatible_choices.size(), true);
    for(uint64_t state=0; state<num_states; ++state) {
        uint64_t qstate = quotient_state_map[state];
        if (states_affected.get(qstate)){
            continue;
        }
        for(uint64_t choice=row_groups[state]; choice<row_groups[state+1]; ++choice) {
            uint64_t qchoice = quotient_choice_map[choice];
            mask.set(qchoice, false);
        }
        uint64_t parent_choice = parent_state_choice[qstate];
        mask.set(parent_choice, true);
    }
    return mask & compatible_choices;
}

/**
 * Finds all optimal choices leading to each state
 * 
 * @param quotient_mdp The quotient MDP
 * @param parent_state_choice The choices of the parent's scheduler
 * 
 * @return Optimal leading choices for each state
*/
template<typename ValueType>
std::vector<std::set<uint64_t>> findOptimalLeadingChoices(
    storm::models::sparse::Mdp<ValueType> const& quotient_mdp,
    std::vector<int>& parent_state_choice
){
    auto num_states = quotient_mdp.getNumberOfStates();
    auto const& row_groups = quotient_mdp.getNondeterministicChoiceIndices();
    std::vector<std::set<uint64_t>> optimal_leading_choices(num_states);
    for(uint64_t state=0; state<num_states; ++state) {
        int parent_choice = parent_state_choice[state];
        if (parent_choice == -1) {
            continue;
        }
        for(auto const& entry: quotient_mdp.getTransitionMatrix().getRow(parent_choice)) {
            uint64_t entry_state = entry.getColumn();
            optimal_leading_choices[entry_state].insert(parent_choice);
        }
    }
    return optimal_leading_choices;
}

/**
 * Finds all affected states from affected choices
 * 
 * @param quotient_mdp The quotient MDP
 * @param choices_to_states The mapping from choices to states
 * @param optimal_choices The bit vector of optimal choices
 * @param compatible_choices The bit vector of compatible choices
 * @param leading_optimals_to_state The optimal leading choices for each state
 * 
 * @return Affected states
*/
template<typename ValueType>
storm::storage::BitVector optimalChoicesToAffectedStates(
    storm::models::sparse::Mdp<ValueType> const& quotient_mdp,
    std::vector<uint64_t> choices_to_states,
    storm::storage::BitVector const& optimal_choices,
    storm::storage::BitVector const& compatible_choices,
    std::vector<std::set<uint64_t>> leading_optimals_to_state
) {
    uint64_t num_states = quotient_mdp.getNumberOfStates();
    uint64_t num_choices = quotient_mdp.getNumberOfChoices();
    storm::storage::BitVector affected_states(num_states, false);
    storm::storage::BitVector was_in_queue(num_choices, false);
    std::queue<uint64_t> queue_affected_choices;

    for(uint64_t choice=0; choice<optimal_choices.size(); ++choice){
        if(optimal_choices.get(choice) && !compatible_choices.get(choice)){
            queue_affected_choices.push(choice);
            was_in_queue.set(choice, true);
        }
    }
    while(!queue_affected_choices.empty()){
        uint64_t affected_qchoice = queue_affected_choices.front();
        queue_affected_choices.pop();
        uint64_t affected_qstate = choices_to_states[affected_qchoice];
        affected_states.set(affected_qstate, true);
        for (uint64_t leading_qchoice: leading_optimals_to_state[affected_qstate]){
            if (compatible_choices.get(leading_qchoice) && !was_in_queue.get(leading_qchoice)){
                queue_affected_choices.push(leading_qchoice);
                was_in_queue.set(leading_qchoice, true);
            }
        }
    }
    return affected_states;
}
//---------------------------------------


/*std::pair<std::vector<uint64_t>,storm::storage::BitVector> fixPolicyForFamily(
    std::vector<uint64_t> const& policy, uint64_t invalid_action,
    storm::storage::BitVector const& family_choices,
    uint64_t initial_state, uint64_t num_choices,
    std::vector<std::vector<uint64_t>> const& state_to_actions,
    std::vector<std::vector<std::vector<uint64_t>>> const& state_action_choices,
    std::vector<std::vector<uint64_t>> const& choice_destinations
) {

    uint64_t num_states = state_to_actions.size();

    std::vector<uint64_t> policy_fixed(num_states,invalid_action);
    storm::storage::BitVector choice_mask(num_choices,false);

    storm::storage::BitVector state_visited(num_states,false);
    state_visited.set(initial_state,true);

    std::queue<uint64_t> state_queue;
    state_queue.push(initial_state);
    while(not state_queue.empty()) {
        auto state = state_queue.front();
        state_queue.pop();
        // get action executed in the state
        auto action = policy[state];
        if(action == invalid_action) {
            action = state_to_actions[state][0];
        }
        policy_fixed[state] = action;
        // expand through the choices that correspond to this action
        for(auto choice: state_action_choices[state][action]) {
            if(not family_choices[choice]) {
                continue;
            }
            choice_mask.set(choice,true);
            for(auto dst: choice_destinations[choice]) {
                if(not state_visited[dst]) {
                    state_visited.set(dst,true);
                    state_queue.push(dst);
                }
            }   
        }
    }
    return std::make_pair(policy_fixed,choice_mask);
}*/

}


void bindings_coloring(py::module& m) {

    m.def("janiMapChoicesToHoleAssignments", &synthesis::janiMapChoicesToHoleAssignments<double>);
    m.def("addChoiceLabelsFromJani", &synthesis::addChoiceLabelsFromJani<double>);

    m.def("computeChoiceDestinations", &synthesis::computeChoiceDestinations<double>);
    //----------------xshevc01----------------
    m.def("findAllPredecessors", &synthesis::findAllPredecessors<double>);
    m.def("mapChoicesToStates", &synthesis::mapChoicesToStates<double>);
    m.def("affectedStatesToMask", &synthesis::affectedStatesToMask<double>);
    m.def("findOptimalLeadingChoices", &synthesis::findOptimalLeadingChoices<double>);
    m.def("optimalChoicesToAffectedStates", &synthesis::optimalChoicesToAffectedStates<double>);
    //---------------------------------------
    m.def("schedulerToStateToGlobalChoice", &synthesis::schedulerToStateToGlobalChoice<double>);
    m.def("computeInconsistentHoleVariance", &synthesis::computeInconsistentHoleVariance);
    
    m.def("policyToChoicesForFamily", &synthesis::policyToChoicesForFamily);

    

    py::class_<synthesis::Family>(m, "Family")
        .def(py::init<>(), "Constructor.")
        .def(py::init<synthesis::Family const&>(), "Constructor.", py::arg("other"))
        .def("numHoles", &synthesis::Family::numHoles)
        .def("addHole", &synthesis::Family::addHole)
        
        .def("holeOptions", &synthesis::Family::holeOptions)
        .def("holeOptionsMask", &synthesis::Family::holeOptionsMask)
        .def("holeSetOptions", py::overload_cast<uint64_t, std::vector<uint64_t> const&>(&synthesis::Family::holeSetOptions))
        .def("holeSetOptions", py::overload_cast<uint64_t, storm::storage::BitVector const&>(&synthesis::Family::holeSetOptions))
        .def("holeNumOptions", &synthesis::Family::holeNumOptions)
        .def("holeNumOptionsTotal", &synthesis::Family::holeNumOptionsTotal)
        .def("holeContains", &synthesis::Family::holeContains)
        ;

    py::class_<synthesis::Coloring>(m, "Coloring")
        .def(py::init<synthesis::Family const&, std::vector<uint64_t> const&, std::vector<std::vector<std::pair<uint64_t,uint64_t>>> >(), "Constructor.")
        .def("getChoiceToAssignment", &synthesis::Coloring::getChoiceToAssignment)
        .def("getStateToHoles", &synthesis::Coloring::getStateToHoles)
        .def("getUncoloredChoices", &synthesis::Coloring::getUncoloredChoices)
        .def("selectCompatibleChoices", &synthesis::Coloring::selectCompatibleChoices)
        .def("collectHoleOptions", &synthesis::Coloring::collectHoleOptions)
        ;

}
