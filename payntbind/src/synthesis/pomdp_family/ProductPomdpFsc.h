#pragma once

#include "src/synthesis/translation/ItemKeyTranslator.h"

#include <storm/models/sparse/Model.h>
#include <storm/models/sparse/Mdp.h>
#include <storm/storage/BitVector.h>


namespace synthesis {
    
    
    template<typename ValueType>
    class ProductPomdpFsc {

    public:

        ProductPomdpFsc(
            storm::models::sparse::Model<ValueType> const& quotient,
            std::vector<uint32_t> state_to_obs_class,
            uint64_t num_actions,
            std::vector<uint64_t> choice_to_action
        );

        /**
         * Create a product of the quotient POMDP and the given FSC.
         * @param action_function for each node in the FSC and for each observation class, an index of the choice
         * @param action_function for each node in the FSC and for each observation class, a memory update
         */
        void applyFsc(
            std::vector<std::vector<uint64_t>> action_function,
            std::vector<std::vector<uint64_t>> update_function
        );

        /** The constructed product with an FSC. */
        std::shared_ptr<storm::models::sparse::Mdp<ValueType>> product;
        /** For each choice of the product MDP, the original choice. */
        std::vector<uint64_t> product_choice_to_choice;
        /** For each state of the product MDP, the original state. */
        std::vector<uint64_t> product_state_to_state;


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

        /** For each state and memory value, the state in the product. */
        ItemKeyTranslator<uint64_t> state_translator;
        uint64_t translateInitialState();

        uint64_t numberOfTranslatedStates();  
        uint64_t numberOfTranslatedChoices();

        
        void buildStateSpace(
            std::vector<std::vector<uint64_t>> action_function,
            std::vector<std::vector<uint64_t>> update_function
        );
        storm::storage::SparseMatrix<ValueType> buildTransitionMatrix(
            std::vector<std::vector<uint64_t>> action_function,
            std::vector<std::vector<uint64_t>> update_function
        );
        

        void clearMemory();

    };
}