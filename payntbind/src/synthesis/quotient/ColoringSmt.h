#pragma once

#include "src/synthesis/quotient/Family.h"
#include "src/synthesis/quotient/TreeNode.h"

#include <storm/models/sparse/NondeterministicModel.h>
#include <storm/storage/BitVector.h>
#include <storm/utility/Stopwatch.h>

#include <cstdint>
#include <vector>
#include <memory>

#include <z3++.h>

namespace synthesis {

using BitVector = storm::storage::BitVector;

template<typename ValueType = double>
class ColoringSmt {
public:

    ColoringSmt(
        storm::models::sparse::NondeterministicModel<ValueType> const& model,
        std::vector<std::string> const& variable_name,
        std::vector<std::vector<int64_t>> const& variable_domain,
        std::vector<std::tuple<uint64_t,uint64_t,uint64_t>> const& tree_list
    );

    /** For each hole, get a list of name-type pairs.  */
    std::vector<std::pair<std::string,std::string>> getFamilyInfo();

    /** Whether a check for an admissible family member is done before choice selection. */
    const bool CHECK_FAMILY_CONSISTENCE = true;
    /** Whether a check for constent scheduler existence is done after choice selection. */
    const bool CHECK_CONSISTENT_SCHEDULER_EXISTENCE = false;
    /** Get a mask of choices compatible with the family. */
    BitVector selectCompatibleChoices(Family const& subfamily);
    /** Get a mask of sub-choices of \p base_choices compatible with the family. */
    BitVector selectCompatibleChoices(Family const& subfamily, BitVector const& base_choices);

    /**
     * Verify whether the given choices have an associated non-conficting hole assignment (within the given family).
     * @return a pair (A,B) where A is true iff the choice selection is consistent; B is either a satisfying hole
     * assignment if A holds, or a list of inconsistent hole assignments to be used for splitting.
     */
    std::pair<bool,std::vector<std::vector<uint64_t>>> areChoicesConsistent(
        BitVector const& choices, Family const& subfamily
    );
    std::pair<bool,std::vector<std::vector<uint64_t>>> areChoicesConsistent2(
        BitVector const& choices, Family const& subfamily
    );

    std::map<std::string,storm::utility::Stopwatch> timers;
    std::vector<std::pair<std::string,double>> getProfilingInfo() {
        std::vector<std::pair<std::string,double>> profiling;
        for(auto const& [method,timer]: timers) {
            profiling.emplace_back(method, (double)(timer.getTimeInMilliseconds())/1000);
        }
        return profiling;
    }

protected:

    /** The initial state. */
    const uint64_t initial_state;
    /** Valuation of each state. */
    std::vector<std::vector<uint64_t>> state_valuation;

    /** Row groups of the quotient. */
    const std::vector<uint64_t> row_groups;
    /** For each choice, the state it comes from. */
    std::vector<uint64_t> choice_to_state;
    /** Number of states in the quotient. */
    const uint64_t numStates() const;
    /** Number of choices in the quotient. */
    const uint64_t numChoices() const;
    /** For each state, a list of target states. */
    std::vector<std::vector<uint64_t>> choice_destinations;

    /** Number of MDP actions. */
    uint64_t num_actions;
    /** For each choice, its unique action. */
    const std::vector<uint64_t> choice_to_action;

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
    /** Number of tree paths. */
    uint64_t numPaths();

    /** SMT solver context. */
    z3::context ctx;
    /** SMT solver. */
    z3::solver solver;
    /** Unrefined family. */
    Family family;

    bool check();

    /** For each path, an index of the hole that occurs at its end. */
    std::vector<uint64_t> path_action_hole;
    /** For each choice and path, a label passed to SMT solver. */
    std::vector<std::vector<std::string>> choice_path_label;
    
    /** For each choice and path, the corresponding (negated!) expression describing the prefix. */
    std::vector<std::vector<z3::expr>> choice_path;
    /** For each choice, its color expressed as a conjunction of all path implications. */
    std::vector<z3::expr_vector> choice_path_and_action;

    z3::expr harmonizing_variable;
    /** For each choice and path, the corresponding (negated!) expression describing the prefix. */
    std::vector<std::vector<z3::expr>> choice_path_harm;
    /** For each choice, its color expressed as a conjunction of all path implications. */
    std::vector<z3::expr_vector> choice_path_and_action_harm;

    /** For each state, whether (in the last subfamily) the path was enabled. */
    std::vector<BitVector> state_path_enabled;

    /** Check whether (in the subfamily) the choice is enabled. */
    bool isChoiceEnabled(Family const& subfamily, uint64_t state, uint64_t choice);
};

}