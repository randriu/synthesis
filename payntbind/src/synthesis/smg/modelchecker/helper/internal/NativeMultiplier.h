#pragma once

/* 
 * code in this file was taken from TEMPEST (https://github.com/PrangerStefan/TempestSynthesis)
 */

#include "Multiplier.h"

#include <storm/solver/OptimizationDirection.h>

namespace synthesis {

    template<typename ValueType>
    class NativeMultiplier : public synthesis::Multiplier<ValueType> {
    public:
        NativeMultiplier(storm::storage::SparseMatrix<ValueType> const& matrix);
        virtual ~NativeMultiplier() = default;

        virtual void multiply(storm::Environment const& env, std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result) const override;
        virtual void multiplyGaussSeidel(storm::Environment const& env, std::vector<ValueType>& x, std::vector<ValueType> const* b, bool backwards = true) const override;
        virtual void multiplyAndReduce(storm::Environment const& env, storm::solver::OptimizationDirection const& dir, std::vector<uint64_t> const& rowGroupIndices, std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result, std::vector<uint_fast64_t>* choices = nullptr, storm::storage::BitVector const* dirOverride = nullptr) const override;
        virtual void multiplyAndReduceGaussSeidel(storm::Environment const& env, storm::solver::OptimizationDirection const& dir, std::vector<uint64_t> const& rowGroupIndices, std::vector<ValueType>& x, std::vector<ValueType> const* b, std::vector<uint_fast64_t>* choices = nullptr, storm::storage::BitVector const* dirOverride = nullptr, bool backwards = true) const override;
        virtual void multiplyRow(uint64_t const& rowIndex, std::vector<ValueType> const& x, ValueType& value) const override;
        virtual void multiplyRow2(uint64_t const& rowIndex, std::vector<ValueType> const& x1, ValueType& val1, std::vector<ValueType> const& x2, ValueType& val2) const override;

    private:
        bool parallelize(storm::Environment const& env) const;

        void multAdd(std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result) const;

        void multAddReduce(storm::solver::OptimizationDirection const& dir, std::vector<uint64_t> const& rowGroupIndices, std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result, std::vector<uint64_t>* choices = nullptr, storm::storage::BitVector const* dirOverride = nullptr) const;

        void multAddParallel(std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result) const;
        void multAddReduceParallel(storm::solver::OptimizationDirection const& dir, std::vector<uint64_t> const& rowGroupIndices, std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result, std::vector<uint64_t>* choices = nullptr, storm::storage::BitVector const* dirOverride = nullptr) const;

    };

}
