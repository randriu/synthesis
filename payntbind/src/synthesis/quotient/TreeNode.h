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

    class Hole {
    public:
        /** Unique hole identifier. */
        uint64_t hole;
        /** Hole name. */
        std::string name;
        /** True if the variable is of interval type, else if it is of enumeration type. */
        bool is_interval_type;

        z3::expr solver_variable;
        std::string solver_string_domain;

        // harmonizing variable
        std::string name_harm;
        z3::expr solver_variable_harm;
        std::string solver_string_domain_harm;

        z3::expr restriction;
        std::string solver_string_restriction;

        uint64_t depth;

        Hole(bool is_interval_type, z3::context& ctx);
        Hole(bool is_interval_type, z3::context& ctx, uint64_t depth);
        void createSolverVariable();
        uint64_t getModelValue(z3::model const& model) const;
        uint64_t getModelValueHarmonizing(z3::model const& model) const;

        z3::expr domainEncoding(Family const& subfamily, bool harmonizing) const;
        void addDomainEncoding(Family const& subfamily, z3::solver& solver) const;

    protected:
        /** Express option domain as an interval. */
        z3::expr domainInterval(Family const& subfamily) const;
        /** Express option domain as enumeration. */
        z3::expr domainEnumeration(Family const& subfamily) const;
    };

    /** Verify expression in the using provided solver. The solver may already contain some assertions. */
    static bool verifyExpression(z3::solver & solver, z3::expr const& expr);

    /** Unique node identifier. */
    uint64_t identifier;
    /** Solver context. */
    z3::context& ctx;
    /** List of variable names. */
    std::vector<std::string> const& variable_name;
    /** List of variable domains, used to derive number of hole options. */
    std::vector<std::vector<int64_t>> const& variable_domain;

    /** Parent node, NULL for the root node. */
    std::shared_ptr<TreeNode> parent;
    /** Child node if the condition holds, NULL for the terminal node. */
    std::shared_ptr<TreeNode> child_true;
    /** Child node if the condition does not hold, NULL for the terminal node. */
    std::shared_ptr<TreeNode> child_false;

    /** Depth of this node in the tree. */
    uint64_t depth;
    /** Every possible path (a sequence of condition steps) that can be taken from this node. */
    std::vector<std::vector<bool>> paths;

    /** Create a tree node with the unique identifier. */
    TreeNode(
        uint64_t identifier, z3::context& ctx,
        std::vector<std::string> const& variable_name,
        std::vector<std::vector<int64_t>> const& variable_domain
    );
    /** Number of program variables. */
    const uint64_t numVariables() const;

    /** Store pointers to parent and children, if exist. */
    void createTree(
        std::vector<std::tuple<uint64_t,uint64_t,uint64_t>> const& tree_list,
        std::vector<std::shared_ptr<TreeNode>> & tree
    );

    /** Return true if this node has no parent. */
    bool isRoot() const;
    /** Return true if this node has no children. */
    bool isTerminal() const;
    /** Return true if this node if a true child of its parent. */
    bool isTrueChild() const;
    /** Retrieve true child of this node if the condition holds, get false child otherwise. */
    std::shared_ptr<TreeNode> getChild(bool condition) const;
    /** Execute the path and the corresponding node of the tree. */
    // const TreeNode *getNodeOfPath(std::vector<bool> const& path, uint64_t step) const;

    /** Create all holes and solver variables associated with this node. */
    virtual void createHoles(Family& family) {}
    /** Collect name and type (action, decision, or variable) of each hole. */
    virtual void loadHoleInfo(std::vector<std::tuple<uint64_t,std::string,std::string>> & hole_info) const {}

    /** Create a list of paths from this node. */
    virtual void createPaths(z3::expr const& harmonizing_variable) {}
    /** Retrieve action hole associated with the path. */
    virtual uint64_t getPathActionHole(std::vector<bool> const& path) {return 0;}

    /** Add a step expression evaluated for a given state valuation. */
    virtual void substitutePrefixExpression(std::vector<bool> const& path, std::vector<uint64_t> const& state_valuation, z3::expr_vector & substituted) const {};
    /** Add an action expression evaluated for a given state valuation. */
    virtual z3::expr substituteActionExpression(std::vector<bool> const& path, uint64_t action) const {return z3::expr(ctx);};
    /** Add a step expression evaluated for a given state valuation (harmonizing). */
    virtual void substitutePrefixExpressionHarmonizing(std::vector<bool> const& path, z3::expr_vector const& state_valuation, z3::expr_vector & substituted) const {};
    /** Add an action expression evaluated for a given state valuation (harmonizing). */
    virtual z3::expr substituteActionExpressionHarmonizing(std::vector<bool> const& path, uint64_t action, z3::expr const& harmonizing_variable) const {return z3::expr(ctx);};

    /** Add encoding of hole option in the given family. */
    virtual void addFamilyEncoding(Family const& subfamily, z3::solver & solver) const {}
    /** Check whether the path is enabled in the given state for the given subfamily. */
    virtual bool isPathEnabledInState(
        std::vector<bool> const& path,
        Family const& subfamily,
        std::vector<uint64_t> const& state_valuation
    ) const {return false;};
    
    /** Extract hole assignments used in the SMT model. */
    virtual void loadHoleAssignmentFromModel(
        z3::model const& model, std::vector<std::vector<uint64_t>> & hole_options
    ) const {}
    virtual void loadHoleAssignmentFromModelHarmonizing(
        z3::model const& model, std::vector<std::vector<uint64_t>> & hole_options, uint64_t harmonizing_hole
    ) const {}
    
    virtual void unsatCoreAnalysis(
        Family const& subfamily,
        std::vector<bool> const& path,
        std::vector<uint64_t> const& state_valuation,
        uint64_t path_action, bool action_enabled,
        std::vector<std::set<uint64_t>> & hole_options
    ) const {}

};


class TerminalNode: public TreeNode {
public:
    const uint64_t num_actions;
    z3::expr action_substitution_variable;
    Hole action_hole;
    z3::expr action_expr;
    z3::expr action_expr_harm;

    TerminalNode(
        uint64_t identifier, z3::context & ctx,
        std::vector<std::string> const& variable_name,
        std::vector<std::vector<int64_t>> const& variable_domain,
        uint64_t num_actions,
        z3::expr const& action_substitution_variable
    );

    void createHoles(Family& family) override;
    void loadHoleInfo(std::vector<std::tuple<uint64_t,std::string,std::string>> & hole_info) const override;
    void createPaths(z3::expr const& harmonizing_variable) override;
    uint64_t getPathActionHole(std::vector<bool> const& path);

    void substitutePrefixExpression(std::vector<bool> const& path, std::vector<uint64_t> const& state_valuation, z3::expr_vector & substituted) const override;
    z3::expr substituteActionExpression(std::vector<bool> const& path, uint64_t action) const override;
    void substitutePrefixExpressionHarmonizing(std::vector<bool> const& path, z3::expr_vector const& state_valuation, z3::expr_vector & substituted) const override;
    z3::expr substituteActionExpressionHarmonizing(std::vector<bool> const& path, uint64_t action, z3::expr const& harmonizing_variable) const override;

    void addFamilyEncoding(Family const& subfamily, z3::solver & solver) const override;
    bool isPathEnabledInState(
        std::vector<bool> const& path,
        Family const& subfamily,
        std::vector<uint64_t> const& state_valuation
    ) const override;

    void loadHoleAssignmentFromModel(
        z3::model const& model, std::vector<std::vector<uint64_t>> & hole_options
    ) const override;
    void loadHoleAssignmentFromModelHarmonizing(
        z3::model const& model, std::vector<std::vector<uint64_t>> & hole_options, uint64_t harmonizing_hole
    ) const override;

    void unsatCoreAnalysis(
        Family const& subfamily,
        std::vector<bool> const& path,
        std::vector<uint64_t> const& state_valuation,
        uint64_t path_action, bool action_enabled,
        std::vector<std::set<uint64_t>> & hole_options
    ) const override;
};


class InnerNode: public TreeNode {
public:

    Hole decision_hole;
    std::vector<Hole> variable_hole;
    z3::expr_vector state_substitution_variables;

    z3::expr step_true;
    z3::expr step_false;

    z3::expr step_true_harm;
    z3::expr step_false_harm;

    InnerNode(
        uint64_t identifier, z3::context & ctx,
        std::vector<std::string> const& variable_name,
        std::vector<std::vector<int64_t>> const& variable_domain,
        z3::expr_vector const& state_substitution_variables
    );

    void createHoles(Family& family) override;
    void loadHoleInfo(std::vector<std::tuple<uint64_t,std::string,std::string>> & hole_info) const override;
    void createPaths(z3::expr const& harmonizing_variable) override;
    uint64_t getPathActionHole(std::vector<bool> const& path);

    void substitutePrefixExpression(std::vector<bool> const& path, std::vector<uint64_t> const& state_valuation, z3::expr_vector & substituted) const override;
    z3::expr substituteActionExpression(std::vector<bool> const& path, uint64_t action) const override;
    void substitutePrefixExpressionHarmonizing(std::vector<bool> const& path, z3::expr_vector const& state_valuation, z3::expr_vector & substituted) const override;
    z3::expr substituteActionExpressionHarmonizing(std::vector<bool> const& path, uint64_t action, z3::expr const& harmonizing_variable) const override;

    void addFamilyEncoding(Family const& subfamily, z3::solver & solver) const override;
    bool isPathEnabledInState(
        std::vector<bool> const& path,
        Family const& subfamily,
        std::vector<uint64_t> const& state_valuation
    ) const override;

    void loadHoleAssignmentFromModel(
        z3::model const& model, std::vector<std::vector<uint64_t>> & hole_options
    ) const override;
    void loadHoleAssignmentFromModelHarmonizing(
        z3::model const& model, std::vector<std::vector<uint64_t>> & hole_options, uint64_t harmonizing_hole
    ) const override;

    void unsatCoreAnalysis(
        Family const& subfamily,
        std::vector<bool> const& path,
        std::vector<uint64_t> const& state_valuation,
        uint64_t path_action, bool action_enabled,
        std::vector<std::set<uint64_t>> & hole_options
    ) const override;
};




}