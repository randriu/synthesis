#include "SubPomdpBuilder.h"

#include "storm/exceptions/InvalidArgumentException.h"

#include "storm/storage/sparse/ModelComponents.h"
#include "storm/storage/SparseMatrix.h"
#include "storm/models/sparse/StandardRewardModel.h"

#include <stack>

namespace synthesis {
    
    SubPomdpBuilder::SubPomdpBuilder(
        storm::models::sparse::Pomdp<double> const& pomdp,
        std::string const& reward_name,
        std::string const& target_label
    )
        : pomdp(pomdp), reward_name(reward_name), target_label(target_label) {

        auto const& tm = pomdp.getTransitionMatrix();
        this->reachable_successors.resize(pomdp.getNumberOfStates());
        for(uint64_t state = 0; state < pomdp.getNumberOfStates(); state++) {
            this->reachable_successors[state] = std::set<uint64_t>();
            for(auto const& entry: tm.getRowGroup(state)) {
                auto successor = entry.getColumn();
                if(successor != state) {
                    this->reachable_successors[state].insert(successor);
                }
            }
        }

        this->relevant_states = storm::storage::BitVector(this->pomdp.getNumberOfStates(),false);
        this->frontier_states = storm::storage::BitVector(this->pomdp.getNumberOfStates(),false);
    }

    void SubPomdpBuilder::setRelevantStates(storm::storage::BitVector const& relevant_states) {
        this->relevant_states = relevant_states;
        this->collectFrontierStates();
    }

    void SubPomdpBuilder::collectFrontierStates() {
        this->frontier_states.clear();
        for(auto state: this->relevant_states) {
            for(uint64_t successor: this->reachable_successors[state]) {
                if(!this->relevant_states[successor]) {
                    this->frontier_states.set(successor,true);
                }
            }
        }
    }

    void SubPomdpBuilder::setRelevantObservations(
        storm::storage::BitVector const& relevant_observations,
        std::map<uint64_t,double> const& initial_belief
    ) {
        this->relevant_observations = relevant_observations;
        this->relevant_states.clear();
        this->frontier_states.clear();

        // traverse the POMDP and identify states with relevant observations that are reachable from the initial belief
        std::stack<uint64_t> state_stack;
        for(const auto &entry : initial_belief) {
            auto state = entry.first;
            this->relevant_states.set(state,true);
            state_stack.push(state);
        }
        while(!state_stack.empty()) {
            auto state = state_stack.top();
            state_stack.pop();
            for(auto dst: this->reachable_successors[state]) {
                auto dst_obs = this->pomdp.getObservation(dst);
                if(this->relevant_observations[dst_obs] && !this->relevant_states[dst]) {
                    // first encounter of a relevant state
                    this->relevant_states.set(dst,true);
                    state_stack.push(dst);
                }
            }
        }
        this->collectFrontierStates();
    }
    

    void SubPomdpBuilder::constructStates() {

        this->num_states_subpomdp = this->relevant_states.getNumberOfSetBits() + this->frontier_states.getNumberOfSetBits() + 2;
        this->num_rows_subpomdp = this->frontier_states.getNumberOfSetBits() + 2;
        for(auto state: this->relevant_states) {
            this->num_rows_subpomdp += this->pomdp.getNumberOfChoices(state);
        }

        auto num_states_pomdp = this->pomdp.getNumberOfStates();
        this->state_sub_to_full = std::vector<uint64_t>(this->num_states_subpomdp,0);
        this->state_full_to_sub = std::vector<uint64_t>(num_states_pomdp,0);

        // indices 0 and 1 are reserved for the initial and the sink state respectively
        uint64_t state_subpomdp = 0;
        this->state_sub_to_full[state_subpomdp++] = num_states_pomdp;
        this->state_sub_to_full[state_subpomdp++] = num_states_pomdp;
        
        for(auto state: this->relevant_states) {
            this->state_full_to_sub[state] = state_subpomdp;
            this->state_sub_to_full[state_subpomdp] = state;
            state_subpomdp++;
        }
        for(auto state: this->frontier_states) {
            this->state_full_to_sub[state] = state_subpomdp;
            this->state_sub_to_full[state_subpomdp] = state;
            state_subpomdp++;
        }
    }

    
    storm::storage::SparseMatrix<double> SubPomdpBuilder::constructTransitionMatrix(
        std::map<uint64_t,double> const& initial_belief
    ) {

        // building the transition matrix
        storm::storage::SparseMatrixBuilder<double> builder(
                this->num_rows_subpomdp, this->num_states_subpomdp, 0, true, true, this->num_states_subpomdp
        );
        uint64_t current_row = 0;

        // initial state distribution
        builder.newRowGroup(current_row);
        for(const auto &entry : initial_belief) {
            auto dst = this->state_full_to_sub[entry.first];
            builder.addNextValue(current_row, dst, entry.second);
        }
        current_row++;

        // sink state self-loop
        builder.newRowGroup(current_row);
        builder.addNextValue(current_row, this->sink_state, 1);
        current_row++;

        // relevant states
        auto const& tm = this->pomdp.getTransitionMatrix();
        auto const& row_groups = this->pomdp.getNondeterministicChoiceIndices();
        for(auto state: this->relevant_states) {
            builder.newRowGroup(current_row);
            for(uint64_t row = row_groups[state]; row < row_groups[state+1]; row++) {
                if(this->discount_factor < 1) {
                    builder.addNextValue(current_row, this->sink_state, 1-this->discount_factor);
                }
                for(auto const& entry: tm.getRow(row)) {
                    auto dst = this->state_full_to_sub[entry.getColumn()];
                    builder.addNextValue(current_row, dst, entry.getValue() * this->discount_factor);
                }
                current_row++;
            }
        }

        // frontier states are rerouted to the sink state with probability 1
        for(const auto state: this->frontier_states) {
            (void) state;
            builder.newRowGroup(current_row);
            builder.addNextValue(current_row, this->sink_state, 1);
            current_row++;
        }

        // transition matrix finalized
        return builder.build();
    }

    storm::models::sparse::StateLabeling SubPomdpBuilder::constructStateLabeling() {
        // initial state labeling
        storm::models::sparse::StateLabeling labeling(this->num_states_subpomdp);
        storm::storage::BitVector label_init(this->num_states_subpomdp, false);
        label_init.set(this->initial_state);
        labeling.addLabel("init", std::move(label_init));

        // target state labeling
        storm::storage::BitVector label_target(this->num_states_subpomdp, false);
        auto const& pomdp_labeling = this->pomdp.getStateLabeling();
        auto const& pomdp_target_states = pomdp_labeling.getStates(this->target_label);
        for(auto state: pomdp_target_states) {
            if(this->relevant_states[state]) {
                label_target.set(this->state_full_to_sub[state]);
            }
        }
        label_target.set(this->sink_state);
        labeling.addLabel(this->target_label, std::move(label_target));
        
        return labeling;
    }

    storm::models::sparse::ChoiceLabeling SubPomdpBuilder::constructChoiceLabeling() {
        // copy existing labels, add fresh label
        storm::models::sparse::ChoiceLabeling labeling(this->num_rows_subpomdp);
        auto const& pomdp_labeling = this->pomdp.getChoiceLabeling();
        for (auto const& label : pomdp_labeling.getLabels()) {
            labeling.addLabel(label, storm::storage::BitVector(this->num_rows_subpomdp,false));
        }
        labeling.addLabel(this->empty_label, storm::storage::BitVector(this->num_rows_subpomdp,false));

        // initial state, sink state
        labeling.addLabelToChoice(this->empty_label, 0);
        labeling.addLabelToChoice(this->empty_label, 1);

        // relevant states
        auto const& row_groups = this->pomdp.getNondeterministicChoiceIndices();
        uint64_t current_row = 2;
        for(auto state: this->relevant_states) {
            for(uint64_t row = row_groups[state]; row<row_groups[state+1]; row++) {
                for(auto label: pomdp_labeling.getLabelsOfChoice(row)) {
                    labeling.addLabelToChoice(label, current_row);
                }
                current_row++;
            }
        }

        // frontier states
        for(auto state: this->frontier_states) {
            (void) state;
            labeling.addLabelToChoice(this->empty_label, current_row++);
        }

        return labeling;
    }

    std::vector<uint32_t> SubPomdpBuilder::constructObservabilityClasses() {
        std::vector<uint32_t> observation_classes(this->num_states_subpomdp);
        uint32_t fresh_observation = this->pomdp.getNrObservations();
        observation_classes[this->initial_state] = fresh_observation;
        observation_classes[this->sink_state] = fresh_observation;
        for(auto state: this->relevant_states) {
            observation_classes[this->state_full_to_sub[state]] = this->pomdp.getObservation(state);
        }
        for(auto state: this->frontier_states) {
            observation_classes[this->state_full_to_sub[state]] = fresh_observation;
        }
        return observation_classes;
    }

    storm::models::sparse::StandardRewardModel<double> SubPomdpBuilder::constructRewardModel() {
        auto const& reward_model = this->pomdp.getRewardModel(this->reward_name);
        std::optional<std::vector<double>> state_rewards;
        std::vector<double> action_rewards(this->num_rows_subpomdp,0);
        uint64_t current_row = 2;
        auto const& row_groups = this->pomdp.getNondeterministicChoiceIndices();
        for(auto state: this->relevant_states) {
            for(uint64_t row = row_groups[state]; row<row_groups[state+1]; row++) {
                action_rewards[current_row++] = reward_model.getStateActionReward(row);
            }
        }
        return storm::models::sparse::StandardRewardModel<double>(std::move(state_rewards), std::move(action_rewards));
    }

    std::shared_ptr<storm::models::sparse::Pomdp<double>> SubPomdpBuilder::restrictPomdp(
        std::map<uint64_t,double> const& initial_belief
    ) {
        this->constructStates();
        storm::storage::sparse::ModelComponents<double> components;
        components.transitionMatrix = this->constructTransitionMatrix(initial_belief);
        components.stateLabeling = this->constructStateLabeling();
        components.choiceLabeling = this->constructChoiceLabeling();
        components.observabilityClasses = this->constructObservabilityClasses();
        components.rewardModels.emplace(this->reward_name, this->constructRewardModel());
        return std::make_shared<storm::models::sparse::Pomdp<double>>(std::move(components));
    }

}
