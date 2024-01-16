#pragma once

#include "madp/src/base/POMDPDiscrete.h"
#include "madp/src/base/DecPOMDPDiscrete.h"

#include "storm/models/sparse/Mdp.h"
#include "storm/models/sparse/Pomdp.h"
#include "storm/models/sparse/StandardRewardModel.h"

#include <string>

namespace synthesis {

    using MadpState = std::pair<uint_fast64_t,uint_fast64_t>;   // state + observation
    using MadpRow = std::vector<std::pair<MadpState,double>>;
    using StormRow = std::vector<std::pair<uint_fast64_t,double>>;

    
    class DecPomdp {

    public:
        DecPomdp(DecPOMDPDiscrete *model);

        /** Number of agents. */
        uint_fast64_t num_agents;
        
        /** For each agent, a list of its action labels. */
        std::vector<std::vector<std::string>> agent_action_labels;
        /** A list of tuples of actions. */
        std::vector<std::vector<uint_fast64_t>> joint_actions;

        /** For each agent, a list of its observation labels. */
        std::vector<std::vector<std::string>> agent_observation_labels;
        /** A list of tuples of observations. */
        std::vector<std::vector<uint_fast64_t>> joint_observations;

        /** The unique initial state. */
        uint_fast64_t initial_state;
        /** Storm-esque transition matrix: for each state, a row group. */
        std::vector<std::vector<StormRow>> transition_matrix;
        /** For each state (row group), a mapping of a row to a joint action. */
        std::vector<std::vector<uint_fast64_t>> row_joint_action;
        /** State to joint observation map. */
        std::vector<uint_fast64_t> state_joint_observation;
        /** For each state (row group), a mapping of a row to its reward. */
        std::vector<std::vector<double>> row_reward;
        // for each row of a POMDP contains its index in its row group
        std::vector<uint64_t> prototype_row_index;

        
        
        
        uint_fast64_t agent_num_actions(uint_fast64_t agent) {
            return this->agent_action_labels[agent].size();
        }
        uint_fast64_t num_joint_actions() {
            return this->joint_actions.size();
        }
        uint_fast64_t agent_num_observations(uint_fast64_t agent) {
            return this->agent_observation_labels[agent].size();
        }
        uint_fast64_t num_joint_observations() {
            return this->joint_observations.size();
        }

        uint_fast64_t num_states() {
            return this->storm_to_madp_states.size();
        }

        uint_fast64_t num_rows();

        /** Retrieve the underlying MDP. */
        std::shared_ptr<storm::models::sparse::Mdp<double>> constructMdp();
       
        std::shared_ptr<storm::models::sparse::Mdp<double>> constructQuotientMdp();
        /** Retrieve the underlying POMDP. */
        std::shared_ptr<storm::models::sparse::Pomdp<double>> constructPomdp();
        /** count succesors for every observation and get prototype row index for every row index */
        void countSuccessors();

        /** If true, the rewards are interpreted as costs. */
        bool reward_minimizing;
        /** Label associated with the reward model. */
        std::string reward_model_name = "reward";

        double discount_factor;

        void applyDiscountFactorTransformation();

        /** Label for the state that simulates initial distribution. */
        std::string init_label = "init";
        /** Label for the states in the initial distribution. */
        std::string no_obs_label = "__no_obs__";

        /** Whether discounting transformation took place. */
        bool discounted = false;
        /** Index of the sink state. */
        uint_fast64_t discount_sink_state;
        /** Label associated with the sink. */
        std::string discount_sink_label = "discount_sink";

        // for each observation contains the number of allocated memory states (initially 1)
        std::vector<uint64_t> observation_memory_size;

        // set memory size to a selected observation
        void setObservationMemorySize(uint64_t obs, uint64_t memory_size);
        // set memory size to all observations
        void setGlobalMemorySize(uint64_t memory_size);

        // for each state contains its prototype state (reverse of prototype_duplicates)
        std::vector<uint64_t> state_prototype;
        // for each state contains its memory index
        std::vector<uint64_t> state_memory;

        /** Number of states of quotient mdp. */
        uint_fast64_t num_quotient_states;

        // for each observation, a list of successor observations
        std::vector<std::vector<uint64_t>> observation_successors;

        // for each observation contains the maximum memory size of a destination
        // across all rows of a prototype state having this observation
        std::vector<uint64_t> max_successor_memory_size;

        // total number of holes
        uint64_t num_holes;
        // for each observation, a list of action holes
        std::vector<std::vector<std::vector<uint64_t>>> action_holes;
        // for each observation, a list of memory holes
        std::vector<std::vector<std::vector<uint64_t>>>  memory_holes;
        
        // for each hole, its size
        std::vector<uint64_t> hole_options;

        // for each row, the corresponding action hole
        std::vector<std::vector<uint64_t>> row_action_hole;
        // for each row, the corresponding option of the action hole
        std::vector<std::vector<uint64_t>> row_action_option;
        // for each row, the corresponding memory hole
        std::vector<std::vector<uint64_t>> row_memory_hole;
        // for each row, the corresponding option of the memory hole
        std::vector<std::vector<uint64_t>> row_memory_option;
            


    private:

        /**
         * Build the state space:
         * - compute total number of states (@num_states)
         * - associate prototype states with their duplicates (@prototype_duplicates)
         * - for each state, remember its prototype (@state_prototype)
         * - for each state, remember its memory (@state_memory)
         */ 
        void buildStateSpace();
        void buildTransitionMatrixSpurious();

        /** Madp to Storm state map. */
        std::map<MadpState, uint_fast64_t> madp_to_storm_states;
        /** Storm to Madp state map. */
        std::vector<MadpState> storm_to_madp_states;

        void collectActions(DecPOMDPDiscrete *model);
        void collectObservations(DecPOMDPDiscrete *model);
        
        bool haveMadpState(MadpState madp_state);
        /**
         * TODO
         */
        uint_fast64_t mapMadpState(MadpState madp_state);

        uint_fast64_t freshJointAction(std::string action_label);
        uint_fast64_t freshJointObservation(std::string observation_label);
        /**
         * Add new state having fresh observation with its self-loop denoted
         * by a fresh joint action with zero reward.
         * @return index of the created state
         */
        uint_fast64_t freshSink(std::string label);

        storm::models::sparse::StateLabeling constructStateLabeling();
        storm::models::sparse::ChoiceLabeling constructChoiceLabeling();
        storm::storage::SparseMatrix<double> constructTransitionMatrix();
        storm::models::sparse::StandardRewardModel<double> constructRewardModel();
        std::vector<uint32_t> constructObservabilityClasses();

        storm::models::sparse::StateLabeling constructQuotientStateLabeling();
        storm::models::sparse::ChoiceLabeling constructQuotientChoiceLabeling();
        storm::storage::SparseMatrix<double> constructQuotientTransitionMatrix();
        storm::models::sparse::StandardRewardModel<double> constructQuotientRewardModel();

        void resetDesignSpace();
        void buildDesignSpaceSpurious(); 

        // for each prototype state contains a list of its duplicates (including itself)
        std::vector<std::vector<uint64_t>> prototype_duplicates;

        // row groups of the resulting transition matrix
        std::vector<uint64_t> row_groups;
        // for each row contains index of the prototype row
        std::vector<uint64_t> row_prototype;
        // for each row contains a memory update associated with it 
        std::vector<uint64_t> row_memory;
        //number of rows of the quotient mdp
        uint_fast64_t num_quotient_rows;
        
        std::vector<std::vector<uint_fast64_t>> nr_agent_actions_at_observation;
        
    };

    
    /**
     * Parse MADP file and convert transition matrix as well as
     * probabilistic observations of the resulting dec-POMDP to a
     * Storm-friendly representation.
     * @return NULL on parsing error
     */
     std::unique_ptr<DecPomdp> parseDecPomdp(std::string filename);

} // namespace synthesis

