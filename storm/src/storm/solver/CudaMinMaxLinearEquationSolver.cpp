#include "storm/solver/CudaMinMaxLinearEquationSolver.h"

#include "storm/utility/vector.h" // selectVectorValues
#include "storm/exceptions/IllegalArgumentException.h"
#include "storm/exceptions/InvalidStateException.h"
#include "storm/exceptions/InvalidEnvironmentException.h"

#include "storm/environment/solver/MinMaxSolverEnvironment.h"

#include "storm-config.h"
#ifdef STORM_HAVE_CUDASYNTHESIS
#	include "cudaForStorm.h"
#endif

namespace storm {
    namespace solver {

        template<typename ValueType>
        CudaMinMaxLinearEquationSolver<ValueType>::CudaMinMaxLinearEquationSolver() {
            // Intentionally left empty.
        }

        template<typename ValueType>
        CudaMinMaxLinearEquationSolver<ValueType>::CudaMinMaxLinearEquationSolver(storm::storage::SparseMatrix<ValueType> const& A) : StandardMinMaxLinearEquationSolver<ValueType>(A) {
            // Intentionally left empty.
        }

        template<typename ValueType>
        CudaMinMaxLinearEquationSolver<ValueType>::CudaMinMaxLinearEquationSolver(storm::storage::SparseMatrix<ValueType>&& A) : StandardMinMaxLinearEquationSolver<ValueType>(std::move(A)) {
            // Intentionally left empty.
        }

        template<typename ValueType>
        CudaMinMaxLinearEquationSolver<ValueType>::CSRMatrix::CSRMatrix(storm::storage::SparseMatrix<ValueType> const* A) {

            this->matrixRowCount = A->getRowCount();
            this->matrixNnzCount = A->getNonzeroEntryCount();
            this->matrixRowGroupCount = A->getRowGroupCount();

            auto *columnsIndicesAndValues = &(A->getColumnsAndValues());
            for (auto it = std::make_move_iterator(columnsIndicesAndValues->begin()),
                     end = std::make_move_iterator(columnsIndicesAndValues->end()); it != end; ++it) {
                this->columnIndices.push_back(std::move(it->getColumn()));
                this->nnzValues.push_back(std::move(it->getValue()));
            }
            
            this->rowStartIndices = &(A->getRowIndications());
            this->rowGroupIndices = &(A->getRowGroupIndices());
        }


        template<typename ValueType>
		bool CudaMinMaxLinearEquationSolver<ValueType>::internalSolveEquations(Environment const& env, OptimizationDirection dir, std::vector<ValueType>& x, std::vector<ValueType> const& b) const {
#ifdef STORM_HAVE_CUDASYNTHESIS

            ValueType precision = storm::utility::convertNumber<ValueType>(env.solver().minMax().getPrecision());
            uint64_t maxIters = env.solver().minMax().getMaximalNumberOfIterations();
            bool relative = env.solver().minMax().getRelativeTerminationCriterion();

            CSRMatrix matrix(this->A);
            bool result = false;
            size_t globalIterations = 0;

            std::cout << "matrix:\n";
            std::cout << *(this->A) << "\n";
            std::cout << sizeof(matrix.rowStartIndices) << "\n";

            std::cout << "rowStartIndices:\n";
            for (int i = 0; i < matrix.rowStartIndices->size(); i++) {
                std::cout << matrix.rowStartIndices->at(i) << ", ";
            }std::cout << "\n";
            std::cout << "columnIndices:\n";
            for (int i = 0; i < matrix.columnIndices.size(); i++) {
                std::cout << matrix.columnIndices.at(i) << ", ";
            }std::cout << "\n";
            std::cout << "nnzValues:\n";
            for (int i = 0; i < matrix.nnzValues.size(); i++) {
                std::cout << matrix.nnzValues.at(i) << ", ";
            }std::cout << "\n";
            std::cout << "rowGroupIndices:\n";
            for (int i = 0; i < matrix.rowGroupIndices->size(); i++) {
                std::cout << matrix.rowGroupIndices->at(i) << ", ";
            }std::cout << "\n";
            

            if (dir == OptimizationDirection::Minimize) {
                //TODO:call minimize GPU solver
                result = false;
            } else {
                //TODO:call maximize GPU solver
                result = false;   
            }

            if (!result) {
                STORM_LOG_WARN("Iterative solver did not converged after " << globalIterations << " iterations.");
                STORM_LOG_ERROR("An error occurred in the CUDA Plugin. Can not continue.");
                throw storm::exceptions::InvalidStateException() << "An error occurred in the CUDA Plugin. Can not continue.";
            } else {
                STORM_LOG_INFO("Iterative solver converged after " << globalIterations << " iterations.");
            }

#else
            STORM_LOG_ERROR("This version of storm does not support CUDA acceleration. Internal Error!");
            throw storm::exceptions::InvalidStateException() << "This version of storm does not support CUDA acceleration. Internal Error!";
#endif

            return result;
        }

        // Explicitly instantiate the solver.
		template class CudaMinMaxLinearEquationSolver<double>;
    } // namespace solver
} // namespace storm