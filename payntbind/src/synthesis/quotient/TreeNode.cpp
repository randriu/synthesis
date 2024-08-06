#include "TreeNode.h"

#include <storm/exceptions/InvalidArgumentException.h>
#include <storm/exceptions/NotImplementedException.h>
#include <storm/exceptions/IllegalFunctionCallException.h>

#include <sstream>

namespace synthesis {


TreeNode::HoleInfo::HoleInfo(z3::context& ctx): solver_variable(ctx), restriction(ctx) {
    // left intentionally blank
}

bool TreeNode::verifyExpression(z3::solver & solver, z3::expr const& expr) {
    solver.push();
    solver.add(expr);
    auto result = solver.check();
    solver.pop();
    return result == z3::sat;
}

TreeNode::TreeNode(uint64_t identifier, z3::context& ctx) : identifier(identifier), ctx(ctx) {
    parent = NULL;
    child_true = NULL;
    child_false = NULL;
    depth = 0;
}

void TreeNode::createTree(
    std::vector<std::tuple<uint64_t,uint64_t,uint64_t>> const& tree_list, std::vector<std::shared_ptr<TreeNode>> & tree
) {
    auto [parent_index,child_true_index,child_false_index] = tree_list[identifier];
    if(parent_index < tree.size()) {
        parent = tree[parent_index];
        depth = parent->depth+1;
    }
    if(child_true_index < tree.size()) {
        child_true = tree[child_true_index];
        child_true->createTree(tree_list,tree);
    }
    if(child_false_index < tree.size()) {
        child_false = tree[child_false_index];
        child_false->createTree(tree_list,tree);
    }
}


bool TreeNode::isRoot() const {
    return parent == NULL;
}

bool TreeNode::isTerminal() const {
    return child_true == NULL;
}

bool TreeNode::isTrueChild() const {
    STORM_LOG_THROW(not isRoot(), storm::exceptions::IllegalFunctionCallException, "the node has no parent");
    return identifier == parent->child_true->identifier;
}



TerminalNode::TerminalNode(uint64_t identifier, z3::context & ctx, uint64_t num_actions
) : TreeNode(identifier,ctx), num_actions(num_actions), action_hole(ctx), action_expr(ctx) {
    // left intentionally blank
}

void TerminalNode::createHoles(Family& family) {
    action_hole.hole = family.addHole(num_actions);
    action_hole.name = "A_" + std::to_string(identifier);
    action_hole.solver_variable = ctx.int_const(action_hole.name.c_str());
    action_hole.solver_string = "h" + std::to_string(action_hole.hole);
}

void TerminalNode::loadHoleInfo(std::vector<std::pair<std::string,std::string>> & hole_info) const {
    hole_info[action_hole.hole] = std::make_pair(action_hole.name,"__action__");
}

void TerminalNode::createSteps(z3::expr_vector const& substitution_variables) {
    action_expr = action_hole.solver_variable == substitution_variables.back();
}

void TerminalNode::createPaths(z3::expr_vector const& substitution_variables) {
    createSteps(substitution_variables);
    paths.push_back({std::make_pair(true,0)});
}

void TerminalNode::loadPathExpression(
    std::vector<std::pair<bool,uint64_t>> const& path, z3::expr_vector & path_expression
) const {
    STORM_LOG_THROW(path_expression.size() == depth, storm::exceptions::InvalidArgumentException, "path depth error");
    path_expression.push_back(action_expr);
}

void TerminalNode::addFamilyEncoding(Family const& subfamily, z3::solver& solver) const {
    z3::expr_vector options(ctx);
    for(uint64_t option: subfamily.holeOptions(action_hole.hole)) {
        options.push_back(action_hole.solver_variable == (int)option);
    }
    solver.add(z3::mk_or(options), action_hole.solver_string.c_str());
    std::cout << z3::mk_or(options) << std::endl;
}

void TerminalNode::loadHoleAssignmentFromModel(z3::model const& model, std::vector<std::vector<uint64_t>> & hole_options) const {
    hole_options[action_hole.hole].push_back(action_hole.getModelValue(model));
}






InnerNode::InnerNode(
    uint64_t identifier,
    z3::context & ctx,
    std::vector<std::string> const& variable_name,
    std::vector<std::vector<int64_t>> const& variable_domain
) : TreeNode(identifier,ctx), variable_name(variable_name), variable_domain(variable_domain), decision_hole(ctx) {
    // left intentionally blank
}


const uint64_t InnerNode::numVariables() const {
    return variable_name.size();
}

const uint64_t InnerNode::variableValueToHoleOption(uint64_t variable, int64_t value) const {
    for(uint64_t hole_option = 0; hole_option < variable_domain[variable].size(); ++hole_option) {
        if(variable_domain[variable][hole_option] == value) {
            return hole_option;
        }
    }
    STORM_LOG_THROW(false, storm::exceptions::InvalidArgumentException, "hole option not found");
}

std::shared_ptr<TreeNode> InnerNode::getChild(bool condition) const {
    return condition ? child_true : child_false;
}

std::vector<z3::expr> const& InnerNode::getSteps(bool condition) const {
    return condition ? steps_true : steps_false;
}

void InnerNode::createHoles(Family& family) {
    for(uint64_t variable = 0; variable < numVariables(); ++variable) {
        HoleInfo hole(ctx);
        hole.hole = family.addHole(variable_domain[variable].size()-1);
        hole.name = variable_name[variable] + "_" + std::to_string(identifier);
        hole.solver_variable = ctx.int_const(hole.name.c_str());
        hole.solver_string = "h" + std::to_string(hole.hole);
        variable_hole.push_back(hole);
    }
    decision_hole.hole = family.addHole(numVariables());
    decision_hole.name = "V_" + std::to_string(identifier);
    decision_hole.solver_variable = ctx.int_const(decision_hole.name.c_str());
    decision_hole.solver_string = "h" + std::to_string(decision_hole.hole);

    if(not isRoot()) {
        // add restrictions
        for(uint64_t variable = 0; variable < numVariables(); ++variable) {
            z3::expr const& var_node = variable_hole[variable].solver_variable;
            z3::expr const& var_parent = std::dynamic_pointer_cast<InnerNode>(parent)->variable_hole[variable].solver_variable;
            z3::expr const& dv = decision_hole.solver_variable;
            if(isTrueChild()) {
                variable_hole[variable].restriction = dv != (int)variable or var_node < var_parent;
            } else {
                variable_hole[variable].restriction = dv != (int)variable or var_node > var_parent;
            }
        }
    }
    child_true->createHoles(family);
    child_false->createHoles(family);
}

void InnerNode::loadHoleInfo(std::vector<std::pair<std::string,std::string>> & hole_info) const {
    hole_info[decision_hole.hole] = std::make_pair(decision_hole.name,"__decision__");
    for(uint64_t variable = 0; variable < numVariables(); ++variable) {
        HoleInfo const& hole = variable_hole[variable];
        hole_info[hole.hole] = std::make_pair(hole.name,variable_name[variable]);
    }
    child_true->loadHoleInfo(hole_info);
    child_false->loadHoleInfo(hole_info);
}

void InnerNode::createSteps(z3::expr_vector const& substitution_variables) {
    for(uint64_t variable = 0; variable < numVariables(); ++variable) {
        z3::expr const& dv = decision_hole.solver_variable;
        z3::expr const& vv = variable_hole[variable].solver_variable;
        steps_true.push_back( dv == (int)variable and substitution_variables[variable] <= vv);
        steps_false.push_back(dv == (int)variable and substitution_variables[variable] > vv);
    }
}

void InnerNode::createPaths(z3::expr_vector const& substitution_variables) {
    createSteps(substitution_variables);
    child_true->createPaths(substitution_variables);
    child_false->createPaths(substitution_variables);
    for(bool condition: {true,false}) {
        std::shared_ptr<TreeNode> child = getChild(condition);
        for(uint64_t variable = 0; variable < numVariables(); ++variable) {
            for(std::vector<std::pair<bool,uint64_t>> const& suffix: child->paths) {
                std::vector<std::pair<bool,uint64_t>> path;
                path.emplace_back(condition,variable);
                path.insert(path.end(),suffix.begin(),suffix.end());
                paths.push_back(path);
            }
        }
    }
}

void InnerNode::loadPathExpression(
    std::vector<std::pair<bool,uint64_t>> const& path, z3::expr_vector & path_expression
) const {
    STORM_LOG_THROW(path_expression.size() == depth, storm::exceptions::InvalidArgumentException, "path depth error");
    auto [step_to_true_child,step] = path[depth];
    std::shared_ptr<TreeNode> child = getChild(step_to_true_child);
    std::vector<z3::expr> const& steps = getSteps(step_to_true_child);
    // append NEGATED step condition
    path_expression.push_back(not steps[step]);
    child->loadPathExpression(path,path_expression);
}

void InnerNode::addFamilyEncoding(Family const& subfamily, z3::solver& solver) const {
    z3::expr_vector options(ctx);
    for(uint64_t option: subfamily.holeOptions(decision_hole.hole)) {
        options.push_back(decision_hole.solver_variable == (int)option);
    }
    solver.add(z3::mk_or(options), decision_hole.solver_string.c_str());
    std::cout << z3::mk_or(options) << std::endl;

    // variable holes
    for(uint64_t variable = 0; variable < numVariables(); ++variable) {
        HoleInfo const& hole = variable_hole[variable];
        std::vector<uint64_t> const& family_options = subfamily.holeOptions(hole.hole);
        // convention: hole options in the family are ordered
        int domain_min = variable_domain[variable][family_options.front()];
        int domain_max = variable_domain[variable][family_options.back()];
        z3::expr encoding = (domain_min <= hole.solver_variable) and (hole.solver_variable <= domain_max);
        if(domain_min == domain_max) {
            encoding = (hole.solver_variable == domain_min);
        }
        if(not isRoot()) {
            encoding = encoding and hole.restriction;
        }
        solver.add(encoding, hole.solver_string.c_str());
        std::cout << encoding << std::endl;
    }
    child_true->addFamilyEncoding(subfamily,solver);
    child_false->addFamilyEncoding(subfamily,solver);
}

void InnerNode::loadHoleAssignmentFromModel(z3::model const& model, std::vector<std::vector<uint64_t>> & hole_options) const {
    hole_options[decision_hole.hole].push_back(decision_hole.getModelValue(model));
    for(uint64_t variable = 0; variable < numVariables(); ++variable) {
        HoleInfo const& hole = variable_hole[variable];
        int64_t value = hole.getModelValue(model);
        uint64_t hole_option  = variableValueToHoleOption(variable,value);
        hole_options[hole.hole].push_back(hole_option);
    }
    child_true->loadHoleAssignmentFromModel(model,hole_options);
    child_false->loadHoleAssignmentFromModel(model,hole_options);
}


void TerminalNode::loadHoleAssignmentOfPath(
    z3::solver & solver,
    std::vector<std::pair<bool,uint64_t>> const& path,
    z3::expr_vector const& path_expression,
    std::vector<int64_t> const& choice_substitution,
    z3::expr_vector const& substitution_variables,
    z3::expr_vector const& choice_substitution_expr,
    std::vector<std::set<uint64_t>> & hole_options
) const {
    bool sat = verifyExpression(solver,path_expression.back());
    if(sat) {
        hole_options[action_hole.hole].insert(choice_substitution.back());
        std::cout << action_hole.name << " = " << choice_substitution.back() << std::endl;
    }
}

void InnerNode::loadHoleAssignmentOfPath(
    z3::solver & solver,
    std::vector<std::pair<bool,uint64_t>> const& path,
    z3::expr_vector const& path_expression,
    std::vector<int64_t> const& choice_substitution,
    z3::expr_vector const& substitution_variables,
    z3::expr_vector const& choice_substitution_expr,
    std::vector<std::set<uint64_t>> & hole_options
) const {
    auto [step_to_true_child,variable] = path[depth];
    bool sat = verifyExpression(solver,path_expression[depth]);
    if(sat) {
        hole_options[decision_hole.hole].insert(variable);
        std::cout << decision_hole.name << " = " << variable << std::endl;
        int64_t value = choice_substitution[variable];
        uint64_t hole_option  = variableValueToHoleOption(variable,value);
        hole_options[variable_hole[variable].hole].insert(hole_option);
        std::cout << variable_hole[variable].name << " = " << hole_option << std::endl;
    }
    getChild(step_to_true_child)->loadHoleAssignmentOfPath(solver,path,path_expression,choice_substitution,substitution_variables,choice_substitution_expr,hole_options);
}

}