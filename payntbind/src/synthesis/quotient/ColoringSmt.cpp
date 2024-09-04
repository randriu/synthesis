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
    std::vector<std::tuple<uint64_t,uint64_t,uint64_t>> const& tree_list
) : initial_state(*model.getInitialStates().begin()),
    row_groups(model.getNondeterministicChoiceIndices()),
    choice_destinations(synthesis::computeChoiceDestinations(model)),
    choice_to_action(synthesis::extractActionLabels(model).second),
    variable_name(variable_name), variable_domain(variable_domain),
    solver(ctx), harmonizing_variable(ctx) {

    timers[__FUNCTION__].start();
    // std::cout << __FUNCTION__ << " start" << std::endl;

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

    // create the tree
    uint64_t num_nodes = tree_list.size();
    uint64_t num_actions = *std::max_element(choice_to_action.begin(),choice_to_action.end())-1;
    for(uint64_t node = 0; node < num_nodes; ++node) {
        auto [parent,child_true,child_false] = tree_list[node];
        STORM_LOG_THROW(
            (child_true != num_nodes) == (child_false != num_nodes), storm::exceptions::UnexpectedException,
            "Inner node has only one child."
        );
        if(child_true != num_nodes) {
            tree.push_back(std::make_shared<InnerNode>(node,ctx,this->variable_name,this->variable_domain));
        } else {
            tree.push_back(std::make_shared<TerminalNode>(node,ctx,this->variable_name,this->variable_domain,num_actions));
        }
    }
    getRoot()->createTree(tree_list,tree);

    // create substitution variables
    z3::expr_vector substitution_variables(ctx);
    for(auto const& name: variable_name) {
        substitution_variables.push_back(ctx.int_const(name.c_str()));
    }
    substitution_variables.push_back(ctx.int_const("act"));
    getRoot()->createHoles(family);
    getRoot()->createPaths(substitution_variables);
    harmonizing_variable = ctx.int_const("__harm__");
    getRoot()->createPathsHarmonizing(substitution_variables, harmonizing_variable);
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
            STORM_LOG_THROW(domain_option_found, storm::exceptions::UnexpectedException, "Hole option not found.");
        }
    }

    // create choice substitutions
    std::vector<z3::expr_vector> choice_substitution_expr;
    for(uint64_t state = 0; state < numStates(); ++state) {
        for(uint64_t choice = row_groups[state]; choice < row_groups[state+1]; ++choice) {
            z3::expr_vector substitution_expr(ctx);
            for(uint64_t value: state_valuation[state]) {
                substitution_expr.push_back(ctx.int_val(value));
            }
            substitution_expr.push_back(ctx.int_val(choice_to_action[choice]));
            choice_substitution_expr.push_back(substitution_expr);
        }
    }

    // collect all path expressions
    std::vector<z3::expr_vector> path_expressions;
    for(std::vector<bool> const& path: getRoot()->paths) {
        z3::expr_vector expression(ctx);
        getRoot()->loadPathExpression(path,expression);
        path_expressions.push_back(expression);

        const TreeNode *node = getRoot()->getNodeOfPath(path,path.size()-1);
        const TerminalNode * terminal = dynamic_cast<const TerminalNode *>(node);
        path_action_hole.push_back(terminal->action_hole.hole);
    }

    // create choice colors
    timers["ColoringSmt:: create choice colors"].start();
    for(uint64_t state = 0; state < numStates(); ++state) {
        for(uint64_t choice = row_groups[state]; choice < row_groups[state+1]; ++choice) {
            std::vector<z3::expr> path_exprs;
            std::vector<z3::expr> path_exprs_harm;
            z3::expr_vector path_and_action(ctx);
            z3::expr_vector path_and_action_harm(ctx);
            std::vector<std::string> path_label;

            for(uint64_t path = 0; path < numPaths(); ++path) {
                std::string label = "p" + std::to_string(choice) + "_" + std::to_string(path);
                path_label.push_back(label);

                z3::expr_vector path_steps_evaluated(ctx);
                for(uint64_t step = 0; step < path_expressions[path].size()-1; ++step) {
                    z3::expr step_expr = path_expressions[path][step];
                    path_steps_evaluated.push_back(step_expr.substitute(substitution_variables,choice_substitution_expr[choice]));
                }
                z3::expr action_evaluated = path_expressions[path].back().substitute(substitution_variables,choice_substitution_expr[choice]);
                z3::expr path_evaluated = not z3::mk_and(path_steps_evaluated); // mind the negation
                path_exprs.push_back(path_evaluated);
                path_and_action.push_back(path_evaluated or action_evaluated);
            }
            choice_path_label.push_back(path_label);

            choice_path.push_back(path_exprs);
            choice_path_and_action.push_back(path_and_action);
        }
    }

    // create harmonizing variants
    std::vector<const TreeNode::Hole *> all_holes(family.numHoles());
    getRoot()->loadAllHoles(all_holes);
    std::vector<std::vector<uint64_t>> path_holes(numPaths());
    for(uint64_t path = 0; path < numPaths(); ++path) {
        getRoot()->loadPathHoles(getRoot()->paths[path],path_holes[path]);
    }
    std::vector<z3::expr_vector> hole_what;
    std::vector<z3::expr_vector> hole_with;
    for(const TreeNode::Hole *hole: all_holes) {
        z3::expr_vector what(ctx); what.push_back(hole->solver_variable); hole_what.push_back(what);
        z3::expr_vector with(ctx); with.push_back(hole->solver_variable_harm); hole_with.push_back(with);
    }

    for(uint64_t choice = 0; choice < numChoices(); ++choice) {
        z3::expr_vector path_variants(ctx);
        for(uint64_t path = 0; path < numPaths(); ++path) {
            std::vector<z3::expr> choice_path_variants;
            z3::expr e = choice_path_and_action[choice][path];
            z3::expr_vector variants(ctx);
            variants.push_back(e);
            for(uint64_t hole: path_holes[path]) {
                variants.push_back(
                    (harmonizing_variable == (int)hole) and e.substitute(hole_what[hole],hole_with[hole])
                );
            }
            path_variants.push_back(z3::mk_or(variants));
            // std::cout << choice_path_and_action[choice][path] << std::endl;
            // std::cout << path_variants.back() << std::endl;
        }
        choice_path_and_action_harm.push_back(path_variants);
    }
    timers["ColoringSmt:: create choice colors"].stop();

    // std::cout << __FUNCTION__ << " end" << std::endl;
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

template<typename ValueType>std::vector<std::pair<std::string,std::string>> ColoringSmt<ValueType>::getFamilyInfo() {
    std::vector<std::pair<std::string,std::string>> hole_info(family.numHoles());
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
                uint64_t choice = row_groups[state];
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
                // enabled_choices.push_back(z3::mk_and(choice_path_and_action[choice]));
                enabled_choices.push_back(choice_path_and_action_expr[choice]);
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
std::pair<bool,std::vector<std::vector<uint64_t>>> ColoringSmt<ValueType>::areChoicesConsistent(BitVector const& choices, Family const& subfamily) {
    timers[__FUNCTION__].start();


    timers["areChoicesConsistent::1 is scheduler consistent?"].start();
    solver.push();
    getRoot()->addFamilyEncoding(subfamily,solver);
    solver.push();
    for(uint64_t choice: choices) {
        uint64_t state = choice_to_state[choice];
        for(uint64_t path: state_path_enabled[state]) {
            const char *label = choice_path_label[choice][path].c_str();

            solver.add(choice_path_and_action[choice][path], label);
            
            /*bool action_enabled = subfamily.holeContains(path_action_hole[path],choice_to_action[choice]);
            if(action_enabled) {
                solver.add(choice_path_and_action[choice][path], label);
            } else {
                solver.add(choice_path[choice][path], label);
            }*/
        }
    }
    bool consistent = check();
    timers["areChoicesConsistent::1 is scheduler consistent?"].stop();

    std::vector<std::set<uint64_t>> hole_options(family.numHoles());
    std::vector<std::vector<uint64_t>> hole_options_vector(family.numHoles());
    if(consistent) {
        z3::model model = solver.get_model();
        solver.pop();
        solver.pop();
        getRoot()->loadHoleAssignmentFromModel(model,hole_options_vector);
        timers[__FUNCTION__].stop();
        return std::make_pair(true,hole_options_vector);
    }

    z3::expr_vector unsat_core = solver.unsat_core();
    solver.pop();

    // std::cout << "-- unsat core start --" << std::endl;
    timers["areChoicesConsistent::2 unsat core analysis"].start();
    for(z3::expr expr: unsat_core) {
        std::istringstream iss(expr.decl().name().str());
        // std::cout << expr << std::endl;
        char prefix; iss >> prefix;
        if(prefix == 'h' or prefix == 'z') {
            continue;
        }

        uint64_t choice,path; iss >> choice; iss >> prefix; iss >> path;
        uint64_t action = choice_to_action[choice];
        bool action_enabled = subfamily.holeContains(path_action_hole[path],choice_to_action[choice]);
        // std::cout << "state = " << choice_to_state[choice] << ", choice = " << choice << ", path = " << path << std::endl;
        /*if(action_enabled) {
            std::cout << "UC: " << choice_path_and_action[choice][path] << std::endl;
        } else {
            std::cout << "UC: " << (choice_path[choice][path]) << std::endl;
        }*/
        getRoot()->unsatCoreAnalysis(
            subfamily, getRoot()->paths[path], state_valuation[choice_to_state[choice]],
            choice_to_action[choice], action_enabled, hole_options
        );
    }
    // std::cout << "-- unsat core end --" <<std::endl;
    solver.pop();
    timers["areChoicesConsistent::2 unsat core analysis"].stop();

    for(uint64_t hole = 0; hole < family.numHoles(); ++hole) {
        hole_options_vector[hole].assign(hole_options[hole].begin(),hole_options[hole].end());
    }
    timers[__FUNCTION__].stop();
    return std::make_pair(false,hole_options_vector);
}


template<typename ValueType>
std::pair<bool,std::vector<std::vector<uint64_t>>> ColoringSmt<ValueType>::areChoicesConsistent2(BitVector const& choices, Family const& subfamily) {
    timers[__FUNCTION__].start();

    timers["areChoicesConsistent::1 is scheduler consistent?"].start();
    solver.push();
    getRoot()->addFamilyEncoding(subfamily,solver);
    solver.push();
    for(uint64_t choice: choices) {
        uint64_t state = choice_to_state[choice];
        for(uint64_t path: state_path_enabled[state]) {
            const char *label = choice_path_label[choice][path].c_str();

            solver.add(choice_path_and_action[choice][path], label);
            
            /*bool action_enabled = subfamily.holeContains(path_action_hole[path],choice_to_action[choice]);
            if(action_enabled) {
                solver.add(choice_path_and_action[choice][path], label);
            } else {
                solver.add(choice_path[choice][path], label);
            }*/
        }
    }
    bool consistent = check();
    timers["areChoicesConsistent::1 is scheduler consistent?"].stop();

    if(consistent) {
        z3::model model = solver.get_model();
        solver.pop();
        solver.pop();
        std::vector<std::vector<uint64_t>> hole_options_vector(family.numHoles());
        getRoot()->loadHoleAssignmentFromModel(model,hole_options_vector);
        timers[__FUNCTION__].stop();
        return std::make_pair(true,hole_options_vector);
    }
    solver.pop();

    timers["areChoicesConsistent::2 better unsat core"].start();
    solver.push();
    std::queue<uint64_t> unexplored_states;
    unexplored_states.push(initial_state);
    BitVector state_reached(numStates(),false);
    state_reached.set(initial_state,true);
    uint64_t states_explored = 0;
    consistent = true;
    while(consistent) {
        STORM_LOG_THROW(not unexplored_states.empty(), storm::exceptions::UnexpectedException, "all states explored but UNSAT core not found");
        uint64_t state = unexplored_states.front(); unexplored_states.pop();
        // std::cout << "exploring state " << state;
        states_explored += 1;
        for(uint64_t choice = row_groups[state]; choice < row_groups[state+1]; ++choice) {
            if(not choices[choice]) {
                continue;
            }
            // std::cout << "adding choice = " << choice << std::endl;
            for(uint64_t path = 0; path < numPaths(); ++path) {
                if(not state_path_enabled[state][path]) {
                    continue;
                }
                const char *label = choice_path_label[choice][path].c_str();
                solver.add(choice_path_and_action[choice][path], label);
            }
            consistent = check();
            if(not consistent) {
                // std::cout << "inconsistent" << std::endl;
                break;
            }
            for(uint64_t dst: choice_destinations[choice]) {
                if(not state_reached[dst]) {
                    unexplored_states.push(dst);
                    state_reached.set(dst,true);
                }
            }
        }
    }
    // std::cout << "states_explored = " << states_explored << std::endl;
    z3::expr_vector unsat_core = solver.unsat_core();
    solver.pop();
    timers["areChoicesConsistent::2 better unsat core"].stop();

    bool PRINT_UNSAT_CORE = false;
    if(PRINT_UNSAT_CORE)
        std::cout << "-- unsat core start --" << std::endl;
    timers["areChoicesConsistent::3 unsat core analysis"].start();
    solver.push();
    for(z3::expr expr: unsat_core) {
        std::istringstream iss(expr.decl().name().str());
        char prefix; iss >> prefix;
        if(prefix == 'h' or prefix == 'z') {
            continue;
        }

        uint64_t choice,path; iss >> choice; iss >> prefix; iss >> path;
        const char *label = choice_path_label[choice][path].c_str();
        solver.add(choice_path_and_action_harm[choice][path], label);
        if(PRINT_UNSAT_CORE) {
            bool action_enabled = subfamily.holeContains(path_action_hole[path],choice_to_action[choice]);
            std::cout << "choice = " << choice << ", path = " << path << ", enabled = " << action_enabled << std::endl;
            std::cout << choice_path_and_action[choice][path] << std::endl;
            // std::cout << choice_path_and_action_harm[choice][path] << std::endl;
        }
        
    }
    // std::cout << "harmonizing holes: ";
    /*uint64_t num_harmonizing_holes = 0;
    std::vector<const TreeNode::Hole *> all_holes(family.numHoles());
    getRoot()->loadAllHoles(all_holes);
    uint64_t min_depth = 10;
    uint64_t max_depth = 0;
    uint64_t harmonizing_hole;
    for(uint64_t hole = 0; hole < family.numHoles(); ++hole) {
        solver.push();
        solver.add(harmonizing_variable == (int)hole, "harmonizing domain");
        bool consistent = check();
        if(consistent) {
            // std::cout << hole << ",";
            num_harmonizing_holes += 1;
            // if(all_holes[hole]->depth < min_depth) {
            //     min_depth = all_holes[hole]->depth;
            //     harmonizing_hole = hole;
            // }
            if(all_holes[hole]->depth >= max_depth) {
                max_depth = all_holes[hole]->depth;
                harmonizing_hole = hole;
            }
        }
        solver.pop();
    }*/
    // std::cout << " (" << num_harmonizing_holes << "/" << family.numHoles() << ")" << std::endl;
    // solver.add(harmonizing_variable == int(harmonizing_hole), "harmonizing_domain");

    solver.add(0 <= harmonizing_variable and harmonizing_variable < family.numHoles(), "harmonizing_domain");
    consistent = check();
    STORM_LOG_THROW(consistent, storm::exceptions::UnexpectedException, "harmonized UNSAT core is not SAT");
    z3::model model = solver.get_model();

    uint64_t harmonizing_hole = model.eval(harmonizing_variable).get_numeral_uint64();
    std::vector<std::set<uint64_t>> hole_options(family.numHoles());
    getRoot()->loadHarmonizingHoleAssignmentFromModel(model,hole_options,harmonizing_hole);
    if(PRINT_UNSAT_CORE)
        std::cout << "-- unsat core end --" << std::endl;
    
    solver.pop();
    solver.pop();
    timers["areChoicesConsistent::3 unsat core analysis"].stop();

    std::vector<std::vector<uint64_t>> hole_options_vector(family.numHoles());
    for(uint64_t hole = 0; hole < family.numHoles(); ++hole) {
        hole_options_vector[hole].assign(hole_options[hole].begin(),hole_options[hole].end());
    }
    timers[__FUNCTION__].stop();
    return std::make_pair(false,hole_options_vector);
}

template class ColoringSmt<>;

}