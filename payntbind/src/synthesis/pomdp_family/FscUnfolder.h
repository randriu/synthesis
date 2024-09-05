#pragma once

#include "src/synthesis/translation/ItemKeyTranslator.h"

#include <storm/adapters/RationalNumberAdapter.h>
#include <storm/models/sparse/Model.h>
#include <storm/models/sparse/Mdp.h>
#include <storm/storage/BitVector.h>


namespace synthesis {
    
    
    template<typename ValueType>
    class FscUnfolder {

    public:

        FscUnfolder(
            storm::models::sparse::Model<ValueType> const& quotient,
            std::vector<uint32_t> const& state_to_obs_class,
            uint64_t num_actions,
            std::vector<uint64_t> const& choice_to_action
        );

        /**
         * Create a product of the quotient POMDP and the given FSC.
         * @param action_function for each node in the FSC and for each observation class, a dictionary containing
         *  entries (action,probability)
         * @param action_function for each node in the FSC and for each (posterior) observation class, a dictionary
         *  containing entries (memory,probability)
         */
        void applyFsc(
            std::vector<std::vector<std::map<uint64_t,double>>> action_function,
            std::vector<std::vector<std::map<uint64_t,double>>> update_function
        );

        /** The constructed product with an FSC. */
        std::shared_ptr<storm::models::sparse::Mdp<ValueType>> product;
        /** For each choice of the product MDP, the original choice. */
        std::vector<uint64_t> product_choice_to_choice;
        /** For each state of the product MDP, the original state. */
        std::vector<uint64_t> product_state_to_state;
        /** For each state of the product MDP, the correponding state-memory-action-transitioned tuple. */
        std::vector<std::pair<uint64_t,std::tuple<uint64_t,uint64_t,bool>>> product_state_to_state_memory_action_transitioned;


    private:
        
        /** The quotient model. */
        storm::models::sparse::Model<ValueType> const& quotient;
        /** For each state of the quotient, its observation class. */
        std::vector<uint32_t> state_to_obs_class;
        /** Overall number of actions. */
        uint64_t num_actions;
        /** For each choice of the quotient, the corresponding action. */
        std::vector<uint64_t> choice_to_action;
        /** For each state-action pair, a list of choices that implement this action. */
        std::vector<std::vector<std::set<uint64_t>>> state_action_choices;

        uint64_t invalidAction();
        uint64_t invalidChoice();

        /**
         * Each state is a tuple (s,n,act,tr) with the following semantics:
         * - from state (s,n,-,-), an action act is selected according to gamma(n,O(s)), transitioning to (s,n,act,-)
         * - from state (s,n,act,-), a variant of action act is executed, transitioning to (s',n,-,+)
         * - from state (s',n,-,+), a memory update n' is selected according delta(n,O(s')), transitioning to (s',n',-,-)
         **/
        ItemKeyTranslator<std::tuple<uint64_t,uint64_t,bool>> state_translator;
        uint64_t translateInitialState();
        uint64_t numberOfTranslatedStates();
        uint64_t numberOfTranslatedChoices();

        void buildStateSpace(
            std::vector<std::vector<std::map<uint64_t,double>>> action_function,
            std::vector<std::vector<std::map<uint64_t,double>>> update_function
        );
        storm::storage::SparseMatrix<ValueType> buildTransitionMatrix(
            std::vector<std::vector<std::map<uint64_t,double>>> action_function,
            std::vector<std::vector<std::map<uint64_t,double>>> update_function
        );

        void clearMemory();

    };
}