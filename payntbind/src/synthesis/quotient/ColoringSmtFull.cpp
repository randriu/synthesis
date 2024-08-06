#include "ColoringSmtFull.h"

#include <storm/exceptions/InvalidArgumentException.h>
#include <storm/exceptions/NotImplementedException.h>
#include <storm/exceptions/IllegalFunctionCallException.h>

#include <sstream>

namespace synthesis {

ColoringSmtFull::ColoringSmtFull(
        std::vector<uint64_t> const& row_groups,
        std::vector<uint64_t> const& choice_to_action,
        storm::storage::sparse::StateValuations const& state_valuations,
        std::vector<std::string> const& variable_name,
        std::vector<std::vector<int64_t>> const& variable_domain,
        std::vector<std::tuple<uint64_t,uint64_t,uint64_t>> const& tree_list
) : choice_to_action(choice_to_action), row_groups(row_groups),
    variable_name(variable_name), variable_domain(variable_domain),
    solver(ctx), substitution_variables(ctx) {

    // extract variables in the order of variable_name
    std::vector<storm::expressions::Variable> program_variables;
    auto const& valuation = state_valuations.at(0);
    for(auto const& name: variable_name) {
        bool variable_found = false;
        for(auto x = valuation.begin(); x != valuation.end(); ++x) {
            storm::expressions::Variable const& program_variable = x.getVariable();
            if(program_variable.getName() == name) {
                program_variables.push_back(program_variable);
                variable_found = true;
                break;
            }
        }
        STORM_LOG_THROW(variable_found, storm::exceptions::InvalidArgumentException, "unexpected variable name");
    }

    // create the tree
    uint64_t num_nodes = tree_list.size();
    uint64_t num_actions = *std::max_element(choice_to_action.begin(),choice_to_action.end())-1;
    for(uint64_t node = 0; node < num_nodes; ++node) {
        auto [parent,child_true,child_false] = tree_list[node];
        STORM_LOG_THROW(
            (child_true != num_nodes) == (child_false != num_nodes), storm::exceptions::InvalidArgumentException,
            "inner node has only one child"
        );
        if(child_true != num_nodes) {
            tree.push_back(std::make_shared<InnerNode>(node,ctx,this->variable_name,this->variable_domain));
        } else {
            tree.push_back(std::make_shared<TerminalNode>(node,ctx,num_actions));
        }
    }
    getRoot()->createTree(tree_list,tree);

    // create substitution variables
    for(auto const& name: variable_name) {
        substitution_variables.push_back(ctx.int_const(name.c_str()));
    }
    substitution_variables.push_back(ctx.int_const("act"));
    getRoot()->createHoles(family);
    getRoot()->createPaths(substitution_variables);

    // collect all path expressions
    std::vector<z3::expr_vector> path_expressions;
    for(std::vector<std::pair<bool,uint64_t>> const& path: getRoot()->paths) {
        z3::expr_vector path_expression(ctx);
        getRoot()->loadPathExpression(path,path_expression);
        path_expressions.push_back(path_expression);
    }

    // create choice substitutions
    for(uint64_t state = 0; state < numStates(); ++state) {
        std::vector<int64_t> state_substitution;
        for(uint64_t variable = 0; variable < variable_name.size(); ++variable) {
            storm::expressions::Variable const& program_variable = program_variables[variable];
            int value = getVariableValueAtState(state_valuations,state,program_variable);
            state_substitution.push_back(value);
        }
        for(uint64_t choice = row_groups[state]; choice < row_groups[state+1]; ++choice) {
            uint64_t action = choice_to_action[choice];
            std::vector<int64_t> substitution = state_substitution;
            substitution.push_back(action);
            choice_substitution.push_back(substitution);
            z3::expr_vector substitution_expr(ctx);
            for(int64_t value: substitution) {
                substitution_expr.push_back(ctx.int_val(value));
            }
            choice_substitution_expr.push_back(substitution_expr);
        }
    }

    // create choice colors
    for(uint64_t state = 0; state < numStates(); ++state) {
        for(uint64_t choice = row_groups[state]; choice < row_groups[state+1]; ++choice) {
            std::vector<z3::expr_vector> path_step_of_choice;
            z3::expr_vector paths(ctx);
            std::vector<std::string> clause_label;

            // evaluate each path and create the corresponding colors
            for(z3::expr_vector const& path_expression: path_expressions) {
                z3::expr_vector path_step(ctx);
                for(z3::expr step: path_expression) {
                    path_step.push_back(step.substitute(substitution_variables,choice_substitution_expr[choice]));
                }
                // TODO check if the clause can be satisfied
                uint64_t path_index = paths.size();
                path_step_of_choice.push_back(path_step);
                paths.push_back(z3::mk_or(path_step));
                std::string label = "c" + std::to_string(choice) + "_" + std::to_string(path_index);
                clause_label.push_back(label);
            }

            choice_path_step.push_back(path_step_of_choice);
            choice_path.push_back(paths);
            choice_path_label.push_back(clause_label);
        }
    }
}

const uint64_t ColoringSmtFull::numStates() const {
    return row_groups.size()-1;
}

const uint64_t ColoringSmtFull::numChoices() const {
    return choice_to_action.size();
}

uint64_t ColoringSmtFull::numNodes() const {
    return tree.size();
}

std::shared_ptr<TreeNode> ColoringSmtFull::getRoot() {
    return tree[0];
}

const uint64_t ColoringSmtFull::numVariables() const {
    return variable_name.size();
}

int ColoringSmtFull::getVariableValueAtState(
    storm::storage::sparse::StateValuations const& state_valuations, uint64_t state, storm::expressions::Variable variable
) const {
    if(variable.hasBooleanType()) {
        return (int)state_valuations.getBooleanValue(state,variable);
    } else {
        return state_valuations.getIntegerValue(state,variable);
    }
}

std::vector<std::pair<std::string,std::string>> ColoringSmtFull::getFamilyInfo() {
    std::vector<std::pair<std::string,std::string>> hole_info(family.numHoles());
    getRoot()->loadHoleInfo(hole_info);
    return hole_info;
}


void ColoringSmtFull::addChoiceEncoding(uint64_t choice, bool add_label) {
    if(not add_label) {
        solver.add(choice_path[choice]);
        return;
    }
    auto const& paths = choice_path[choice];
    for(uint64_t path = 0; path < paths.size(); ++path) {
        solver.add(paths[path], choice_path_label[choice][path].c_str());
    }
}

BitVector ColoringSmtFull::selectCompatibleChoices(Family const& subfamily) {
    return selectCompatibleChoices(subfamily,BitVector(numChoices(),true));
}

BitVector ColoringSmtFull::selectCompatibleChoices(Family const& subfamily, BitVector const& base_choices) {
    BitVector selection(numChoices(),false);

    // check if the subfamily itself satisfies hole restrictions
    solver.push();
    getRoot()->addFamilyEncoding(subfamily,solver);
    if(solver.check() == z3::unsat) {
        solver.pop();
        std::cout << "family is UNSAT" << std::endl;
        return selection;
    }

    // check individual choices
    std::vector<std::vector<uint64_t>> state_enabled_choices(numStates());
    for(uint64_t state = 0; state < numStates(); ++state) {
        for(uint64_t choice = row_groups[state]; choice < row_groups[state+1]; ++choice) {
            if(not base_choices[choice]) {
                continue;
            }
            solver.push();
            selectCompatibleChoicesTimer.start();
            addChoiceEncoding(choice,false);
            z3::check_result result = solver.check();
            selectCompatibleChoicesTimer.stop();
            solver.pop();
            if(result == z3::sat) {
                selection.set(choice,true);
                state_enabled_choices[state].push_back(choice);
            }
        }
        if(state_enabled_choices[state].empty()) {
            solver.pop();
            selection.clear();
            std::cout << "no choice enabled in state " << state << std::endl;
            return selection;
        }
    }

    // check selected choices simultaneously
    solver.push();
    for(std::vector<uint64_t> const& choices: state_enabled_choices) {
        z3::expr_vector enabled_choices(ctx);
        for(uint64_t choice: choices) {
            enabled_choices.push_back(z3::mk_and(choice_path[choice]));
        }
        solver.add(z3::mk_or(enabled_choices));
    }
    if(solver.check() == z3::unsat) {
        std::cout << "no consistent scheduler exists " << std::endl;
        selection.clear();
    }
    solver.pop();

    solver.pop();
    return selection;
}


std::pair<bool,std::vector<std::vector<uint64_t>>> ColoringSmtFull::areChoicesConsistent(BitVector const& choices, Family const& subfamily) {

    solver.push();
    getRoot()->addFamilyEncoding(subfamily,solver);
    solver.push();
    for(auto choice: choices) {
        addChoiceEncoding(choice,true);
    }
    z3::check_result result = solver.check();

    std::vector<std::set<uint64_t>> hole_options(family.numHoles());
    std::vector<std::vector<uint64_t>> hole_options_vector(family.numHoles());
    if(result == z3::sat) {
        z3::model model = solver.get_model();
        solver.pop();
        solver.pop();
        getRoot()->loadHoleAssignmentFromModel(model,hole_options_vector);
        return std::make_pair(true,hole_options_vector);
    }

    z3::expr_vector unsat_core = solver.unsat_core();
    solver.pop();
    for(z3::expr expr: unsat_core) {
        std::istringstream iss(expr.decl().name().str());
        char prefix; iss >> prefix;
        if(prefix == 'h') {
            continue;
        }

        uint64_t choice,path; iss >> choice; iss >> prefix; iss >> path;
        uint64_t action = choice_to_action[choice];
        std::cout << "checking: " << choice_path[choice][path] << std::endl;
        getRoot()->loadHoleAssignmentOfPath(
            solver, getRoot()->paths[path], choice_path_step[choice][path], choice_substitution[choice], substitution_variables, choice_substitution_expr[choice], hole_options
        );
    }
    solver.pop();

    for(uint64_t hole = 0; hole < family.numHoles(); ++hole) {
        hole_options_vector[hole].assign(hole_options[hole].begin(),hole_options[hole].end());
    }
    return std::make_pair(false,hole_options_vector);
}

}