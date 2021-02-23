#ifndef STORM_SOLVER_CUDAMINMAXLINEAREQUATIONSOLVER_H_
#define STORM_SOLVER_CUDAMINMAXLINEAREQUATIONSOLVER_H_

#include "storm/solver/StandardMinMaxLinearEquationSolver.h"
#include "storm/storage/SparseMatrix.h"
#include "storm/exceptions/NotImplementedException.h"
#include "storm/exceptions/NotSupportedException.h"

#include "storm-config.h"

#ifdef STORM_HAVE_CUDASYNTHESIS
#include "cudaForStorm.h"
#endif

namespace storm {
    namespace solver {

        template<class ValueType>
        class CudaMinMaxLinearEquationSolver : public StandardMinMaxLinearEquationSolver<ValueType> {
        public:
            CudaMinMaxLinearEquationSolver();
            CudaMinMaxLinearEquationSolver(storm::storage::SparseMatrix<ValueType> const& A);
            CudaMinMaxLinearEquationSolver(storm::storage::SparseMatrix<ValueType>&& A);
            
            /**
             * @brief 
             * 
             * @param env 
             * @param dir 
             * @param x 
             * @param b 
             * @return true 
             * @return false 
             */
            virtual bool internalSolveEquations(Environment const& env, OptimizationDirection dir, std::vector<ValueType>& x, std::vector<ValueType> const& b) const override;

        private:
            /**
             * @brief 
             * 
             */
            struct CSRMatrix {
                CSRMatrix(storm::storage::SparseMatrix<ValueType> const* A);

                uint_fast64_t matrixRowCount;
                uint_fast64_t matrixNnzCount;
                uint_fast64_t matrixRowGroupCount;
                
                const std::vector<typename storm::storage::SparseMatrix<ValueType>::index_type>* rowGroupIndices;
                const std::vector<typename storm::storage::SparseMatrix<ValueType>::index_type>* rowStartIndices;
                std::vector<typename storm::storage::SparseMatrix<ValueType>::index_type> columnIndices;
                std::vector<ValueType> nnzValues;
            };
        };

        /**
         * @brief 
         * 
         * @tparam IndexType 
         * @tparam ValueType 
         * @param x 
         * @return true 
         * @return false 
         */
        template <typename IndexType, typename ValueType>
        bool __ValueIteration_mvReduce_minimize(uint_fast64_t const, double const, bool const, std::vector<uint_fast64_t> const&, std::vector<storm::storage::MatrixEntry<IndexType, ValueType>> const&, std::vector<ValueType>& x, std::vector<ValueType> const&, std::vector<uint_fast64_t> const&, size_t&) {
            //
            STORM_LOG_THROW(false, storm::exceptions::NotImplementedException, "Unsupported template arguments.");
        }
        template <>
        inline bool __ValueIteration_mvReduce_minimize<uint_fast64_t, double>(uint_fast64_t const maxIterationCount, double const precision, bool const relativePrecisionCheck, std::vector<uint_fast64_t> const& matrixRowIndices, std::vector<storm::storage::MatrixEntry<uint_fast64_t, double>> const& columnIndicesAndValues, std::vector<double>& x, std::vector<double> const& b, std::vector<uint_fast64_t> const& nondeterministicChoiceIndices, size_t& iterationCount) {
#ifdef STORM_HAVE_CUDASYNTHESIS
            return false;
            // return ValueIteration_mvReduce_uint64_double_minimize(maxIterationCount, precision, relativePrecisionCheck, matrixRowIndices, columnIndicesAndValues, x, b, nondeterministicChoiceIndices, iterationCount);
#else
            STORM_LOG_THROW(false, storm::exceptions::NotSupportedException, "Storm is compiled without CUDA support.");
#endif
        }
        template <>
        inline bool __ValueIteration_mvReduce_minimize<uint_fast64_t, float>(uint_fast64_t const maxIterationCount, double const precision, bool const relativePrecisionCheck, std::vector<uint_fast64_t> const& matrixRowIndices, std::vector<storm::storage::MatrixEntry<uint_fast64_t, float>> const& columnIndicesAndValues, std::vector<float>& x, std::vector<float> const& b, std::vector<uint_fast64_t> const& nondeterministicChoiceIndices, size_t& iterationCount) {
#ifdef STORM_HAVE_CUDASYNTHESIS
            return false;
            // return ValueIteration_mvReduce_uint64_float_minimize(maxIterationCount, precision, relativePrecisionCheck, matrixRowIndices, columnIndicesAndValues, x, b, nondeterministicChoiceIndices, iterationCount);
#else
            STORM_LOG_THROW(false, storm::exceptions::NotSupportedException, "Storm is compiled without CUDA support.");
#endif
        }

        /**
         * @brief 
         * 
         * @tparam IndexType 
         * @tparam ValueType 
         * @return true 
         * @return false 
         */
        template <typename IndexType, typename ValueType>
        bool __ValueIteration_mvReduce_maximize(uint_fast64_t const, double const, bool const, std::vector<uint_fast64_t> const&, std::vector<storm::storage::MatrixEntry<IndexType, ValueType>> const&, std::vector<ValueType>&, std::vector<ValueType> const&, std::vector<uint_fast64_t> const&, size_t&) {
            STORM_LOG_THROW(false, storm::exceptions::NotImplementedException, "Unsupported template arguments.");
        }
        template <>
        inline bool __ValueIteration_mvReduce_maximize<uint_fast64_t, double>(uint_fast64_t const maxIterationCount, double const precision, bool const relativePrecisionCheck, std::vector<uint_fast64_t> const& matrixRowIndices, std::vector<storm::storage::MatrixEntry<uint_fast64_t, double>> const& columnIndicesAndValues, std::vector<double>& x, std::vector<double> const& b, std::vector<uint_fast64_t> const& nondeterministicChoiceIndices, size_t& iterationCount) {
#ifdef STORM_HAVE_CUDASYNTHESIS
            return false;
            // return ValueIteration_mvReduce_uint64_double_maximize(maxIterationCount, precision, relativePrecisionCheck, matrixRowIndices, columnIndicesAndValues, x, b, nondeterministicChoiceIndices, iterationCount);
#else
            STORM_LOG_THROW(false, storm::exceptions::NotSupportedException, "Storm is compiled without CUDA support.");
#endif
        }
        template <>
        inline bool __ValueIteration_mvReduce_maximize<uint_fast64_t, float>(uint_fast64_t const maxIterationCount, double const precision, bool const relativePrecisionCheck, std::vector<uint_fast64_t> const& matrixRowIndices, std::vector<storm::storage::MatrixEntry<uint_fast64_t, float>> const& columnIndicesAndValues, std::vector<float>& x, std::vector<float> const& b, std::vector<uint_fast64_t> const& nondeterministicChoiceIndices, size_t& iterationCount) {
#ifdef STORM_HAVE_CUDASYNTHESIS
            return false;
            // return ValueIteration_mvReduce_uint64_float_maximize(maxIterationCount, precision, relativePrecisionCheck, matrixRowIndices, columnIndicesAndValues, x, b, nondeterministicChoiceIndices, iterationCount);
#else
            STORM_LOG_THROW(false, storm::exceptions::NotSupportedException, "Storm is compiled without CUDA support.");
#endif
        }
    } // namespace solver
} // namespace storm

#endif /* STORM_SOLVER_CUDAMINMAXLINEAREQUATIONSOLVER_H_ */