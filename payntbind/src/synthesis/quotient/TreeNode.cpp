#include "TreeNode.h"

#include <storm/exceptions/UnexpectedException.h>

#include <sstream>

namespace synthesis {


TreeNode::Hole::Hole(bool is_interval_type, z3::context& ctx)
: is_interval_type(is_interval_type), solver_variable(ctx), restriction(ctx) {
    // left intentionally blank
}

void TreeNode::Hole::createSolverVariable() {
    solver_variable = solver_variable.ctx().int_const(name.c_str());
    solver_string_domain = "h_" + std::to_string(hole);
    solver_string_restriction = "r_" + std::to_string(hole);
}

uint64_t TreeNode::Hole::getModelValue(z3::model const& model) const {
    return model.eval(solver_variable).get_numeral_int64();
}

z3::expr TreeNode::Hole::domainEncoding(Family const& subfamily) const {
    if(is_interval_type) {
        return domainInterval(subfamily);
    } else {
        return domainEnumeration(subfamily);
    }
}

void TreeNode::Hole::addDomainEncoding(Family const& subfamily, z3::solver& solver) const {
    z3::expr encoding = domainEncoding(subfamily);
    // std::cout << solver_string_domain.c_str() << " : " << encoding << std::endl;
    solver.add(encoding, solver_string_domain.c_str());
    if(is_interval_type) {
        // std::cout << solver_string_restriction.c_str() << " : " << restriction << std::endl;
        // solver.add(restriction, solver_string_restriction.c_str());    
    }
}

z3::expr TreeNode::Hole::domainInterval(Family const& subfamily) const {
    std::vector<uint64_t> const& domain = subfamily.holeOptions(hole);
    int domain_min = domain.front();
    int domain_max = domain.back();
    if(domain_min < domain_max) {
        return (domain_min <= solver_variable) and (solver_variable <= domain_max);
    } else {
        return (solver_variable == domain_min);
    }
}

z3::expr TreeNode::Hole::domainEnumeration(Family const& subfamily) const {
    z3::expr_vector options(solver_variable.ctx());
    for(uint64_t option: subfamily.holeOptions(hole)) {
        options.push_back(solver_variable == (int)option);
    }
    return z3::mk_or(options);
}


bool TreeNode::verifyExpression(z3::solver & solver, z3::expr const& expr) {
    solver.push();
    solver.add(expr);
    z3::check_result result = solver.check();
    solver.pop();
    return result == z3::sat;
}

TreeNode::TreeNode(
    uint64_t identifier, z3::context& ctx,
    std::vector<std::string> const& variable_name,
    std::vector<std::vector<int64_t>> const& variable_domain
) : identifier(identifier), ctx(ctx), variable_name(variable_name), variable_domain(variable_domain) {
    parent = NULL;
    child_true = NULL;
    child_false = NULL;
    depth = 0;
}

const uint64_t TreeNode::numVariables() const {
    return variable_name.size();
}

void TreeNode::createTree(
    std::vector<std::tuple<uint64_t,uint64_t,uint64_t>> const& tree_list,
    std::vector<std::shared_ptr<TreeNode>> & tree
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
    return identifier == parent->child_true->identifier;
}

std::shared_ptr<TreeNode> TreeNode::getChild(bool condition) const {
    return condition ? child_true : child_false;
}

const TreeNode *TreeNode::getNodeOfPath(std::vector<bool> const& path, uint64_t step) const {
    if(step == depth) {
        return this;
    }
    bool step_to_true_child = path[depth];
    return getChild(step_to_true_child)->getNodeOfPath(path,step);
}




TerminalNode::TerminalNode(
        uint64_t identifier, z3::context & ctx,
        std::vector<std::string> const& variable_name, std::vector<std::vector<int64_t>> const& variable_domain,
        uint64_t num_actions
) : TreeNode(identifier,ctx,variable_name,variable_domain), num_actions(num_actions), action_hole(false,ctx), action_expr(ctx) {}

void TerminalNode::createHoles(Family& family) {
    action_hole.hole = family.addHole(num_actions);
    action_hole.name = "A_" + std::to_string(identifier);
    action_hole.createSolverVariable();
}

void TerminalNode::loadHoleInfo(std::vector<std::pair<std::string,std::string>> & hole_info) const {
    hole_info[action_hole.hole] = std::make_pair(action_hole.name,"__action__");
}

void TerminalNode::createPaths(z3::expr_vector const& substitution_variables) {
    action_expr = action_hole.solver_variable == substitution_variables.back();
    paths.push_back({true});
}

void TerminalNode::loadPathExpression(
    std::vector<bool> const& path, z3::expr_vector & expression
) const {
    expression.push_back(action_expr);
}

void TerminalNode::addFamilyEncoding(Family const& subfamily, z3::solver& solver) const {
    action_hole.addDomainEncoding(subfamily,solver);
}

void TerminalNode::loadHoleAssignmentFromModel(z3::model const& model, std::vector<std::vector<uint64_t>> & hole_options) const {
    hole_options[action_hole.hole].push_back(action_hole.getModelValue(model));
}

bool TerminalNode::isPathEnabledInState(
    std::vector<bool> const& path, Family const& subfamily, std::vector<uint64_t> const& state_valuation
) const {
    return true;
}

void TerminalNode::unsatCoreAnalysisMeta(
    Family const& subfamily,
    std::vector<bool> const& path,
    std::vector<uint64_t> const& state_valuation,
    uint64_t path_action, bool action_enabled,
    std::vector<std::set<uint64_t>> & hole_options
) const {
    if(not action_enabled) {
        return;
    }
    hole_options[action_hole.hole].insert(path_action);
}






InnerNodeSpecific::InnerNodeSpecific(
        uint64_t identifier, z3::context & ctx,
        std::vector<std::string> const& variable_name,
        std::vector<std::vector<int64_t>> const& variable_domain,
        uint64_t variable
) : TreeNode(identifier,ctx,variable_name,variable_domain), variable(variable), variable_hole(true,ctx),
step_true(ctx), step_false(ctx) {}

void InnerNodeSpecific::createHoles(Family& family) {
    variable_hole.hole = family.addHole(variable_domain[variable].size()-1);
    variable_hole.name = variable_name[variable] + "_" + std::to_string(identifier);
    variable_hole.createSolverVariable();

    // add restrictions
    InnerNodeSpecific *node = this;
    InnerNodeSpecific *node_parent = std::dynamic_pointer_cast<InnerNodeSpecific>(node->parent).get();
    InnerNodeSpecific *lower_bound = NULL;
    InnerNodeSpecific *upper_bound = NULL;
    while(node_parent != NULL) {
        if(node_parent->variable == variable) {
            if(node->isTrueChild()) {
                if(upper_bound == NULL) {
                    upper_bound = node_parent;
                }
            } else {
                if(lower_bound == NULL) {
                    lower_bound = node_parent;
                }
            }
            if(upper_bound != NULL and lower_bound != NULL) {
                break;
            }
        }
        node = node_parent;
        node_parent = std::dynamic_pointer_cast<InnerNodeSpecific>(node->parent).get();
    }
    z3::expr_vector restriction(ctx);
    if(lower_bound != NULL) {
        restriction.push_back(variable_hole.solver_variable >= lower_bound->variable_hole.solver_variable);
    }
    if(upper_bound != NULL) {
        restriction.push_back(variable_hole.solver_variable <= upper_bound->variable_hole.solver_variable);
    }
    variable_hole.restriction = z3::mk_and(restriction);
    child_true->createHoles(family);
    child_false->createHoles(family);
}

void InnerNodeSpecific::loadHoleInfo(std::vector<std::pair<std::string,std::string>> & hole_info) const {
    hole_info[variable_hole.hole] = std::make_pair(variable_hole.name,variable_name[variable]);
    child_true->loadHoleInfo(hole_info);
    child_false->loadHoleInfo(hole_info);
}

void InnerNodeSpecific::createPaths(z3::expr_vector const& substitution_variables) {
    child_true->createPaths(substitution_variables);
    child_false->createPaths(substitution_variables);

    step_true = substitution_variables[variable] <= variable_hole.solver_variable;
    step_false = substitution_variables[variable] > variable_hole.solver_variable;
    for(bool condition: {true,false}) {
        std::shared_ptr<TreeNode> child = getChild(condition);
        for(std::vector<bool> const& suffix: child->paths) {
            std::vector<bool> path;
            path.push_back(condition);
            path.insert(path.end(),suffix.begin(),suffix.end());
            paths.push_back(path);
        }
    }
}

void InnerNodeSpecific::loadPathExpression(
    std::vector<bool> const& path, z3::expr_vector & expression
) const {
    bool step_to_true_child = path[depth];
    z3::expr const& step = step_to_true_child ? step_true : step_false;
    expression.push_back(step);
    getChild(step_to_true_child)->loadPathExpression(path,expression);
}

void InnerNodeSpecific::addFamilyEncoding(Family const& subfamily, z3::solver& solver) const {
    variable_hole.addDomainEncoding(subfamily,solver);
    child_true->addFamilyEncoding(subfamily,solver);
    child_false->addFamilyEncoding(subfamily,solver);
}

bool InnerNodeSpecific::isPathEnabledInState(
    std::vector<bool> const& path, Family const& subfamily, std::vector<uint64_t> const& state_valuation
) const {
    bool step_to_true_child = path[depth];
    uint64_t value = state_valuation[variable];
    std::vector<uint64_t> const& domain = subfamily.holeOptions(variable_hole.hole);
    if(    step_to_true_child and not (value <= domain.back())) {
        return false;
    }
    if(not step_to_true_child and not (value > domain.front())) {
        return false;
    }
    return getChild(step_to_true_child)->isPathEnabledInState(path,subfamily,state_valuation);
}

void InnerNodeSpecific::loadHoleAssignmentFromModel(z3::model const& model, std::vector<std::vector<uint64_t>> & hole_options) const {
    uint64_t hole_option = variable_hole.getModelValue(model);
    hole_options[variable_hole.hole].push_back(hole_option);
    child_true->loadHoleAssignmentFromModel(model,hole_options);
    child_false->loadHoleAssignmentFromModel(model,hole_options);
}

void InnerNodeSpecific::unsatCoreAnalysisMeta(
    Family const& subfamily,
    std::vector<bool> const& path,
    std::vector<uint64_t> const& state_valuation,
    uint64_t path_action, bool action_enabled,
    std::vector<std::set<uint64_t>> & hole_options
) const {
    bool step_to_true_child = path[depth];
    std::vector<uint64_t> const& domain = subfamily.holeOptions(variable_hole.hole);
    if(action_enabled == step_to_true_child) {
        if(state_valuation[variable] <= domain.back()) {
            hole_options[variable_hole.hole].insert(domain.back());
        }
    } else {
        if(state_valuation[variable] > domain.front()) {
            hole_options[variable_hole.hole].insert(domain.front());
        }
    }
    getChild(step_to_true_child)->unsatCoreAnalysisMeta(subfamily,path,state_valuation,path_action,action_enabled,hole_options);
}





InnerNodeGeneric::InnerNodeGeneric(
        uint64_t identifier, z3::context & ctx,
        std::vector<std::string> const& variable_name,
        std::vector<std::vector<int64_t>> const& variable_domain
) : TreeNode(identifier,ctx,variable_name,variable_domain), decision_hole(false,ctx), step_true(ctx), step_false(ctx) {}

void InnerNodeGeneric::createHoles(Family& family) {
    for(uint64_t variable = 0; variable < numVariables(); ++variable) {
        Hole hole(true,ctx);
        hole.hole = family.addHole(variable_domain[variable].size()-1);
        hole.name = variable_name[variable] + "_" + std::to_string(identifier);
        hole.createSolverVariable();
        variable_hole.push_back(hole);
    }
    decision_hole.hole = family.addHole(numVariables());
    decision_hole.name = "V_" + std::to_string(identifier);
    decision_hole.createSolverVariable();

    InnerNodeGeneric *node = this;
    InnerNodeGeneric *node_parent = std::dynamic_pointer_cast<InnerNodeGeneric>(node->parent).get();
    std::vector<InnerNodeGeneric *> lower_bounds;
    std::vector<InnerNodeGeneric *> upper_bounds;
    while(node_parent != NULL) {
        if(node->isTrueChild()) {
            upper_bounds.push_back(node_parent);
        } else {
            lower_bounds.push_back(node_parent);
        }
        node = node_parent;
        node_parent = std::dynamic_pointer_cast<InnerNodeGeneric>(node->parent).get();
    }
    for(uint64_t variable = 0; variable < numVariables(); ++variable) {
        // Vi=v => (V_lb=v => Xlb <= Xi) and (V_ub=v => Xi <= Xub)
        z3::expr lhs = decision_hole.solver_variable != (int)variable;
        z3::expr_vector rhs(ctx);
        z3::expr const& var_node = variable_hole[variable].solver_variable;
        for(InnerNodeGeneric *bound: lower_bounds) {
            z3::expr const& var_bound = bound->variable_hole[variable].solver_variable;
            rhs.push_back(bound->decision_hole.solver_variable != (int)variable or var_bound <= var_node);
        }
        for(InnerNodeGeneric *bound: upper_bounds) {
            z3::expr const& var_bound = bound->variable_hole[variable].solver_variable;
            rhs.push_back(bound->decision_hole.solver_variable != (int)variable or var_node <= var_bound);
        }
        variable_hole[variable].restriction = lhs or z3::mk_and(rhs);
    }
    child_true->createHoles(family);
    child_false->createHoles(family);
}

void InnerNodeGeneric::loadHoleInfo(std::vector<std::pair<std::string,std::string>> & hole_info) const {
    hole_info[decision_hole.hole] = std::make_pair(decision_hole.name,"__decision__");
    for(uint64_t variable = 0; variable < numVariables(); ++variable) {
        Hole const& hole = variable_hole[variable];
        hole_info[hole.hole] = std::make_pair(hole.name,variable_name[variable]);
    }
    child_true->loadHoleInfo(hole_info);
    child_false->loadHoleInfo(hole_info);
}

void InnerNodeGeneric::createPaths(z3::expr_vector const& substitution_variables) {
    child_true->createPaths(substitution_variables);
    child_false->createPaths(substitution_variables);

    // create steps
    z3::expr_vector step_true_options(ctx);
    z3::expr_vector step_false_options(ctx);
    for(uint64_t variable = 0; variable < numVariables(); ++variable) {
        z3::expr const& dv = decision_hole.solver_variable;
        z3::expr const& vv = variable_hole[variable].solver_variable;
        
        step_true_options.push_back( dv == (int)variable and substitution_variables[variable] <= vv);
        step_false_options.push_back(dv == (int)variable and substitution_variables[variable]  > vv);
    }
    step_true = z3::mk_or(step_true_options);
    step_false = z3::mk_or(step_false_options);

    // create paths
    for(bool condition: {true,false}) {
        std::shared_ptr<TreeNode> child = getChild(condition);
        for(std::vector<bool> const& suffix: child->paths) {
            std::vector<bool> path;
            path.push_back(condition);
            path.insert(path.end(),suffix.begin(),suffix.end());
            paths.push_back(path);
        }
    }
}

void InnerNodeGeneric::loadPathExpression(
    std::vector<bool> const& path, z3::expr_vector & expression
) const {
    bool step_to_true_child = path[depth];
    z3::expr const& step = step_to_true_child ? step_true : step_false;
    expression.push_back(step);
    getChild(step_to_true_child)->loadPathExpression(path,expression);
}

void InnerNodeGeneric::addFamilyEncoding(Family const& subfamily, z3::solver& solver) const {
    decision_hole.addDomainEncoding(subfamily,solver);
    for(Hole const& hole: variable_hole) {
        hole.addDomainEncoding(subfamily,solver);
    }
    child_true->addFamilyEncoding(subfamily,solver);
    child_false->addFamilyEncoding(subfamily,solver);
}

bool InnerNodeGeneric::isPathEnabledInState(
    std::vector<bool> const& path, Family const& subfamily, std::vector<uint64_t> const& state_valuation
) const {
    bool step_to_true_child = path[depth];
    for(uint64_t variable = 0; variable < numVariables(); ++variable) {
        z3::expr const& dv = decision_hole.solver_variable;
        if(not subfamily.holeContains(decision_hole.hole,variable)) {
            continue;
        }
        z3::expr const& vv = variable_hole[variable].solver_variable;
        uint64_t value = state_valuation[variable];
        std::vector<uint64_t> const& domain = subfamily.holeOptions(variable_hole[variable].hole);
        if( (step_to_true_child and value <= domain.back()) or (not step_to_true_child and value > domain.front()) ) {
            return getChild(step_to_true_child)->isPathEnabledInState(path,subfamily,state_valuation);
        }
    }
    return false;
}

void InnerNodeGeneric::loadHoleAssignmentFromModel(z3::model const& model, std::vector<std::vector<uint64_t>> & hole_options) const {
    hole_options[decision_hole.hole].push_back(decision_hole.getModelValue(model));
    for(Hole const& hole: variable_hole) {
        hole_options[hole.hole].push_back(hole.getModelValue(model));
    }
    child_true->loadHoleAssignmentFromModel(model,hole_options);
    child_false->loadHoleAssignmentFromModel(model,hole_options);
}

void InnerNodeGeneric::unsatCoreAnalysisMeta(
    Family const& subfamily,
    std::vector<bool> const& path,
    std::vector<uint64_t> const& state_valuation,
    uint64_t path_action, bool action_enabled,
    std::vector<std::set<uint64_t>> & hole_options
) const {
    bool step_to_true_child = path[depth];

    if(action_enabled) {
        bool sat_variable_found = false;
        uint64_t sat_variable;
        uint64_t sat_variable_option;
        for(uint64_t variable: subfamily.holeOptions(decision_hole.hole)) {
            std::vector<uint64_t> const& domain = subfamily.holeOptions(variable_hole[variable].hole);
            if(step_to_true_child and state_valuation[variable] <= domain.back()) {
                sat_variable_found = true;
                sat_variable = variable;
                sat_variable_option = domain.back();
                break;
            }
            if(not step_to_true_child and state_valuation[variable] > domain.front()) {
                sat_variable_found = true;
                sat_variable = variable;
                sat_variable_option = domain.front();
                break;
            }
        }
        STORM_LOG_THROW(
            sat_variable_found, storm::exceptions::UnexpectedException,
            "Sat variable assignment not found."
        );
        hole_options[decision_hole.hole].insert(sat_variable);
        hole_options[variable_hole[sat_variable].hole].insert(sat_variable_option);
    } else {
        bool sat_variable_found = false;
        uint64_t sat_variable;
        uint64_t sat_variable_option;
        for(uint64_t variable: subfamily.holeOptions(decision_hole.hole)) {
            std::vector<uint64_t> const& domain = subfamily.holeOptions(variable_hole[variable].hole);
            if(step_to_true_child and not (state_valuation[variable] <= domain.front()) ) {
                sat_variable_found = true;
                sat_variable = variable;
                sat_variable_option = domain.front();
                break;
            }
            if(not step_to_true_child and not (state_valuation[variable] > domain.back()) ) {
                sat_variable_found = true;
                sat_variable = variable;
                sat_variable_option = domain.back();
                break;
            }
        }
        if(sat_variable_found) {
            hole_options[decision_hole.hole].insert(sat_variable);
            hole_options[variable_hole[sat_variable].hole].insert(sat_variable_option);
            return;
        }        
    }
    getChild(step_to_true_child)->unsatCoreAnalysisMeta(subfamily,path,state_valuation,path_action,action_enabled,hole_options);   
}


}
