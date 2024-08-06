#pragma once

#include "src/synthesis/quotient/Family.h"
#include "src/synthesis/quotient/TreeNode.h"

#include <storm/storage/BitVector.h>
#include <storm/storage/sparse/StateValuations.h>
#include <storm/utility/Stopwatch.h>

#include <cstdint>
#include <vector>
#include <memory>

#include <z3++.h>

namespace synthesis {

using BitVector = storm::storage::BitVector;

class ColoringSmtFull {
public:

    ColoringSmtFull(
        std::vector<uint64_t> const& row_groups,
        std::vector<uint64_t> const& choice_to_action,
        storm::storage::sparse::StateValuations const& state_valuations,
        std::vector<std::string> const& variable_name,
        std::vector<std::vector<int64_t>> const& variable_domain,
        std::vector<std::tuple<uint64_t,uint64_t,uint64_t>> const& tree_list
    );

    std::vector<std::pair<std::string,std::string>> getFamilyInfo();

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
    /** Row groups of the quotient. */
    const std::vector<uint64_t> row_groups;
    /** For each choice, its unique action. */
    const std::vector<uint64_t> choice_to_action;
    /** Number of states in the quotient. */
    const uint64_t numStates() const;
    /** Number of choices in the quotient. */
    const uint64_t numChoices() const;

    /** For each variable, its name. */
    const std::vector<std::string> variable_name;
    /** For each variable, a list of its options. */
    const std::vector<std::vector<int64_t>> variable_domain;
    /** Number of (relevant) program variables. */
    const uint64_t numVariables() const;

    /** A list of tree nodes. */
    std::vector<std::shared_ptr<TreeNode>> tree;
    /** Number of tree nodes. */
    uint64_t numNodes() const;
    /** Retreive tree root. */
    std::shared_ptr<TreeNode> getRoot();



    /** Unrefined family. */
    Family family;
    /** SMT solver context. */
    z3::context ctx;
    /** SMT solver. */
    z3::solver solver;

    /** A list of solver variables, one for each program variable and the last one for the action selection. */
    z3::expr_vector substitution_variables;
    /** For each choice, the corresponding substitution. */
    std::vector<std::vector<int64_t>> choice_substitution;
    /** For each choice, the corresponding substitution (SMT expression). */
    std::vector<z3::expr_vector> choice_substitution_expr;

    /** For each choice, its color expressed as a list of paths consisting of steps. */
    std::vector<std::vector<z3::expr_vector>> choice_path_step;
    /** For each choice, its color expressed as a list of paths. */
    std::vector<z3::expr_vector> choice_path;
    /** For each clause, a predefined label. */
    std::vector<std::vector<std::string>> choice_path_label;

    int getVariableValueAtState(
        storm::storage::sparse::StateValuations const& state_valuations, uint64_t state,
        storm::expressions::Variable variable
    ) const;

    /** Create SMT encoding for the given choice. */
    void addChoiceEncoding(uint64_t choice, bool add_label);
};

}