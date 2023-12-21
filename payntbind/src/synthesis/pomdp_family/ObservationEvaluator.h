#pragma once

#include "storm/storage/prism/Program.h"
#include "storm/models/sparse/Model.h"
#include "storm/models/sparse/Mdp.h"
#include "storm/models/sparse/Pomdp.h"
#include "storm/storage/BitVector.h"

namespace synthesis {

    template<typename ValueType>
    class ObservationEvaluator {

    public:

        ObservationEvaluator(
            storm::prism::Program & prism,
            storm::models::sparse::Model<ValueType> const& model
        );

        /** Number of observation expressions. */
        uint32_t num_obs_expressions;
        /** For each observation expression its label. */
        std::vector<std::string> obs_expr_label;
        /** For each observation expression whether it is boolean. */
        std::vector<bool> obs_expr_is_boolean;
        
        /** Number of observation classes. */
        uint32_t num_obs_classes = 0;
        /** For each state its observation class. */
        std::vector<uint32_t> state_to_obs_class;

        /** Get the value of the observation expression in the given observation class. */
        uint32_t observationClassValue(uint32_t obs_class, uint32_t obs_expr);

        /**
         * Create a sub-POMDP from the given sub-MDP by associating its states with observations.
         * @param mdp a sub-MDP
         * @param state_sub_to_full for each state of the sub-MDP the index of the original state
         */
        std::shared_ptr<storm::models::sparse::Pomdp<ValueType>> addObservationsToSubMdp(
            storm::models::sparse::Mdp<ValueType> const& sub_mdp,
            std::vector<uint64_t> state_sub_to_full
        );

        // TODO observation valuations

    private:
        /** Bitwidth of observation expression value size. */
        static const int OBS_EXPR_VALUE_SIZE = 64;
        /** Mapping of observation expressions evaluation to a unique observation class. */
        std::map<storm::storage::BitVector,uint32_t> obs_evaluation_to_class;
        /** Mapping of observation class to observation expressions evaluation. */
        std::vector<storm::storage::BitVector> obs_class_to_evaluation;
        
    };

}