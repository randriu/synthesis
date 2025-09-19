/* 
 * code in this file was taken from TEMPEST (https://github.com/PrangerStefan/TempestSynthesis)
 */

#include "GmmxxMultiplier.h"

#include <boost/optional.hpp>
#include <storm/exceptions/NotSupportedException.h>
#include <storm/utility/macros.h>

namespace synthesis {

    template<typename ValueType>
    GmmxxMultiplier<ValueType>::GmmxxMultiplier(storm::storage::SparseMatrix<ValueType> const& matrix) : Multiplier<ValueType>(matrix) {
        // Intentionally left empty.
    }

    template<typename ValueType>
    void GmmxxMultiplier<ValueType>::initialize() const {
        if (gmmMatrix.nrows() == 0) {
            gmmMatrix = std::move(*storm::adapters::GmmxxAdapter<ValueType>().toGmmxxSparseMatrix(this->matrix));
        }
    }

    template<typename ValueType>
    void GmmxxMultiplier<ValueType>::clearCache() const {
        gmmMatrix = gmm::csr_matrix<ValueType>();
        Multiplier<ValueType>::clearCache();
    }

    template<typename ValueType>
    void GmmxxMultiplier<ValueType>::multiply(storm::Environment const& env, std::vector<ValueType> const& x, std::vector<ValueType> *b, std::vector<ValueType>& result) const {
        initialize();
        std::vector<ValueType>* target = &result;
        if (&x == &result) {
            if (this->cachedVector) {
                this->cachedVector->resize(x.size());
            } else {
                this->cachedVector = std::make_unique<std::vector<ValueType>>(x.size());
            }
            target = this->cachedVector.get();
        }
        multAdd(x, b, *target);
        if (&x == &result) {
            std::swap(result, *this->cachedVector);
        }
    }

    template<typename ValueType>
    void GmmxxMultiplier<ValueType>::multiplyAndReduce(storm::Environment const& env, storm::solver::OptimizationDirection const& dir, std::vector<uint64_t> const& rowGroupIndices, std::vector<ValueType> const& x, std::vector<ValueType> *b, std::vector<ValueType>& result, std::vector<uint_fast64_t>* choices, storm::storage::BitVector const* dirOverride) const {
        initialize();
        std::vector<ValueType>* target = &result;
        if (&x == &result) {
            if (this->cachedVector) {
                this->cachedVector->resize(x.size());
            } else {
                this->cachedVector = std::make_unique<std::vector<ValueType>>(x.size());
            }
            target = this->cachedVector.get();
        }
        multAddReduceHelper(dir, rowGroupIndices, x, b, *target, choices, dirOverride, false);
        if (&x == &result) {
            std::swap(result, *this->cachedVector);
        }
    }

    template<typename ValueType>
    void GmmxxMultiplier<ValueType>::multAdd(std::vector<ValueType> const& x, std::vector<ValueType> *b, std::vector<ValueType>& result) const {
        if (b) {
            if (b == &result) {
                gmm::mult_add(gmmMatrix, x, result);
            } else {
                gmm::mult_add(gmmMatrix, x, *b);
                result = *b;
            }
        } else {
            gmm::mult(gmmMatrix, x, result);
        }
    }

    template<typename ValueType>
    void GmmxxMultiplier<ValueType>::multAddReduceHelper(storm::solver::OptimizationDirection const& dir, std::vector<uint64_t> const& rowGroupIndices, std::vector<ValueType> const& x, std::vector<ValueType> *b, std::vector<ValueType>& result, std::vector<uint64_t>* choices, storm::storage::BitVector const* dirOverride, bool backwards) const {
        bool isOverridden = (dirOverride && !dirOverride->empty()) ? true : false;
        if (dir == storm::OptimizationDirection::Minimize) {
            if(isOverridden) {
                if (backwards) {
                    multAddReduceHelper<storm::utility::ElementLess<ValueType>, true, true>(rowGroupIndices, x, b, result, choices, dirOverride);
                } else {
                    multAddReduceHelper<storm::utility::ElementLess<ValueType>, false, true>(rowGroupIndices, x, b, result, choices, dirOverride);
                }
            } else {
                if (backwards) {
                    multAddReduceHelper<storm::utility::ElementLess<ValueType>, true, false>(rowGroupIndices, x, b, result, choices);
                } else {
                    multAddReduceHelper<storm::utility::ElementLess<ValueType>, false, false>(rowGroupIndices, x, b, result, choices);
                }
            }
        } else {
            if(isOverridden) {
                if (backwards) {
                    multAddReduceHelper<storm::utility::ElementGreater<ValueType>, true, true>(rowGroupIndices, x, b, result, choices, dirOverride);
                } else {
                    multAddReduceHelper<storm::utility::ElementGreater<ValueType>, false, true>(rowGroupIndices, x, b, result, choices, dirOverride);
                }
            } else {
                if (backwards) {
                    multAddReduceHelper<storm::utility::ElementGreater<ValueType>, true, false>(rowGroupIndices, x, b, result, choices);
                } else {
                    multAddReduceHelper<storm::utility::ElementGreater<ValueType>, false, false>(rowGroupIndices, x, b, result, choices);
                }
            }
        }
    }

    template<typename ValueType>
    template<typename Compare, bool backwards, bool directionOverridden>
    void GmmxxMultiplier<ValueType>::multAddReduceHelper(std::vector<uint64_t> const& rowGroupIndices, std::vector<ValueType> const& x, std::vector<ValueType> *b, std::vector<ValueType>& result, std::vector<uint64_t>* choices, storm::storage::BitVector const* dirOverride) const {
        Compare compare;
        typedef std::vector<ValueType> VectorType;
        typedef gmm::csr_matrix<ValueType> MatrixType;

        typename gmm::linalg_traits<VectorType>::const_iterator add_it, add_ite;
        if (b) {
            add_it = backwards ? gmm::vect_end(*b) - 1 : gmm::vect_begin(*b);
            add_ite = backwards ?gmm::vect_begin(*b) - 1 : gmm::vect_end(*b);
        }
        typename gmm::linalg_traits<VectorType>::iterator target_it = backwards ? gmm::vect_end(result) - 1 : gmm::vect_begin(result);
        typename gmm::linalg_traits<MatrixType>::const_row_iterator itr = backwards ? mat_row_const_end(gmmMatrix) - 1 : mat_row_const_begin(gmmMatrix);
        typename std::vector<uint64_t>::iterator choice_it;
        if (choices) {
            choice_it = backwards ? choices->end() - 1 : choices->begin();
        }

        // Variables for correctly tracking choices (only update if new choice is strictly better).
        ValueType oldSelectedChoiceValue;
        uint64_t selectedChoice;

        uint64_t currentRow = backwards ? gmmMatrix.nrows() - 1 : 0;
        uint64_t currentRowGroup = backwards ? rowGroupIndices.size() - 2 : 0;
        auto row_group_it = backwards ? rowGroupIndices.end() - 2 : rowGroupIndices.begin();
        auto row_group_ite = backwards ? rowGroupIndices.begin() - 1 : rowGroupIndices.end() - 1;
        //if(choices) STORM_LOG_DEBUG(" ");
        while (row_group_it != row_group_ite) {
            ValueType currentValue = storm::utility::zero<ValueType>();

            // Only multiply and reduce if the row group is not empty.
            if (*row_group_it != *(row_group_it + 1)) {
                // Process the (backwards ? last : first) row of the current row group
                if (b) {
                    currentValue = *add_it;
                }

                currentValue += vect_sp(gmm::linalg_traits<MatrixType>::row(itr), x);

                if (choices) {
                    selectedChoice = currentRow - *row_group_it;
                    if (*choice_it == selectedChoice) {
                        oldSelectedChoiceValue = currentValue;
                    }
                }

                // move row-based iterators to the next row
                if (backwards) {
                    --itr;
                    --currentRow;
                    --add_it;
                } else {
                    ++itr;
                    ++currentRow;
                    ++add_it;
                }

                // Process the (rowGroupSize-1) remaining rows within the current row Group
                uint64_t rowGroupSize = *(row_group_it + 1) - *row_group_it;
                uint choiceforprintout = 0;
                //std::cout << currentRowGroup << ": " << currentValue << ", ";
                //STORM_LOG_DEBUG(std::setprecision(3) << vect_sp(gmm::linalg_traits<MatrixType>::row(itr), x) << " + " << *add_it << "; ");
                //STORM_LOG_DEBUG(std::setprecision(3) << vect_sp(gmm::linalg_traits<MatrixType>::row(itr), x) << " + " << *add_it << "; ");
                for (uint64_t i = 1; i < rowGroupSize; ++i) {
                    ValueType newValue = b ? *add_it : storm::utility::zero<ValueType>();
                    newValue += vect_sp(gmm::linalg_traits<MatrixType>::row(itr), x);

                    if (choices && currentRow == *choice_it + *row_group_it) {
                        oldSelectedChoiceValue = newValue;
                    }
                    //std::cout << newValue << ", ";
                    //STORM_LOG_DEBUG(std::setprecision(3) << vect_sp(gmm::linalg_traits<MatrixType>::row(itr), x) << " + " << *add_it << "; ");
                    if(!directionOverridden) {
                        if(compare(newValue, currentValue)) {
                            currentValue = newValue;
                            if (choices) {
                                selectedChoice = currentRow - *row_group_it;
                            }
                            choiceforprintout = currentRow - *row_group_it;
                        }
                    } else {
                        if(dirOverride->get(currentRowGroup) ? compare(currentValue, newValue) : compare(newValue, currentValue)) {
                            currentValue = newValue;
                            if (choices) {
                                selectedChoice = currentRow - *row_group_it;
                            }
                            choiceforprintout = currentRow - *row_group_it;
                        }
                    }
                    // move row-based iterators to the next row
                    if (backwards) {
                            --itr;
                            --currentRow;
                            --add_it;
                    } else {
                            ++itr;
                            ++currentRow;
                            ++add_it;
                    }
                }
                //STORM_LOG_DEBUG("\t= " << currentValue << "\tchoice: " << choiceforprintout);
                //std::cout << std::fixed << std::setprecision(2) << " | v(" << currentRowGroup << ")=" << currentValue << " c: " << choiceforprintout << " |\n" ;
                // Finally write value to target vector.
                *target_it = currentValue;
                if(choices) {
                    if(!directionOverridden) {
                        if(compare(currentValue, oldSelectedChoiceValue) ) {
                            *choice_it = selectedChoice;
                        }
                    } else {
                        if(dirOverride->get(currentRowGroup) ? compare(oldSelectedChoiceValue, currentValue) : compare(currentValue, oldSelectedChoiceValue) ) {
                            *choice_it = selectedChoice;
                        }
                    }
                }
            }

            // move rowGroup-based iterators to the next row group
            if (backwards) {
                --row_group_it;
                --choice_it;
                --target_it;
                --currentRowGroup;
            } else {
                ++row_group_it;
                ++choice_it;
                ++target_it;
                ++currentRowGroup;
            }
        }
            //std::cout << std::endl;
    }

    template<>
    template<typename Compare, bool backwards, bool directionOverridden>
    void GmmxxMultiplier<storm::RationalFunction>::multAddReduceHelper(std::vector<uint64_t> const& rowGroupIndices, std::vector<storm::RationalFunction> const& x, std::vector<storm::RationalFunction> *b, std::vector<storm::RationalFunction>& result, std::vector<uint64_t>* choices, storm::storage::BitVector const* dirOverride) const {
        STORM_LOG_THROW(false, storm::exceptions::NotSupportedException, "Operation not supported for this data type.");
    }

    template class GmmxxMultiplier<double>;

}
