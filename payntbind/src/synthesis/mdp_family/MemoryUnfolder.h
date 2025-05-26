#pragma once

#include "src/synthesis/translation/ItemKeyTranslator.h"

#include <storm/adapters/RationalNumberAdapter.h>
#include <storm/models/sparse/Model.h>
#include <storm/models/sparse/Mdp.h>
#include <storm/storage/BitVector.h>


namespace synthesis {

    template<typename ValueType>
    class MemoryUnfolder {
    public:

        MemoryUnfolder(storm::models::sparse::Mdp<ValueType> const& mdp);

        std::shared_ptr<storm::models::sparse::Mdp<ValueType>> constructUnfoldedModel(
            uint64_t memory_size
        );

        // unfolded MDP
        std::shared_ptr<storm::models::sparse::Mdp<ValueType>> unfoldedMdp;

        // maps new choices to original choices
        std::vector<uint64_t> choiceMap;

        // for each state contains its prototype state
        std::vector<uint64_t> statePrototype;
        // for each state contains its memory index
        std::vector<uint64_t> stateMemory;


    private:

        // original MDP
        storm::models::sparse::Mdp<ValueType> const& mdp;

    };
    
}