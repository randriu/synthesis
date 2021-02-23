#include "jacobiIteration.h"

#include <thrust/functional.h>
#include <thrust/transform.h>
#include <thrust/device_ptr.h>
#include <thrust/reduce.h>

#include <cuda_runtime.h>
#include <cuda.h>
#include <cusparse.h>

#define FULL_WARP_MASK 0xffffffff
#define USE_CUSPARSE

template<typename T, bool Relative>
struct equalModuloPrecision : public thrust::binary_function<T,T,T>
{
__host__ __device__ T operator()(const T &x, const T &y) const
{
    if (Relative) {
		if (y == 0) {
			return ((x >= 0) ? (x) : (-x));
		}
		const T result = (x - y) / y;
		return ((result >= 0) ? (result) : (-result));
    } else {
        const T result = (x - y);
		return ((result >= 0) ? (result) : (-result));
    }
}
};

/**
 * @brief 
 * 
 * @tparam ValueType 
 * @param b 
 * @param D 
 * @param x 
 * @param n 
 */
template<typename ValueType>
__global__ void 
gather(const ValueType *b, const ValueType *D, ValueType *x, const uint_fast64_t n) {
    uint_fast64_t i = blockDim.x * blockIdx.x + threadIdx.x;

    if(i < n) {
        x[i] = (b[i] - x[i]) * D[i];
    }
}

/**
 * @brief 
 * 
 * @param x 
 */
__inline__ __device__ 
uint_fast64_t prev_power_of_2 (uint_fast64_t x) {
    
    x = x | (x >> 1);
    x = x | (x >> 2);
    x = x | (x >> 4);
    x = x | (x >> 8);
    x = x | (x >> 16);
    x = x | (x >> 32);
    
    return x - (x >> 1);
}

/**
 * @brief 
 * 
 * @tparam ValueType 
 * @param val 
 */
template<typename ValueType>
__inline__ __device__ 
ValueType warp_reduce (ValueType val) {

    val += __shfl_down_sync(FULL_WARP_MASK, val, 16);
    val += __shfl_down_sync(FULL_WARP_MASK, val, 8);
    val += __shfl_down_sync(FULL_WARP_MASK, val, 4);
    val += __shfl_down_sync(FULL_WARP_MASK, val, 2);
    val += __shfl_down_sync(FULL_WARP_MASK, val, 1);

    return val;
}

/**
 * @brief 
 * 
 * @tparam ValueType 
 * @param col_ids 
 * @param row_ptr 
 * @param row_blocks 
 * @param data 
 * @param x 
 * @param y 
 */
template<typename ValueType>
__global__ void csr_spmv_adaptive_kernel (const uint_fast64_t *col_ids, const uint_fast64_t *row_ptr, const uint_fast64_t *row_blocks, const ValueType *data, const ValueType *x, ValueType *y) {

    const uint_fast64_t block_row_begin = row_blocks[blockIdx.x];
    const uint_fast64_t block_row_end = row_blocks[blockIdx.x + 1];
    const uint_fast64_t nnz_per_block = row_ptr[block_row_end] - row_ptr[block_row_begin]; 

    __shared__ ValueType cache[NNZ_PER_WG];

    if (block_row_end - block_row_begin > 1) {
        // CSR-Stream case...
        const uint_fast64_t i = threadIdx.x;
        const uint_fast64_t block_data_begin = row_ptr[block_row_begin];
        const uint_fast64_t thread_data_begin = block_data_begin + i;

        /**
         * Some block of rows may contain less than NNZ_PER_WG elements. But at 
         * most NNZ_PER_WG elements. (NNZ_PER_WG == blockDim.x -- Each thread has
         * one non-zero element to process.)
         */

        if (i < nnz_per_block) 
            cache[i] = data[thread_data_begin] * x[col_ids[thread_data_begin]];
        __syncthreads ();
        
        /**
         * If matrix is too sparse each thread will reduce 1 row. So one row
         * is reduced by one thread. In case that matrix is not too sparse and there
         * is more non-zero elements in one row than one row is reduced by multiple 
         * threads.
         */
        const uint_fast64_t threads_for_reduction = prev_power_of_2(blockDim.x/(block_row_end - block_row_begin));
            
        if (threads_for_reduction > 1) {
            // Reduce all non zeroes of row by multiple thread
            const uint_fast64_t thread_in_block = i % threads_for_reduction;
            const uint_fast64_t local_row = block_row_begin + i/threads_for_reduction;

            ValueType sum = 0.0;

            if (local_row < block_row_end) {
                const uint_fast64_t local_first_element = row_ptr[local_row] - row_ptr[block_row_begin];
                const uint_fast64_t local_last_element = row_ptr[local_row + 1] - row_ptr[block_row_begin];

                for(uint_fast64_t local_element = local_first_element + thread_in_block;
                    local_element < local_last_element;
                    local_element += threads_for_reduction) 
                    {
                        sum += cache[local_element];    
                    }
            }
            __syncthreads();
            cache[i] = sum;

            // Now each row has "threads_for_reduction" values in cache
            for (int j = threads_for_reduction / 2; j > 0; j >>= 1) {
                // Reduce for each row
                __syncthreads();

                const bool use_result = thread_in_block < j && i + j < NNZ_PER_WG;

                if (use_result)
                    sum += cache[i+j];
                __syncthreads();

                if(use_result)
                    cache[i] = sum;
            }
          
            if(thread_in_block == 0 && local_row < block_row_end)
                y[local_row] = sum;
        
        } else {
            // Reduce all non zeros of row by single thread
            uint_fast64_t local_row = block_row_begin + i;

            while (local_row < block_row_end) {
                ValueType sum = 0.0;

                for (uint_fast64_t j = row_ptr[local_row] - block_data_begin;
                    j < row_ptr[local_row + 1] - block_data_begin;
                    j++) 
                    {
                        sum += cache[j];
                    }
                y[local_row] = sum;
                local_row += NNZ_PER_WG;
            }
        }
    } else {
        /**
         * Row Block == Row => NNZ_PER_WG <= nnz_per_block
         * If a block of rows contains only one row, then it can have 
         * NNZ_PER_WG (blockDim.x) <= nnz_per_block (also blockDim.x > nnz_per_block 
         * is possible). 
         */
        const uint_fast64_t nnz_per_block = row_ptr[block_row_end] - row_ptr[block_row_begin]; 

        if (nnz_per_block <= 64) {
            // CSR-Vector case...
            const uint_fast64_t thread_id = threadIdx.x;
            const uint_fast64_t warp_id = thread_id / warpSize;
            ValueType sum = 0.0;

            if (warp_id == 0) {
                // only one warp processes a whole row
                const uint_fast64_t row_start = row_ptr[block_row_begin];
                const uint_fast64_t row_end = row_ptr[block_row_end];

                for(uint_fast64_t element = row_start + thread_id; element < row_end; element += warpSize) {
                    sum += data[element] * x[col_ids[element]];
                }

                sum = warp_reduce<ValueType>(sum);

                if(thread_id == 0)
                    y[block_row_begin] = sum;
            }
        }  else {
            // CSR-VectorL case...
            const uint_fast64_t thread_id = threadIdx.x;
             
            const uint_fast64_t row_start = row_ptr[block_row_begin];
            const uint_fast64_t row_end = row_ptr[block_row_end];
            
            ValueType sum = 0.0;
            for(uint_fast64_t element = row_start + thread_id; element < row_end; element += blockDim.x)
                sum += data[element] * x[col_ids[element]];

            cache[thread_id] = sum;
            __syncthreads();

            for(int stride = blockDim.x / 2; stride > 0;  stride >>= 1) {
                if(thread_id < stride) 
                    cache[thread_id] += cache[thread_id + stride];
                __syncthreads();
            }

            __syncthreads();

            if(thread_id == 0) 
                y[block_row_begin] = cache[thread_id];
        }
    }
}

template<bool Relative, typename ValueType, cudaDataType CUDA_DATATYPE>
bool jacobiIteration_solver(
                uint_fast64_t const maxIterationCount, 
                ValueType const precision,
                uint_fast64_t const matrixRowCount,
                uint_fast64_t const matrixNnzCount,
                uint_fast64_t const matrixBlockCount,
                std::vector<ValueType>& x,
                std::vector<ValueType> const& b,
                std::vector<ValueType> const& nnzValues,
                std::vector<ValueType> const& D,
                std::vector<uint_fast64_t> const& columnIndices,
                std::vector<uint_fast64_t> const& rowStartIndices,
                std::vector<uint_fast64_t> const& rowBlocks,
                size_t& iterationCount)
{
    std::cout << "CUDA Jacobi method\n";

    uint_fast64_t* device_columnIndices = nullptr;
    uint_fast64_t* device_rowStartIndices = nullptr; 
    uint_fast64_t* device_rowBlocks = nullptr;

    ValueType* device_x = nullptr;
    ValueType* device_xSwap = nullptr;
    ValueType* device_b = nullptr;
    ValueType* device_D = nullptr;
    ValueType* device_nnzValues = nullptr;

    bool converged = false;
    iterationCount = 0;

    // Device memory allocation
    cudaError_t cudaMallocResult;
    bool errorOccured = false;

    dim3 gatherGridDim(ceil(double(matrixRowCount)/NNZ_PER_WG));

#ifdef USE_CUSPARSE
    ValueType            alpha      = 1.0f;
    ValueType            beta       = 0.0f;
    // CUSPARSE APIs
    cusparseHandle_t     handle = NULL;
    cusparseSpMatDescr_t matA;
    cusparseDnVecDescr_t vecX, vecY;
    void*                dBuffer    = NULL;
    size_t               bufferSize = 0;
#endif

    cudaMallocResult = cudaMalloc<uint_fast64_t>((&device_columnIndices), sizeof(uint_fast64_t) * columnIndices.size());
    if (cudaMallocResult != cudaSuccess) {
        std::cout << "Could not allocate memory for Matrix Column Indices, Error Code " << cudaMallocResult << "." << std::endl;
        errorOccured = true;
        goto cleanup;
    }

    cudaMallocResult = cudaMalloc<uint_fast64_t>((&device_rowStartIndices), sizeof(uint_fast64_t) * (matrixRowCount + 1));
    if (cudaMallocResult != cudaSuccess) {
        std::cout << "Could not allocate memory for Row Start Indices, Error Code " << cudaMallocResult << "." << std::endl;
        errorOccured = true;
        goto cleanup;
    }

#ifndef USE_CUSPARSE
    cudaMallocResult = cudaMalloc<uint_fast64_t>((&device_rowBlocks), sizeof(uint_fast64_t) * (matrixBlockCount + 1));
    if (cudaMallocResult != cudaSuccess) {
        std::cout << "Could not allocate memory for Row Blocks, Error Code " << cudaMallocResult << "." << std::endl;
        errorOccured = true;
        goto cleanup;
    }
#endif

    cudaMallocResult = cudaMalloc<ValueType>((&device_x), sizeof(ValueType) * matrixRowCount);
    if (cudaMallocResult != cudaSuccess) {
        std::cout << "Could not allocate memory for Vector x, Error Code " << cudaMallocResult << "." << std::endl;
        errorOccured = true;
        goto cleanup;
    }

    cudaMallocResult = cudaMalloc<ValueType>((&device_xSwap), sizeof(ValueType) * matrixRowCount);
    if (cudaMallocResult != cudaSuccess) {
        std::cout << "Could not allocate memory for Vector x swap, Error Code " << cudaMallocResult << "." << std::endl;
        errorOccured = true;
        goto cleanup;
    }

    cudaMallocResult = cudaMalloc<ValueType>((&device_b), sizeof(ValueType) * matrixRowCount);
    if (cudaMallocResult != cudaSuccess) {
        std::cout << "Could not allocate memory for Vector b, Error Code " << cudaMallocResult << "." << std::endl;
        errorOccured = true;
        goto cleanup;
    }

    cudaMallocResult = cudaMalloc<ValueType>((&device_D), sizeof(ValueType) * matrixRowCount);
    if (cudaMallocResult != cudaSuccess) {
        std::cout << "Could not allocate memory for Vector D, Error Code " << cudaMallocResult << "." << std::endl;
        errorOccured = true;
        goto cleanup;
    }

    cudaMallocResult = cudaMalloc<ValueType>((&device_nnzValues), sizeof(ValueType) * matrixNnzCount);
    if (cudaMallocResult != cudaSuccess) {
        std::cout << "Could not allocate memory for Vector of Matrix Values, Error Code " << cudaMallocResult << "." << std::endl;
        errorOccured = true;
        goto cleanup;
    }
    // Memory allocated, copy data to device
    cudaError_t cudaCopyResult;

    cudaCopyResult = cudaMemcpy(device_columnIndices, columnIndices.data(), sizeof(uint_fast64_t) * columnIndices.size(), cudaMemcpyHostToDevice);
    if (cudaCopyResult != cudaSuccess) {
        std::cout << "Could not copy data for Matrix Column Indices, Error Code " << cudaCopyResult << std::endl;
		errorOccured = true;
		goto cleanup;
    }

    cudaCopyResult = cudaMemcpy(device_rowStartIndices, rowStartIndices.data(), sizeof(uint_fast64_t) * (matrixRowCount + 1), cudaMemcpyHostToDevice);
    if (cudaCopyResult != cudaSuccess) {
        std::cout << "Could not copy data for Matrix Row Start Indices, Error Code " << cudaCopyResult << std::endl;
		errorOccured = true;
		goto cleanup;
    }

#ifndef USE_CUSPARSE
    cudaCopyResult = cudaMemcpy(device_rowBlocks, rowBlocks.data(), sizeof(uint_fast64_t) * (matrixBlockCount + 1), cudaMemcpyHostToDevice);
    if (cudaCopyResult != cudaSuccess) {
        std::cout << "Could not copy data for Matrix Row Blocks, Error Code " << cudaCopyResult << std::endl;
		errorOccured = true;
		goto cleanup;
    }
#endif
    
    cudaCopyResult = cudaMemcpy(device_x, x.data(), sizeof(ValueType) * matrixRowCount, cudaMemcpyHostToDevice);
    if (cudaCopyResult != cudaSuccess) {
        std::cout << "Could not copy data for Vector x, Error Code " << cudaCopyResult << std::endl;
		errorOccured = true;
		goto cleanup;
    }

    cudaCopyResult = cudaMemset(device_xSwap, 0, sizeof(ValueType) * matrixRowCount);
    if (cudaCopyResult != cudaSuccess) {
		std::cout << "Could not zero the Swap Vector x, Error Code " << cudaCopyResult << std::endl;
		errorOccured = true;
		goto cleanup;
    }

    cudaCopyResult = cudaMemcpy(device_b, b.data(), sizeof(ValueType) * matrixRowCount, cudaMemcpyHostToDevice);
    if (cudaCopyResult != cudaSuccess) {
        std::cout << "Could not copy data for Vector b, Error Code " << cudaCopyResult << std::endl;
		errorOccured = true;
		goto cleanup;
    }

    cudaCopyResult = cudaMemcpy(device_D, D.data(), sizeof(ValueType) * matrixRowCount, cudaMemcpyHostToDevice);
    if (cudaCopyResult != cudaSuccess) {
        std::cout << "Could not copy data for Vector D, Error Code " << cudaCopyResult << std::endl;
		errorOccured = true;
		goto cleanup;
    }
    
    cudaCopyResult = cudaMemcpy(device_nnzValues, nnzValues.data(), sizeof(ValueType) * matrixNnzCount, cudaMemcpyHostToDevice);
    if (cudaCopyResult != cudaSuccess) {
        std::cout << "Could not copy data for Matrix, Error Code " << cudaCopyResult << std::endl;
		errorOccured = true;
		goto cleanup;
    }

#ifdef USE_CUSPARSE
    // CUSPARSE APIs
    cusparseCreate(&handle); 
    // Create sparse matrix A in CSR format
    cusparseCreateCsr(&matA, matrixRowCount, matrixRowCount, matrixNnzCount, (void*)device_rowStartIndices, (void*)device_columnIndices, (void*)device_nnzValues, CUSPARSE_INDEX_64I, CUSPARSE_INDEX_64I, CUSPARSE_INDEX_BASE_ZERO, CUDA_DATATYPE);
    // Create dense vector X
    cusparseCreateDnVec(&vecX, matrixRowCount, (void*)device_x, CUDA_DATATYPE);
    // Create dense vector Y
    cusparseCreateDnVec(&vecY, matrixRowCount, (void*)device_xSwap, CUDA_DATATYPE);
    // allocate an external buffer
    cusparseSpMV_bufferSize(
        handle, CUSPARSE_OPERATION_NON_TRANSPOSE,
        &alpha, matA, vecX, &beta, vecY, CUDA_DATATYPE,
        CUSPARSE_CSRMV_ALG2, &bufferSize); 
    cudaMalloc(&dBuffer, bufferSize); 
#endif

    // Data is on device, start Kernel
    while (!converged && iterationCount < maxIterationCount) {
        // call kernels 
#ifdef USE_CUSPARSE        
        cusparseSpMV(handle, CUSPARSE_OPERATION_NON_TRANSPOSE, &alpha, matA, vecX, &beta, vecY, CUDA_DATATYPE, CUSPARSE_CSRMV_ALG2, dBuffer);
#else
        csr_spmv_adaptive_kernel<ValueType><<<matrixBlockCount, NNZ_PER_WG>>>(device_columnIndices, device_rowStartIndices, device_rowBlocks, device_nnzValues, device_x, device_xSwap); 
#endif
        gather<ValueType><<<gatherGridDim, NNZ_PER_WG>>>(device_b, device_D, device_xSwap, matrixRowCount);

        // Check for convergence
		// Transform: x = abs(x - xSwap)/ xSwap
		thrust::device_ptr<ValueType> devicePtrThrust_x(device_x);
		thrust::device_ptr<ValueType> devicePtrThrust_x_end(device_x + matrixRowCount);
        thrust::device_ptr<ValueType> devicePtrThrust_xSwap(device_xSwap);
        thrust::transform(devicePtrThrust_x, devicePtrThrust_x_end, devicePtrThrust_xSwap, devicePtrThrust_x, equalModuloPrecision<ValueType, Relative>());
        // Reduce: get Max over x and check for res < Precision
		ValueType maxX = thrust::reduce(devicePtrThrust_x, devicePtrThrust_x_end, -std::numeric_limits<ValueType>::max(), thrust::maximum<ValueType>());
		converged = (maxX < precision);
		++iterationCount;

		// Swap pointers, device_x always contains the most current result
        std::swap(device_x, device_xSwap);

#ifdef USE_CUSPARSE
        // set new values for vecX and vecY
        cusparseDnVecSetValues(vecX, (void*)device_x);
        cusparseDnVecSetValues(vecY, (void*)device_xSwap);
#endif
    }

    if (!converged && (iterationCount == maxIterationCount)) {
		iterationCount = 0;
		errorOccured = true;
    }
    
    // Get x (result) back from the device
	cudaCopyResult = cudaMemcpy(x.data(), device_x, sizeof(ValueType) * matrixRowCount, cudaMemcpyDeviceToHost);
	if (cudaCopyResult != cudaSuccess) {
		std::cout << "Could not copy back data for result vector x, Error Code " << cudaCopyResult << std::endl;
		errorOccured = true;
		goto cleanup;
	}

    // All code related to freeing memory and clearing up the device
cleanup:
    cudaError_t cudaFreeResult;

    if (device_columnIndices != nullptr) {
        cudaFreeResult = cudaFree(device_columnIndices);
        if (cudaFreeResult != cudaSuccess) {
            std::cout << "Could not free Memory of Matrix Column Indices, Error Code " << cudaFreeResult << "." << std::endl;
			errorOccured = true;
        }
        device_columnIndices = nullptr;
    }
    if (device_rowStartIndices != nullptr) {
        cudaFreeResult = cudaFree(device_rowStartIndices);
        if (cudaFreeResult != cudaSuccess) {
            std::cout << "Could not free Memory of Row Start Indices, Error Code " << cudaFreeResult << "." << std::endl;
			errorOccured = true;
        }
        device_rowStartIndices = nullptr;
    }
    if (device_rowBlocks != nullptr) {
        cudaFreeResult = cudaFree(device_rowBlocks);
        if (cudaFreeResult != cudaSuccess) {
            std::cout << "Could not free Memory of Row Blocks, Error Code " << cudaFreeResult << "." << std::endl;
			errorOccured = true;
        }
        device_rowBlocks = nullptr;
    }
    if (device_x != nullptr) {
        cudaFreeResult = cudaFree(device_x);
        if (cudaFreeResult != cudaSuccess) {
            std::cout << "Could not free Memory of Vector x, Error Code " << cudaFreeResult << "." << std::endl;
			errorOccured = true;
        }
        device_x = nullptr;
    }
    if (device_xSwap != nullptr) {
        cudaFreeResult = cudaFree(device_xSwap);
        if (cudaFreeResult != cudaSuccess) {
            std::cout << "Could not free Memory of Vector x swap, Error Code " << cudaFreeResult << "." << std::endl;
			errorOccured = true;
        }
        device_xSwap = nullptr;
    }
    if (device_b != nullptr) {
        cudaFreeResult = cudaFree(device_b);
        if (cudaFreeResult != cudaSuccess) {
            std::cout << "Could not free Memory of Vector b, Error Code " << cudaFreeResult << "." << std::endl;
			errorOccured = true;
        }
        device_b = nullptr;
    }
    if (device_D != nullptr) {
        cudaFreeResult = cudaFree(device_D);
        if (cudaFreeResult != cudaSuccess) {
            std::cout << "Could not free Memory of Vector D, Error Code " << cudaFreeResult << "." << std::endl;
			errorOccured = true;
        }
        device_D = nullptr;
    }
    if (device_nnzValues != nullptr) {
        cudaFreeResult = cudaFree(device_nnzValues);
        if (cudaFreeResult != cudaSuccess) {
            std::cout << "Could not free Memory of Matrix Values, Error Code " << cudaFreeResult << "." << std::endl;
			errorOccured = true;
        }
        device_nnzValues = nullptr;
    }

#ifdef USE_CUSPARSE
    // destroy matrix/vector descriptors
    cusparseDestroySpMat(matA);
    cusparseDestroyDnVec(vecX);
    cusparseDestroyDnVec(vecY);
    cusparseDestroy(handle);
    
    // device memory deallocation
    cudaFree(dBuffer);
#endif

    std::cout << "--------------------------------------------------------------\n";
    std::cout << "METRICS\n";
    std::cout << "Jacobi Iterations: " << iterationCount << "\n";
    std::cout << "Matrix dimension: " << matrixRowCount << "\n";
    std::cout << "Matrix nnz count: " << matrixNnzCount << "\n";
    std::cout << "--------------------------------------------------------------\n";

    return !errorOccured;
}

bool jacobiIteration_solver_double(uint_fast64_t const maxIterationCount, 
                double const precision,
                uint_fast64_t const matrixRowCount,
                uint_fast64_t const matrixNnzCount,
                uint_fast64_t const matrixBlockCount,
                std::vector<double> & x,
                std::vector<double> const& b,
                std::vector<double> const& nnzValues,
                std::vector<double> const& D,
                std::vector<uint_fast64_t> const& columnIndices,
                std::vector<uint_fast64_t> const& rowStartIndices,
                std::vector<uint_fast64_t> const& rowBlocks,
                size_t& iterationCount,
                bool const relativePrecisionCheck) {
    if (relativePrecisionCheck) {
        return jacobiIteration_solver<true, double, CUDA_R_64F>(maxIterationCount, precision, matrixRowCount, matrixNnzCount, matrixBlockCount, x, b, nnzValues, D, columnIndices, rowStartIndices, rowBlocks, iterationCount);
    } else {
        return jacobiIteration_solver<false, double, CUDA_R_64F>(maxIterationCount, precision, matrixRowCount, matrixNnzCount, matrixBlockCount, x, b, nnzValues, D, columnIndices, rowStartIndices, rowBlocks, iterationCount);
    }
}

bool jacobiIteration_solver_float(uint_fast64_t const maxIterationCount, 
                float const precision,
                uint_fast64_t const matrixRowCount,
                uint_fast64_t const matrixNnzCount,
                uint_fast64_t const matrixBlockCount,
                std::vector<float> & x,
                std::vector<float> const& b,
                std::vector<float> const& nnzValues,
                std::vector<float> const& D,
                std::vector<uint_fast64_t> const& columnIndices,
                std::vector<uint_fast64_t> const& rowStartIndices,
                std::vector<uint_fast64_t> const& rowBlocks,
                size_t& iterationCount,
                bool const relativePrecisionCheck) {
    if (relativePrecisionCheck) {
        return jacobiIteration_solver<true, float, CUDA_R_32F>(maxIterationCount, precision, matrixRowCount, matrixNnzCount, matrixBlockCount, x, b, nnzValues, D, columnIndices, rowStartIndices, rowBlocks, iterationCount);
    } else {
        return jacobiIteration_solver<false, float, CUDA_R_32F>(maxIterationCount, precision, matrixRowCount, matrixNnzCount, matrixBlockCount, x, b, nnzValues, D, columnIndices, rowStartIndices, rowBlocks, iterationCount);
    }
}
