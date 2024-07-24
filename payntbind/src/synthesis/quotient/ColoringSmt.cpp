#include "ColoringSmt.h"

#include <storm/exceptions/InvalidArgumentException.h>

#include <sstream>

namespace synthesis {


ColoringSmt::ColoringSmt(
    std::vector<uint64_t> const& row_groups,
    std::vector<uint64_t> const& choice_to_action,
    storm::storage::sparse::StateValuations const& state_valuations,
    std::vector<std::string> const& hole_to_variable_name,
    std::vector<std::pair<std::vector<uint64_t>,std::vector<uint64_t>>> hole_bounds,
    synthesis::Family const& family,
    std::vector<std::vector<int64_t>> hole_domain
) : choice_to_action(choice_to_action), row_groups(row_groups), family(family), hole_domain(hole_domain), solver(context) {
    
    num_actions = 1 + *max_element(choice_to_action.begin(),choice_to_action.end());
    std::vector<storm::expressions::Variable> variables;
    auto const& valuation = state_valuations.at(0);
    for(auto x = valuation.begin(); x != valuation.end(); ++x) {
        variables.push_back(x.getVariable());
    }
    std::vector<uint64_t> hole_variable(family.numHoles(),variables.size());
    
    hole_corresponds_to_program_variable = storm::storage::BitVector(family.numHoles());

    
    // create solver variables for each hole
    for(uint64_t hole = 0; hole < family.numHoles(); ++hole) {
        std::string const& var_name = hole_to_variable_name[hole];
        bool corresponds_to_program_variable = (var_name != "");
        hole_corresponds_to_program_variable.set(hole,corresponds_to_program_variable);
        std::string name;
        if(corresponds_to_program_variable) {
            name = var_name + "_" + std::to_string(hole);
            uint64_t var_index;
            for(var_index = 0; var_index < variables.size(); ++var_index) {
                if(variables[var_index].getName() == var_name) {
                    hole_variable[hole] = var_index;
                    break;
                }
            }
            STORM_LOG_THROW(var_index < variables.size(), storm::exceptions::InvalidArgumentException, "unexpected variable name");
        } else {
            name = "A_" + std::to_string(hole);
        }
        z3::expr v = context.int_const(name.c_str());
        hole_to_solver_variable.push_back(v);
    }

    // create formula describing hole relationships
    for(uint64_t hole = 0; hole < family.numHoles(); ++hole) {
        uint64_t var = hole_variable[hole];
        z3::expr_vector restriction_clauses(context);
        if(hole_corresponds_to_program_variable[hole]) {
            // see if any of its bounds is a hole associated with the same variable
            auto solver_variable = hole_to_solver_variable[hole];
            auto const& [lower_bounds,upper_bounds] = hole_bounds[hole];
            for(auto bound: lower_bounds) {
                if(hole_variable[bound] == var) {
                    restriction_clauses.push_back(hole_to_solver_variable[bound] < solver_variable);
                }
            }
            for(auto bound: upper_bounds) {
                if(hole_variable[bound] == var) {
                    restriction_clauses.push_back(solver_variable <= hole_to_solver_variable[bound]);
                }
            }
        }
        hole_restriction.push_back(z3::mk_and(restriction_clauses));
    }

    // create choice colors    
    for(uint64_t state = 0; state < numStates(); ++state) {
        for(uint64_t choice = row_groups[state]; choice < row_groups[state+1]; ++choice) {
            uint64_t action = choice_to_action[choice];
            
            std::vector<z3::expr_vector> terminals;
            std::vector<std::vector<std::pair<uint64_t,int>>> terminal_evaluation;
            z3::expr_vector clauses(context);
            std::vector<std::string> clause_label;
            // for each action hole, create clauses that describe this choice selection
            for(uint64_t hole: ~hole_corresponds_to_program_variable) {
                auto const& [lower_bounds,upper_bounds] = hole_bounds[hole];
                z3::expr_vector terminal_atoms(context);
                std::vector<std::pair<uint64_t,int>> evaluation;
                terminal_atoms.push_back((hole_to_solver_variable[hole] == (int)action));
                evaluation.emplace_back(hole,(int)action);

                // add atoms describing lower and upper bounds
                // negate each atom due to boolean conversion
                // translate variable values to hole options
                for(auto bound: lower_bounds) {
                    auto program_variable = variables[hole_variable[bound]];
                    auto solver_variable = hole_to_solver_variable[bound];
                    int value = getVariableValueAtState(state_valuations,state,program_variable);
                    terminal_atoms.push_back(value <= solver_variable);
                    evaluation.emplace_back(bound,value);
                }
                for(auto bound: upper_bounds) {
                    auto program_variable = variables[hole_variable[bound]];
                    auto solver_variable = hole_to_solver_variable[bound];
                    int value = getVariableValueAtState(state_valuations,state,program_variable);
                    terminal_atoms.push_back(value > solver_variable);
                    evaluation.emplace_back(bound,value);
                }
                uint64_t clause_index = clauses.size();
                std::string label = "c" + std::to_string(choice) + "_" + std::to_string(clause_index);

                terminals.push_back(terminal_atoms);
                terminal_evaluation.push_back(evaluation);
                clauses.push_back(z3::mk_or(terminal_atoms));
                clause_label.push_back(label);
            }
            choice_terminal.push_back(terminals);
            choice_clause.push_back(clauses);
            choice_terminal_evaluation.push_back(terminal_evaluation);
            choice_clause_label.push_back(clause_label);
        }
    }
}


const uint64_t ColoringSmt::numStates() const {
    return row_groups.size()-1;
}

const uint64_t ColoringSmt::numChoices() const {
    return choice_to_action.size();
}

int ColoringSmt::getVariableValueAtState(
        storm::storage::sparse::StateValuations const& state_valuations, uint64_t state, storm::expressions::Variable variable
) const {
    if(variable.hasBooleanType()) {
        return (int)state_valuations.getBooleanValue(state,variable);
    } else {
        return state_valuations.getIntegerValue(state,variable);
    }
    
}

void ColoringSmt::addHoleEncoding(Family const& family, uint64_t hole) {
    auto solver_variable = hole_to_solver_variable[hole];
    auto const& family_options = family.holeOptions(hole);
    std::string label = "h" + std::to_string(hole);
    const char* label_str = label.c_str();
    if(hole_corresponds_to_program_variable[hole]) {
        // variable hole
        auto const& domain = hole_domain[hole];
        // convention: hole options in the family are ordered
        int domain_min = domain[family_options.front()];
        int domain_max = domain[family_options.back()];
        // z3::expr encoding = (domain_min <= solver_variable) and (solver_variable <= domain_max) and hole_restriction[hole];
        z3::expr encoding = (domain_min <= solver_variable) and (solver_variable <= domain_max);
        solver.add(encoding, label_str);
    } else {
        // action hole
        z3::expr_vector action_selection_clauses(context);
        for(auto option: family_options) {
            action_selection_clauses.push_back(solver_variable == (int)option);
        }
        z3::expr encoding =  z3::mk_or(action_selection_clauses);
        solver.add(encoding, label_str);    
    }
}

void ColoringSmt::addFamilyEncoding(Family const& family) {
    for(uint64_t hole = 0; hole < family.numHoles(); ++hole) {
        addHoleEncoding(family,hole);
    }
}

void ColoringSmt::addChoiceEncoding(uint64_t choice, bool add_label) {
    if(not add_label) {
        solver.add(choice_clause[choice]);
        return;
    }
    auto const& clauses = choice_clause[choice];
    for(uint64_t index = 0; index < clauses.size(); ++index) {
        solver.add(clauses[index], choice_clause_label[choice][index].c_str());
    }
}

BitVector ColoringSmt::selectCompatibleChoices(Family const& subfamily) {
    return selectCompatibleChoices(subfamily,BitVector(numChoices(),true));
}

BitVector ColoringSmt::selectCompatibleChoices(Family const& subfamily, BitVector const& base_choices) {
    BitVector selection(numChoices(),false);
    
    // check if sub-family itself satisfies hole restrictions
    solver.push();
    addFamilyEncoding(subfamily);
    if(solver.check() == z3::unsat) {
        solver.pop();
        return selection;
    }
    
    // check individual choices
    std::vector<std::vector<uint64_t>> state_enabled_choices(numStates());
    for(uint64_t state = 0; state < numStates(); ++state) {
        bool all_choices_disabled = true;
        for(uint64_t choice = row_groups[state]; choice < row_groups[state+1]; ++choice) {
            if(not base_choices[choice]) {
                continue;
            }
            solver.push();
            selectCompatibleChoicesTimer.start();
            addChoiceEncoding(choice,false);
            z3::check_result result = solver.check();
            selectCompatibleChoicesTimer.stop();
            if(result == z3::sat) {
                all_choices_disabled = false;
                selection.set(choice,true);
                state_enabled_choices[state].push_back(choice);
            }
            solver.pop();
        }
        if(all_choices_disabled) {
            solver.pop();
            selection.clear();
            return selection;
        }
    }

    // check selected choices simultaneously
    solver.push();
    for(std::vector<uint64_t> const& choices: state_enabled_choices) {
        z3::expr_vector enabled_choices(context);
        for(uint64_t choice: choices) {
            enabled_choices.push_back(z3::mk_and(choice_clause[choice]));
        }
        solver.add(z3::mk_or(enabled_choices));
    }
    if(solver.check() == z3::unsat) {
        selection.clear();
    }
    solver.pop();
    
    solver.pop();
    return selection;
}


std::pair<bool,std::vector<std::vector<uint64_t>>> ColoringSmt::areChoicesConsistent(BitVector const& choices, Family const& subfamily) {

    solver.push();
    addFamilyEncoding(subfamily);
    for(auto choice: choices) {
        addChoiceEncoding(choice);
    }
    z3::check_result result = solver.check();
    
    std::vector<std::set<uint64_t>> hole_options(family.numHoles());
    std::vector<std::vector<uint64_t>> hole_options_vector(family.numHoles());
    if(result == z3::sat) {
        z3::model model = solver.get_model();
        solver.pop();
        for(uint64_t hole = 0; hole < family.numHoles(); ++hole) {
            z3::expr solver_variable = hole_to_solver_variable[hole];
            uint64_t value = model.eval(solver_variable).get_numeral_int64();
            hole_options_vector[hole].push_back(value);
        }
        return std::make_pair(true,hole_options_vector);
    }
    
    z3::expr_vector unsat_core = solver.unsat_core();
    solver.pop();
    for(auto expr: unsat_core) {
        std::istringstream iss(expr.decl().name().str());
        char prefix; iss >> prefix;
        if(prefix == 'h') {
            continue;
        }

        // choice clause
        uint64_t choice,clause; iss >> choice; iss >> prefix; iss >> clause;
        uint64_t action = choice_to_action[choice];
        uint64_t action_hole;
        // filter clauses that are unsat within the subfamily
        // std::cout << "checking: " << choice_clause[choice][clause] << std::endl;
        solver.push();
        addFamilyEncoding(subfamily);
        for(uint64_t terminal = 0; terminal < choice_terminal[choice][clause].size(); ++terminal) {
            solver.push();
            solver.add(choice_terminal[choice][clause][terminal]);
            auto result = solver.check();
            solver.pop();
            if(result == z3::unsat) {
                continue;
            } 
            // std::cout << choice_terminal[choice][clause][terminal] << std::endl;
            auto const& [hole,value] = choice_terminal_evaluation[choice][clause][terminal];
            hole_options[hole].insert(value);
        }
        solver.pop();
    }

    for(uint64_t hole = 0; hole < family.numHoles(); ++hole) {
        hole_options_vector[hole].assign(hole_options[hole].begin(),hole_options[hole].end());
    }
    return std::make_pair(false,hole_options_vector);
}




}