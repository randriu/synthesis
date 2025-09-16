#pragma once

/* 
 * code in this file was taken from TEMPEST (https://github.com/PrangerStefan/TempestSynthesis)
 */

#include <vector>

#include <storm/storage/BitVector.h>
#include <storm/solver/OptimizationDirection.h>
#include <storm/storage/SparseMatrix.h>
#include <storm/environment/solver/MultiplierEnvironment.h>

namespace synthesis {

    template<typename ValueType>
    class Multiplier {
    public:

        Multiplier(storm::storage::SparseMatrix<ValueType> const& matrix);

        virtual ~Multiplier() = default;

        /*
        * Clears the currently cached data of this multiplier in order to free some memory.
        */
        virtual void clearCache() const;

        /*!
        * Performs a matrix-vector multiplication x' = A*x + b.
        *
        * @param x The input vector with which to multiply the matrix. Its length must be equal
        * to the number of columns of A.
        * @param b If non-null, this vector is added after the multiplication. If given, its length must be equal
        * to the number of rows of A.
        * @param result The target vector into which to write the multiplication result. Its length must be equal
        * to the number of rows of A. Can be the same as the x vector.
        */
        virtual void multiply(storm::Environment const& env, std::vector<ValueType> const& x, std::vector<ValueType> *b, std::vector<ValueType>& result) const = 0;

        /*!
        * Performs a matrix-vector multiplication x' = A*x + b and then minimizes/maximizes over the row groups
        * so that the resulting vector has the size of number of row groups of A.
        *
        * @param dir The direction for the reduction step.
        * @param rowGroupIndices A vector storing the row groups over which to reduce.
        * @param x The input vector with which to multiply the matrix. Its length must be equal
        * to the number of columns of A.
        * @param b If non-null, this vector is added after the multiplication. If given, its length must be equal
        * to the number of rows of A.
        * @param result The target vector into which to write the multiplication result. Its length must be equal
        * to the number of rows of A. Can be the same as the x vector.
        * @param choices If given, the choices made in the reduction process are written to this vector.
        */
        void multiplyAndReduce(storm::Environment const& env, storm::solver::OptimizationDirection const& dir, std::vector<ValueType> const& x, std::vector<ValueType> *b, std::vector<ValueType>& result, std::vector<uint_fast64_t>* choices = nullptr, storm::storage::BitVector const* dirOverride = nullptr) const;
        virtual void multiplyAndReduce(storm::Environment const& env, storm::solver::OptimizationDirection const& dir, std::vector<uint64_t> const& rowGroupIndices, std::vector<ValueType> const& x, std::vector<ValueType> *b, std::vector<ValueType>& result, std::vector<uint_fast64_t>* choices = nullptr, storm::storage::BitVector const* dirOverride = nullptr) const = 0;


        /*!
        * Performs repeated matrix-vector multiplication, using x[0] = x and x[i + 1] = A*x[i] + b. After
        * performing the necessary multiplications, the result is written to the input vector x. Note that the
        * matrix A has to be given upon construction time of the solver object.
        *
        * @param x The initial vector with which to perform matrix-vector multiplication. Its length must be equal
        * to the number of columns of A.
        * @param b If non-null, this vector is added after each multiplication. If given, its length must be equal
        * to the number of rows of A.
        * @param n The number of times to perform the multiplication.
        */
        void repeatedMultiply(storm::Environment const& env, std::vector<ValueType>& x, std::vector<ValueType> *b, uint64_t n) const;

        void reduce(storm::Environment const& env, storm::OptimizationDirection const& dir, std::vector<storm::storage::SparseMatrix<double>::index_type> const& rowGroupIndices, std::vector<ValueType> const& choiceValues, std::vector<ValueType>& result, std::vector<uint_fast64_t>* choices = nullptr, storm::storage::BitVector const* dirOverride = nullptr) const;

        protected:
            mutable std::unique_ptr<std::vector<ValueType>> cachedVector;
            storm::storage::SparseMatrix<ValueType> const& matrix;
    };

    template<typename ValueType>
    class MultiplierFactory {
    public:
        MultiplierFactory() = default;
        ~MultiplierFactory() = default;

        std::unique_ptr<synthesis::Multiplier<ValueType>> create(storm::Environment const& env, storm::storage::SparseMatrix<ValueType> const& matrix);
    };
}
