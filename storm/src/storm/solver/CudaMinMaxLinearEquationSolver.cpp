#include "storm/solver/CudaMinMaxLinearEquationSolver.h"

#include "storm/utility/vector.h" // selectVectorValues
#include "storm/exceptions/IllegalArgumentException.h"
#include "storm/exceptions/InvalidStateException.h"
#include "storm/exceptions/InvalidEnvironmentException.h"
#include "storm/settings/SettingsManager.h"
#include "storm/settings/modules/MinMaxEquationSolverSettings.h"

#include "storm/environment/solver/MinMaxSolverEnvironment.h"

#include "storm-config.h"
#ifdef STORM_HAVE_CUDASYNTHESIS
#include "cudaForStorm.h"
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
            bool result = false;
            
#ifdef STORM_HAVE_CUDASYNTHESIS

            ValueType precision = storm::utility::convertNumber<ValueType>(env.solver().minMax().getPrecision());
            uint64_t maxIters = env.solver().minMax().getMaximalNumberOfIterations();
            bool relative = env.solver().minMax().getRelativeTerminationCriterion();

            CSRMatrix matrix(this->A);
            size_t globalIterations = 0;
            uint_fast64_t schedulerSize;
            bool const extractScheduler = this->isTrackSchedulerSet();
            bool const solveMultipleInstances = env.solver().minMax().isSolveMultipleInstancesSet(); 
            
            const std::vector<uint_fast64_t>* rowGroupIndicesAsKeys = (solveMultipleInstances) ? &(this->A->getRowGroupIndicesAsKeys()) : NULL;

            if (extractScheduler) {
                schedulerSize = (solveMultipleInstances) ? this->A->getSchedulerSize() : this->A->getRowGroupCount();
                this->schedulerChoices = std::vector<uint_fast64_t>(schedulerSize); 
            }

            if (dir == OptimizationDirection::Minimize) {
                result = __valueIteration_solver_minimize<uint_fast64_t, ValueType>(schedulerSize, solveMultipleInstances, maxIters, precision, relative, *matrix.rowStartIndices, matrix.columnIndices, matrix.nnzValues, x, b, *matrix.rowGroupIndices, *rowGroupIndicesAsKeys, globalIterations, extractScheduler, &this->schedulerChoices.get());
            } else {
                result = __valueIteration_solver_maximize<uint_fast64_t, ValueType>(schedulerSize, solveMultipleInstances, maxIters, precision, relative, *matrix.rowStartIndices, matrix.columnIndices, matrix.nnzValues, x, b, *matrix.rowGroupIndices, *rowGroupIndicesAsKeys, globalIterations, extractScheduler, &this->schedulerChoices.get());
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