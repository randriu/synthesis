/* 
 * code in this file was taken from TEMPEST (https://github.com/PrangerStefan/TempestSynthesis)
 */

#include "GmmxxMultiplier.h"

#include <boost/optional.hpp>
#include <storm/settings/modules/CoreSettings.h>
#include <storm/exceptions/NotSupportedException.h>
#include <storm/utility/macros.h>

namespace synthesis {

    template<typename ValueType>
    GmmxxMultiplier<ValueType>::GmmxxMultiplier(storm::storage::SparseMatrix<ValueType> const& matrix) : Multiplier<ValueType>(matrix) {
        // Intentionally left empty.
        //STORM_LOG_DEBUG("\n" << matrix);
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
    bool GmmxxMultiplier<ValueType>::parallelize(storm::Environment const& env) const {
#ifdef STORM_HAVE_INTELTBB
        return storm::settings::getModule<storm::settings::modules::CoreSettings>().isUseIntelTbbSet();
#else
        return false;
#endif
    }

    template<typename ValueType>
    void GmmxxMultiplier<ValueType>::multiply(storm::Environment const& env, std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result) const {
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
    void GmmxxMultiplier<ValueType>::multiplyGaussSeidel(storm::Environment const& env, std::vector<ValueType>& x, std::vector<ValueType> const* b, bool backwards) const {
        initialize();
        STORM_LOG_ASSERT(gmmMatrix.nr == gmmMatrix.nc, "Expecting square matrix.");
        if (backwards) {
            if (b) {
                gmm::mult_add_by_row_bwd(gmmMatrix, x, *b, x, gmm::abstract_dense());
            } else {
                gmm::mult_by_row_bwd(gmmMatrix, x, x, gmm::abstract_dense());
            }
        } else {
            if (b) {
                gmm::mult_add_by_row(gmmMatrix, x, *b, x, gmm::abstract_dense());
            } else {
                gmm::mult_by_row(gmmMatrix, x, x, gmm::abstract_dense());
            }
        }
    }

    template<typename ValueType>
    void GmmxxMultiplier<ValueType>::multiplyAndReduce(storm::Environment const& env, storm::solver::OptimizationDirection const& dir, std::vector<uint64_t> const& rowGroupIndices, std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result, std::vector<uint_fast64_t>* choices, storm::storage::BitVector const* dirOverride) const {
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
        if (parallelize(env)) {
            multAddReduceParallel(dir, rowGroupIndices, x, b, *target, choices, dirOverride);
        } else {
            multAddReduceHelper(dir, rowGroupIndices, x, b, *target, choices, dirOverride, false);
        }
        if (&x == &result) {
            std::swap(result, *this->cachedVector);
        }
    }

    template<typename ValueType>
    void GmmxxMultiplier<ValueType>::multiplyAndReduceGaussSeidel(storm::Environment const& env, storm::solver::OptimizationDirection const& dir, std::vector<uint64_t> const& rowGroupIndices, std::vector<ValueType>& x, std::vector<ValueType> const* b, std::vector<uint_fast64_t>* choices, storm::storage::BitVector const* dirOverride, bool backwards) const {
        initialize();
        multAddReduceHelper(dir, rowGroupIndices, x, b, x, choices, dirOverride, backwards);
    }

    template<typename ValueType>
    void GmmxxMultiplier<ValueType>::multiplyRow(uint64_t const& rowIndex, std::vector<ValueType> const& x, ValueType& value) const {
        initialize();
        value += vect_sp(gmm::mat_const_row(gmmMatrix, rowIndex), x, typename gmm::linalg_traits<gmm::csr_matrix<ValueType>>::storage_type(), typename gmm::linalg_traits<std::vector<ValueType>>::storage_type());
    }

    template<typename ValueType>
    void GmmxxMultiplier<ValueType>::multAdd(std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result) const {
        if (b) {
            if (b == &result) {
                gmm::mult_add(gmmMatrix, x, result);
            } else {
                gmm::mult_add(gmmMatrix, x, *b, result);
            }
        } else {
            gmm::mult(gmmMatrix, x, result);
        }
    }

    template<typename ValueType>
    void GmmxxMultiplier<ValueType>::multAddReduceHelper(storm::solver::OptimizationDirection const& dir, std::vector<uint64_t> const& rowGroupIndices, std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result, std::vector<uint64_t>* choices, storm::storage::BitVector const* dirOverride, bool backwards) const {
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
    void GmmxxMultiplier<ValueType>::multAddReduceHelper(std::vector<uint64_t> const& rowGroupIndices, std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result, std::vector<uint64_t>* choices, storm::storage::BitVector const* dirOverride) const {
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
    void GmmxxMultiplier<storm::RationalFunction>::multAddReduceHelper(std::vector<uint64_t> const& rowGroupIndices, std::vector<storm::RationalFunction> const& x, std::vector<storm::RationalFunction> const* b, std::vector<storm::RationalFunction>& result, std::vector<uint64_t>* choices, storm::storage::BitVector const* dirOverride) const {
        STORM_LOG_THROW(false, storm::exceptions::NotSupportedException, "Operation not supported for this data type.");
    }

    template<typename ValueType>
    void GmmxxMultiplier<ValueType>::multAddParallel(std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result) const {
#ifdef STORM_HAVE_INTELTBB
        if (b) {
            if (b == &result) {
                gmm::mult_add_parallel(gmmMatrix, x, result);
            } else {
                gmm::mult_add_parallel(gmmMatrix, x, *b, result);
            }
        } else {
            gmm::mult_parallel(gmmMatrix, x, result);
        }
#else
        STORM_LOG_WARN("Storm was built without support for Intel TBB, defaulting to sequential version.");
        multAdd(x, b, result);
#endif
    }

#ifdef STORM_HAVE_INTELTBB
    template<typename ValueType, typename Compare>
    class TbbMultAddReduceFunctor {
    public:
        TbbMultAddReduceFunctor(std::vector<uint64_t> const& rowGroupIndices, gmm::csr_matrix<ValueType> const& matrix, std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result, std::vector<uint64_t>* choices, storm::storage::BitVector const* dirOverride = nullptr) : rowGroupIndices(rowGroupIndices), matrix(matrix), x(x), b(b), result(result), choices(choices), dirOverride(dirOverride) {
            // Intentionally left empty.
        }

        void operator()(tbb::blocked_range<unsigned long> const& range) const {
            typedef std::vector<ValueType> VectorType;
            typedef gmm::csr_matrix<ValueType> MatrixType;

            auto groupIt = rowGroupIndices.begin() + range.begin();
            auto groupIte = rowGroupIndices.begin() + range.end();

            auto itr = mat_row_const_begin(matrix) + *groupIt;
            typename std::vector<ValueType>::const_iterator bIt;
            if (b) {
                bIt = b->begin() + *groupIt;
            }
            typename std::vector<uint64_t>::iterator choiceIt;
            if (choices) {
                choiceIt = choices->begin() + range.begin();
            }
            bool dirOverridden = false;
            if(dirOverride && !dirOverride.get()->empty()) {
                dirOverridden = true;
            }

            auto resultIt = result.begin() + range.begin();

            // Variables for correctly tracking choices (only update if new choice is strictly better).
            ValueType oldSelectedChoiceValue;
            uint64_t selectedChoice;

            uint64_t currentRow = *groupIt;
            for (; groupIt != groupIte; ++groupIt, ++resultIt, ++choiceIt) {
                ValueType currentValue = storm::utility::zero<ValueType>();

                // Only multiply and reduce if the row group is not empty.
                if (*groupIt != *(groupIt + 1)) {
                    if (b) {
                        currentValue = *bIt;
                        ++bIt;
                    }

                    currentValue += vect_sp(gmm::linalg_traits<MatrixType>::row(itr), x);

                    if (choices) {
                        selectedChoice = currentRow - *groupIt;
                        if (*choiceIt == selectedChoice) {
                            oldSelectedChoiceValue = currentValue;
                        }
                    }

                    ++itr;
                    ++currentRow;

                    for (auto itre = mat_row_const_begin(matrix) + *(groupIt + 1); itr != itre; ++itr, ++bIt, ++currentRow) {
                        ValueType newValue = b ? *bIt : storm::utility::zero<ValueType>();
                        newValue += vect_sp(gmm::linalg_traits<MatrixType>::row(itr), x);

                        if(!dirOverridden) {
                            if (compare(newValue, currentValue)) {
                                currentValue = newValue;
                                if (choices) {
                                    selectedChoice = currentRow - *groupIt;
                                }
                            }
                        } else {
                            if (dirOverride.get()->get(*groupIt) ? compare(currentValue, newValue) : compare(newValue, currentValue)) {
                                currentValue = newValue;
                                if (choices) {
                                    selectedChoice = currentRow - *groupIt;
                                }
                            }

                        }
                    }
                }

                // Finally write value to target vector.
                *resultIt = currentValue;
                if(!dirOverridden) {
                    if (choices && compare(currentValue, oldSelectedChoiceValue)) {
                        *choiceIt = selectedChoice;
                    }
                } else {
                    if (choices && dirOverride.get()->get(*groupIt) ? compare(oldSelectedChoiceValue, currentValue) : compare(currentValue, oldSelectedChoiceValue)) {
                        *choiceIt = selectedChoice;
                    }
                }
            }
        }

    private:
        Compare compare;
        std::vector<uint64_t> const& rowGroupIndices;
        gmm::csr_matrix<ValueType> const& matrix;
        std::vector<ValueType> const& x;
        std::vector<ValueType> const* b;
        std::vector<ValueType>& result;
        std::vector<uint64_t>* choices;
        boost::optional<storm::storage::BitVector*> const dirOverride = boost::none;
    };
#endif

    template<typename ValueType>
    void GmmxxMultiplier<ValueType>::multAddReduceParallel(storm::solver::OptimizationDirection const& dir, std::vector<uint64_t> const& rowGroupIndices, std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result, std::vector<uint64_t>* choices, storm::storage::BitVector const* dirOverride) const {
#ifdef STORM_HAVE_INTELTBB
        if (dir == storm::OptimizationDirection::Minimize) {
            tbb::parallel_for(tbb::blocked_range<unsigned long>(0, rowGroupIndices.size() - 1, 100), TbbMultAddReduceFunctor<ValueType, storm::utility::ElementLess<ValueType>>(rowGroupIndices, this->gmmMatrix, x, b, result, choices, dirOverride));
        } else {
            tbb::parallel_for(tbb::blocked_range<unsigned long>(0, rowGroupIndices.size() - 1, 100), TbbMultAddReduceFunctor<ValueType, storm::utility::ElementGreater<ValueType>>(rowGroupIndices, this->gmmMatrix, x, b, result, choices, dirOverride));
        }
#else
        STORM_LOG_WARN("Storm was built without support for Intel TBB, defaulting to sequential version.");
        multAddReduceHelper(dir, rowGroupIndices, x, b, result, choices, dirOverride);
#endif
    }

    template<>
    void GmmxxMultiplier<storm::RationalFunction>::multAddReduceParallel(storm::solver::OptimizationDirection const& dir, std::vector<uint64_t> const& rowGroupIndices, std::vector<storm::RationalFunction> const& x, std::vector<storm::RationalFunction> const* b, std::vector<storm::RationalFunction>& result, std::vector<uint64_t>* choices, storm::storage::BitVector const* dirOverride) const {
        STORM_LOG_THROW(false, storm::exceptions::NotSupportedException, "This operation is not supported.");
    }

    template class GmmxxMultiplier<double>;

}
