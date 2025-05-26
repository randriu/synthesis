#pragma once

#include "src/synthesis/translation/ItemKeyTranslator.h"

#include <storm/adapters/RationalNumberAdapter.h>
#include <storm/models/sparse/Model.h>
#include <storm/models/sparse/Mdp.h>
#include <storm/storage/BitVector.h>


namespace synthesis {
    
    template<typename ValueType>
    storm::models::sparse::Mdp<ValueType> constructUnfoldedModel(
        storm::models::sparse::Mdp<ValueType> const& mdp,
        uint64_t memory_size
    );
}