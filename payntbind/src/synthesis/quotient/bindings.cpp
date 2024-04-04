#include "../synthesis.h"

#include "JaniChoices.h"
#include "Family.h"
#include "Coloring.h"

#include <storm/models/sparse/Mdp.h>
#include <storm/storage/BitVector.h>
#include <storm/models/sparse/Mdp.h>
#include <storm/storage/sparse/JaniChoiceOrigins.h>

#include <storm/storage/Scheduler.h>

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


template<typename ValueType>
std::shared_ptr<storm::models::sparse::Mdp<ValueType>> removeSelfLoops(
    storm::models::sparse::Mdp<ValueType> const& mdp
) {
    storm::storage::sparse::ModelComponents<ValueType> components;
    auto num_states = mdp.getNumberOfStates();
    auto num_choices = mdp.getNumberOfChoices();
    auto const& tm = mdp.getTransitionMatrix();

    storm::storage::SparseMatrixBuilder<ValueType> builder(num_choices, num_states, 0, true, true, num_states);
    std::map<std::string,std::vector<ValueType>> rewards;
    for(auto const& [reward_name,reward_model]: mdp.getRewardModels()) {
        rewards[reward_name] = std::vector<ValueType>(num_choices,0);
    }

    uint64_t self_loops_removed = 0;

    for(uint64_t state = 0; state < num_states; ++state) {
        if(state == 0) {
            builder.newRowGroup(builder.getLastRow());
        } else {
            builder.newRowGroup(builder.getLastRow()+1);
        }

        for(auto const& choice: tm.getRowGroupIndices(state)) {

            // preemptively load rewards
            for(auto const& [reward_name,reward_model]: mdp.getRewardModels()) {
                rewards[reward_name][choice] += reward_model.getStateActionReward(choice);
            }

            // get self-loop probability
            ValueType self_loop_prob = 0;
            for(auto const& entry: tm.getRow(choice)) {
                if(entry.getColumn() == state) {
                    self_loop_prob = entry.getValue();
                    break;
                }
            }
            if(self_loop_prob == 1) {
                // keep this choice absorbing
                builder.addNextValue(choice,state,1);
                continue;
            }

            // non-unit self-loop
            if(self_loop_prob > 0) {
                self_loops_removed += 1;
            }
            ValueType factor = 1-self_loop_prob;
            for(auto const& entry: tm.getRow(choice)) {
                uint64_t dst = entry.getColumn();
                if(dst == state) {
                    continue;
                }
                builder.addNextValue(choice, dst, entry.getValue() / factor);
                for(auto [reward_name,choice_rewards]: rewards) {
                    choice_rewards[choice] /= factor;
                }
            }
        }
    }

    std::cout << "self-loops simplified: " << self_loops_removed << std::endl;
    components.transitionMatrix =  builder.build();
    components.stateLabeling = mdp.getStateLabeling();
    components.choiceLabeling = mdp.getOptionalChoiceLabeling();
    for(auto const& [reward_name,choice_rewards]: rewards) {
        std::optional<std::vector<ValueType>> state_rewards;
        auto reward_model = storm::models::sparse::StandardRewardModel<ValueType>(std::move(state_rewards), std::move(choice_rewards));
        components.rewardModels.emplace(reward_name,reward_model);
    }
    return std::make_shared<storm::models::sparse::Mdp<ValueType>>(std::move(components));
}

template<typename ValueType>
std::shared_ptr<storm::models::sparse::Mdp<ValueType>> mergeChoices(
    storm::models::sparse::Mdp<ValueType> const& mdp,
    synthesis::Coloring const& coloring
) {

    BitVector const& uncolored_choices = coloring.getUncoloredChoices();

    storm::storage::sparse::ModelComponents<ValueType> components;
    auto num_states = mdp.getNumberOfStates();
    auto num_choices = mdp.getNumberOfChoices();
    auto const& tm = mdp.getTransitionMatrix();

    storm::storage::SparseMatrixBuilder<ValueType> builder(num_choices, num_states, 0, true, true, num_states);
    std::map<std::string,std::vector<ValueType>> rewards;
    for(auto const& [reward_name,reward_model]: mdp.getRewardModels()) {
        rewards[reward_name] = std::vector<ValueType>(num_choices);
    }

    uint64_t choices_bypassed = 0;
    for(uint64_t state = 0; state < num_states; ++state) {
        if(state == 0) {
            builder.newRowGroup(builder.getLastRow());
        } else {
            builder.newRowGroup(builder.getLastRow()+1);
        }

        for(auto const& choice1: tm.getRowGroupIndices(state)) {

            for(auto const& [reward_name,reward_model]: mdp.getRewardModels()) {
                rewards[reward_name][choice1] += reward_model.getStateActionReward(choice1);
            }

            for(auto const& entry: tm.getRow(choice1)) {
                uint64_t dst = entry.getColumn();
                ValueType dst_prob = entry.getValue();
                bool have_matching_choice = false;
                uint64_t matching_choice;

                if(state != dst) {
                    for(auto const& choice2: tm.getRowGroupIndices(dst)) {
                        if(not uncolored_choices[choice1] and coloring.haveSameColor(choice1,choice2)) {
                            have_matching_choice = true;
                            matching_choice = choice2;
                            choices_bypassed += 1;
                            break;
                        }
                    }
                }
                if(not have_matching_choice) {
                    builder.addNextValue(choice1,dst,dst_prob);
                } else {
                    for(auto const& entry2: tm.getRow(matching_choice)) {
                        builder.addNextValue(choice1,entry2.getColumn(),dst_prob*entry2.getValue());
                    }
                    for(auto const& [reward_name,reward_model]: mdp.getRewardModels()) {
                        rewards[reward_name][choice1] += dst_prob * reward_model.getStateActionReward(matching_choice);
                    }
                }

            }
        }

    }

    std::cout << "choices bypassed: " << choices_bypassed << std::endl;
    components.transitionMatrix =  builder.build();
    components.stateLabeling = mdp.getStateLabeling();
    components.choiceLabeling = mdp.getOptionalChoiceLabeling();
    for(auto const& [reward_name,choice_rewards]: rewards) {
        std::optional<std::vector<ValueType>> state_rewards;
        auto reward_model = storm::models::sparse::StandardRewardModel<ValueType>(std::move(state_rewards), std::move(choice_rewards));
        components.rewardModels.emplace(reward_name,reward_model);
    }
    return std::make_shared<storm::models::sparse::Mdp<ValueType>>(std::move(components));
}


}


void bindings_coloring(py::module& m) {

    m.def("janiMapChoicesToHoleAssignments", &synthesis::janiMapChoicesToHoleAssignments<double>);
    m.def("addChoiceLabelsFromJani", &synthesis::addChoiceLabelsFromJani<double>);

    m.def("computeChoiceDestinations", &synthesis::computeChoiceDestinations<double>);

    m.def("schedulerToStateToGlobalChoice", &synthesis::schedulerToStateToGlobalChoice<double>);
    m.def("computeInconsistentHoleVariance", &synthesis::computeInconsistentHoleVariance);
    
    m.def("policyToChoicesForFamily", &synthesis::policyToChoicesForFamily);

    m.def("removeSelfLoops", &synthesis::removeSelfLoops<double>);
    m.def("mergeChoices", &synthesis::mergeChoices<double>);


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
