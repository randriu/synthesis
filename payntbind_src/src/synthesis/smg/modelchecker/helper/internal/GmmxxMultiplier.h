#pragma once

/* 
 * code in this file was taken from TEMPEST (https://github.com/PrangerStefan/TempestSynthesis)
 */

#include "Multiplier.h"

#include <storm/environment/Environment.h>
#include <storm/storage/BitVector.h>
#include <storm/storage/SparseMatrix.h>
#include <storm/adapters/GmmxxAdapter.h>

namespace synthesis {

    template<typename ValueType>
    class GmmxxMultiplier : public synthesis::Multiplier<ValueType> {
    public:
        GmmxxMultiplier(storm::storage::SparseMatrix<ValueType> const& matrix);
        virtual ~GmmxxMultiplier() = default;

        virtual void multiply(storm::Environment const& env, std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result) const override;
        virtual void multiplyGaussSeidel(storm::Environment const& env, std::vector<ValueType>& x, std::vector<ValueType> const* b, bool backwards = true) const override;
        virtual void multiplyAndReduce(storm::Environment const& env, storm::solver::OptimizationDirection const& dir, std::vector<uint64_t> const& rowGroupIndices, std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result, std::vector<uint_fast64_t>* choices = nullptr, storm::storage::BitVector const* dirOverride = nullptr) const override;
        virtual void multiplyAndReduceGaussSeidel(storm::Environment const& env, storm::solver::OptimizationDirection const& dir, std::vector<uint64_t> const& rowGroupIndices, std::vector<ValueType>& x, std::vector<ValueType> const* b, std::vector<uint_fast64_t>* choices = nullptr, storm::storage::BitVector const* dirOverride = nullptr, bool backwards = true) const override;
        virtual void multiplyRow(uint64_t const& rowIndex, std::vector<ValueType> const& x, ValueType& value) const override;
        virtual void clearCache() const override;

    private:
        void initialize() const;

        bool parallelize(storm::Environment const& env) const;

        void multAdd(std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result) const;
        void multAddParallel(std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result) const;
        void multAddReduceParallel(storm::solver::OptimizationDirection const& dir, std::vector<uint64_t> const& rowGroupIndices, std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result, std::vector<uint64_t>* choices = nullptr, storm::storage::BitVector const* dirOverride = nullptr) const;
        void multAddReduceHelper(storm::solver::OptimizationDirection const& dir, std::vector<uint64_t> const& rowGroupIndices, std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result, std::vector<uint64_t>* choices = nullptr, storm::storage::BitVector const* dirOverride = nullptr, bool backwards = true) const;

        template<typename Compare, bool backwards = true, bool directionOverridden = false>
        void multAddReduceHelper(std::vector<uint64_t> const& rowGroupIndices, std::vector<ValueType> const& x, std::vector<ValueType> const* b, std::vector<ValueType>& result, std::vector<uint64_t>* choices = nullptr, storm::storage::BitVector const* dirOverride = nullptr) const;

        mutable gmm::csr_matrix<ValueType> gmmMatrix;
    };

}
