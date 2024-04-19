#include "Coloring.h"

#include <iostream>

namespace synthesis {


Coloring::Coloring(
    Family const& family, std::vector<uint64_t> const& row_groups,
    std::vector<std::vector<std::pair<uint64_t,uint64_t>>> choice_to_assignment
) : family(family), choice_to_assignment(choice_to_assignment) {
    
    auto num_choices = numChoices();
    colored_choices.resize(num_choices,false);
    uncolored_choices.resize(num_choices,false);
    for(uint64_t choice = 0; choice<num_choices; ++choice) {
        if(choice_to_assignment[choice].empty()) {
            uncolored_choices.set(choice,true);
        } else {
            colored_choices.set(choice,true);
        }
    }


    auto num_holes = family.numHoles();
    choice_to_holes.resize(num_choices);
    for(uint64_t choice = 0; choice<num_choices; ++choice) {
        choice_to_holes[choice] = BitVector(num_holes,false);
        for(auto const& [hole,option]: choice_to_assignment[choice]) {
            choice_to_holes[choice].set(hole,true);
        }
    }


    auto num_states = row_groups.size()-1;
    state_to_holes.resize(num_states);
    is_simple = true;
    for(uint64_t state = 0; state<num_states; ++state) {
        state_to_holes[state] = BitVector(num_holes,false);
        for(uint64_t choice = row_groups[state]; choice<row_groups[state+1]; ++choice) {
            state_to_holes[state] = state_to_holes[state] | choice_to_holes[choice]; 
        }
        if(state_to_holes[state].getNumberOfSetBits() > 1) {
            is_simple = false;
        }
    }
}

uint64_t Coloring::numChoices() const {
    return choice_to_assignment.size();
}

std::vector<std::vector<std::pair<uint64_t,uint64_t>>> const& Coloring::getChoiceToAssignment() const {
    return choice_to_assignment;
}

std::vector<BitVector> const& Coloring::getStateToHoles() const {
    return state_to_holes;
}

BitVector const& Coloring::getUncoloredChoices() const {
    return uncolored_choices;
}

BitVector Coloring::selectCompatibleChoices(Family const& subfamily) const {
    auto selection = BitVector(uncolored_choices);
    for(auto choice: colored_choices) {
        if(subfamily.includesAssignment(choice_to_assignment[choice])) {
            selection.set(choice,true);
        }
    }
    return selection;
}



std::vector<BitVector> Coloring::collectHoleOptionsMask(BitVector const& choices) const {

    std::vector<BitVector> hole_options_mask(family.numHoles());
    for(uint64_t hole = 0; hole < family.numHoles(); ++hole) {
        hole_options_mask[hole] = BitVector(family.holeNumOptionsTotal(hole),false);
    }
    for(auto choice: choices) {
        for(auto const& [hole,option]: choice_to_assignment[choice]) {
            hole_options_mask[hole].set(option,true);
        }
    }
    return hole_options_mask;
}


std::vector<std::vector<uint64_t>> Coloring::collectHoleOptions(BitVector const& choices) const {
    auto hole_options_mask = collectHoleOptionsMask(choices);
    std::vector<std::vector<uint64_t>> hole_options(family.numHoles());
    for(uint64_t hole = 0; hole < family.numHoles(); ++hole) {
        for(auto option: hole_options_mask[hole]) {
            hole_options[hole].push_back(option);
        }
    }
    return hole_options;
}


bool Coloring::haveSameColor(uint64_t choice1, uint64_t choice2) const {
    auto const& assignment1 = choice_to_assignment[choice1];
    auto const& assignment2 = choice_to_assignment[choice2];
    if(assignment1.size() != assignment2.size()) {
        return false;
    }
    for(uint64_t index = 0; index < assignment1.size(); ++index) {
        if(assignment1[index] != assignment2[index]) {
            return false;
        }
    }
    return true;
}

void Coloring::addFreshState() {
    choice_to_assignment.resize(numChoices()+1);
    choice_to_holes.push_back(BitVector(family.numHoles(),false));
    state_to_holes.push_back(BitVector(family.numHoles(),false));
    uncolored_choices.resize(numChoices(),true);
    colored_choices.resize(numChoices(),false);
}

}