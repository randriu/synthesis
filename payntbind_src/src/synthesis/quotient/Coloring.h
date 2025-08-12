#pragma once

#include "src/synthesis/quotient/Family.h"

#include <storm/storage/BitVector.h>

#include <cstdint>
#include <vector>
#include <memory>

namespace synthesis {

using BitVector = storm::storage::BitVector;


class Coloring {
public:
    
    Coloring(
        Family const& family, std::vector<uint64_t> const& row_groups,
        std::vector<std::vector<std::pair<uint64_t,uint64_t>>> choice_to_assignment
    );

    /** Get choice-to-assignment mapping. */
    std::vector<std::vector<std::pair<uint64_t,uint64_t>>> const& getChoiceToAssignment() const;
    /** Get a mapping from states to holes involved in its choices. */
    std::vector<BitVector> const& getStateToHoles() const;
    
    /** Get a mask of choices compatible with the family. */
    BitVector selectCompatibleChoices(Family const& subfamily) const;
    /** For each hole, collect options (colors) involved in any of the given choices. */
    std::vector<std::vector<uint64_t>> collectHoleOptions(BitVector const& choices) const;
    
protected:

    /** Reference to the unrefined family. */
    Family family;
    /** For each choice, a list of hole-option pairs (colors). */
    const std::vector<std::vector<std::pair<uint64_t,uint64_t>>> choice_to_assignment;

    /** Number of choices in the quotient. */
    const uint64_t numChoices() const;
    
    /** For each state, identification of holes associated with its choices. */
    std::vector<BitVector> choice_to_holes;
    /** For each state, identification of holes associated with its choices. */
    std::vector<BitVector> state_to_holes;

    /** Choices not labeled by any hole. */
    BitVector uncolored_choices;
    /** Choices labeled by some hole. */
    BitVector colored_choices;

    /** For each hole, collect options (colors) involved in any of the given choices. */
    std::vector<BitVector> collectHoleOptionsMask(BitVector const& choices) const;
};

}