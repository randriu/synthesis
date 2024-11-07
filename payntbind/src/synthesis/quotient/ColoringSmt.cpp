#include "ColoringSmt.h"

#include "src/synthesis/translation/choiceTransformation.h"

#include <storm/storage/sparse/StateValuations.h>
#include <storm/exceptions/UnexpectedException.h>

#include <sstream>
#include <queue>

namespace synthesis {

template<typename ValueType>
ColoringSmt<ValueType>::ColoringSmt(
    storm::models::sparse::NondeterministicModel<ValueType> const& model,
    std::vector<std::string> const& variable_name,
    std::vector<std::vector<int64_t>> const& variable_domain,
    std::vector<std::tuple<uint64_t,uint64_t,uint64_t>> const& tree_list,
    bool disable_counterexamples
) : initial_state(*model.getInitialStates().begin()),
    row_groups(model.getNondeterministicChoiceIndices()),
    choice_destinations(synthesis::computeChoiceDestinations(model)),
    choice_to_action(synthesis::extractActionLabels(model).second),
    variable_name(variable_name), variable_domain(variable_domain),
    solver(ctx), harmonizing_variable(ctx), disable_counterexamples(disable_counterexamples) {

    timers[__FUNCTION__].start();

    for(uint64_t state = 0; state < numStates(); ++state) {
        for(uint64_t choice = row_groups[state]; choice < row_groups[state+1]; ++choice) {
            choice_to_state.push_back(state);
        }
    }

    // extract variables in the order of variable_name
    std::vector<storm::expressions::Variable> program_variables;
    storm::storage::sparse::StateValuations const& state_valuations = model.getStateValuations();
    auto const& valuation = state_valuations.at(0);
    for(std::string const& name: variable_name) {
        bool variable_found = false;
        for(auto x = valuation.begin(); x != valuation.end(); ++x) {
            storm::expressions::Variable const& program_variable = x.getVariable();
            if(program_variable.getName() == name) {
                program_variables.push_back(program_variable);
                variable_found = true;
                break;
            }
        }
        STORM_LOG_THROW(variable_found, storm::exceptions::UnexpectedException, "Unexpected variable name.");
    }

    // create substitution variables
    z3::expr_vector state_substitution_variables(ctx);
    z3::expr_vector choice_substitution_variables(ctx);
    for(auto const& name: variable_name) {
        z3::expr variable = ctx.int_const(name.c_str());
        state_substitution_variables.push_back(variable);
        choice_substitution_variables.push_back(variable);
    }
    z3::expr action_substitution_variable = ctx.int_const("act");
    choice_substitution_variables.push_back(action_substitution_variable);

    // create the tree
    uint64_t num_nodes = tree_list.size();
    uint64_t num_actions = *std::max_element(choice_to_action.begin(),choice_to_action.end())+1;
    for(uint64_t node = 0; node < num_nodes; ++node) {
        auto [parent,child_true,child_false] = tree_list[node];
        STORM_LOG_THROW(
            (child_true != num_nodes) == (child_false != num_nodes), storm::exceptions::UnexpectedException,
            "Inner node has only one child."
        );
        if(child_true != num_nodes) {
            tree.push_back(std::make_shared<InnerNode>(node,ctx,this->variable_name,this->variable_domain,state_substitution_variables));
        } else {
            tree.push_back(std::make_shared<TerminalNode>(node,ctx,this->variable_name,this->variable_domain,num_actions,action_substitution_variable));
        }
    }
    getRoot()->createTree(tree_list,tree);

    getRoot()->createHoles(family);
    harmonizing_variable = ctx.int_const("__harm__");
    getRoot()->createPaths(harmonizing_variable);

    for(uint64_t state = 0; state < numStates(); ++state) {
        state_path_enabled.push_back(BitVector(numPaths()));
    }

    // store state valuations in terms of hole options
    state_valuation.resize(numStates());
    for(uint64_t state = 0; state < numStates(); ++state) {
        for(uint64_t variable = 0; variable < variable_name.size(); ++variable) {
            storm::expressions::Variable const& program_variable = program_variables[variable];
            int64_t value;
            if(program_variable.hasBooleanType()) {
                value = (int64_t)state_valuations.getBooleanValue(state,program_variable);
            } else {
                value = state_valuations.getIntegerValue(state,program_variable);
            }
            bool domain_option_found = false;
            for(uint64_t domain_option = 0; domain_option < variable_domain[variable].size(); ++domain_option) {
                if(variable_domain[variable][domain_option] == value) {
                    state_valuation[state].push_back(domain_option);
                    domain_option_found = true;
                    break;
                }
            }
            STORM_LOG_THROW(domain_option_found, storm::exceptions::UnexpectedException, "hole option not found.");
        }
    }

    // create state substitutions
    std::vector<z3::expr_vector> state_substitution_expr;
    for(uint64_t state = 0; state < numStates(); ++state) {
        z3::expr_vector substitution_expr(ctx);
        for(uint64_t value: state_valuation[state]) {
            substitution_expr.push_back(ctx.int_val(value));
        }
        state_substitution_expr.push_back(substitution_expr);
    }

    // create choice colors
    timers["ColoringSmt:: create choice colors"].start();

    for(std::vector<bool> const& path: getRoot()->paths) {
        path_action_hole.push_back(getRoot()->getPathActionHole(path));
    }

    choice_path_label.resize(numChoices());
    for(uint64_t state = 0; state < numStates(); ++state) {
        for(uint64_t choice = row_groups[state]; choice < row_groups[state+1]; ++choice) {
            for(uint64_t path = 0; path < numPaths(); ++path) {
                std::string label = "p" + std::to_string(choice) + "_" + std::to_string(path);
                choice_path_label[choice].push_back(label);
            }
        }
    }

    std::vector<z3::expr_vector> state_path_expression;
    for(uint64_t state = 0; state < numStates(); ++state) {
        getRoot()->createPrefixSubstitutions(state_valuation[state]);
        state_path_expression.push_back(z3::expr_vector(ctx));
        for(uint64_t path = 0; path < numPaths(); ++path) {
            z3::expr_vector evaluated(ctx);
            getRoot()->substitutePrefixExpression(getRoot()->paths[path], evaluated);
            state_path_expression[state].push_back(z3::mk_or(evaluated));
        }
    }
    std::vector<z3::expr_vector> action_path_expression;
    for(uint64_t action = 0; action < num_actions; ++action) {
        action_path_expression.push_back(z3::expr_vector(ctx));
        for(uint64_t path = 0; path < numPaths(); ++path) {
            z3::expr evaluated = getRoot()->substituteActionExpression(getRoot()->paths[path], action);
            action_path_expression[action].push_back(evaluated);
        }
    }

    for(uint64_t state = 0; state < numStates(); ++state) {
        for(uint64_t choice = row_groups[state]; choice < row_groups[state+1]; ++choice) {
            choice_path_expresssion.push_back(z3::expr_vector(ctx));
            uint64_t action = choice_to_action[choice];
            for(uint64_t path = 0; path < numPaths(); ++path) {
                choice_path_expresssion[choice].push_back(state_path_expression[state][path] or action_path_expression[action][path]);
            }
        }
    }
    timers["ColoringSmt:: create choice colors"].stop();

    if(disable_counterexamples) {
        timers[__FUNCTION__].stop();
        return;
    }

    timers["ColoringSmt:: create harmonizing variants"].start();
    std::vector<z3::expr_vector> state_path_expression_harmonizing;
    for(uint64_t state = 0; state < numStates(); ++state) {
        getRoot()->createPrefixSubstitutionsHarmonizing(state_substitution_expr[state]);
        state_path_expression_harmonizing.push_back(z3::expr_vector(ctx));
        for(uint64_t path = 0; path < numPaths(); ++path) {
            z3::expr_vector evaluated(ctx);
            getRoot()->substitutePrefixExpressionHarmonizing(getRoot()->paths[path], evaluated);
            state_path_expression_harmonizing[state].push_back(z3::mk_or(evaluated));
        }
    }
    std::vector<z3::expr_vector> action_path_expression_harmonizing;
    for(uint64_t action = 0; action < num_actions; ++action) {
        action_path_expression_harmonizing.push_back(z3::expr_vector(ctx));
        for(uint64_t path = 0; path < numPaths(); ++path) {
            z3::expr evaluated = getRoot()->substituteActionExpressionHarmonizing(getRoot()->paths[path], action, harmonizing_variable);
            action_path_expression_harmonizing[action].push_back(evaluated);
        }
    }
    for(uint64_t state = 0; state < numStates(); ++state) {
        for(uint64_t choice = row_groups[state]; choice < row_groups[state+1]; ++choice) {
            choice_path_expresssion_harm.push_back(z3::expr_vector(ctx));
            uint64_t action = choice_to_action[choice];
            for(uint64_t path = 0; path < numPaths(); ++path) {
                choice_path_expresssion_harm[choice].push_back(state_path_expression_harmonizing[state][path] or action_path_expression_harmonizing[action][path]);
            }
        }
    }
    timers["ColoringSmt:: create harmonizing variants"].stop();

    timers[__FUNCTION__].stop();
}

template<typename ValueType>
const uint64_t ColoringSmt<ValueType>::numStates() const {
    return row_groups.size()-1;
}

template<typename ValueType>
const uint64_t ColoringSmt<ValueType>::numChoices() const {
    return row_groups.back();
}

template<typename ValueType>
const uint64_t ColoringSmt<ValueType>::numVariables() const {
    return variable_name.size();
}

template<typename ValueType>
uint64_t ColoringSmt<ValueType>::numNodes() const {
    return tree.size();
}

template<typename ValueType>
std::shared_ptr<TreeNode> ColoringSmt<ValueType>::getRoot() {
    return tree[0];
}

template<typename ValueType>
uint64_t ColoringSmt<ValueType>::numPaths() {
    return getRoot()->paths.size();
}

template<typename ValueType>
bool ColoringSmt<ValueType>::check() {
    timers["solver.check()"].start();
    bool sat = solver.check() == z3::sat;
    timers["solver.check()"].stop();
    return sat;
}

template<typename ValueType>std::vector<std::tuple<uint64_t,std::string,std::string>> ColoringSmt<ValueType>::getFamilyInfo() {
    std::vector<std::tuple<uint64_t,std::string,std::string>> hole_info(family.numHoles());
    getRoot()->loadHoleInfo(hole_info);
    return hole_info;
}

template<typename ValueType>
BitVector ColoringSmt<ValueType>::selectCompatibleChoices(Family const& subfamily) {
    return selectCompatibleChoices(subfamily,BitVector(numChoices(),true));
}

template<typename ValueType>
BitVector ColoringSmt<ValueType>::selectCompatibleChoices(Family const& subfamily, BitVector const& base_choices) {
    timers[__FUNCTION__].start();

    if(CHECK_FAMILY_CONSISTENCE) {
        // check if the subfamily itself satisfies hole restrictions
        timers["selectCompatibleChoices::1 is family sat"].start();
        solver.push();
        getRoot()->addFamilyEncoding(subfamily,solver);
        bool subfamily_sat = check();
        solver.pop();
        timers["selectCompatibleChoices::1 is family sat"].stop();
        STORM_LOG_THROW(
            subfamily_sat, storm::exceptions::UnexpectedException,
            "family is UNSAT (?)"
        );
    }
    
    // for every action, compute for every path whether it admits this acitons
    /*std::vector<BitVector> action_path_enabled;
    for(uint64_t action = 0; action < num_actions; ++action) {
        action_path_enabled.push_back(BitVector(numPaths(),false));
        for(uint64_t path = 0; path < numPaths(); ++path) {
            action_path_enabled[action].set(path,subfamily.holeContains(path_action_hole[path],action));
        }
    }*/

    // check individual choices
    timers["selectCompatibleChoices::2 state exploration"].start();
    BitVector selection(numChoices(),false);
    // std::vector<std::vector<uint64_t>> state_enabled_choices(numStates());
    std::queue<uint64_t> unexplored_states;
    unexplored_states.push(initial_state);
    BitVector state_reached(numStates(),false);
    state_reached.set(initial_state,true);

    while(not unexplored_states.empty()) {
        uint64_t state = unexplored_states.front(); unexplored_states.pop();
        /*std::cout << "state: ";
        for(uint64_t variable = 0; variable < numVariables(); ++variable) {
            std::cout << variable_name[variable] << " = " << variable_domain[variable][state_valuation[state][variable]] << ", ";
        }
        std::cout << std::endl;*/
        state_path_enabled[state].clear();
        for(uint64_t path = 0; path < numPaths(); ++path) {
            bool path_enabled = getRoot()->isPathEnabledInState(getRoot()->paths[path],subfamily,state_valuation[state]);
            state_path_enabled[state].set(path,path_enabled);
        }

        bool any_choice_enabled = false;
        for(uint64_t choice = row_groups[state]; choice < row_groups[state+1]; ++choice) {
            if(not base_choices[choice]) {
                continue;
            }
            bool choice_enabled = false;
            for(uint64_t path: state_path_enabled[state]) {
                if(subfamily.holeContains(path_action_hole[path],choice_to_action[choice])) {
                    selection.set(choice,true);
                    any_choice_enabled = true;
                    // state_enabled_choices[state].push_back(choice);
                    for(uint64_t dst: choice_destinations[choice]) {
                        if(not state_reached[dst]) {
                            unexplored_states.push(dst);
                            state_reached.set(dst,true);
                        }
                    }
                    break;
                }
            }
        }
        // if(state_enabled_choices[state].empty()) {
        if(not any_choice_enabled) {
            if(subfamily.isAssignment()) {
                // STORM_LOG_WARN("Hole assignment does not induce a DTMC, enabling first action...");
                // uint64_t choice = row_groups[state]; // pick the first choice
                uint64_t choice = row_groups[state+1]-1; // pick the last choice executing the random choice
                selection.set(choice,true);
                for(uint64_t dst: choice_destinations[choice]) {
                    if(not state_reached[dst]) {
                        unexplored_states.push(dst);
                        state_reached.set(dst,true);
                    }
                }
            } else {
                selection.clear();
                timers["selectCompatibleChoices::2 state exploration"].stop();
                timers[__FUNCTION__].stop();
                return selection;
            }
        }
    }
    timers["selectCompatibleChoices::2 state exploration"].stop();

    if(CHECK_CONSISTENT_SCHEDULER_EXISTENCE) {
        // check selected choices simultaneously
        solver.push();
        getRoot()->addFamilyEncoding(subfamily,solver);
        for(uint64_t state: state_reached) {
            z3::expr_vector enabled_choices(ctx);
            /*for(uint64_t choice: state_enabled_choices[state]) {
                // enabled_choices.push_back(z3::mk_and(choice_path_expresssion[choice]));
                enabled_choices.push_back(choice_path_expresssion_expr[choice]);
            }
            solver.add(z3::mk_or(enabled_choices));*/
        }
        bool consistent_scheduler_exists = check();
        if(not consistent_scheduler_exists) {
            STORM_LOG_WARN_COND(not subfamily.isAssignment(), "Hole assignment does not induce a DTMC.");
            selection.clear();
        }
        solver.pop(); 
    }

    timers[__FUNCTION__].stop();
    return selection;
}

template<typename ValueType>
void ColoringSmt<ValueType>::loadUnsatCore(z3::expr_vector const& unsat_core_expr, Family const& subfamily) {
    timers[__FUNCTION__].start();
    this->unsat_core.clear();
    for(z3::expr expr: unsat_core_expr) {
        std::istringstream iss(expr.decl().name().str());
        char prefix; iss >> prefix;
        if(prefix == 'h' or prefix == 'z') {
            // uint64_t hole; iss >> prefix; iss >> hole;
            continue;
        }
        // prefix == 'p'
        uint64_t choice,path; iss >> choice; iss >> prefix; iss >> path;
        this->unsat_core.emplace_back(choice,path);
        if(PRINT_UNSAT_CORE) {
            bool action_enabled = subfamily.holeContains(path_action_hole[path],choice_to_action[choice]);
            std::cout << "choice = " << choice << ", path = " << path << ", enabled = " << action_enabled << std::endl;
            std::cout << choice_path_expresssion[choice][path] << std::endl;
        }
    }
    timers[__FUNCTION__].stop();
    return;

    for(uint64_t index = 0; index < this->unsat_core.size()-1; ++index) {
        auto [choice,path] = this->unsat_core[index];
        solver.push();
        solver.add(choice_path_expresssion[choice][path]);
    }
    while(true) {
        if(check()) {
            // pop remaining expressions
            for(uint64_t index = 0; index < this->unsat_core.size()-1; ++index) {
                solver.pop();
            }
            break;
        }
        this->unsat_core.pop_back();
        solver.pop();
    }
    timers[__FUNCTION__].stop();
}

template<typename ValueType>
std::pair<bool,std::vector<std::vector<uint64_t>>> ColoringSmt<ValueType>::areChoicesConsistent(BitVector const& choices, Family const& subfamily) {
    timers[__FUNCTION__].start();
    std::vector<std::vector<uint64_t>> hole_options_vector(family.numHoles());

    timers["areChoicesConsistent::1 is scheduler consistent?"].start();
    solver.push();
    getRoot()->addFamilyEncoding(subfamily,solver);
    solver.push();
    for(uint64_t choice: choices) {
        uint64_t state = choice_to_state[choice];
        for(uint64_t path: state_path_enabled[state]) {
            const char *label = choice_path_label[choice][path].c_str();
            solver.add(choice_path_expresssion[choice][path], label);
        }
    }
    bool consistent = check();
    timers["areChoicesConsistent::1 is scheduler consistent?"].stop();

    if(consistent) {
        z3::model model = solver.get_model();
        solver.pop();
        solver.pop();
        getRoot()->loadHoleAssignmentFromModel(model,hole_options_vector);
        timers[__FUNCTION__].stop();
        return std::make_pair(true,hole_options_vector);
    }

    if(disable_counterexamples) {
        solver.pop();
        solver.pop();
        timers[__FUNCTION__].stop();
        return std::make_pair(false,hole_options_vector);
    }

    solver.pop();

    timers["areChoicesConsistent::2 better unsat core"].start();
    solver.push();
    std::queue<uint64_t> unexplored_states;
    unexplored_states.push(initial_state);
    BitVector state_reached(numStates(),false);
    state_reached.set(initial_state,true);
    consistent = true;
    while(consistent) {
        STORM_LOG_THROW(not unexplored_states.empty(), storm::exceptions::UnexpectedException, "all states explored but UNSAT core not found");
        uint64_t state = unexplored_states.front(); unexplored_states.pop();
        for(uint64_t choice = row_groups[state]; choice < row_groups[state+1]; ++choice) {
            if(not choices[choice]) {
                continue;
            }
            for(uint64_t path: state_path_enabled[state]) {
                const char *label = choice_path_label[choice][path].c_str();
                solver.add(choice_path_expresssion[choice][path], label);
            }
            consistent = check();
            if(not consistent) {
                break;
            }
            for(uint64_t dst: choice_destinations[choice]) {
                if(not state_reached[dst]) {
                    unexplored_states.push(dst);
                    state_reached.set(dst,true);
                }
            }
            break;
        }
    }
    z3::expr_vector unsat_core_expr = solver.unsat_core();
    solver.pop();
    loadUnsatCore(unsat_core_expr,subfamily);
    timers["areChoicesConsistent::2 better unsat core"].stop();

    if(PRINT_UNSAT_CORE)
        std::cout << "-- unsat core start --" << std::endl;
    timers["areChoicesConsistent::3 unsat core analysis"].start();
    for(auto [choice,path]: this->unsat_core) {
        const char *label = choice_path_label[choice][path].c_str();
        solver.add(choice_path_expresssion_harm[choice][path], label);
    }

    z3::model model(ctx);

    /*z3::expr_vector harmonizing_variable_domain(ctx);
    for(uint64_t hole: harmonizing_hole_hint) {
        harmonizing_variable_domain.push_back(harmonizing_variable == (int)hole);
    }
    solver.add(z3::mk_or(harmonizing_variable_domain), "harmonizing_domain");*/

    /*bool harmonizing_hole_found = false;
    for(uint64_t hole = 0; hole < family.numHoles(); ++hole) {
        solver.push();
        solver.add(harmonizing_variable == (int)hole, "harmonizing_domain");
        if(check()) {
            harmonizing_hole_found = true;
            model = solver.get_model();
            solver.pop();
            break;
        }
        solver.pop();
    }
    STORM_LOG_THROW(harmonizing_hole_found, storm::exceptions::UnexpectedException, "harmonized UNSAT core is not SAT");*/

    solver.add(0 <= harmonizing_variable and harmonizing_variable < family.numHoles(), "harmonizing_domain");
    consistent = check();
    STORM_LOG_THROW(consistent, storm::exceptions::UnexpectedException, "harmonized UNSAT core is not SAT");
    model = solver.get_model();

    solver.pop();
    uint64_t harmonizing_hole = model.eval(harmonizing_variable).get_numeral_uint64();

    getRoot()->loadHoleAssignmentFromModel(model,hole_options_vector);
    getRoot()->loadHoleAssignmentFromModelHarmonizing(model,hole_options_vector,harmonizing_hole);
    if(hole_options_vector[harmonizing_hole][0] > hole_options_vector[harmonizing_hole][1]) {
        uint64_t tmp = hole_options_vector[harmonizing_hole][0];
        hole_options_vector[harmonizing_hole][0] = hole_options_vector[harmonizing_hole][1];
        hole_options_vector[harmonizing_hole][1] = tmp;
    }
    if(PRINT_UNSAT_CORE)
        std::cout << "-- unsat core end --" << std::endl;
    timers["areChoicesConsistent::3 unsat core analysis"].stop();

    timers[__FUNCTION__].stop();
    return std::make_pair(false,hole_options_vector);
}


template class ColoringSmt<>;

}