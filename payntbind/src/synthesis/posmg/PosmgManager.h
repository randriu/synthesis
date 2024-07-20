#pragma once

#include "Posmg.h"

namespace synthesis {

class PosmgManager {
    public:

        PosmgManager(Posmg const& posmg);

        /**
         * @brief unfold memory
         */
        std::shared_ptr<storm::models::sparse::Mdp<double>> constructMdp();

        std::vector<u_int64_t> getObservationMapping();

        void setObservationMemorySize(uint64_t observation, uint64_t memorySize);

    private:

        /**
         * @brief Fill the optPlayerObservationMap property
         */
        void calculateObservationMap();

        /**
         * @brief For each optimizing player observation calculate set of all succesor states
         */
        void calculateObservationSuccesors();

        /**
         * @brief For each optimizing player observation calculate number of available actions.
         */
        void calculateObservationActions();


        /**
         * @brief Calculate total number of states after unfolding
         */
        void buildStateSpace();

        /**
         * @brief Prepare properties for constructTransitionMatrix
         */
        void buildTransitionMatrixSpurious();

        /**
         * @brief Translate prototype state to new state based on memory index
         *
         * @param prototype Prototype state
         * @param memory Memory index of the new state
         * @return uint64_t The new state
         */
        uint64_t translateState(uint64_t prototype, uint64_t memory);

        storm::storage::SparseMatrix<double> constructTransitionMatrix();

        storm::models::sparse::StateLabeling constructStateLabeling();

        void resetDesignSpace();

        void buildDesignSpaceSpurious();


        /**
         * @brief Determine if state belonsgs to optimizing player (specified by optimizingPlayer property).
         *
         * @param state State to determine
         * @return true state belongs to optimizing player
         * @return false state doesn't belong to optimizing player
         */
        bool isOptPlayerState(uint64_t state);

        /**
         * @brief Return true if element is in vector, else false.
         *
         * @param v The vector to search in.
         * @param elem The element to search for.
         * @return true if elem is in v
         * @return false if elem is not in v
         */
        bool contains(std::vector<uint64_t> v, uint64_t elem);

        /** original POSMG */
        Posmg const& posmg;

        /** For now, optimizing player is hard coded to 0 */
        uint64_t optimizingPlayer = 0;

        /** Mapping from optimizing player observations (index) to global observation (value)
         * @details Because we solve games, where one player (optimizing player) has partial
         * observability and the other player has complete observability, we keep a vector of
         * optimizing player's observations, which also serves as a mapping.
         */
        std::vector<u_int64_t> optPlayerObservationMap;

        /** Number of states in unfolded smg */
        uint64_t stateCount;

        // For each optimizing player observation contains the number of allocated memory states (initially 1)
        std::vector<uint64_t> optPlayerObservationMemorySize;

        // For each prototype state contains a list of its duplicates (including itself)
        std::vector<std::vector<uint64_t>> prototypeDuplicates;

        // For each state contains number of his duplicates (including itself)
        std::vector<uint64_t> stateDuplicateCount;

        // For each optimizing player observation contains maximum number of duplicates from all succesors
        std::map<uint64_t, uint64_t> maxSuccesorDuplicateCount;

        // For each state contains its prototype state (reverse of prototypeDuplicates)
        std::vector<uint64_t> statePrototype;

        // For each state contains its memory index
        std::vector<uint64_t> stateMemory;

        // For each optimizing player observation contains set of succesor states
        std::map<uint64_t, std::set<uint64_t>> succesors;

        // For each optimizing player observation contains number of available actions
        std::unordered_map<uint64_t, uint64_t> optPlayerObservationActions;

        // Number of rows in unfolded MDP
        uint64_t rowCount;

        // Row groups of the resulting transition matrix
        std::vector<uint64_t> rowGroups;

        // For each row contains index of the prototype row
        std::vector<uint64_t> rowPrototype;

        // For each row contains a memory update associated with it
        std::vector<uint64_t> rowMemory;

        // Unfolded mdp created from posmg
        std::shared_ptr<storm::models::sparse::Mdp<double>> mdp;


}; // class PosmgManager

} // namespace synthesis