#pragma once

/* 
 * code in this file was taken from TEMPEST (https://github.com/PrangerStefan/TempestSynthesis)
 */

#include <vector>
#include <storm/storage/Scheduler.h>

namespace synthesis {
    template<typename ValueType>
    struct SMGSparseModelCheckingHelperReturnType {

        SMGSparseModelCheckingHelperReturnType(SMGSparseModelCheckingHelperReturnType const&) = delete;
        SMGSparseModelCheckingHelperReturnType(SMGSparseModelCheckingHelperReturnType&&) = default;

        SMGSparseModelCheckingHelperReturnType(std::vector<ValueType>&& values, storm::storage::BitVector&& relevantStates, std::unique_ptr<storm::storage::Scheduler<ValueType>>&& scheduler, std::vector<ValueType>&& choiceValues) : values(std::move(values)), relevantStates(relevantStates), scheduler(std::move(scheduler)), choiceValues(std::move(choiceValues)) {
            // Intentionally left empty.
        }

        virtual ~SMGSparseModelCheckingHelperReturnType() {
            // Intentionally left empty.
        }

        // The values computed for the states.
        std::vector<ValueType> values;

        // The relevant states for which choice values have been computed.
        storm::storage::BitVector relevantStates;

        // A scheduler, if it was computed.
        std::unique_ptr<storm::storage::Scheduler<ValueType>> scheduler;

        // The values computed for the available choices.
        std::vector<ValueType> choiceValues;
    };
}
