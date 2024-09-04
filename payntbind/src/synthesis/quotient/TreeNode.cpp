#include "TreeNode.h"

#include <storm/exceptions/UnexpectedException.h>

#include <sstream>

namespace synthesis {


TreeNode::Hole::Hole(bool is_interval_type, z3::context& ctx)
: is_interval_type(is_interval_type), solver_variable(ctx), solver_variable_harm(ctx), restriction(ctx) {
    // left intentionally blank
}

TreeNode::Hole::Hole(bool is_interval_type, z3::context& ctx, uint64_t depth)
: is_interval_type(is_interval_type), solver_variable(ctx), solver_variable_harm(ctx), restriction(ctx), depth(depth) {
    // left intentionally blank
}

void TreeNode::Hole::createSolverVariable() {
    solver_variable = solver_variable.ctx().int_const(name.c_str());
    solver_string_domain = "h_" + std::to_string(hole);
    solver_string_domain_harm = "z_" + std::to_string(hole);
    solver_string_restriction = "r_" + std::to_string(hole);

    name_harm = name + "_h";
    solver_variable_harm = solver_variable.ctx().int_const(name_harm.c_str());
}

uint64_t TreeNode::Hole::getModelValue(z3::model const& model) const {
    return model.eval(solver_variable).get_numeral_int64();
}
uint64_t TreeNode::Hole::getModelValueHarmonizing(z3::model const& model) const {
    return model.eval(solver_variable_harm).get_numeral_int64();
}
void TreeNode::Hole::loadModelValueHarmonizing(z3::model const& model, std::vector<std::set<uint64_t>> & hole_options) const {
    hole_options[hole].insert(getModelValue(model));
    hole_options[hole].insert(getModelValueHarmonizing(model));
}

z3::expr TreeNode::Hole::domainEncoding(Family const& subfamily, bool harmonizing) const {
    z3::expr const& variable = not harmonizing ? solver_variable : solver_variable_harm;
    std::vector<uint64_t> const& domain = subfamily.holeOptions(hole);
    if(is_interval_type) {
        int domain_min = domain.front();
        int domain_max = domain.back();
        if(domain_min < domain_max) {
            return (domain_min <= variable) and (variable <= domain_max);
        } else {
            return (variable == domain_min);
        }
    } else {
        z3::expr_vector options(variable.ctx());
        for(uint64_t option: domain) {
            options.push_back(variable == (int)option);
        }
        return z3::mk_or(options);
    }
}

void TreeNode::Hole::addDomainEncoding(Family const& subfamily, z3::solver& solver) const {
    solver.add(domainEncoding(subfamily, false), solver_string_domain.c_str());
    solver.add(domainEncoding(subfamily, true), solver_string_domain_harm.c_str());

    /*if(is_interval_type) {
        std::cout << solver_string_restriction.c_str() << " : " << restriction << std::endl;
        solver.add(restriction, solver_string_restriction.c_str());    
    }*/
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
) : TreeNode(identifier,ctx,variable_name,variable_domain), num_actions(num_actions), action_hole(false,ctx),
    action_expr(ctx), action_expr_harm(ctx) {}

void TerminalNode::createHoles(Family& family) {
    action_hole.hole = family.addHole(num_actions);
    action_hole.name = "A_" + std::to_string(identifier);
    action_hole.depth = depth;
    action_hole.createSolverVariable();
}

void TerminalNode::loadHoleInfo(std::vector<std::pair<std::string,std::string>> & hole_info) const {
    hole_info[action_hole.hole] = std::make_pair(action_hole.name,"__action__");
}

void TerminalNode::createPaths(z3::expr_vector const& substitution_variables) {
    action_expr = action_hole.solver_variable == substitution_variables.back();
    paths.push_back({true});
}

void TerminalNode::createPathsHarmonizing(z3::expr_vector const& substitution_variables, z3::expr const& harmonizing_variable) {
    z3::expr const& hv = harmonizing_variable;
    int hole = (int)action_hole.hole;
    z3::expr eh = action_hole.solver_variable_harm == substitution_variables.back();
    action_expr_harm = (hv != hole and action_expr) or (hv == hole and ((not action_expr and eh) or (action_expr and not eh)));
}

void TerminalNode::loadPathExpression(std::vector<bool> const& path, z3::expr_vector & expression) const {
    expression.push_back(action_expr);
}

void TerminalNode::loadAllHoles(std::vector<const Hole *> & holes) const {
    holes[action_hole.hole] = &action_hole;
}

void TerminalNode::loadPathHoles(std::vector<bool> const& path, std::vector<uint64_t> & holes) const {
    holes.push_back(action_hole.hole);
}

void TerminalNode::addFamilyEncoding(Family const& subfamily, z3::solver& solver) const {
    action_hole.addDomainEncoding(subfamily,solver);
}

void TerminalNode::loadHoleAssignmentFromModel(z3::model const& model, std::vector<std::vector<uint64_t>> & hole_options) const {
    hole_options[action_hole.hole].push_back(action_hole.getModelValue(model));
}
void TerminalNode::loadHarmonizingHoleAssignmentFromModel(
    z3::model const& model, std::vector<std::set<uint64_t>> & hole_options, uint64_t harmonizing_hole
) const {
    if(action_hole.hole == harmonizing_hole) {
        action_hole.loadModelValueHarmonizing(model,hole_options);
    }
}

void TerminalNode::printHarmonizing(z3::model const& model) const {
    std::cout << action_hole.name_harm << " = " << action_hole.getModelValueHarmonizing(model) << std::endl;
}

bool TerminalNode::isPathEnabledInState(
    std::vector<bool> const& path, Family const& subfamily, std::vector<uint64_t> const& state_valuation
) const {
    return true;
}

void TerminalNode::unsatCoreAnalysis(
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




InnerNode::InnerNode(
        uint64_t identifier, z3::context & ctx,
        std::vector<std::string> const& variable_name,
        std::vector<std::vector<int64_t>> const& variable_domain
) : TreeNode(identifier,ctx,variable_name,variable_domain), decision_hole(false,ctx),
    step_true(ctx), step_false(ctx), step_true_harm(ctx), step_false_harm(ctx) {}

void InnerNode::createHoles(Family& family) {
    decision_hole.hole = family.addHole(numVariables());
    decision_hole.name = "V_" + std::to_string(identifier);
    decision_hole.depth = depth;
    decision_hole.createSolverVariable();
    for(uint64_t variable = 0; variable < numVariables(); ++variable) {
        Hole hole(true,ctx,depth);
        hole.hole = family.addHole(variable_domain[variable].size()-1);
        hole.name = variable_name[variable] + "_" + std::to_string(identifier);
        hole.createSolverVariable();
        variable_hole.push_back(hole);
    }

    InnerNode *node = this;
    InnerNode *node_parent = std::dynamic_pointer_cast<InnerNode>(node->parent).get();
    std::vector<InnerNode *> lower_bounds;
    std::vector<InnerNode *> upper_bounds;
    while(node_parent != NULL) {
        if(node->isTrueChild()) {
            upper_bounds.push_back(node_parent);
        } else {
            lower_bounds.push_back(node_parent);
        }
        node = node_parent;
        node_parent = std::dynamic_pointer_cast<InnerNode>(node->parent).get();
    }
    for(uint64_t variable = 0; variable < numVariables(); ++variable) {
        // Vi=v => (V_lb=v => Xlb <= Xi) and (V_ub=v => Xi <= Xub)
        z3::expr lhs = decision_hole.solver_variable != (int)variable;
        z3::expr_vector rhs(ctx);
        z3::expr const& var_node = variable_hole[variable].solver_variable;
        for(InnerNode *bound: lower_bounds) {
            z3::expr const& var_bound = bound->variable_hole[variable].solver_variable;
            rhs.push_back(bound->decision_hole.solver_variable != (int)variable or var_bound <= var_node);
        }
        for(InnerNode *bound: upper_bounds) {
            z3::expr const& var_bound = bound->variable_hole[variable].solver_variable;
            rhs.push_back(bound->decision_hole.solver_variable != (int)variable or var_node <= var_bound);
        }
        variable_hole[variable].restriction = lhs or z3::mk_and(rhs);
    }
    child_true->createHoles(family);
    child_false->createHoles(family);
}

void InnerNode::loadHoleInfo(std::vector<std::pair<std::string,std::string>> & hole_info) const {
    hole_info[decision_hole.hole] = std::make_pair(decision_hole.name,"__decision__");
    for(uint64_t variable = 0; variable < numVariables(); ++variable) {
        Hole const& hole = variable_hole[variable];
        hole_info[hole.hole] = std::make_pair(hole.name,variable_name[variable]);
    }
    child_true->loadHoleInfo(hole_info);
    child_false->loadHoleInfo(hole_info);
}

void InnerNode::createPaths(z3::expr_vector const& substitution_variables) {
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

void InnerNode::createPathsHarmonizing(z3::expr_vector const& substitution_variables, z3::expr const& harmonizing_variable) {
    child_true->createPathsHarmonizing(substitution_variables, harmonizing_variable);
    child_false->createPathsHarmonizing(substitution_variables, harmonizing_variable);

    // create steps
    z3::expr_vector step_true_options(ctx);
    z3::expr_vector step_false_options(ctx);
    z3::expr const& hv = harmonizing_variable;
    for(uint64_t variable = 0; variable < numVariables(); ++variable) {
        Hole d = decision_hole;
        z3::expr de = d.solver_variable == (int)variable;
        z3::expr deh = d.solver_variable_harm == (int)variable;
        z3::expr expr_decision = (hv != (int)d.hole and de) or (hv == (int)d.hole and ((not de and deh) or (de and not deh)) );

        Hole v = variable_hole[variable];
        z3::expr ve =  substitution_variables[variable] <= v.solver_variable;
        z3::expr veh = substitution_variables[variable] <= v.solver_variable_harm;
        z3::expr expr_true =  (hv != (int)v.hole and ve)     or (hv == (int)v.hole and ((not ve and veh) or (ve and not veh)) );
        z3::expr expr_false = (hv != (int)v.hole and not ve) or (hv == (int)v.hole and ((ve and not veh) or (not ve and veh)) );

        step_true_options.push_back(expr_decision and expr_true);
        step_false_options.push_back(expr_decision and expr_false);        
    }
    step_true_harm = z3::mk_or(step_true_options);
    step_false_harm = z3::mk_or(step_false_options);
}

void InnerNode::loadPathExpression(std::vector<bool> const& path, z3::expr_vector & expression) const {
    bool step_to_true_child = path[depth];
    z3::expr const& step = step_to_true_child ? step_true : step_false;
    expression.push_back(step);
    getChild(step_to_true_child)->loadPathExpression(path,expression);
}

void InnerNode::loadAllHoles(std::vector<const Hole *> & holes) const {
    holes[decision_hole.hole] = &decision_hole;
    for(Hole const& hole: variable_hole) {
        holes[hole.hole] = &hole;
    }
    child_true->loadAllHoles(holes);
    child_false->loadAllHoles(holes);
}

void InnerNode::loadPathHoles(std::vector<bool> const& path, std::vector<uint64_t> & holes) const {
    holes.push_back(decision_hole.hole);
    for(Hole const& hole: variable_hole) {
        holes.push_back(hole.hole);
    }
    getChild(path[depth])->loadPathHoles(path,holes);
}

void InnerNode::addFamilyEncoding(Family const& subfamily, z3::solver& solver) const {
    decision_hole.addDomainEncoding(subfamily,solver);
    for(Hole const& hole: variable_hole) {
        hole.addDomainEncoding(subfamily,solver);
    }
    child_true->addFamilyEncoding(subfamily,solver);
    child_false->addFamilyEncoding(subfamily,solver);
}

bool InnerNode::isPathEnabledInState(
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

void InnerNode::loadHoleAssignmentFromModel(z3::model const& model, std::vector<std::vector<uint64_t>> & hole_options) const {
    hole_options[decision_hole.hole].push_back(decision_hole.getModelValue(model));
    for(Hole const& hole: variable_hole) {
        hole_options[hole.hole].push_back(hole.getModelValue(model));
    }
    child_true->loadHoleAssignmentFromModel(model,hole_options);
    child_false->loadHoleAssignmentFromModel(model,hole_options);
}
void InnerNode::loadHarmonizingHoleAssignmentFromModel(
    z3::model const& model, std::vector<std::set<uint64_t>> & hole_options, uint64_t harmonizing_hole
) const {
    if(decision_hole.hole == harmonizing_hole) {
        decision_hole.loadModelValueHarmonizing(model,hole_options);
        return;
    }
    for(Hole const& hole: variable_hole) {
        if(hole.hole == harmonizing_hole) {
            hole.loadModelValueHarmonizing(model,hole_options);
            return;
        }
    }
    child_true->loadHarmonizingHoleAssignmentFromModel(model,hole_options,harmonizing_hole);
    child_false->loadHarmonizingHoleAssignmentFromModel(model,hole_options,harmonizing_hole);
}

void InnerNode::printHarmonizing(z3::model const& model) const {
    std::cout << decision_hole.name_harm << " = " << decision_hole.getModelValueHarmonizing(model) << std::endl;
    for(Hole const& hole: variable_hole) {
        std::cout << hole.name_harm << " = " << hole.getModelValueHarmonizing(model) << std::endl;
    }
    child_true->printHarmonizing(model);
    child_false->printHarmonizing(model);
}

void InnerNode::unsatCoreAnalysis(
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
    getChild(step_to_true_child)->unsatCoreAnalysis(subfamily,path,state_valuation,path_action,action_enabled,hole_options);
}

}
