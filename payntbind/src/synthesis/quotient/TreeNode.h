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

class TreeNode {
public:

    class HoleInfo {
    public:
        uint64_t hole;
        std::string name;
        z3::expr solver_variable;
        std::string solver_string;
        z3::expr restriction;

        HoleInfo(z3::context& ctx);
        int64_t getModelValue(z3::model const& model) const {
            return model.eval(solver_variable).get_numeral_int64();
        }
    };

    static bool verifyExpression(z3::solver & solver, z3::expr const& expr);

    uint64_t identifier;
    z3::context& ctx;

    std::shared_ptr<TreeNode> parent;
    std::shared_ptr<TreeNode> child_true;
    std::shared_ptr<TreeNode> child_false;

    /** Depth of this node in the tree. */
    uint64_t depth;
    /** Every possible path (a sequence of steps) that can be taken from this node. */
    std::vector<std::vector<std::pair<bool,uint64_t>>> paths;

    TreeNode(uint64_t identifier, z3::context& ctx);

    /** Store pointers to parent and children, if exist. */
    void createTree(
        std::vector<std::tuple<uint64_t,uint64_t,uint64_t>> const& tree_list, std::vector<std::shared_ptr<TreeNode>> & tree
    );

    /** Return true if this node has no parent. */
    bool isRoot() const;
    /** Return true if this node has no children. */
    bool isTerminal() const;
    /** Return true if this node if a true child of its parent. */
    bool isTrueChild() const;

    /** Create all holes and solver variables associated with this node. */
    virtual void createHoles(Family& family) {}
    /** Collect name and type (action,decision, or variable) of each hole. */
    virtual void loadHoleInfo(std::vector<std::pair<std::string,std::string>> & hole_info) const {}
    /** Create expressions that describe steps from this node. */
    virtual void createSteps(z3::expr_vector const& substitution_variables) {}
    /** Create a list of paths from this node. */
    virtual void createPaths(z3::expr_vector const& substitution_variables) {}
    /** Convert path to the path expression. */
    virtual void loadPathExpression(std::vector<std::pair<bool,uint64_t>> const& path, z3::expr_vector & path_expression) const {}
    /** Add encoding of hole option in the given family. */
    virtual void addFamilyEncoding(Family const& subfamily, z3::solver & solver) const {}

    /** TODO */
    virtual void loadHoleAssignmentFromModel(z3::model const& model, std::vector<std::vector<uint64_t>> & hole_options) const {}
    /** TODO */
    virtual void loadHoleAssignmentOfPath(
        z3::solver & solver,
        std::vector<std::pair<bool,uint64_t>> const& path, z3::expr_vector const& path_expression,
        std::vector<int64_t> const& choice_substitution,
        z3::expr_vector const& substitution_variables,
        z3::expr_vector const& choice_substitution_expr,
        std::vector<std::set<uint64_t>> & hole_options
    ) const {}
    
};

class TerminalNode: public TreeNode {
public:
    const uint64_t num_actions;
    HoleInfo action_hole;
    z3::expr action_expr;

    TerminalNode(uint64_t identifier, z3::context & ctx, uint64_t num_actions);

    void createHoles(Family& family) override;
    void loadHoleInfo(std::vector<std::pair<std::string,std::string>> & hole_info) const override;
    void createSteps(z3::expr_vector const& substitution_variables) override;
    void createPaths(z3::expr_vector const& substitution_variables) override;
    void loadPathExpression(std::vector<std::pair<bool,uint64_t>> const& path, z3::expr_vector & path_expression) const override;
    void addFamilyEncoding(Family const& subfamily, z3::solver & solver) const override;
    void loadHoleAssignmentFromModel(z3::model const& model, std::vector<std::vector<uint64_t>> & hole_options) const override;
    void loadHoleAssignmentOfPath(
        z3::solver & solver,
        std::vector<std::pair<bool,uint64_t>> const& path, z3::expr_vector const& path_expression,
        std::vector<int64_t> const& choice_substitution,
        z3::expr_vector const& substitution_variables,
        z3::expr_vector const& choice_substitution_expr,
        std::vector<std::set<uint64_t>> & hole_options
    ) const override;
};


class InnerNode: public TreeNode {
public:

    std::vector<std::string> const& variable_name;
    std::vector<std::vector<int64_t>> const& variable_domain;

    HoleInfo decision_hole;
    std::vector<HoleInfo> variable_hole;
    std::vector<z3::expr> steps_true;
    std::vector<z3::expr> steps_false;

    InnerNode(
        uint64_t identifier,
        z3::context & ctx,
        std::vector<std::string> const& variable_name,
        std::vector<std::vector<int64_t>> const& variable_domain
    );

    const uint64_t numVariables() const;
    /** Convert variable value to the corresponding hole option via variable domain. */
    const uint64_t variableValueToHoleOption(uint64_t variable, int64_t value) const;

    /** Retrieve true child of this node if the condition holds, get false child otherwise. */
    std::shared_ptr<TreeNode> getChild(bool condition) const;
    std::vector<z3::expr> const& getSteps(bool condition) const;

    void createHoles(Family& family) override;
    void loadHoleInfo(std::vector<std::pair<std::string,std::string>> & hole_info) const override;
    void createSteps(z3::expr_vector const& substitution_variables) override;
    void createPaths(z3::expr_vector const& substitution_variables) override;
    void loadPathExpression(std::vector<std::pair<bool,uint64_t>> const& path, z3::expr_vector & path_expression) const override;
    void addFamilyEncoding(Family const& family, z3::solver & solver) const override;
    void loadHoleAssignmentFromModel(z3::model const& model, std::vector<std::vector<uint64_t>> & hole_options) const override;
    void loadHoleAssignmentOfPath(
        z3::solver & solver,
        std::vector<std::pair<bool,uint64_t>> const& path, z3::expr_vector const& path_expression,
        std::vector<int64_t> const& choice_substitution,
        z3::expr_vector const& substitution_variables,
        z3::expr_vector const& choice_substitution_expr,
        std::vector<std::set<uint64_t>> & hole_options
    ) const override;

};

}