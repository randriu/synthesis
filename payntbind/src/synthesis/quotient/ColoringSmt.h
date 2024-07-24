#pragma once

#include "src/synthesis/quotient/Family.h"

#include <storm/storage/BitVector.h>
#include <storm/storage/sparse/StateValuations.h>
#include <storm/utility/Stopwatch.h>

#include <cstdint>
#include <vector>
#include <memory>

#include <z3++.h>

namespace synthesis {

using BitVector = storm::storage::BitVector;


class ColoringSmt {
public:
    
    ColoringSmt(
        std::vector<uint64_t> const& row_groups,
        std::vector<uint64_t> const& choice_to_action,
        storm::storage::sparse::StateValuations const& state_valuations,
        std::vector<std::string> const& hole_to_variable_name,
        std::vector<std::pair<std::vector<uint64_t>,std::vector<uint64_t>>> hole_bounds,
        Family const& family,
        std::vector<std::vector<int64_t>> hole_domain
    );

    /** Get a mask of choices compatible with the family. */
    BitVector selectCompatibleChoices(Family const& subfamily);
    /** Get a mask of sub-choices of \p base_choices compatible with the family. */
    BitVector selectCompatibleChoices(Family const& subfamily, BitVector const& base_choices);

    storm::utility::Stopwatch selectCompatibleChoicesTimer;
    uint64_t selectCompatibleChoicesTime() {
        return (uint64_t) selectCompatibleChoicesTimer.getTimeInMilliseconds();
    }
    /**
     * Verify whether the given choices have an associated non-conficting hole assignment (within the given family).
     * @return a pair (A,B) where A is true iff the choice selection is consistent; B is either satisfying hole assignment
     *  if A holds, or a counterexample to be used for splitting.
     * */
    std::pair<bool,std::vector<std::vector<uint64_t>>> areChoicesConsistent(BitVector const& choices, Family const& subfamily);
    
protected:

    /** Number of MDP actions. */
    uint64_t num_actions;
    /** For each choice, its unique action. */
    const std::vector<uint64_t> choice_to_action;
    /** Row groups of the quotient. */
    std::vector<uint64_t> row_groups;
    /** Number of states in the quotient. */
    const uint64_t numStates() const;
    /** Number of choices in the quotient. */
    const uint64_t numChoices() const;
    
    /** SMT solver context. */
    z3::context context;
    /** SMT solver. */
    z3::solver solver;
    /** For each hole, an SMT variable. */
    std::vector<z3::expr> hole_to_solver_variable;
    /** For each hole, an expression describing its relation to other holes. */
    std::vector<z3::expr> hole_restriction;
    
    /**
     * For each choice, its color expressed as a list of conjuncts (clauses) of
     * disjuncts of atomic clauses (terminals).
     * */
    std::vector<std::vector<z3::expr_vector>> choice_terminal;
    /** For each terminal, a (unique) hole assignment involved. */
    std::vector<std::vector<std::vector<std::pair<uint64_t,int>>>> choice_terminal_evaluation;
    
    /** For each choice, its color expressed as a list of clauses. */
    std::vector<z3::expr_vector> choice_clause;
    /** For each clause, a predefined label. */
    std::vector<std::vector<std::string>> choice_clause_label;

    


    /** Reference to the unrefined family. */
    const Family family;
    /** For each hole associated with an integer variable, a list of its integer options. */
    std::vector<std::vector<int64_t>> hole_domain;
    /** For each hole, whether it corresponds to a variable (and not to action selection). */
    storm::storage::BitVector hole_corresponds_to_program_variable;

    int getVariableValueAtState(
        storm::storage::sparse::StateValuations const& state_valuations, uint64_t state, storm::expressions::Variable variable
    ) const;
    
    /** Create SMT encoding for the given family and the given hole. */
    void addHoleEncoding(Family const& family, uint64_t hole);
    /** Create SMT encoding for the given family. */
    void addFamilyEncoding(Family const& family);
    
    /** Create SMT encoding for the given choice. */
    void addChoiceEncoding(uint64_t choice, bool add_label=true);
    
};

}