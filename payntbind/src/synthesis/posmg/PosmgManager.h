#pragma once

#include "Posmg.h"
#include <set>

namespace synthesis {

template<class ValueType>
class PosmgManager {
    public:

        PosmgManager(Posmg<ValueType> const& posmg, uint64_t optimizingPlayer);

        /**
         * @brief unfold memory
         */
        std::shared_ptr<storm::models::sparse::Mdp<double>> constructMdp();

        std::vector<uint64_t> getObservationMapping();

        void setObservationMemorySize(uint64_t observation, uint64_t memorySize);

        /**
         * @brief Construct and return the state player indications of quotient mdp
         *
         * @return std::vector<uint64_t>
         */
        std::vector<uint64_t> getStatePlayerIndications();

        /**
         * @brief For quotient state return number of available actions
         *
         * @param state Quotient state
         * @return uint64_t
         */
        uint64_t getActionCount(uint64_t state);


        // For each state contains its prototype state (reverse of prototypeDuplicates)
        std::vector<uint64_t> statePrototype;

        // For each state contains its memory index
        std::vector<uint64_t> stateMemory;

        // For each optimizing player observation contains the number of allocated memory states (initially 1)
        //std::vector<uint64_t> optPlayerObservationMemorySize;
        std::unordered_map<uint32_t, uint64_t> optPlayerObservationMemorySize;

        // For each optimizing player observation contains set of succesor states
        std::unordered_map<uint32_t, std::set<uint64_t>> succesors;

        // For each optimizing player observation contains maximum number of duplicates from all succesors
        std::unordered_map<uint32_t, uint64_t> maxSuccesorDuplicateCount;

        // For each optimizing player observation contains number of available actions
        std::unordered_map<uint32_t, uint64_t> optPlayerObservationActions;

        // For each prototype state number of available actions
        std::vector<uint64_t> prototypeActionCount;

        // Total number of holes
        uint64_t holeCount;

        // For each optimizing player observation a vector of action holes
        std::unordered_map<uint32_t, std::vector<uint64_t>> actionHoles;

        // For each non optimizin player state an action hole
        std::unordered_map<uint64_t, uint64_t> nonOptActionHoles;

        // For each optimizing player observation a vector of memory holes
        std::unordered_map<uint32_t, std::vector<uint64_t>> memoryHoles;

        // For each hole, its size
        std::vector<uint64_t> holeOptionCount;

        // For each row contains the corresponding action hole
        std::vector<uint64_t> rowActionHole;
        //std::unordered_map<uint64_t, uint64_t> rowActionHole;

        // For eac row contains the corresponding option of action hole
        std::vector<uint64_t> rowActionOption;
        //std::unordered_map<uint64_t, uint64_t> rowActionOption;

        // For each row contains the correspodning memory hole
        std::vector<uint64_t> rowMemoryHole;
        //std::unordered_map<uint64_t, uint64_t> rowMemoryHole;

        // For each row contains the corresponding option of memory hole
        std::vector<uint64_t> rowMemoryOption;
        //std::unordered_map<uint64_t, uint64_t> rowMemoryOption;

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
         * @brief For each prototype state calculate number of available actions
         */
        void calculatePrototypeActionCount();

        /**
         * @brief For each optimizing player observation calculate number of available actions.
         */
        void calculateObservationActions();

        /**
         * @brief For each prototype row store its index within its row group
         */
        void calculatePrototypeRowIndex();


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
         * @brief Determine if prototype state belongs to optimizing player (specified by optimizingPlayer property).
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
        Posmg<ValueType> const& posmg;

        /** index of optimizing player */
        uint64_t optimizingPlayer;

        /** Mapping from optimizing player observations (index) to global observation (value)
         * @details Because we solve games, where one player (optimizing player) has partial
         * observability and the other player has complete observability, we keep a vector of
         * optimizing player's observations, which also serves as a mapping.
         */
        std::vector<uint64_t> optPlayerObservationMap;

        // For each row in original posmg contains its index withing its row group
        std::vector<uint64_t> prototypeRowIndex;

        /** Number of states in unfolded smg */
        uint64_t stateCount;

        // For each prototype state contains a list of its duplicates (including itself)
        std::vector<std::vector<uint64_t>> prototypeDuplicates;

        // For each state contains number of his duplicates (including itself)
        std::vector<uint64_t> stateDuplicateCount;

        // Number of rows in unfolded MDP
        uint64_t rowCount;

        // Row groups of the resulting transition matrix
        std::vector<uint64_t> rowGroups;

        // For each row contains index of the prototype row
        std::vector<uint64_t> rowPrototype;

        // For each row contains a memory update associated with it
        std::vector<uint64_t> rowMemory;

        // Unfolded mdp created from posmg
        std::shared_ptr<storm::models::sparse::Mdp<ValueType>> mdp;


}; // class PosmgManager

} // namespace synthesis