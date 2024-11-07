#include "DecPomdp.h"

#include "madp/base/Globals.h"
#include "madp/base/E.h"
#include "madp/parser/MADPParser.h"

#include <stack>

namespace synthesis {
    
    
    void DecPomdp::collectActions(DecPOMDPDiscrete *model) {
        
        // individual actions
        this->agent_action_labels.resize(this->num_agents);
        for(uint64_t agent = 0; agent < this->num_agents; agent++) {
            uint64_t num_actions = model->GetNrActions(agent);
            this->agent_action_labels[agent].resize(num_actions);
            std::vector<std::string> action_labels(num_actions);
            for(uint64_t action = 0; action < num_actions; action++) {
                this->agent_action_labels[agent][action] = model->GetAction(agent,action)->GetName();
            }
        }

        // joint actions
        this->joint_actions.resize(model->GetNrJointActions());
        for(uint64_t joint_action_index = 0; joint_action_index < model->GetNrJointActions(); joint_action_index++) {
            for(auto action: model->JointToIndividualActionIndices(joint_action_index)) {
                this->joint_actions[joint_action_index].push_back(action);
            }
        }
    }

    void DecPomdp::collectObservations(DecPOMDPDiscrete *model) {
        
        // individual observations
        this->agent_observation_labels.resize(this->num_agents);
        for(uint64_t agent = 0; agent < this->num_agents; agent++) {
            for(uint64_t obs = 0; obs < model->GetNrObservations(agent); obs++) {
                this->agent_observation_labels[agent].push_back(model->GetObservation(agent,obs)->GetName());
            }
        }

        // joint observations
        uint64_t num_joint_observations = model->GetNrJointObservations();
        this->joint_observations.resize(num_joint_observations);
        for(uint64_t joint_observation_index = 0; joint_observation_index < num_joint_observations; joint_observation_index++) {
            for(auto observation: model->JointToIndividualObservationIndices(joint_observation_index)) {
                this->joint_observations[joint_observation_index].push_back(observation);
            }
        }
    }

    
    bool DecPomdp::haveMadpState(MadpState madp_state) {
        return this->madp_to_storm_states.find(madp_state) != this->madp_to_storm_states.end();
    }
    
    uint64_t DecPomdp::mapMadpState(MadpState madp_state) {
        uint64_t new_state = this->num_states();
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

    
    uint64_t DecPomdp::freshJointAction(std::string action_label) {
        std::vector<uint64_t> action_tuple(this->num_agents);
        for(uint64_t agent = 0; agent < this->num_agents; agent++) {
            action_tuple[agent] = this->agent_num_actions(agent);
            this->agent_action_labels[agent].push_back(action_label);
        }
        uint64_t joint_action = this->num_joint_actions();
        this->joint_actions.push_back(std::move(action_tuple));
        return joint_action;
    }
    
    uint64_t DecPomdp::freshJointObservation(std::string observation_label) {
        std::vector<uint64_t> observation_tuple(this->num_agents);
        for(uint64_t agent = 0; agent < this->num_agents; agent++) {
            observation_tuple[agent] = this->agent_num_observations(agent);
            this->agent_observation_labels[agent].push_back(observation_label);
        }
        uint64_t joint_observation = this->num_joint_observations();
        this->joint_observations.push_back(std::move(observation_tuple));
        return joint_observation;
    }

    uint64_t DecPomdp::freshSink(std::string label) {
        
        uint64_t joint_observation = this->freshJointObservation(label);
        MadpState madp_new_state = std::make_pair(0,joint_observation);
        uint64_t new_state = this->mapMadpState(madp_new_state);

        uint64_t sink_action = this->freshJointAction(label);
        this->row_joint_action[new_state] = std::vector<uint64_t>(1, sink_action);
        this->row_reward[new_state] = std::vector<double>(1, 0);
        this->transition_matrix[new_state] = std::vector<StormRow>(1, StormRow(1, std::make_pair(new_state,1)));

        // resize needed for the added sink state
        for (uint64_t agent = 0; agent < this->num_agents; agent++) {
            this->agent_observation_memory_size[agent].resize(this->agent_num_observations(agent), 1);
            this->agent_prototype_row_index[agent].push_back(0);
        }
        this->prototype_duplicates.resize(this->num_states());
        this->max_successor_memory_size.resize(this->num_joint_observations());

        return new_state;
    }



    DecPomdp::DecPomdp(DecPOMDPDiscrete *model) {
        // agents
        this->num_agents = model->GetNrAgents();
        this->discount_factor = model->GetDiscount();
        this->reward_minimizing = model->GetRewardType() == COST;
        this->agent_prototype_row_index.resize(this->num_agents);


        this->collectActions(model);
        this->collectObservations(model);

        // multiply transition and observation probabilities
        std::vector<std::vector<std::vector<std::pair<MadpState,double>>>> madp_transition_matrix;
        for(uint64_t src = 0; src < model->GetNrStates(); src++) {
            std::vector<std::vector<std::pair<MadpState,double>>> row_group;
            
            for(uint64_t joint_action = 0; joint_action < model->GetNrJointActions(); joint_action++) {
                std::vector<std::pair<MadpState,double>> row;
                
                for(uint64_t dst = 0; dst < model->GetNrStates(); dst++) {
                    double transition_prob = model->GetTransitionProbability(src, joint_action, dst);
                    if(transition_prob == 0) {
                        continue;
                    }
                    
                    for(uint64_t obs = 0; obs < model->GetNrJointObservations(); obs++) {
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
        uint64_t init_joint_observation = this->freshJointObservation(this->init_label);
        // create action that corresponds to the execution of the initial distribution
        uint64_t init_joint_action = this->freshJointAction(this->init_label);
        // create empty observation for states in the initial distribution
        uint64_t empty_joint_observation = this->freshJointObservation(this->no_obs_label);

        // collect initial distribution
        std::vector<MadpRow> initial_distribution_row_group(1);
        uint64_t state = 0;
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
            uint64_t storm_src = this->mapMadpState(madp_src);
            
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
                    uint64_t storm_dst = this->mapMadpState(madp_dst);
                    storm_row.push_back(std::make_pair(storm_dst, madp_state_prob.second));
                }
                storm_row_group.push_back(std::move(storm_row));
            }
            this->transition_matrix[storm_src] = std::move(storm_row_group);
        }

        // map rows to joint actions and rewards
        std::vector<uint64_t> madp_row_group;
        for(uint64_t joint_action = 0; joint_action < model->GetNrJointActions(); joint_action++) {
            madp_row_group.push_back(joint_action);
        }
        assert(this->row_joint_action.size() == this->num_states());
        assert(this->row_reward.size() == this->num_states());
        for(uint64_t storm_state = 0; storm_state < this->num_states(); storm_state++) {
            MadpState madp_state = this->storm_to_madp_states[storm_state];
            if(storm_state == this->initial_state) {
                this->row_joint_action[storm_state] = std::vector<uint64_t>(1,init_joint_action);
                this->row_reward[storm_state] = std::vector<double>(1,0);
            } else {
                this->row_joint_action[storm_state] = madp_row_group;
                std::vector<double> rewards;
                for(uint64_t joint_action = 0; joint_action < model->GetNrJointActions(); joint_action++) {
                    rewards.push_back(model->GetReward(madp_state.first, joint_action));
                }
                this->row_reward[storm_state] = std::move(rewards);
            }
        }

        this->agent_observation_memory_size.resize(this->num_agents);
        for (uint64_t agent = 0; agent < this->num_agents; agent++) {
            this->agent_observation_memory_size[agent].resize(this->agent_num_observations(agent), 1);
        }
        this->prototype_duplicates.resize(this->num_states());
        this->max_successor_memory_size.resize(this->num_joint_observations());

        // for each agent and each row assign corresponding action index
        std::vector<uint64_t> agent_actions_indeces;
        std::vector<uint64_t>::iterator it;
        for (int agent = 0; agent < this->num_agents; agent++) {
            uint64_t row_index = 0;
            for(uint64_t state = 0; state < this->num_states(); state++) {
                agent_actions_indeces.clear();
                uint64_t counter = 0;
                for(auto joint_action: this->row_joint_action[state]) {

                    it = std::find(agent_actions_indeces.begin(), agent_actions_indeces.end(), this->joint_actions[joint_action][agent]);
                    if (it != agent_actions_indeces.end()) {
                        this->agent_prototype_row_index[agent].push_back(it - agent_actions_indeces.begin());
                    }
                    else {
                        agent_actions_indeces.push_back(this->joint_actions[joint_action][agent]);
                        this->agent_prototype_row_index[agent].push_back(counter);
                        counter++;
                    }
                    row_index++;
                }
            }
        }
        this->computeAvailableActions();
        this->countSuccessors();
    }


    void DecPomdp::countSuccessors() {

        auto num_observations = this->num_joint_observations();
        this->observation_successors.resize(num_observations);

        std::vector<std::set<uint64_t>> observation_successor_sets;
        observation_successor_sets.resize(num_observations);

        this->agent_observation_successors.resize(this->num_agents);
        std::vector<std::vector<std::set<uint64_t>>> agent_observation_successor_sets;
        agent_observation_successor_sets.resize(this->num_agents);
        for (uint64_t agent = 0; agent < this->num_agents; agent++) {
            this->agent_observation_successors[agent].resize(this->agent_num_observations(agent));
            agent_observation_successor_sets[agent].resize(this->agent_num_observations(agent));
        }


        for(uint64_t state = 0; state < this->num_states(); state++) {
            auto observ = this->state_joint_observation[state];
            for(auto row: this->transition_matrix[state]) {
                for(auto entry: row) {
                    auto dst = entry.first;
                    double transition_prob = entry.second;
                    if(transition_prob == 0) {
                        continue;
                    }
                    auto dst_obs = this->state_joint_observation[dst];
                    observation_successor_sets[observ].insert(dst_obs);

                    for (uint64_t agent = 0; agent < this->num_agents; agent++) {
                        uint64_t agent_src_obs = this->joint_observations[observ][agent];
                        uint64_t agent_dst_obs = this->joint_observations[dst_obs][agent];
                        agent_observation_successor_sets[agent][agent_src_obs].insert(agent_dst_obs);
                    }
                }
            }
        }
        
        for(uint64_t obs = 0; obs < num_observations; obs++) {
            this->observation_successors[obs] = std::vector<uint64_t>(
                observation_successor_sets[obs].begin(),
                observation_successor_sets[obs].end()
                );
        }

        for (uint64_t agent = 0; agent < this->num_agents; agent++) {
            for (uint64_t agent_obs = 0; agent_obs < this->agent_num_observations(agent); agent_obs++) {
                this->agent_observation_successors[agent][agent_obs] = std::vector<uint64_t>(
                    agent_observation_successor_sets[agent][agent_obs].begin(),
                    agent_observation_successor_sets[agent][agent_obs].end()
                );
            }
        }
    }

    void DecPomdp::computeAvailableActions() {
        // for each agent and each observation compute the number of available actions
        this->num_agent_actions_at_observation.resize(this->num_agents);
        for (int agent = 0; agent < this->num_agents; agent++)
        {
            this->num_agent_actions_at_observation[agent].resize(this->agent_observation_labels[agent].size()); 
        }
        for (int agent = 0; agent < this->num_agents; agent++) {
            for (int state = 0; state < this->num_states(); state++) {
                auto joint_observation = this->state_joint_observation[state];
                auto obs = this->joint_observations[joint_observation][agent];
                if (this->num_agent_actions_at_observation[agent][obs] != 0) {
                    continue;
                } 
                auto actions = this->row_joint_action[state];
                std::set<uint64_t> set_of_actions;
                for (auto action : actions) {
                    set_of_actions.insert(this->joint_actions[action][agent]);
                }
                std::vector<uint64_t> vec_of_actions;
                vec_of_actions.assign( set_of_actions.begin(), set_of_actions.end() );
                this->num_agent_actions_at_observation[agent][obs] = vec_of_actions.size();
            }
        }
    }


    uint64_t DecPomdp::num_rows() {
        uint64_t count = 0;
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
        std::vector<uint64_t> agent_default_memories(this->num_agents, 0);

        storm::storage::BitVector init_flags(this->num_quotient_states, false);
        init_flags.set(this->prototype_duplicates[this->initial_state].at(agent_default_memories));
        labeling.addLabel("init", std::move(init_flags));

        if(this->discounted and this->discount_factor != 1) {
            storm::storage::BitVector discount_sink_flags(this->num_quotient_states, false);
            for (const auto &state_map : this->prototype_duplicates[this->discount_sink_state]) {
                discount_sink_flags.set(state_map.second);
            }
            labeling.addLabel(this->discount_sink_label, std::move(discount_sink_flags));
        }

        return labeling;
    }

    storm::models::sparse::ChoiceLabeling DecPomdp::constructChoiceLabeling() {
        uint64_t num_rows = this->num_rows();

        storm::models::sparse::ChoiceLabeling labeling(num_rows);
        uint64_t current_row = 0;
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
        uint64_t num_rows = this->num_quotient_rows;

        storm::models::sparse::ChoiceLabeling labeling(num_rows);
        uint64_t current_row = 0;
        std::vector<std::string> row_label(num_rows);
        std::set<std::string> all_labels;
        uint64_t row_counter = 0;
        uint64_t joint_action_index = 0;
        uint64_t quotient_row_counter = 0;
        for(uint64_t state = 0; state < this->num_quotient_states; state++) {
            auto prototype_state = this->state_prototype[state];
            auto observ = this->state_joint_observation[prototype_state];
            auto group_joint_actions = this->row_joint_action[prototype_state];
            row_counter = 0;
            for(auto row: this->transition_matrix[prototype_state]) {
                joint_action_index = group_joint_actions[row_counter];
                for(uint64_t mem = 0; mem < this->max_successor_memory_size[observ]; mem++) {
                    std::ostringstream sb;
                    sb << "[ ";
                    auto joint_action = this->joint_actions[joint_action_index];
                    for(uint32_t agent = 0; agent < this->num_agents; agent++) {
                        auto agent_action = joint_action[agent];
                        auto agent_action_label = this->agent_action_labels[agent][agent_action];
                        auto agent_memory = this->row_agent_memory[quotient_row_counter][agent];
                        sb << "(" << agent_action_label << ", " << agent_memory << ") ";
                    }
                    sb << "]";
                    std::string label = sb.str();
                    all_labels.insert(label);
                    row_label[current_row] = label;
                    current_row++;
                }
                quotient_row_counter++;
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
        storm::storage::SparseMatrixBuilder<double> builder(
                this->num_quotient_rows, this->num_quotient_states, 0, true, true, this->num_quotient_states
        );
        std::vector<uint64_t> agent_default_memories(this->num_agents, 0);
        uint64_t row_index = 0;
        for(uint64_t state = 0; state < this->num_quotient_states; state++) {
            auto prototype_state = this->state_prototype[state];
            auto observation = this->state_joint_observation[prototype_state];
            builder.newRowGroup(this->row_groups[state]);
            for (uint64_t row = this->row_groups[state]; row < this->row_groups[state+1]; row++) {
                auto prototype_state_row = this->row_prototype_state[row];
                auto agents_dst_mem = this->row_agent_memory[row];
                for (auto const &entry: this->transition_matrix[prototype_state][prototype_state_row]) {
                    uint64_t dst;
                    auto dst_it = this->prototype_duplicates[entry.first].find(agents_dst_mem);
                    if (dst_it == this->prototype_duplicates[entry.first].end()) {
                        dst = this->prototype_duplicates[entry.first].at(agent_default_memories);
                    } else {
                        dst = (*dst_it).second;
                    }
                    builder.addNextValue(row, dst, entry.second);
                }
            }
        }
        return builder.build();
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

    storm::models::sparse::StandardRewardModel<double> DecPomdp::constructConstraintRewardModel() {
        std::optional<std::vector<double>> state_rewards;
        std::vector<double> action_rewards;
        for(uint64_t state = 0; state < this->num_states(); state++) {
            for(uint64_t row = 0; row < this->transition_matrix[state].size(); row++) {
                auto reward = this->row_reward[state][row];
                // no matter what the bound is there should not be any cost in the initial state or the discount state
                if (reward < this->constraint_bound && (state != this->initial_state && state != this->discount_sink_state)) {
                    action_rewards.push_back(1);
                } else {
                    action_rewards.push_back(0);
                }
            }
        } 
        return storm::models::sparse::StandardRewardModel<double>(std::move(state_rewards), std::move(action_rewards));
    }


    storm::models::sparse::StandardRewardModel<double> DecPomdp::constructQuotientRewardModel() {
        std::optional<std::vector<double>> state_rewards;
        std::vector<double> action_rewards;
        for(uint64_t state = 0; state < this->num_quotient_states; state++) {
            auto prototype_state = this->state_prototype[state];
            auto observation = this->state_joint_observation[prototype_state];
            for(uint64_t row = 0; row < this->transition_matrix[prototype_state].size(); row++) {
                auto reward = this->row_reward[prototype_state][row];
                for(uint64_t dst_mem = 0; dst_mem < this->max_successor_memory_size[observation]; dst_mem++) {
                    action_rewards.push_back(reward);
                }
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

    std::shared_ptr<storm::models::sparse::Mdp<double>> DecPomdp::constructMdp() { 
        storm::storage::sparse::ModelComponents<double> components;
        components.stateLabeling = this->constructStateLabeling();
        components.choiceLabeling = this->constructChoiceLabeling();
        components.transitionMatrix = this->constructTransitionMatrix();
        components.rewardModels.emplace(this->reward_model_name, this->constructRewardModel());
        if (this->constraint_bound < std::numeric_limits<double>::infinity()) {
            components.rewardModels.emplace(this->constraint_reward_model_name, this->constructConstraintRewardModel());
        }
        return std::make_shared<storm::models::sparse::Mdp<double>>(std::move(components));
    }

    std::shared_ptr<storm::models::sparse::Pomdp<double>> DecPomdp::constructPomdp() {
        storm::storage::sparse::ModelComponents<double> components;
        components.stateLabeling = this->constructStateLabeling();
        components.choiceLabeling = this->constructChoiceLabeling();
        components.transitionMatrix = this->constructTransitionMatrix();
        components.rewardModels.emplace(this->reward_model_name, this->constructRewardModel());
        if (this->constraint_bound < std::numeric_limits<double>::infinity()) {
            components.rewardModels.emplace(this->constraint_reward_model_name, this->constructConstraintRewardModel());
        }
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
        for(uint64_t state = 0; state < this->num_states(); state++) {
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
        this->computeAvailableActions();
        this->countSuccessors();
    }

    void DecPomdp::computeJointObservationMemorySize() {
        this->joint_observation_memory_size.clear();
        this->joint_observation_memory_size.resize(this->num_joint_observations());
        for (uint64_t joint_obs = 0; joint_obs < this->num_joint_observations(); joint_obs++) {
            uint64_t joint_obs_memory = 1;
            for (auto agent = 0; agent < this->num_agents; agent++) {
                uint64_t agent_obs = this->joint_observations[joint_obs][agent];
                joint_obs_memory *= this->agent_observation_memory_size[agent][agent_obs];
            }
            this->joint_observation_memory_size[joint_obs] = joint_obs_memory;
        }
    }

    void DecPomdp::buildStateSpace() {
        this->num_quotient_states = 0;
        this->state_prototype.clear();
        this->state_agent_memory.clear();
        this->computeJointObservationMemorySize();
        for (uint64_t prototype = 0; prototype < this->num_states(); prototype++) {
            auto obs = this->state_joint_observation[prototype];
            auto memory_size = this->joint_observation_memory_size[obs];
            this->prototype_duplicates[prototype].clear();
            // state memory needs to be stored individually for each agent
            std::vector<std::vector<uint64_t>> agent_memories;
            std::vector<std::vector<uint64_t>::iterator> agent_memory_iterator;
            agent_memories.resize(this->num_agents);
            agent_memory_iterator.resize(this->num_agents);
            for (uint64_t agent = 0; agent < this->num_agents; agent++) {
                auto agent_obs = this->joint_observations[obs][agent];
                auto agent_mem = this->agent_observation_memory_size[agent][agent_obs];
                agent_memories[agent].resize(agent_mem);
                for (uint64_t i = 0; i < agent_mem; i++) {
                    agent_memories[agent][i] = i;
                }
                agent_memory_iterator[agent] = agent_memories[agent].begin();
            }
            // cartesian product over all agent memories in the current state
            while (agent_memory_iterator[this->num_agents-1] != agent_memories[this->num_agents-1].end()) {
                std::vector<uint64_t> state_memory_vector;
                state_memory_vector.resize(this->num_agents);
                for (uint64_t a = 0; a < this->num_agents; a++) {
                    state_memory_vector[a] = *(agent_memory_iterator[a]);
                }
                // update the values
                this->prototype_duplicates[prototype].insert({state_memory_vector,this->num_quotient_states});
                this->state_prototype.push_back(prototype);
                this->state_agent_memory.push_back(state_memory_vector);
                this->num_quotient_states++;

                // increment iterators accordingly
                agent_memory_iterator[0]++;
                for (uint64_t i = 0; (i < this->num_agents-1) && (agent_memory_iterator[i] == agent_memories[i].end()); i++) {
                    agent_memory_iterator[i] = agent_memories[i].begin();
                    agent_memory_iterator[i+1]++;
                }
            }
        }
    }


    void DecPomdp::buildTransitionMatrixSpurious() {
        this->max_successor_memory_size.resize(this->num_joint_observations(), 0);
        // for each observation, define the maximum successor memory size
        // this will define the number of copies we need to make of each row
        for(uint64_t obs = 0; obs < this->num_joint_observations(); obs++) {
            uint64_t max_mem_size = 0;
            for(auto dst_obs: this->observation_successors[obs]) {
                if(max_mem_size < this->joint_observation_memory_size[dst_obs]) {
                    max_mem_size = this->joint_observation_memory_size[dst_obs];
                }
            }
            this->max_successor_memory_size[obs] = max_mem_size;
        }

        // collect max succesor memory for each agent
        this->agent_max_successor_memory_size.clear();
        this->agent_max_successor_memory_size.resize(this->num_agents);
        for (int agent = 0; agent < this->num_agents; agent++)
        {
            this->agent_max_successor_memory_size[agent].resize(this->agent_num_observations(agent), 0); 
        }

        for (int agent = 0; agent < this->num_agents; agent++){
            for(uint64_t agent_src_obs = 0; agent_src_obs < this->agent_num_observations(agent); agent_src_obs++) {
                uint64_t max_mem_size = 0;
                for(auto dst_obs: this->agent_observation_successors[agent][agent_src_obs]) {
                    if(max_mem_size < this->agent_observation_memory_size[agent][dst_obs]) {
                        max_mem_size = this->agent_observation_memory_size[agent][dst_obs];
                    }
                }
                this->agent_max_successor_memory_size[agent][agent_src_obs] = max_mem_size;
            }
        }

        this->row_groups.resize(this->num_quotient_states+1);
        this->row_prototype.clear();
        this->row_prototype_state.clear();
        this->row_agent_memory.clear();
        uint64_t prototype_row = 0;
        std::map<uint64_t, uint64_t> prototype_state_to_row;
        
        // TODO can simplify this: state (s,x) will have the same rows as state (s,0)
        for (uint64_t state = 0; state < this->num_quotient_states; state++) {
            this->row_groups[state] = this->row_prototype_state.size();
            auto prototype_state = this->state_prototype[state];
            auto joint_obs = this->state_joint_observation[prototype_state];
            auto prototype_state_to_row_it = prototype_state_to_row.find(prototype_state);
            if (prototype_state_to_row_it == prototype_state_to_row.end()) {
                prototype_state_to_row.insert({prototype_state, prototype_row});
            } else {
                prototype_row = (*prototype_state_to_row_it).second;
            }

            std::vector<std::vector<uint64_t>> agent_max_successor_memories;
            std::vector<std::vector<uint64_t>::iterator> agent_memory_iterator;
            agent_max_successor_memories.resize(this->num_agents);
            agent_memory_iterator.resize(this->num_agents);
            for (uint64_t agent = 0; agent < this->num_agents; agent++) {
                auto agent_obs = this->joint_observations[joint_obs][agent];
                auto agent_max_successor_mem = this->agent_max_successor_memory_size[agent][agent_obs];
                agent_max_successor_memories[agent].resize(agent_max_successor_mem);
                for (uint64_t i = 0; i < agent_max_successor_mem; i++) {
                    agent_max_successor_memories[agent][i] = i;
                }
                agent_memory_iterator[agent] = agent_max_successor_memories[agent].begin();
            }

            uint64_t prototype_state_row = 0;
            for (auto row: this->transition_matrix[prototype_state]) {
                // cartesian product over all agent max successor memories from the current state
                while (agent_memory_iterator[this->num_agents-1] != agent_max_successor_memories[this->num_agents-1].end()) {
                    std::vector<uint64_t> row_memory_vector;
                    row_memory_vector.resize(this->num_agents);
                    for (uint64_t a = 0; a < this->num_agents; a++) {
                        row_memory_vector[a] = *(agent_memory_iterator[a]);
                    }
                    this->row_prototype_state.push_back(prototype_state_row);
                    this->row_prototype.push_back(prototype_row);
                    this->row_agent_memory.push_back(row_memory_vector);

                    agent_memory_iterator[0]++;
                    for (uint64_t i = 0; (i < this->num_agents-1) && (agent_memory_iterator[i] == agent_max_successor_memories[i].end()); i++) {
                        agent_memory_iterator[i] = agent_max_successor_memories[i].begin();
                        agent_memory_iterator[i+1]++;
                    }
                }
                prototype_state_row++;
                prototype_row++;
                for (uint64_t agent = 0; agent < this->num_agents; agent++) {
                    agent_memory_iterator[agent] = agent_max_successor_memories[agent].begin();
                }
            }
        }
        this->num_quotient_rows = this->row_prototype_state.size();
        this->row_groups[this->num_quotient_states] = this->num_quotient_rows;
    }

    // TODO check if clear really clears everything like this...
    void DecPomdp::resetDesignSpace() {
        this->num_holes = 0;
        this->agent_action_holes.clear();
        this->agent_action_holes.resize(this->num_agents); 
        for (int agent = 0; agent < this->num_agents; agent++)
        {
            this->agent_action_holes[agent].resize(this->agent_num_observations(agent)); 
        }
        this->agent_memory_holes.clear();
        this->agent_memory_holes.resize(this->num_agents);
        for (int agent = 0; agent < this->num_agents; agent++)
        {
            this->agent_memory_holes[agent].resize(this->agent_num_observations(agent)); 
        }
        this->hole_options.clear();

        this->agent_row_action_hole.clear();
        this->agent_row_action_hole.resize(this->num_agents);
        for (int agent = 0; agent < this->num_agents; agent++)
        {
            this->agent_row_action_hole[agent].resize(this->num_quotient_rows); 
        }
        this->agent_row_action_option.clear();
        this->agent_row_action_option.resize(this->num_agents);
        for (int agent = 0; agent < this->num_agents; agent++)
        {
            this->agent_row_action_option[agent].resize(this->num_quotient_rows); 
        }
        this->agent_row_memory_hole.clear();
        this->agent_row_memory_hole.resize(this->num_agents);
        for (int agent = 0; agent < this->num_agents; agent++)
        {
            this->agent_row_memory_hole[agent].resize(this->num_quotient_rows); 
        }
        this->agent_row_memory_option.clear();
        this->agent_row_memory_option.resize(this->num_agents);
        for (int agent = 0; agent < this->num_agents; agent++)
        {
            this->agent_row_memory_option[agent].resize(this->num_quotient_rows); 
        }
    }

    void DecPomdp::buildDesignSpaceSpurious() {
        this->resetDesignSpace();

        // for each (a,z,n) create an action and a memory hole (if necessary)
        // store hole range
        for (int agent = 0; agent < this->num_agents; agent++) {
            for(uint64_t obs = 0; obs < this->agent_observation_labels[agent].size(); obs++) {
                if(this->num_agent_actions_at_observation[agent][obs] > 1) {
                    for(uint64_t mem = 0; mem < this->agent_observation_memory_size[agent][obs]; mem++) { 
                        this->agent_action_holes[agent][obs].push_back(this->num_holes);
                        this->hole_options.push_back(this->num_agent_actions_at_observation[agent][obs]);
                        this->num_holes++;
                    }
                }
                if(this->agent_max_successor_memory_size[agent][obs] > 1) {
                    for(uint64_t mem = 0; mem < this->agent_observation_memory_size[agent][obs]; mem++) {
                        this->agent_memory_holes[agent][obs].push_back(this->num_holes);
                        this->hole_options.push_back(this->agent_observation_memory_size[agent][obs]);
                        this->num_holes++;
                    }
                }
            }
        }

        // map each row to the corresponding holes
        for (uint64_t state = 0; state < this->num_quotient_states; state++) {
            auto prototype = this->state_prototype[state];
            auto joint_obs = this->state_joint_observation[prototype];
            for (uint64_t agent = 0; agent < this->num_agents; agent++) {
                auto agent_obs = this->joint_observations[joint_obs][agent];
                auto agent_mem = this->state_agent_memory[state][agent];
                for (uint64_t row = this->row_groups[state]; row < this->row_groups[state+1]; row++) {
                    auto prototype_row = this->row_prototype[row];
                    auto row_agent_index = this->agent_prototype_row_index[agent][prototype_row];
                    auto row_agent_mem = this->row_agent_memory[row][agent];
                    if (this->num_agent_actions_at_observation[agent][agent_obs] > 1) {
                        // there is an action hole that corresponds to this state
                        auto action_hole = this->agent_action_holes[agent][agent_obs][agent_mem];
                        this->agent_row_action_hole[agent][row] = action_hole;
                        this->agent_row_action_option[agent][row] = row_agent_index;
                    } else {
                        // no corresponding action hole
                        this->agent_row_action_hole[agent][row] = this->num_holes;
                    }
                    if (this->agent_max_successor_memory_size[agent][agent_obs] > 1) {
                        // there is a memory hole that corresponds to this state
                        auto memory_hole = this->agent_memory_holes[agent][agent_obs][agent_mem];
                        this->agent_row_memory_hole[agent][row] = memory_hole;
                        this->agent_row_memory_option[agent][row] = row_agent_mem;
                    } else {
                        // no corresponding memory hole
                        this->agent_row_memory_hole[agent][row] = this->num_holes;
                    }
                }
            }
        }
    }

    std::shared_ptr<storm::models::sparse::Mdp<double>> DecPomdp::constructQuotientMdp() {
        this->buildStateSpace();
        this->buildTransitionMatrixSpurious();

        storm::storage::sparse::ModelComponents<double> components;
        components.stateLabeling = this->constructQuotientStateLabeling();
        components.choiceLabeling = this->constructQuotientChoiceLabeling();
        components.transitionMatrix = this->constructQuotientTransitionMatrix();
        components.rewardModels.emplace(this->reward_model_name, this->constructQuotientRewardModel());
        this->buildDesignSpaceSpurious();
        return std::make_shared<storm::models::sparse::Mdp<double>>(std::move(components));
    }


    void DecPomdp::setAgentObservationMemorySize(uint64_t agent, uint64_t obs, uint64_t memory_size) {
        this->agent_observation_memory_size[agent][obs] = memory_size;
    }

    void DecPomdp::setGlobalMemorySize(uint64_t memory_size) {
        for (uint64_t agent = 0; agent < this->num_agents; agent++) {
            for (uint64_t obs = 0; obs < this->agent_num_observations(agent); obs++) {
                this->agent_observation_memory_size[agent][obs] = memory_size;
            }
        }
    }

}
