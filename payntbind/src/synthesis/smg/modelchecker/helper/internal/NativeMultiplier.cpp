/* 
 * code in this file was taken from TEMPEST (https://github.com/PrangerStefan/TempestSynthesis)
 */

#include "NativeMultiplier.h"

#include <storm/settings/modules/CoreSettings.h>
#include <storm/storage/SparseMatrix.h>
#include <storm/utility/macros.h>

namespace synthesis {

    std::vector<storm::storage::sparse::state_type> getMatrixRowIndications(storm::storage::SparseMatrix<double> const& matrix) {
        std::vector<storm::storage::sparse::state_type> rowIndications;
        rowIndications.push_back(0);
        storm::storage::sparse::state_type indicationCounter = 0;
        for (storm::storage::sparse::state_type row = 0; row < matrix.getRowCount(); row++) {
            for (auto const &entry: matrix.getRow(row)) {
                indicationCounter++;
            }
            rowIndications.push_back(indicationCounter);
        }

        return rowIndications;
    }

    // multiplyAndReduceBackward
    template<typename Compare>
    void multiplyAndReduceBackward(storm::storage::SparseMatrix<double> const& matrix, std::vector<uint64_t> const& rowGroupIndices, std::vector<double> const& vector, std::vector<double> const* summand, std::vector<double>& result, std::vector<uint_fast64_t>* choices, storm::storage::BitVector const* dirOverride) {
        Compare compare;

        // Using SynthesisMatrix class as I can't modify the SparseMatrix class to access private member!!!
        // synthesis::SynthesisMatrix tempMatrix(matrix);

        auto rowIndications = synthesis::getMatrixRowIndications(matrix);

        auto elementIt = matrix.end() - 1;
        auto rowGroupIt = rowGroupIndices.end() - 2;
        auto rowIt = rowIndications.end() - 2;
        typename std::vector<double>::const_iterator summandIt;
        if (summand) {
            summandIt = summand->end() - 1;
        }
        typename std::vector<uint_fast64_t>::iterator choiceIt;
        if (choices) {
            choiceIt = choices->end() - 1;
        }

        // Variables for correctly tracking choices (only update if new choice is strictly better).
        double oldSelectedChoiceValue;
        uint64_t selectedChoice;

        uint64_t currentRow = matrix.getRowCount() - 1;
        uint64_t currentRowGroup = matrix.getRowGroupCount() - 2;
        for (auto resultIt = result.end() - 1, resultIte = result.begin() - 1; resultIt != resultIte; --resultIt, --choiceIt, --rowGroupIt, --currentRowGroup) {
            double currentValue = storm::utility::zero<double>();

            // Only multiply and reduce if there is at least one row in the group.
            if (*rowGroupIt < *(rowGroupIt + 1)) {
                if (summand) {
                    currentValue = *summandIt;
                    --summandIt;
                }

                for (auto elementIte = matrix.begin() + *rowIt - 1; elementIt != elementIte; --elementIt) {
                    currentValue += elementIt->getValue() * vector[elementIt->getColumn()];
                }
                if (choices) {
                    selectedChoice = currentRow - *rowGroupIt;
                    if (*choiceIt == selectedChoice) {
                        oldSelectedChoiceValue = currentValue;
                    }
                }
                --rowIt;
                --currentRow;

                for (uint64_t i = *rowGroupIt + 1, end = *(rowGroupIt + 1); i < end; --rowIt, --currentRow, ++i, --summandIt) {
                    double newValue = summand ? *summandIt : storm::utility::zero<double>();
                    for (auto elementIte = matrix.begin() + *rowIt - 1; elementIt != elementIte; --elementIt) {
                        newValue += elementIt->getValue() * vector[elementIt->getColumn()];
                    }

                    if (choices && currentRow == *choiceIt + *rowGroupIt) {
                        oldSelectedChoiceValue = newValue;
                    }

                    if(true) {
                        if (dirOverride->get(currentRowGroup) ? compare(currentValue, newValue) : compare(newValue, currentValue)) {
                            currentValue = newValue;
                            if (choices) {
                                selectedChoice = currentRow - *rowGroupIt;
                            }
                        }
                    } else {
                        if (compare(newValue, currentValue)) {
                            currentValue = newValue;
                            if (choices) {
                                selectedChoice = currentRow - *rowGroupIt;
                            }
                        }
                    }
                }

                // Finally write value to target vector.
                *resultIt = currentValue;
                if(true) {
                    if (choices && dirOverride->get(currentRowGroup) ? compare(oldSelectedChoiceValue, currentValue) : compare(currentValue, oldSelectedChoiceValue)) {
                        *choiceIt = selectedChoice;
                    }
                } else {
                    if (choices && compare(currentValue, oldSelectedChoiceValue)) {
                        *choiceIt = selectedChoice;
                    }
                }
            }
        }
    }

    void multiplyAndReduceBackward(storm::storage::SparseMatrix<double> const& matrix, storm::solver::OptimizationDirection const& dir, std::vector<uint64_t> const& rowGroupIndices, std::vector<double> const& vector, std::vector<double> const* summand, std::vector<double>& result, std::vector<uint_fast64_t>* choices, storm::storage::BitVector const* dirOverride) {
        if(dirOverride && !dirOverride->empty()) {
            if (dir == storm::OptimizationDirection::Minimize) {
                synthesis::multiplyAndReduceBackward<storm::utility::ElementLess<double>>(matrix, rowGroupIndices, vector, summand, result, choices, dirOverride);
            } else {
                synthesis::multiplyAndReduceBackward<storm::utility::ElementGreater<double>>(matrix, rowGroupIndices, vector, summand, result, choices, dirOverride);
            }
        } else {
            matrix.multiplyAndReduceBackward(dir, rowGroupIndices, vector, summand, result, choices);
        }
    }


    // multiplyAndReduceForward
    template<typename Compare>
    void multiplyAndReduceForward(storm::storage::SparseMatrix<double> const& matrix, std::vector<uint64_t> const& rowGroupIndices, std::vector<double> const& vector, std::vector<double> const* summand, std::vector<double>& result, std::vector<uint_fast64_t>* choices, storm::storage::BitVector const* dirOverride) {
        Compare compare;

        // Using SynthesisMatrix class as I can't modify the SparseMatrix class to access private member rowIndications!!!
        // synthesis::SynthesisMatrix tempMatrix(matrix);

        auto rowIndications = synthesis::getMatrixRowIndications(matrix);

        auto elementIt = matrix.begin();
        auto rowGroupIt = rowGroupIndices.begin();
        auto rowIt = rowIndications.begin();
        typename std::vector<double>::const_iterator summandIt;
        if (summand) {
            summandIt = summand->begin();
        }
        typename std::vector<uint_fast64_t>::iterator choiceIt;
        if (choices) {
            choiceIt = choices->begin();
        }

        // Variables for correctly tracking choices (only update if new choice is strictly better).
        double oldSelectedChoiceValue;
        uint64_t selectedChoice;

        uint64_t currentRow = 0;
        uint64_t currentRowGroup = 0;
        for (auto resultIt = result.begin(), resultIte = result.end(); resultIt != resultIte; ++resultIt, ++choiceIt, ++rowGroupIt, ++currentRowGroup) {
            double currentValue = storm::utility::zero<double>();

            // Only multiply and reduce if there is at least one row in the group.
            if (*rowGroupIt < *(rowGroupIt + 1)) {
                if (summand) {
                    currentValue = *summandIt;
                    ++summandIt;
                }

                for (auto elementIte = matrix.begin() + *(rowIt + 1); elementIt != elementIte; ++elementIt) {
                    currentValue += elementIt->getValue() * vector[elementIt->getColumn()];
                }

                if (choices) {
                    selectedChoice = 0;
                    if (*choiceIt == 0) {
                        oldSelectedChoiceValue = currentValue;
                    }
                }

                ++rowIt;
                ++currentRow;

                for (; currentRow < *(rowGroupIt + 1); ++rowIt, ++currentRow) {
                    double newValue = summand ? *summandIt : storm::utility::zero<double>();
                    for (auto elementIte = matrix.begin() + *(rowIt + 1); elementIt != elementIte; ++elementIt) {
                        newValue += elementIt->getValue() * vector[elementIt->getColumn()];
                    }

                    if (choices && currentRow == *choiceIt + *rowGroupIt) {
                        oldSelectedChoiceValue = newValue;
                    }

                    if(true) {
                        if (dirOverride->get(currentRowGroup) ? compare(currentValue, newValue) : compare(newValue, currentValue)) {
                            currentValue = newValue;
                            if (choices) {
                                selectedChoice = currentRow - *rowGroupIt;
                            }
                        }
                    } else {
                        if (compare(newValue, currentValue)) {
                            currentValue = newValue;
                            if (choices) {
                                selectedChoice = currentRow - *rowGroupIt;
                            }
                        }
                    }
                    if (summand) {
                        ++summandIt;
                    }
                }

                // Finally write value to target vector.
                *resultIt = currentValue;
                if(true) {
                    if (choices && (dirOverride->get(currentRowGroup) ? compare(oldSelectedChoiceValue, currentValue) : compare(currentValue, oldSelectedChoiceValue))) {
                        *choiceIt = selectedChoice;
                    }
                } else {
                    if (choices && (compare(currentValue, oldSelectedChoiceValue))) {
                        *choiceIt = selectedChoice;
                    }
                }
            }
        }
    }

    void multiplyAndReduceForward(storm::storage::SparseMatrix<double> const& matrix, storm::solver::OptimizationDirection const& dir, std::vector<uint64_t> const& rowGroupIndices, std::vector<double> const& vector, std::vector<double> const* summand, std::vector<double>& result, std::vector<uint_fast64_t>* choices, storm::storage::BitVector const* dirOverride) {
        if(dirOverride && !dirOverride->empty()) {
            if (dir == storm::OptimizationDirection::Minimize) {
                synthesis::multiplyAndReduceForward<storm::utility::ElementLess<double>>(matrix, rowGroupIndices, vector, summand, result, choices, dirOverride);
            } else {
                synthesis::multiplyAndReduceForward<storm::utility::ElementGreater<double>>(matrix, rowGroupIndices, vector, summand, result, choices, dirOverride);
            }
        } else {
            matrix.multiplyAndReduceForward(dir, rowGroupIndices, vector, summand, result, choices);
        }
    }


    void multiplyAndReduce(storm::storage::SparseMatrix<double> const& matrix, storm::solver::OptimizationDirection const& dir, std::vector<uint64_t> const& rowGroupIndices, std::vector<double> const& vector, std::vector<double> const* summand, std::vector<double>& result, std::vector<uint_fast64_t>* choices, storm::storage::BitVector const* dirOverride) {

        // If the vector and the result are aliases, we need and temporary vector.
        std::vector<double>* target;
        std::vector<double> temporary;
        if (&vector == &result) {
            STORM_LOG_WARN("Vectors are aliased but are not allowed to be. Using temporary, which is potentially slow.");
            temporary = std::vector<double>(vector.size());
            target = &temporary;
        } else {
            target = &result;
        }
        synthesis::multiplyAndReduceForward(matrix, dir, rowGroupIndices, vector, summand, *target, choices, dirOverride);

        if (target == &temporary) {
            std::swap(temporary, result);
        }
    }



    template<typename ValueType>
    NativeMultiplier<ValueType>::NativeMultiplier(storm::storage::SparseMatrix<ValueType> const& matrix) : Multiplier<ValueType>(matrix) {
        // Intentionally left empty.
    }

    template<typename ValueType>
    bool NativeMultiplier<ValueType>::parallelize(storm::Environment const& env) const {
#ifdef STORM_HAVE_INTELTBB
        return storm::settings::getModule<storm::settings::modules::CoreSettings>().isUseIntelTbbSet();
#else
        return false;
#endif
    }

    template<typename ValueType>
    void NativeMultiplier<ValueType>::multiply(storm::Environment const& env, std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result) const {
        std::vector<ValueType>* target = &result;
        if (&x == &result) {
            if (this->cachedVector) {
                this->cachedVector->resize(x.size());
            } else {
                this->cachedVector = std::make_unique<std::vector<ValueType>>(x.size());
            }
            target = this->cachedVector.get();
        }
        if (parallelize(env)) {
            multAddParallel(x, b, *target);
        } else {
            multAdd(x, b, *target);
        }
        if (&x == &result) {
            std::swap(result, *this->cachedVector);
        }
    }

    template<typename ValueType>
    void NativeMultiplier<ValueType>::multiplyGaussSeidel(storm::Environment const& env, std::vector<ValueType>& x, std::vector<ValueType> const* b, bool backwards) const {
        if (backwards) {
            this->matrix.multiplyWithVectorBackward(x, x, b);
        } else {
            this->matrix.multiplyWithVectorForward(x, x, b);
        }
    }

    template<typename ValueType>
    void NativeMultiplier<ValueType>::multiplyAndReduce(storm::Environment const& env, storm::solver::OptimizationDirection const& dir, std::vector<uint64_t> const& rowGroupIndices, std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result, std::vector<uint_fast64_t>* choices, storm::storage::BitVector const* dirOverride) const {
        std::vector<ValueType>* target = &result;
        if (&x == &result) {
            if (this->cachedVector) {
                this->cachedVector->resize(x.size());
            } else {
                this->cachedVector = std::make_unique<std::vector<ValueType>>(x.size());
            }
            target = this->cachedVector.get();
        }
        if (parallelize(env)) {
            multAddReduceParallel(dir, rowGroupIndices, x, b, *target, choices, dirOverride);
        } else {
            multAddReduce(dir, rowGroupIndices, x, b, *target, choices, dirOverride);
        }
        if (&x == &result) {
            std::swap(result, *this->cachedVector);
        }
    }

    template<typename ValueType>
    void NativeMultiplier<ValueType>::multiplyAndReduceGaussSeidel(storm::Environment const& env, storm::solver::OptimizationDirection const& dir, std::vector<uint64_t> const& rowGroupIndices, std::vector<ValueType>& x, std::vector<ValueType> const* b, std::vector<uint_fast64_t>* choices, storm::storage::BitVector const* dirOverride, bool backwards) const {
        if (backwards) {
            synthesis::multiplyAndReduceBackward(this->matrix, dir, rowGroupIndices, x, b, x, choices, dirOverride);
        } else {
            synthesis::multiplyAndReduceForward(this->matrix, dir, rowGroupIndices, x, b, x, choices, dirOverride);
        }
    }

    template<typename ValueType>
    void NativeMultiplier<ValueType>::multiplyRow(uint64_t const& rowIndex, std::vector<ValueType> const& x, ValueType& value) const {
        for (auto const& entry : this->matrix.getRow(rowIndex)) {
            value += entry.getValue() * x[entry.getColumn()];
        }
    }

    template<typename ValueType>
    void NativeMultiplier<ValueType>::multiplyRow2(uint64_t const& rowIndex, std::vector<ValueType> const& x1, ValueType& val1, std::vector<ValueType> const& x2, ValueType& val2) const {
        for (auto const& entry : this->matrix.getRow(rowIndex)) {
            val1 += entry.getValue() * x1[entry.getColumn()];
            val2 += entry.getValue() * x2[entry.getColumn()];
        }
    }

    template<typename ValueType>
    void NativeMultiplier<ValueType>::multAdd(std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result) const {
        this->matrix.multiplyWithVector(x, result, b);
    }

    template<typename ValueType>
    void NativeMultiplier<ValueType>::multAddReduce(storm::solver::OptimizationDirection const& dir, std::vector<uint64_t> const& rowGroupIndices, std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result, std::vector<uint64_t>* choices, storm::storage::BitVector const* dirOverride) const {
        synthesis::multiplyAndReduce(this->matrix, dir, rowGroupIndices, x, b, result, choices, dirOverride);
    }

    template<typename ValueType>
    void NativeMultiplier<ValueType>::multAddParallel(std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result) const {
#ifdef STORM_HAVE_INTELTBB
        this->matrix.multiplyWithVectorParallel(x, result, b);
#else
        STORM_LOG_WARN("Storm was built without support for Intel TBB, defaulting to sequential version.");
        multAdd(x, b, result);
#endif
    }

    template<typename ValueType>
    void NativeMultiplier<ValueType>::multAddReduceParallel(storm::solver::OptimizationDirection const& dir, std::vector<uint64_t> const& rowGroupIndices, std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result, std::vector<uint64_t>* choices, storm::storage::BitVector const* dirOverride) const {
#ifdef STORM_HAVE_INTELTBB
        this->matrix.multiplyAndReduceParallel(dir, rowGroupIndices, x, b, result, choices, dirOverride);
#else
        STORM_LOG_WARN("Storm was built without support for Intel TBB, defaulting to sequential version.");
        multAddReduce(dir, rowGroupIndices, x, b, result, choices);
#endif
    }

    template class NativeMultiplier<double>;

}
