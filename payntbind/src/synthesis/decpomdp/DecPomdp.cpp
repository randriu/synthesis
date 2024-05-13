// Contributions of MASTER'S THESIS 
// INDUCTIVE SYNTHESIS OF FINITE STATE CONTROLLERS FOR DECENTRALIZED POMDPS
// by Vojtech Hranicka

// This file contains construction of Quotient MDP
// added functions: setObservationMemorySize, setGlobalMemorySize, constructQuotientStateLabeling, constructQuotientChoiceLabeling, constructQuotientTransitionMatrix,
// constructQuotientRewardModel, resetDesignSpace, construct_memory_joint_observation, construct_acton_to_memory_joint_observation, construct_state_to_memory_joint_observation, buildDesignSpaceSpurious
// Some unction in this file are inspirated by functions in PomdpManager.cpp
#include "DecPomdp.h"

#include "madp/src/base/Globals.h"
#include "madp/src/base/E.h"
#include "madp/src/parser/MADPParser.h"

#include <stack>

namespace synthesis {
    
    
    void DecPomdp::collectActions(DecPOMDPDiscrete *model) {
        
        // individual actions
        this->agent_action_labels.resize(this->num_agents);
        for(uint_fast64_t agent = 0; agent < this->num_agents; agent++) {
            uint_fast64_t num_actions = model->GetNrActions(agent);
            this->agent_action_labels[agent].resize(num_actions);
            std::vector<std::string> action_labels(num_actions);
            for(uint_fast64_t action = 0; action < num_actions; action++) {
                this->agent_action_labels[agent][action] = model->GetAction(agent,action)->GetName();
            }
        }

        // joint actions
        this->joint_actions.resize(model->GetNrJointActions());
        for(uint_fast64_t joint_action_index = 0; joint_action_index < model->GetNrJointActions(); joint_action_index++) {
            for(auto action: model->JointToIndividualActionIndices(joint_action_index)) {
                this->joint_actions[joint_action_index].push_back(action);
            }
        }
    }

    void DecPomdp::collectObservations(DecPOMDPDiscrete *model) {
        
        // individual observations
        this->agent_observation_labels.resize(this->num_agents);
        for(uint_fast64_t agent = 0; agent < this->num_agents; agent++) {
            for(uint_fast64_t obs = 0; obs < model->GetNrObservations(agent); obs++) {
                this->agent_observation_labels[agent].push_back(model->GetObservation(agent,obs)->GetName());
            }
        }

        // joint observations
        uint_fast64_t num_joint_observations = model->GetNrJointObservations();
        this->joint_observations.resize(num_joint_observations);
        for(uint_fast64_t joint_observation_index = 0; joint_observation_index < num_joint_observations; joint_observation_index++) {
            for(auto observation: model->JointToIndividualObservationIndices(joint_observation_index)) {
                this->joint_observations[joint_observation_index].push_back(observation);
            }
        }
    }

    
    bool DecPomdp::haveMadpState(MadpState madp_state) {
        return this->madp_to_storm_states.find(madp_state) != this->madp_to_storm_states.end();
    }
    
    uint_fast64_t DecPomdp::mapMadpState(MadpState madp_state) {
        uint_fast64_t new_state = this->num_states();
        auto const result = this->madp_to_storm_states.insert(std::make_pair(madp_state, new_state));
        if (result.second) {
            // new state
            this->storm_to_madp_states.push_back(madp_state);
            this->transition_matrix.resize(this->num_states());
            this->row_joint_action.resize(this->num_states());
            this->row_reward.resize(this->num_states());

            this->state_joint_observation.resize(this->num_states());
            this->state_joint_observation[new_state] = madp_state.second;
        }
        return result.first->second;
    }

    
    uint_fast64_t DecPomdp::freshJointAction(std::string action_label) {
        std::vector<uint_fast64_t> action_tuple(this->num_agents);
        for(uint_fast64_t agent = 0; agent < this->num_agents; agent++) {
            action_tuple[agent] = this->agent_num_actions(agent);
            this->agent_action_labels[agent].push_back(action_label);
        }
        uint_fast64_t joint_action = this->num_joint_actions();
        this->joint_actions.push_back(std::move(action_tuple));
        return joint_action;
    }
    
    uint_fast64_t DecPomdp::freshJointObservation(std::string observation_label) {
        std::vector<uint_fast64_t> observation_tuple(this->num_agents);
        for(uint_fast64_t agent = 0; agent < this->num_agents; agent++) {
            observation_tuple[agent] = this->agent_num_observations(agent);
            this->agent_observation_labels[agent].push_back(observation_label);
        }
        uint_fast64_t joint_observation = this->num_joint_observations();
        this->joint_observations.push_back(std::move(observation_tuple));
        return joint_observation;
    }

    uint_fast64_t DecPomdp::freshSink(std::string label) {
        
        uint_fast64_t joint_observation = this->freshJointObservation(label);
        MadpState madp_new_state = std::make_pair(0,joint_observation);
        uint_fast64_t new_state = this->mapMadpState(madp_new_state);

        uint_fast64_t sink_action = this->freshJointAction(label);
        this->row_joint_action[new_state] = std::vector<uint_fast64_t>(1, sink_action);
        this->row_reward[new_state] = std::vector<double>(1, 0);
        this->transition_matrix[new_state] = std::vector<StormRow>(1, StormRow(1, std::make_pair(new_state,1)));

        return new_state;
    }



    DecPomdp::DecPomdp(DecPOMDPDiscrete *model) {
        // agents
        
        this->num_agents = model->GetNrAgents();
        this->discount_factor = model->GetDiscount();
        this->reward_minimizing = model->GetRewardType() == COST;

        this->collectActions(model);
        this->collectObservations(model);

        // multiply transition and observation probabilities
        std::vector<std::vector<std::vector<std::pair<MadpState,double>>>> madp_transition_matrix;
        for(uint_fast64_t src = 0; src < model->GetNrStates(); src++) {
            std::vector<std::vector<std::pair<MadpState,double>>> row_group;
            
            for(uint_fast64_t joint_action = 0; joint_action < model->GetNrJointActions(); joint_action++) {
                std::vector<std::pair<MadpState,double>> row;
                
                for(uint_fast64_t dst = 0; dst < model->GetNrStates(); dst++) {
                    double transition_prob = model->GetTransitionProbability(src, joint_action, dst);
                    if(transition_prob == 0) {
                        continue;
                    }
                    
                    for(uint_fast64_t obs = 0; obs < model->GetNrJointObservations(); obs++) {
                        double observation_prob = model->GetObservationProbability(joint_action, dst, obs);
                        if(observation_prob == 0) {
                            continue;
                        }
                        row.push_back(std::make_pair(std::make_pair(dst,obs), transition_prob*observation_prob));
                    }
                }
                row_group.push_back(row);
            }
            madp_transition_matrix.push_back(row_group);
        }

        // create initial observation for the (unique) initial state
        uint_fast64_t init_joint_observation = this->freshJointObservation(this->init_label);
        // create action that corresponds to the execution of the initial distribution
        uint_fast64_t init_joint_action = this->freshJointAction(this->init_label);
        // create empty observation for states in the initial distribution
        uint_fast64_t empty_joint_observation = this->freshJointObservation(this->no_obs_label);

        // collect initial distribution
        std::vector<MadpRow> initial_distribution_row_group(1);
        uint_fast64_t state = 0;
        for(auto prob: model->GetISD()->ToVectorOfDoubles()) {
            if(prob > 0) {
                initial_distribution_row_group[0].push_back(std::make_pair(std::make_pair(state,empty_joint_observation),prob));
            }
            state++;
        }
        
        // explore the reachable state space from the initial state
        std::stack<MadpState> reachable_states;
        MadpState madp_initial = std::make_pair(0,init_joint_observation);
        this->initial_state = this->mapMadpState(madp_initial);
        reachable_states.push(madp_initial);
        while(!reachable_states.empty()) {
            MadpState madp_src = reachable_states.top();
            reachable_states.pop();
            uint_fast64_t storm_src = this->mapMadpState(madp_src);
            
            std::vector<std::vector<std::pair<MadpState,double>>> *row_group;
            if(storm_src == this->initial_state) {
                row_group = &initial_distribution_row_group;
            } else {
                row_group = &madp_transition_matrix[madp_src.first];
            }

            std::vector<StormRow> storm_row_group;
            for(auto &row : *row_group) {
                StormRow storm_row;
                for(auto &madp_state_prob: row) {
                    MadpState madp_dst = madp_state_prob.first;
                    if(!this->haveMadpState(madp_dst)) {
                        reachable_states.push(madp_dst);
                    }
                    uint_fast64_t storm_dst = this->mapMadpState(madp_dst);
                    storm_row.push_back(std::make_pair(storm_dst, madp_state_prob.second));
                }
                storm_row_group.push_back(std::move(storm_row));
            }
            this->transition_matrix[storm_src] = std::move(storm_row_group);
        }

        // map rows to joint actions and rewards
        std::vector<uint_fast64_t> madp_row_group;
        for(uint_fast64_t joint_action = 0; joint_action < model->GetNrJointActions(); joint_action++) {
            madp_row_group.push_back(joint_action);
        }
        assert(this->row_joint_action.size() == this->num_states());
        assert(this->row_reward.size() == this->num_states());
        for(uint_fast64_t storm_state = 0; storm_state < this->num_states(); storm_state++) {
            MadpState madp_state = this->storm_to_madp_states[storm_state];
            if(storm_state == this->initial_state) {
                this->row_joint_action[storm_state] = std::vector<uint_fast64_t>(1,init_joint_action);
                this->row_reward[storm_state] = std::vector<double>(1,0);
            } else {
                this->row_joint_action[storm_state] = madp_row_group;
                std::vector<double> rewards;
                for(uint_fast64_t joint_action = 0; joint_action < model->GetNrJointActions(); joint_action++) {
                    rewards.push_back(model->GetReward(madp_state.first, joint_action));
                }
                this->row_reward[storm_state] = std::move(rewards);
            }
        }

        this->observation_memory_size.resize(this->joint_observations.size() + 1, 1); //TODO +1 is for sink state
        this->target_states.resize(this->num_states(), false);
        this->prototype_duplicates.resize(this->num_states() + 1); //TODO +1 is for sink state
    }

    uint_fast64_t DecPomdp::num_rows() {
        uint_fast64_t count = 0;
        for(auto row_group: this->transition_matrix) {
            count += row_group.size();
        }
        return count;
    }



    storm::models::sparse::StateLabeling DecPomdp::constructStateLabeling() {
        storm::models::sparse::StateLabeling labeling(this->num_states());

        storm::storage::BitVector init_flags(this->num_states(), false);
        init_flags.set(this->initial_state);
        labeling.addLabel(this->init_label, std::move(init_flags));

        if(this->discounted) {
            storm::storage::BitVector discount_sink_flags(this->num_states(), false);
            discount_sink_flags.set(this->discount_sink_state);
            labeling.addLabel(this->discount_sink_label, std::move(discount_sink_flags));
        }
        
        return labeling;
    }

    storm::models::sparse::StateLabeling DecPomdp::constructQuotientStateLabeling() {
        storm::models::sparse::StateLabeling labeling(this->num_quotient_states);

        storm::storage::BitVector init_flags(this->num_quotient_states, false);
        init_flags.set(this->prototype_duplicates[this->initial_state][0] );
        labeling.addLabel("init", std::move(init_flags));

        if(this->discounted and this->discount_factor != 1) {
            storm::storage::BitVector discount_sink_flags(this->num_quotient_states, false);
            discount_sink_flags.set(this->prototype_duplicates[this->discount_sink_state][0]);
            labeling.addLabel(this->discount_sink_label, std::move(discount_sink_flags));
        }
        else{
            storm::storage::BitVector target_flags(this->num_quotient_states, false);
            for (uint64_t prototype = 0; prototype < this->num_states() ; prototype++){
                if (not this->target_states[prototype])
                {
                    continue;
                }
                for(auto duplicate: this->prototype_duplicates[prototype]) {
                    target_flags.set(duplicate);
                }
            }
            
            
            labeling.addLabel(this->target_label, std::move(target_flags));
        }
        
        return labeling;
    }

    storm::models::sparse::ChoiceLabeling DecPomdp::constructChoiceLabeling() {
        uint_fast64_t num_rows = this->num_rows();
        
        storm::models::sparse::ChoiceLabeling labeling(num_rows);
        uint_fast64_t current_row = 0;
        std::vector<std::string> row_label(num_rows);
        std::set<std::string> all_labels;
        for(auto row_group: this->row_joint_action) {
            for(auto joint_action_index: row_group) {
                std::ostringstream sb;
                sb << "(";
                auto joint_action = this->joint_actions[joint_action_index];
                for(uint32_t agent = 0; agent < this->num_agents; agent++) {
                    auto agent_action = joint_action[agent];
                    auto agent_action_label = this->agent_action_labels[agent][agent_action];
                    sb << agent_action_label;
                    if(agent < this->num_agents-1) {
                        sb << ",";
                    }
                }
                sb << ")";
                std::string label = sb.str();
                all_labels.insert(label);
                row_label[current_row] = label;
                current_row++;
            }
        }
        for(auto label: all_labels) {
            storm::storage::BitVector flags(num_rows, false);
            labeling.addLabel(label, flags);
        }
        for(uint64_t row = 0; row < num_rows; row++) {
            labeling.addLabelToChoice(row_label[row], row);
        }

        return labeling;
    }

    storm::models::sparse::ChoiceLabeling DecPomdp::constructQuotientChoiceLabeling() {
        uint_fast64_t num_rows = this->num_quotient_rows;

        storm::models::sparse::ChoiceLabeling labeling(num_rows);
        uint_fast64_t current_row = 0;
        std::vector<std::string> row_label(num_rows);
        std::set<std::string> all_labels;
        uint_fast64_t row_counter = 0;
        uint_fast64_t joint_action_index = 0;
        for(uint64_t state = 0; state < this->num_quotient_states; state++) {
            auto prototype_state = this->state_prototype[state];
            auto observ = this->state_joint_observation[prototype_state];
            auto group_joint_actions = this->row_joint_action[prototype_state];
            row_counter = 0;
            for(auto row: this->transition_matrix[prototype_state]) {
                joint_action_index = group_joint_actions[row_counter];
                for(uint64_t mem = 0; mem < max_successor_memory_size[observ]; mem++) {
                    std::ostringstream sb;
                    sb << "(";
                    auto joint_action = this->joint_actions[joint_action_index];
                    for(uint32_t agent = 0; agent < this->num_agents; agent++) {
                        auto agent_action = joint_action[agent];
                        auto agent_action_label = this->agent_action_labels[agent][agent_action];
                        sb << agent_action_label;
                        sb << ",";
                    }
                    sb << mem;
                    sb << ")";
                    std::string label = sb.str();
                    all_labels.insert(label);
                    row_label[current_row] = label;
                    current_row++;
                }
                row_counter++;
            }
        }
        for(auto label: all_labels) {
            storm::storage::BitVector flags(num_rows, false);
            labeling.addLabel(label, flags);
        }
        for(uint64_t row = 0; row < num_rows; row++) {
            labeling.addLabelToChoice(row_label[row], row);
        }
        return labeling ;
    }

    storm::storage::SparseMatrix<double> DecPomdp::constructTransitionMatrix() {
        

        storm::storage::SparseMatrixBuilder<double> builder(
                this->num_rows(), this->num_states(), 0, true, true, this->num_states()
        );
        uint64_t current_row = 0;
        for(uint64_t state = 0; state < this->num_states(); state++) {
            builder.newRowGroup(current_row);
            for(auto row: this->transition_matrix[state]) {
                for(auto entry: row) {
                    builder.addNextValue(current_row, entry.first, entry.second);
                } 
                current_row++;
            }
        }
        return builder.build();
    }

    storm::storage::SparseMatrix<double> DecPomdp::constructQuotientTransitionMatrix() {
        
        storm::storage::SparseMatrixBuilder<double> builder2(
                this->num_quotient_rows, this->num_quotient_states, 0, true, true, this->num_quotient_states
        );
        uint64_t row_index = 0;
        for(uint64_t state = 0; state < this->num_quotient_states; state++) {
            auto prototype_state = this->state_prototype[state];
            auto observation = this->state_joint_observation[prototype_state];
            builder2.newRowGroup(this->row_groups[state]);
            for(auto row: this->transition_matrix[prototype_state]) {
                for(uint64_t dst_mem = 0; dst_mem < max_successor_memory_size[observation]; dst_mem++) {
                    for(auto entry: row) {

                        auto dst = this->prototype_duplicates[entry.first][dst_mem];
                        if (entry.first == this->discount_sink_state)
                        {
                           dst = this->prototype_duplicates[entry.first][0];
                        }
                        builder2.addNextValue(row_index, dst, entry.second);
                        
                    }
                    row_index++;
                }
                
            }
        
        }
        return builder2.build();
    }

    storm::models::sparse::StandardRewardModel<double> DecPomdp::constructRewardModel() {
        std::optional<std::vector<double>> state_rewards;
        std::vector<double> action_rewards;
        for(uint64_t state = 0; state < this->num_states(); state++) {
            for(uint64_t row = 0; row < this->transition_matrix[state].size(); row++) {
                auto reward = this->row_reward[state][row];
                action_rewards.push_back(reward);
            }
        } 
        return storm::models::sparse::StandardRewardModel<double>(std::move(state_rewards), std::move(action_rewards));
    }

    storm::models::sparse::StandardRewardModel<double> DecPomdp::constructQuotientRewardModel() {
        std::optional<std::vector<double>> state_rewards;
        std::vector<double> action_rewards;
        uint64_t row_index = 0;
        for(uint64_t state = 0; state < this->num_quotient_states; state++) {
            auto prototype_state = this->state_prototype[state];
            auto observation = this->state_joint_observation[prototype_state];
            row_index = 0;
            for(auto row: this->transition_matrix[prototype_state]) {
                for(uint64_t dst_mem = 0; dst_mem < max_successor_memory_size[observation]; dst_mem++) {
                auto reward = this->row_reward[prototype_state][row_index];
                action_rewards.push_back(reward);
                
                }
                row_index++;
            }
        } 
        return storm::models::sparse::StandardRewardModel<double>(std::move(state_rewards), std::move(action_rewards));
    }



    std::vector<uint32_t> DecPomdp::constructObservabilityClasses() {
        std::vector<uint32_t> observation_classes(this->num_states());
        for(uint64_t state = 0; state < this->num_states(); state++) {
            observation_classes[state] = this->state_joint_observation[state];
        }
        return observation_classes;
    }


    std::shared_ptr<storm::models::sparse::Mdp<double>> DecPomdp::constructQuotientMdp() { 
        this->buildStateSpace();
        this->countSuccessors();
        this->buildTransitionMatrixSpurious();

        storm::storage::sparse::ModelComponents<double> components;
        components.stateLabeling = this->constructQuotientStateLabeling();
        components.choiceLabeling = this->constructQuotientChoiceLabeling();
        components.transitionMatrix = this->constructQuotientTransitionMatrix();
        components.rewardModels.emplace(this->reward_model_name, this->constructQuotientRewardModel());
        this->resetDesignSpace();
        this->buildDesignSpaceSpurious(); 
        return std::make_shared<storm::models::sparse::Mdp<double>>(std::move(components));
    }

    std::shared_ptr<storm::models::sparse::Mdp<double>> DecPomdp::constructMdp() { 
        storm::storage::sparse::ModelComponents<double> components;
        components.stateLabeling = this->constructStateLabeling();
        components.choiceLabeling = this->constructChoiceLabeling();
        components.transitionMatrix = this->constructTransitionMatrix();
        components.rewardModels.emplace(this->reward_model_name, this->constructRewardModel());
        return std::make_shared<storm::models::sparse::Mdp<double>>(std::move(components));
    }

    std::shared_ptr<storm::models::sparse::Pomdp<double>> DecPomdp::constructPomdp() {
        storm::storage::sparse::ModelComponents<double> components;
        components.stateLabeling = this->constructStateLabeling();
        components.choiceLabeling = this->constructChoiceLabeling();
        components.transitionMatrix = this->constructTransitionMatrix();
        components.rewardModels.emplace(this->reward_model_name, this->constructRewardModel());
        components.observabilityClasses = this->constructObservabilityClasses();
        return std::make_shared<storm::models::sparse::Pomdp<double>>(std::move(components));
    }


    POMDPDiscrete *parse_as_pomdp(std::string filename) {
        try {
            POMDPDiscrete *model = new POMDPDiscrete("","",filename);
            model->SetSparse(true);
            MADPParser parser(model);
            return model;
        } catch(E& e) {
            e.Print();
            return NULL;
        }
    }

    DecPOMDPDiscrete *parse_as_decpomdp(std::string filename) {
        try {
            DecPOMDPDiscrete *model = new DecPOMDPDiscrete("","",filename);
            model->SetSparse(true);
            MADPParser parser(model);
            return model;
        } catch(E& e) {
            e.Print();
            return NULL;
        }
    }

    DecPOMDPDiscrete *parseMadp(std::string filename) {
        
        DecPOMDPDiscrete *model;
        
        STORM_PRINT_AND_LOG("MADP: trying to parse as POMDP...\n");
        model = parse_as_pomdp(filename);
        if(model != NULL) {
            STORM_PRINT_AND_LOG("MADP: parsing success\n");
            return model;
        }

        STORM_PRINT_AND_LOG("MADP: parsing success\n");
        STORM_PRINT_AND_LOG("MADP: trying to parse as dec-POMDP...\n");
        model = parse_as_decpomdp(filename);
        if(model != NULL) {
            STORM_PRINT_AND_LOG("MADP: parsing success\n");
            return model;
        }

        if(model == NULL) {
            STORM_PRINT_AND_LOG("MADP: parsing failure\n");
        }
        return model;
        
    }

    std::unique_ptr<DecPomdp> parseDecPomdp(std::string filename) {
        DecPOMDPDiscrete *madp_decpomdp = parseMadp(filename);
        if(madp_decpomdp == NULL) {
            return NULL;
        }
        // debug: MADP info
        // std::cerr << madp_decpomdp->SoftPrint() << std::endl;
        std::unique_ptr<DecPomdp> decpomdp = std::make_unique<DecPomdp>(madp_decpomdp);
        free(madp_decpomdp);
        return decpomdp;
    }

    
    void DecPomdp::applyDiscountFactorTransformation() {

        if(this->discounted || this->discount_factor == 1) {
            return;
        }
        this->discount_sink_state = this->freshSink(this->discount_sink_label);
        for(uint_fast64_t state = 0; state < this->num_states(); state++) {
            if(state == this->initial_state || state == this->discount_sink_state) {
                // no discounting in the initial state because it selects the actual initial state
                continue;
            }
            for(StormRow &row: this->transition_matrix[state]) {
                for(auto &entry: row) {
                    entry.second *= this->discount_factor;
                }
                row.push_back(std::make_pair(this->discount_sink_state,1-this->discount_factor));
            }
        }
        this->discounted = true;
    }

    void DecPomdp::setObservationMemorySize(uint64_t obs, uint64_t memory_size) {
            this->observation_memory_size[obs] = memory_size;
        }

    void DecPomdp::setGlobalMemorySize(uint64_t memory_size) {
            for(uint64_t obs = 0; obs < this->num_joint_observations(); obs++) {
                this->observation_memory_size[obs] = memory_size;
            }
            if (this->discounted && this->discount_factor != 1 )
            {
                auto obs = this->state_joint_observation[this->discount_sink_state];
                this->observation_memory_size[obs] = 1;
            }
        }

    void DecPomdp::setTargetState(uint64_t state) {
            this->target_states[state] = true;
        }

    void DecPomdp::buildStateSpace() {
        this->num_quotient_states = 0;
        this->state_prototype.clear();
        this->state_memory.clear();
        for(uint64_t prototype = 0; prototype < this->num_states(); prototype++) {
            auto obs = this->state_joint_observation[prototype];
            auto memory_size = this->observation_memory_size[obs];
            this->prototype_duplicates[prototype].clear();
            this->prototype_duplicates[prototype].reserve(memory_size);
            for(uint64_t memory = 0; memory < memory_size; memory++) {
                this->prototype_duplicates[prototype].push_back(this->num_quotient_states);
                this->state_prototype.push_back(prototype);
                this->state_memory.push_back(memory);
                this->num_quotient_states++;
            }
        }
    }


    void DecPomdp::countSuccessors() {

        this->prototype_row_index.resize(num_rows(),0);
        uint64_t row_index = 0;
        uint64_t group_index = 0;

        auto num_observations = this->num_joint_observations();
        this->observation_successors.resize(num_observations); 

        std::vector<std::set<uint64_t>> observation_successor_sets;
        observation_successor_sets.resize(num_observations);

        for(uint64_t state = 0; state < this->num_states(); state++) {
            auto observ = this->state_joint_observation[state];
            for(auto row: this->transition_matrix[state]) {
                for(auto entry: row) {
                    auto dst = entry.first;
                    double transition_prob = entry.second;
                    if(transition_prob == 0) {
                        continue;
                    }
                    observation_successor_sets[observ].insert(dst);
                    

                }
                this->prototype_row_index[row_index] = group_index;
                group_index++;
                row_index++;

            }
            group_index = 0;
        
        }
        
        for(uint64_t obs = 0; obs < num_observations; obs++) {
            this->observation_successors[obs] = std::vector<uint64_t>(
                observation_successor_sets[obs].begin(),
                observation_successor_sets[obs].end()
                );
            
        }
    }



    void DecPomdp::buildTransitionMatrixSpurious() {
            this->max_successor_memory_size.resize(this->num_joint_observations());
            // for each observation, define the maximum successor memory size
            // this will define the number of copies we need to make of each row
            for(uint64_t obs = 0; obs < this->num_joint_observations(); obs++) {
                uint64_t max_mem_size = 1; //TODO there was 0
                for(auto dst_state: this->observation_successors[obs]) {
                    auto dst_obs = this->state_joint_observation[dst_state];
                    if(max_mem_size < this->observation_memory_size[dst_obs]) {
                        max_mem_size = this->observation_memory_size[dst_obs];
                    }
                }
                this->max_successor_memory_size[obs] = max_mem_size;
                // std::cout << "this->observation_memory_size[obs] " << this->observation_memory_size[obs] << std::endl;
            }

            //collect max succesor memory for each agent

            this->agent_max_successor_memory_size.clear();
            this->agent_max_successor_memory_size.resize(this->num_agents);
            for (int agent = 0; agent < this->num_agents; agent++)
            {
                this->agent_max_successor_memory_size[agent].resize(this->agent_observation_labels[agent].size()); 
            }

            for(uint64_t joint_obs = 0; joint_obs < this->num_joint_observations(); joint_obs++) { //TODO can be optimalize
                for (int agent = 0; agent < this->num_agents; agent++){
                    uint64_t obs = this->joint_observations[joint_obs][agent];
                    uint64_t max_mem_size = 1; //TODO there was 0
                    for(auto dst_state: this->observation_successors[joint_obs]) {
                        auto dst_obs = this->state_joint_observation[dst_state];
                        if(max_mem_size < this->observation_memory_size[dst_obs]) {
                            max_mem_size = this->observation_memory_size[dst_obs];
                        }
                    }
                    this->agent_max_successor_memory_size[agent][obs] = max_mem_size;
                }
                
            }



            this->row_groups.resize(this->num_quotient_states);
            this->row_prototype.clear();
            this->row_memory.clear();

            uint64_t prototype_row = 0;
            uint64_t old_prototype_state = 0;
            uint64_t prototype_row_group = 0;
            
            // TODO can simplify this: state (s,x) will have the same rows as state (s,0)
            for(uint64_t state = 0; state < this->num_quotient_states; state++) {
                this->row_groups[state] = this->row_prototype.size();
                auto prototype_state = this->state_prototype[state];
                if (prototype_state != old_prototype_state)
                    {
                        prototype_row_group = prototype_row;
                    }
                prototype_row = prototype_row_group;
                auto observ = this->state_joint_observation[prototype_state];
                for(auto row: this->transition_matrix[prototype_state]) {
                    for(uint64_t dst_mem = 0; dst_mem < max_successor_memory_size[observ]; dst_mem++) {
                        // std::cout << "3 " << std::endl;
                        this->row_prototype.push_back(prototype_row);
                        // std::cout << "4 " << std::endl;
                        this->row_memory.push_back(dst_mem);
                        // std::cout << "5 " << std::endl;
                    }
                    prototype_row++;
                    


                }
                old_prototype_state = prototype_state;
            }
            this->num_quotient_rows = this->row_prototype.size();
           
        }

    void DecPomdp::resetDesignSpace() {
            auto num_observations = this->num_joint_observations();
            this->num_holes = 0;
            this->action_holes.clear();
            this->action_holes.resize(this->num_agents); 
            for (int agent = 0; agent < this->num_agents; agent++)
            {
               this->action_holes[agent].resize(this->agent_num_observations(agent)); 
            }
            this->memory_holes.clear();
            this->memory_holes.resize(this->num_agents);
            for (int agent = 0; agent < this->num_agents; agent++)
            {
               this->memory_holes[agent].resize(this->agent_num_observations(agent)); 
            }
            this->hole_options.clear();

            this->row_action_hole.clear();
            this->row_action_hole.resize(this->num_agents);
            for (int agent = 0; agent < this->num_agents; agent++)
            {
               this->row_action_hole[agent].resize(this->num_quotient_rows); 
            }
            this->row_action_option.clear();
            this->row_action_option.resize(this->num_agents);
            for (int agent = 0; agent < this->num_agents; agent++)
            {
               this->row_action_option[agent].resize(this->num_quotient_rows); 
            }
            this->row_memory_hole.clear();
            this->row_memory_hole.resize(this->num_agents);
            for (int agent = 0; agent < this->num_agents; agent++)
            {
               this->row_memory_hole[agent].resize(this->num_quotient_rows); 
            }
            this->row_memory_option.clear();
            this->row_memory_option.resize(this->num_agents);
            for (int agent = 0; agent < this->num_agents; agent++)
            {
               this->row_memory_option[agent].resize(this->num_quotient_rows); 
            }
            

            //count number of actions at observation for each agent
            this->nr_agent_actions_at_observation.clear();
            this->nr_agent_actions_at_observation.resize(this->num_agents);
            for (int agent = 0; agent < this->num_agents; agent++)
            {
                this->nr_agent_actions_at_observation[agent].resize(this->agent_observation_labels[agent].size()); 
            }

            for (int agent = 0; agent < this->num_agents; agent++){
               for (int state = 0; state < this->num_states(); state++){
                    auto joint_observation = this->state_joint_observation[state];
                    auto obs = this->joint_observations[joint_observation][agent];
                    if (this->nr_agent_actions_at_observation[agent][obs] != 0)
                     {
                        continue;
                     } 
                     auto actions = this->row_joint_action[state];
                     std::set<uint_fast64_t> set_of_actions;
                     for (auto action : actions)
                     {
                         set_of_actions.insert(this->joint_actions[action][agent]);
                     }
                    std::vector<uint_fast64_t> vec_of_actions;
                    vec_of_actions.assign( set_of_actions.begin(), set_of_actions.end() );

                     this->nr_agent_actions_at_observation[agent][obs] = vec_of_actions.size();
               }
                
            }
            // std::cout << "this->nr_agent_actions_at_observation cpp" << this->nr_agent_actions_at_observation << std::endl;

            // find index of option for each agent action
            this->agent_prototype_row_index.clear();
            this->agent_prototype_row_index.resize(this->num_agents);
            for (int agent = 0; agent < this->num_agents; agent++)
            {
               this->agent_prototype_row_index[agent].resize(this->num_rows() ,0); 
            }

            uint64_t row_index = 0;
            std::vector<uint_fast64_t> agent_actions_indexes;
            std::vector<uint_fast64_t>::iterator it;
            uint_fast64_t counter = 0;

            for (int agent = 0; agent < this->num_agents; agent++){
                row_index = 0;
                // agent_actions_indexes.clear();
                for(uint64_t state = 0; state < this->num_states(); state++) {
                    agent_actions_indexes.clear();
                    counter = 0;
                    for(auto row: this->row_joint_action[state]) {

                        it = std::find(agent_actions_indexes.begin(), agent_actions_indexes.end(), this->joint_actions[row][agent]);
                        if (it != agent_actions_indexes.end()) 
                        {
                            this->agent_prototype_row_index[agent][row_index] = it - agent_actions_indexes.begin();
                        }
                        else{
                            agent_actions_indexes.push_back( this->joint_actions[row][agent]);
                            this->agent_prototype_row_index[agent][row_index] = counter;
                            counter++;
                        }

                        row_index++;

                    }
                
                }
            }
            // std::cout << " this->agent_prototype_row_index " <<  this->agent_prototype_row_index << std::endl;

            
    
                        

        }

    void DecPomdp::construct_memory_joint_observation() {
        this->memory_joint_observation.clear();
        this->memory_joint_observation.resize(this->joint_observations.size());
        uint64_t id = 0;
        for (int obs = 0; obs < this->joint_observations.size(); ++obs)
            {
                this->memory_joint_observation[obs].resize(this->observation_memory_size[obs] ,0); 
                for (int mem = 0; mem < this->observation_memory_size[obs] ; ++mem){
                    // std::cout << mem  << std::endl;
                    this->memory_joint_observation[obs][mem] = id;
                    id++;
                }
            }
        this->nr_memory_joint_observations = id;
    }

    void DecPomdp::construct_acton_to_memory_joint_observation() {
        this->action_to_memory_joint_observation.clear();
        // this->action_to_memory_joint_observation.resize(this->num_joint_actions());

        
        // TODO can simplify this: state (s,x) will have the same rows as state (s,0)
        for(uint64_t state = 0; state < this->num_quotient_states; state++) {
            auto prototype_state = this->state_prototype[state];
            auto state_mem = this->state_memory[state];
            auto observ = this->state_joint_observation[prototype_state];
            for(auto row: this->transition_matrix[prototype_state]) {
                // std::cout << "2 " << std::endl;
                for(uint64_t dst_mem = 0; dst_mem < max_successor_memory_size[observ]; dst_mem++) {
                    // std::cout << "3 " << std::endl;
                    this->action_to_memory_joint_observation.push_back(this->memory_joint_observation[observ][state_mem]);
                }               
            }
        }
    }

    void DecPomdp::construct_state_to_memory_joint_observation() {
        this->state_to_memory_joint_observation.clear();
        // this->action_to_memory_joint_observation.resize(this->num_joint_actions());

        
        // TODO can simplify this: state (s,x) will have the same rows as state (s,0)
        for(uint64_t state = 0; state < this->num_quotient_states; state++) {
            auto prototype_state = this->state_prototype[state];
            auto state_mem = this->state_memory[state];
            auto observ = this->state_joint_observation[prototype_state];
            this->state_to_memory_joint_observation.push_back(this->memory_joint_observation[observ][state_mem]);
        }

        // std::cout << "this->state_to_memory_joint_observation" << this->state_to_memory_joint_observation  << std::endl;
    }

    void DecPomdp::buildDesignSpaceSpurious() {
            this->resetDesignSpace();
            this->construct_memory_joint_observation();
            this->construct_acton_to_memory_joint_observation();
            this->construct_state_to_memory_joint_observation();
            
            // for each (z,n) create an action and a memory hole (if necessary)
            // store hole range
            // ? inverse mapping ?
            for (int agent = 0; agent < this->num_agents; agent++) {
                for(uint64_t obs = 0; obs < this->agent_observation_labels[agent].size(); obs++) {
                    if(this->nr_agent_actions_at_observation[agent][obs] > 1) {
                        for(uint64_t mem = 0; mem <  std::pow(this->observation_memory_size[obs], 1.0 / this->num_agents); mem++) { //TODO obs must be joint observation
                            this->action_holes[agent][obs].push_back(this->num_holes);
                            this->hole_options.push_back(this->nr_agent_actions_at_observation[agent][obs]);
                            // std::cout << "created A(" << obs << "," << mem << ") = " << this->num_holes << " in {} of size " << this->observation_actions[obs] << std::endl;
                            this->num_holes++;
                        }
                    }
                    if(this->agent_max_successor_memory_size[agent][obs] > 1) {
                        for(uint64_t mem = 0; mem < std::pow(this->observation_memory_size[obs], 1.0 / this->num_agents); mem++) { //TODO obs must be joint observation
                            this->memory_holes[agent][obs].push_back(this->num_holes);
                            this->hole_options.push_back(std::pow(this->agent_max_successor_memory_size[agent][obs] , 1.0 / this->num_agents));
                            // std::cout << "created N(" << obs << "," << mem << ") = " << this->num_holes << " in {} of size " << this->max_successor_memory_size[obs] << std::endl;
                            this->num_holes++;
                        }
                    }
                }
            }
            // std::cout << "this->action_holes" << this->action_holes << std::endl;

            uint64_t row = 0;
            uint64_t old_state = 0;
            uint64_t row_group = 0;

             // map each row to some action (memory) hole (if applicable) and its value
            for(uint64_t state = 0; state < this->num_quotient_states; state++) {
                auto prototype = this->state_prototype[state];
                auto joint_observation = this->state_joint_observation[prototype];
                auto unprocessed_mem = this->state_memory[state]; 
                for (int agent = 0; agent < this->num_agents; agent++) {
                    if (state != old_state)
                    {
                        row_group = row;
                        old_state = state;
                    }
                    row = row_group;
                    auto obs = this->joint_observations[joint_observation][agent];
                    uint64_t mem_index = (uint64_t)std::pow(std::pow(this->max_successor_memory_size[joint_observation], 1.0 / this->num_agents), this->num_agents - 1 - agent);
                    auto mem = unprocessed_mem /  mem_index; //TODO work only with same memory for each agent
                    // std::cout << "agent " << agent << "mem_index " << mem_index << "unprocessed_mem " << unprocessed_mem << "mem " << mem << std::endl;
                    unprocessed_mem = (uint64_t)unprocessed_mem %  mem_index;
                    for(auto matrix_row: this->transition_matrix[prototype]) {
                        for(uint64_t dst_mem = 0; dst_mem < max_successor_memory_size[joint_observation]; dst_mem++) {
                            auto prototype_row = this->row_prototype[row];
                            auto row_index = this->agent_prototype_row_index[agent][prototype_row];
                            auto row_mem = this->row_memory[row];
                            if(this->nr_agent_actions_at_observation[agent][obs] > 1) {
                                // there is an action hole that corresponds to this state
                                auto action_hole = this->action_holes[agent][obs][mem];
                                                             
                                // std::cout << "action_hole " << action_hole << std::endl;
                                this->row_action_hole[agent][row] = action_hole;
                                this->row_action_option[agent][row] = row_index; // must be index of agent action option, not joint option 
                            } else {
                                // no corresponding action hole
                                this->row_action_hole[agent][row] = this->num_holes;
                                // std::cout << "a joint_observation " << joint_observation << std::endl;
                            }
                            if(this->max_successor_memory_size[joint_observation] > 1) {
                                // there is a memory hole that corresponds to this state
                                auto memory_hole = this->memory_holes[agent][obs][mem];
                                // std::cout << "check  2" << std::endl;
                                this->row_memory_hole[agent][row] = memory_hole;
                                // std::cout << "check  3" << std::endl;
                                this->row_memory_option[agent][row] = mem;
                                // std::cout << "check  4" << std::endl;
                            } else {
                                this->row_memory_hole[agent][row] = this->num_holes;
                                // std::cout << "state " << state << std::endl;
                            }
                            row++;
                        }
                    } 
                    
                }
            }
            

            // fill row_memory_option
            row = 0;
            for(uint64_t state = 0; state < this->num_quotient_states; state++) {
                auto prototype = this->state_prototype[state];
                auto joint_observation = this->state_joint_observation[prototype];
                for(auto matrix_row: this->transition_matrix[prototype]) {
                    for(uint64_t dst_mem = 0; dst_mem < max_successor_memory_size[joint_observation]; dst_mem++) {
                        auto unprocessed_mem = this->row_memory[row];
                        for (int agent = 0; agent < this->num_agents; agent++) {

                            uint64_t mem_index = (uint64_t)std::pow(std::pow(this->observation_memory_size[joint_observation], 1.0 / this->num_agents), this->num_agents - 1 - agent);
                            auto mem = unprocessed_mem /  mem_index; //TODO work only with same memory for each agent
                            // std::cout << "agent " << agent << "mem_index " << mem_index << "unprocessed_mem " << unprocessed_mem << "mem " << mem << std::endl;
                            unprocessed_mem = (uint64_t)unprocessed_mem %  mem_index;

                            if(this->max_successor_memory_size[joint_observation] > 1) {
                                this->row_memory_option[agent][row] = mem;
                            } 
                        }
                        row++;
                    }
                }
            }
        
    }

}
