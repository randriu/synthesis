#pragma once

#include "madp/src/base/POMDPDiscrete.h"
#include "madp/src/base/DecPOMDPDiscrete.h"

#include <storm/adapters/RationalNumberAdapter.h>
#include <storm/models/sparse/Mdp.h>
#include <storm/models/sparse/Pomdp.h>
#include <storm/models/sparse/StandardRewardModel.h>

#include <string>

namespace synthesis {

    using MadpState = std::pair<uint64_t,uint64_t>;   // state + observation
    using MadpRow = std::vector<std::pair<MadpState,double>>;
    using StormRow = std::vector<std::pair<uint64_t,double>>;

    
    class DecPomdp {

    public:

        DecPomdp(DecPOMDPDiscrete *model);

        /** Number of agents. */
        uint64_t num_agents;
        
        /** For each agent, a list of its action labels. */
        std::vector<std::vector<std::string>> agent_action_labels;
        /** A list of tuples of actions. */
        std::vector<std::vector<uint64_t>> joint_actions;

        /** For each agent, a list of its observation labels. */
        std::vector<std::vector<std::string>> agent_observation_labels;
        /** A list of tuples of observations. */
        std::vector<std::vector<uint64_t>> joint_observations;

        /** The unique initial state. */
        uint64_t initial_state;
        /** Storm-esque transition matrix: for each state, a row group. */
        std::vector<std::vector<StormRow>> transition_matrix;
        /** For each state (row group), a mapping of a row to a joint action. */
        std::vector<std::vector<uint64_t>> row_joint_action;
        /** State to joint observation map. */
        std::vector<uint64_t> state_joint_observation;
        /** For each state (row group), a mapping of a row to its reward. */
        std::vector<std::vector<double>> row_reward;

        /** For each agent and each of its observations contains number of allowed actions */
        std::vector<std::vector<uint64_t>> num_agent_actions_at_observation;
        
        
        
        uint64_t agent_num_actions(uint64_t agent) {
            return this->agent_action_labels[agent].size();
        }
        uint64_t num_joint_actions() {
            return this->joint_actions.size();
        }
        uint64_t agent_num_observations(uint64_t agent) {
            return this->agent_observation_labels[agent].size();
        }
        uint64_t num_joint_observations() {
            return this->joint_observations.size();
        }

        uint64_t num_states() {
            return this->storm_to_madp_states.size();
        }

        uint64_t num_rows();

        /** Retrieve the underlying MDP. */
        std::shared_ptr<storm::models::sparse::Mdp<double>> constructMdp();

        std::shared_ptr<storm::models::sparse::Mdp<double>> constructQuotientMdp(); // TODO make this consistent with how POMDPs are treated
        /** Retrieve the underlying POMDP. */
        std::shared_ptr<storm::models::sparse::Pomdp<double>> constructPomdp();

        /** If true, the rewards are interpreted as costs. */
        bool reward_minimizing;
        /** Label associated with the reward model. */
        std::string reward_model_name = "reward";
        /** Label associated with the constraint reward model. */
        std::string constraint_reward_model_name = "constraint";

        double discount_factor;

        void applyDiscountFactorTransformation();

        void set_constraint_bound(double bound) {
            this->constraint_bound = bound;
        };

        /** Label for the state that simulates initial distribution. */
        std::string init_label = "init";
        /** Label for the states in the initial distribution. */
        std::string no_obs_label = "__no_obs__";

        /** Whether discounting transformation took place. */
        bool discounted = false;
        /** Index of the sink state. */
        uint64_t discount_sink_state;
        /** Label associated with the sink. */
        std::string discount_sink_label = "discount_sink";

        /** For each agent and each observation contains the number of allocated memory states (initially 1) */
        std::vector<std::vector<uint64_t>> agent_observation_memory_size;

        /** Set memory size for selected agent and selected observation */
        void setAgentObservationMemorySize(uint64_t agent, uint64_t obs, uint64_t memory_size);
        /** Set memory size to all observations */
        void setGlobalMemorySize(uint64_t memory_size);

        /** For each state contains its prototype state (reverse of prototype_duplicates) */
        std::vector<uint64_t> state_prototype;
        /** For each state and agent contains its memory index */
        std::vector<std::vector<uint64_t>> state_agent_memory;

        /** Number of states of quotient mdp. */
        uint64_t num_quotient_states;

        /** Number of rows of the quotient mdp */
        uint64_t num_quotient_rows;

        /** For each observation, a list of successor observations */
        std::vector<std::vector<uint64_t>> observation_successors;

        /** For each agent and each of its observations, a list of successor observations */
        std::vector<std::vector<std::vector<uint64_t>>> agent_observation_successors;

        /** For each joint observation contains the maximum memory size of a destination
            across all rows of a prototype state having this observation */
        std::vector<uint64_t> max_successor_memory_size;

        /** Total number of holes */
        uint64_t num_holes;
        /** For each observation, a list of action holes */
        std::vector<std::vector<std::vector<uint64_t>>> agent_action_holes;
        /** For each observation, a list of memory holes */
        std::vector<std::vector<std::vector<uint64_t>>> agent_memory_holes;

        /** For each hole, its size */
        std::vector<uint64_t> hole_options;

        /** For each agent and each row, the corresponding action hole */
        std::vector<std::vector<uint64_t>> agent_row_action_hole;
        /** For each agent and each row, the corresponding option of the action hole */
        std::vector<std::vector<uint64_t>> agent_row_action_option;
        /** For each agent and each row, the corresponding memory hole */
        std::vector<std::vector<uint64_t>> agent_row_memory_hole;
        /** For each agent and each row, the corresponding option of the memory hole */
        std::vector<std::vector<uint64_t>> agent_row_memory_option;

        /** For each agent observation contains the maximum memory size of a destination
            across all rows of a prototype state having this observation */
        std::vector<std::vector<uint64_t>> agent_max_successor_memory_size;

        /** For each combination of memory and joint observation, the coresponding unique number */
        std::vector<std::vector<uint64_t>> memory_joint_observation;
        /** For each action, set of memory_joint_observation */
        std::vector<uint64_t> action_to_memory_joint_observation;
        /** For each state, set of memory_joint_observation */
        std::vector<uint64_t> state_to_memory_joint_observation;


    private:

        /**
         * Build the state space:
         * - compute total number of states (@num_states)
         * - associate prototype states with their duplicates (@prototype_duplicates)
         * - for each state, remember its prototype (@state_prototype)
         * - for each state and for each agent remember its memory (@state_memory)
         */
        void buildStateSpace();
        void buildTransitionMatrixSpurious();

        /** Madp to Storm state map. */
        std::map<MadpState, uint64_t> madp_to_storm_states;
        /** Storm to Madp state map. */
        std::vector<MadpState> storm_to_madp_states;

        // bound for creating CPOMDP
        double constraint_bound = std::numeric_limits<double>::infinity();

        void collectActions(DecPOMDPDiscrete *model);
        void collectObservations(DecPOMDPDiscrete *model);

        /** Count succesors for every observation and get prototype row index for every row index */
        void countSuccessors();
        /** for each agent and each observation compute the number of available actions */
        void computeAvailableActions();
        
        bool haveMadpState(MadpState madp_state);
        /**
         * TODO
         */
        uint64_t mapMadpState(MadpState madp_state);

        uint64_t freshJointAction(std::string action_label);
        uint64_t freshJointObservation(std::string observation_label);
        /**
         * Add new state having fresh observation with its self-loop denoted
         * by a fresh joint action with zero reward.
         * @return index of the created state
         */
        uint64_t freshSink(std::string label);

        storm::models::sparse::StateLabeling constructStateLabeling();
        storm::models::sparse::ChoiceLabeling constructChoiceLabeling();
        storm::storage::SparseMatrix<double> constructTransitionMatrix();
        storm::models::sparse::StandardRewardModel<double> constructRewardModel();
        storm::models::sparse::StandardRewardModel<double> constructConstraintRewardModel();
        std::vector<uint32_t> constructObservabilityClasses();

        storm::models::sparse::StateLabeling constructQuotientStateLabeling();
        storm::models::sparse::ChoiceLabeling constructQuotientChoiceLabeling();
        storm::storage::SparseMatrix<double> constructQuotientTransitionMatrix();
        storm::models::sparse::StandardRewardModel<double> constructQuotientRewardModel();

        /** Compute the combined memory for joint observations based on 'agent_observation_memory_size' */
        void computeJointObservationMemorySize();
        /** For each joint observation contains the number of combined memory nodes */
        std::vector<uint64_t> joint_observation_memory_size;

        void resetDesignSpace();
        void buildDesignSpaceSpurious();

        /** For each prototype state contains a list of its duplicates (including itself) */
        std::vector<std::map<std::vector<uint64_t>,uint64_t>> prototype_duplicates;

        /** Row groups of the resulting transition matrix */
        std::vector<uint64_t> row_groups;
        /** For each row contains index of the prototype row in the state it belongs to */
        std::vector<uint64_t> row_prototype_state;
        /** For each row contains index of the prototype row */
        std::vector<uint64_t> row_prototype;
        /** For each row and each agent contains a memory update associated with it */
        std::vector<std::vector<uint64_t>> row_agent_memory;
        /** For each agent and each prototype row, the index of agent's action */
        std::vector<std::vector<uint64_t>> agent_prototype_row_index;
        
    };

    
    /**
     * Parse MADP file and convert transition matrix as well as
     * probabilistic observations of the resulting dec-POMDP to a
     * Storm-friendly representation.
     * @return NULL on parsing error
     */
     std::unique_ptr<DecPomdp> parseDecPomdp(std::string filename);

} // namespace synthesis

