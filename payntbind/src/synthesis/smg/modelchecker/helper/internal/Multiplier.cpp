/* 
 * code in this file was taken from TEMPEST (https://github.com/PrangerStefan/TempestSynthesis)
 */

#include "Multiplier.h"

#include <storm/utility/macros.h>
#include <storm/exceptions/IllegalArgumentException.h>
#include <storm/utility/SignalHandler.h>
#include <storm/utility/ProgressMeasurement.h>

#include "GmmxxMultiplier.h"
#include "NativeMultiplier.h"

namespace synthesis {

    template<typename ValueType>
    Multiplier<ValueType>::Multiplier(storm::storage::SparseMatrix<ValueType> const& matrix) : matrix(matrix) {
        // Intentionally left empty.
    }

    template<typename ValueType>
    void Multiplier<ValueType>::clearCache() const {
        cachedVector.reset();
    }

    template<typename ValueType>
    void Multiplier<ValueType>::multiplyAndReduce(storm::Environment const& env, storm::solver::OptimizationDirection const& dir, std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result, std::vector<uint_fast64_t>* choices, storm::storage::BitVector const* dirOverride) const {
        multiplyAndReduce(env, dir, this->matrix.getRowGroupIndices(), x, b, result, choices, dirOverride);
    }

    template<typename ValueType>
    void Multiplier<ValueType>::multiplyAndReduceGaussSeidel(storm::Environment const& env, storm::solver::OptimizationDirection const& dir, std::vector<ValueType>& x, std::vector<ValueType> const* b, std::vector<uint_fast64_t>* choices, storm::storage::BitVector const* dirOverride, bool backwards) const {
        multiplyAndReduceGaussSeidel(env, dir, this->matrix.getRowGroupIndices(), x, b, choices, dirOverride, backwards);
    }

    template<typename ValueType>
    void Multiplier<ValueType>::repeatedMultiply(storm::Environment const& env, std::vector<ValueType>& x, std::vector<ValueType> const* b, uint64_t n) const {
        storm::utility::ProgressMeasurement progress("multiplications");
        progress.setMaxCount(n);
        progress.startNewMeasurement(0);
        for (uint64_t i = 0; i < n; ++i) {
            progress.updateProgress(i);
            multiply(env, x, b, x);
            if (storm::utility::resources::isTerminate()) {
                STORM_LOG_WARN("Aborting after " << i << " of " << n << " multiplications.");
                break;
            }
        }
    }

    template<typename ValueType>
    void Multiplier<ValueType>::repeatedMultiplyAndReduce(storm::Environment const& env, storm::solver::OptimizationDirection const& dir, std::vector<ValueType>& x, std::vector<ValueType> const* b, uint64_t n, storm::storage::BitVector const* dirOverride) const {
        storm::utility::ProgressMeasurement progress("multiplications");
        progress.setMaxCount(n);
        progress.startNewMeasurement(0);
        for (uint64_t i = 0; i < n; ++i) {
            multiplyAndReduce(env, dir, x, b, x);
            if (storm::utility::resources::isTerminate()) {
                STORM_LOG_WARN("Aborting after " << i << " of " << n << " multiplications");
                break;
            }
        }
    }

    template<typename ValueType>
    void Multiplier<ValueType>::repeatedMultiplyAndReduceWithChoices(storm::Environment const& env, storm::solver::OptimizationDirection const& dir, std::vector<ValueType>& x, std::vector<ValueType> const* b, uint64_t n, storm::storage::BitVector const* dirOverride, std::vector<ValueType>& choiceValues, std::vector<storm::storage::SparseMatrix<double>::index_type> rowGroupIndices) const {
        storm::utility::ProgressMeasurement progress("multiplications");
        progress.setMaxCount(n);
        progress.startNewMeasurement(0);
        for (uint64_t i = 0; i < n; ++i) {
            multiply(env, x, b, choiceValues);
            reduce(env, dir, rowGroupIndices, choiceValues, x);
            if (storm::utility::resources::isTerminate()) {
                STORM_LOG_WARN("Aborting after " << i << " of " << n << " multiplications");
                break;
            }
        }
    }

    template<typename ValueType>
    void Multiplier<ValueType>::multiplyRow2(uint64_t const& rowIndex, std::vector<ValueType> const& x1, ValueType& val1, std::vector<ValueType> const& x2, ValueType& val2) const {
        multiplyRow(rowIndex, x1, val1);
        multiplyRow(rowIndex, x2, val2);
    }

    template<typename ValueType>
    void synthesis::Multiplier<ValueType>::reduce(storm::Environment const& env, storm::solver::OptimizationDirection const& dir, std::vector<storm::storage::SparseMatrix<double>::index_type> const& rowGroupIndices, std::vector<ValueType> const& choiceValues, std::vector<ValueType>& result, std::vector<uint_fast64_t>* choices, storm::storage::BitVector const* dirOverride) const {
        auto choiceValue_it = choiceValues.begin();
        auto optChoice_it = choiceValues.begin();
        for(uint state = 0; state < rowGroupIndices.size(); state++) {
            uint rowGroupSize;
            if(state == 0) {
                rowGroupSize = rowGroupIndices[state];
            } else {
                rowGroupSize = rowGroupIndices[state] - rowGroupIndices[state - 1];
            }
            if(dirOverride != nullptr) {
                if((dir == storm::OptimizationDirection::Minimize && !dirOverride->get(state)) || (dir == storm::OptimizationDirection::Maximize && dirOverride->get(state))) {
                    optChoice_it = std::min_element(choiceValue_it, choiceValue_it + rowGroupSize);
                } else {
                    optChoice_it = std::max_element(choiceValue_it, choiceValue_it + rowGroupSize);
                }
            } else {
                if(dir == storm::OptimizationDirection::Minimize) {
                    optChoice_it = std::min_element(choiceValue_it, choiceValue_it + rowGroupSize);
                } else {
                    optChoice_it = std::max_element(choiceValue_it, choiceValue_it + rowGroupSize);
                }
            }
            result.at(state) = *optChoice_it;
            if(choices) {
                choices->at(state) = std::distance(choiceValue_it, optChoice_it);
            }
            choiceValue_it += rowGroupSize;
        }
    }

    template<typename ValueType>
    std::unique_ptr<synthesis::Multiplier<ValueType>> MultiplierFactory<ValueType>::create(storm::Environment const& env, storm::storage::SparseMatrix<ValueType> const& matrix) {
        auto type = env.solver().multiplier().getType();

        // Adjust the multiplier type if an eqsolver was specified but not a multiplier
        if (!env.solver().isLinearEquationSolverTypeSetFromDefaultValue() && env.solver().multiplier().isTypeSetFromDefault()) {
            bool changed = false;
            if (env.solver().getLinearEquationSolverType() == storm::solver::EquationSolverType::Gmmxx && type != storm::solver::MultiplierType::Gmmxx) {
                type = storm::solver::MultiplierType::Gmmxx;
                changed = true;
            } else if (env.solver().getLinearEquationSolverType() == storm::solver::EquationSolverType::Native && type != storm::solver::MultiplierType::Native) {
                type = storm::solver::MultiplierType::Native;
                changed = true;
            }
            STORM_LOG_INFO_COND(!changed, "Selecting '" + toString(type) + "' as the multiplier type to match the selected equation solver. If you want to override this, please explicitly specify a different multiplier type.");
        }

        switch (type) {
            case storm::solver::MultiplierType::Gmmxx:
                return std::make_unique<synthesis::GmmxxMultiplier<ValueType>>(matrix);
            case storm::solver::MultiplierType::Native:
                return std::make_unique<synthesis::NativeMultiplier<ValueType>>(matrix);
        }
        STORM_LOG_THROW(false, storm::exceptions::IllegalArgumentException, "Unknown MultiplierType");
    }

    template class synthesis::Multiplier<double>;
    template class synthesis::MultiplierFactory<double>;

}
