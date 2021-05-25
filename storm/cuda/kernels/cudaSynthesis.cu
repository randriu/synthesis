#include "cudaSynthesis.h"

#include <thrust/functional.h>
#include <thrust/transform.h>
#include <thrust/device_ptr.h>
#include <thrust/device_vector.h>
#include <thrust/host_vector.h>
#include <thrust/copy.h>
#include <thrust/reduce.h>
#include <thrust/remove.h>
#include <thrust/replace.h>
#include <thrust/scan.h>
#include <thrust/iterator/constant_iterator.h>
#include <thrust/iterator/discard_iterator.h>

#include <cub/device/device_segmented_reduce.cuh>

#include <cuda_runtime.h>
#include <cuda.h>
#include <cusparse.h>

#define FULL_WARP_MASK 0xffffffff
#define USE_CUSPARSE

#define CHECK_CUDA(ans) { cudaAssert((ans), __FILE__, __LINE__); }
inline void cudaAssert(cudaError_t code, const char *file, int line, bool abort=true)
{
   if (code != cudaSuccess) {
      fprintf(stderr,"CUDA API assert: %s %s %d\n", cudaGetErrorString(code), file, line);
      if (abort) exit(code);
   }
}

#define CHECK_CUSPARSE(func) { cusparseAssert((func), __FILE__, __LINE__); }                                                  
inline void cusparseAssert(cusparseStatus_t code, const char *file, int line, bool abort=true)
{                                                                             
    if (code != CUSPARSE_STATUS_SUCCESS) {                                   
        fprintf(stderr,"CUSPARSE API assert: %s %s %d\n", cusparseGetErrorString(code), file, line);    
        if (abort) exit(code);                                             
    }                                                                          
}

/*******************************************************************************/
/*                             DEVICE CODE                                     */
/*******************************************************************************/

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

template<typename T>
struct is_minus_one
{
  __host__ __device__
  bool operator()(const T x) {
    return (x == T(-1.0));
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
ValueType sumSingleWarpReg (ValueType val) {

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
 * @param val 
 * @param threads_per_row 
 */
 template<typename ValueType>
 __inline__ __device__ 
 ValueType minSingleWarpReg (ValueType val, ValueType minMaxInitializer, uint32_t threads_per_row) {
    ValueType localMin = minMaxInitializer;
    
    switch (threads_per_row) {
        case 32:
            localMin = __shfl_down_sync(FULL_WARP_MASK, val, 16); 
            val = (val < localMin) ? val : localMin;
        case 16:
            localMin = __shfl_down_sync(FULL_WARP_MASK, val, 8); 
            val = (val < localMin) ? val : localMin;
        case 8:
            localMin = __shfl_down_sync(FULL_WARP_MASK, val, 4); 
            val = (val < localMin) ? val : localMin;
        case 4:
            localMin = __shfl_down_sync(FULL_WARP_MASK, val, 2); 
            val = (val < localMin) ? val : localMin;
        case 2:
            localMin = __shfl_down_sync(FULL_WARP_MASK, val, 1); 
            val = (val < localMin) ? val : localMin;
    }

    return val;
 }

 /**
 * @brief 
 * 
 * @tparam ValueType 
 * @param val 
 * @param threads_per_row  
 */
 template<typename ValueType>
 __inline__ __device__ 
 ValueType maxSingleWarpReg (ValueType val, ValueType minMaxInitializer, uint32_t threads_per_row) {
    ValueType localMax = minMaxInitializer;
    
    switch (threads_per_row) {
        case 32:
            localMax = __shfl_down_sync(FULL_WARP_MASK, val, 16); 
            val = (val > localMax) ? val : localMax;
        case 16:
            localMax = __shfl_down_sync(FULL_WARP_MASK, val, 8); 
            val = (val > localMax) ? val : localMax;
        case 8:
            localMax = __shfl_down_sync(FULL_WARP_MASK, val, 4); 
            val = (val > localMax) ? val : localMax;
        case 4:
            localMax = __shfl_down_sync(FULL_WARP_MASK, val, 2); 
            val = (val > localMax) ? val : localMax;
        case 2:
            localMax = __shfl_down_sync(FULL_WARP_MASK, val, 1); 
            val = (val > localMax) ? val : localMax;
    }

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
__global__ void csr_spmv_adaptable_kernel (const uint_fast64_t *col_ids, const uint_fast64_t *row_ptr, const uint_fast64_t *row_blocks, const ValueType *data, const ValueType *x, ValueType *y) {

    const uint_fast64_t block_begin = row_blocks[blockIdx.x];
    const uint_fast64_t block_end = row_blocks[blockIdx.x + 1];
    const uint_fast64_t nnz_per_block = row_ptr[block_end] - row_ptr[block_begin]; 

    __shared__ ValueType multRes[NNZ_PER_WG];

    if (block_end - block_begin > 1) {
        // CSR-Stream case...
        const uint_fast64_t thread_id = threadIdx.x;
        const uint_fast64_t block_data_begin = row_ptr[block_begin];
        const uint_fast64_t thread_data_begin = block_data_begin + thread_id;
        /**
         * Block of rows may contain less than NNZ_PER_WG elements. But at 
         * most NNZ_PER_WG elements. (NNZ_PER_WG == blockDim.x -- Each thread has
         * one non-zero element to process.)
         */
        if (thread_id < nnz_per_block) 
            multRes[thread_id] = data[thread_data_begin] * x[col_ids[thread_data_begin]];
        __syncthreads ();
        
        /**
         * If matrix is too sparse each thread will reduce 1 row. So one row
         * is reduced by one thread. In case that matrix is not too sparse and there
         * is more non-zero elements in one row than one row is reduced by multiple 
         * threads.
         */
        const uint_fast64_t threads_for_reduction = prev_power_of_2(blockDim.x/(block_end - block_begin));
        if (threads_for_reduction > 1) {
            // Reduce all non zeroes of row by multiple thread
            const uint_fast64_t thread_in_block = thread_id % threads_for_reduction;
            const uint_fast64_t local_row = block_begin + thread_id/threads_for_reduction;

            ValueType sum = 0.0;

            if (local_row < block_end) {
                const uint_fast64_t local_first_element = row_ptr[local_row] - row_ptr[block_begin];
                const uint_fast64_t local_last_element = row_ptr[local_row + 1] - row_ptr[block_begin];

                for(uint_fast64_t local_element = local_first_element + thread_in_block; local_element < local_last_element; local_element += threads_for_reduction) {
                    sum += multRes[local_element];    
                }
            }
            __syncthreads();
            multRes[thread_id] = sum;

            // Now each row has "threads_for_reduction" values in multRes
            for (int j = threads_for_reduction / 2; j > 0; j >>= 1) {
                // Reduce for each row
                __syncthreads();

                const bool use_result = thread_in_block < j && thread_id + j < NNZ_PER_WG;

                sum = (use_result) ? sum + multRes[thread_id + j] : sum;
                __syncthreads();

                if(use_result)
                    multRes[thread_id] = sum;
            }
          
            if(thread_in_block == 0 && local_row < block_end)
                y[local_row] = sum;
        
        } else {
            // Reduce all non zeros of row by single thread
            uint_fast64_t local_row = block_begin + thread_id;
            while (local_row < block_end) {
                ValueType sum = 0.0;

                for (uint_fast64_t j = row_ptr[local_row] - block_data_begin; j < row_ptr[local_row + 1] - block_data_begin; j++) {
                    sum += multRes[j];
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
        const uint_fast64_t nnz_per_block = row_ptr[block_end] - row_ptr[block_begin]; 

        if (nnz_per_block <= 64) {
            // CSR-Vector case...
            const uint_fast64_t thread_id = threadIdx.x;
            const uint_fast64_t warp_id = thread_id / warpSize;
            ValueType sum = 0.0;

            if (warp_id == 0) {
                // only one warp processes a whole row
                const uint_fast64_t row_start = row_ptr[block_begin];
                const uint_fast64_t row_end = row_ptr[block_end];

                for(uint_fast64_t element = row_start + thread_id; element < row_end; element += warpSize) {
                    sum += data[element] * x[col_ids[element]];
                }

                sum = sumSingleWarpReg<ValueType>(sum);

                if(thread_id == 0)
                    y[block_begin] = sum;
            }
        }  else {
            // CSR-VectorL case...
            const uint_fast64_t thread_id = threadIdx.x;
             
            const uint_fast64_t row_start = row_ptr[block_begin];
            const uint_fast64_t row_end = row_ptr[block_end];
            
            ValueType sum = 0.0;
            for(uint_fast64_t element = row_start + thread_id; element < row_end; element += blockDim.x)
                sum += data[element] * x[col_ids[element]];

            multRes[thread_id] = sum;
            __syncthreads();

            for(int stride = blockDim.x / 2; stride > 0;  stride >>= 1) {
                if(thread_id < stride) 
                    multRes[thread_id] += multRes[thread_id + stride];
                __syncthreads();
            }

            __syncthreads();

            if(thread_id == 0) 
                y[block_begin] = multRes[thread_id];
        }
    }
}

template <typename ValueType, unsigned int GROUPS_PER_BLOCK, unsigned int THREADS_PER_GROUP, bool Maximize>
__launch_bounds__(GROUPS_PER_BLOCK * THREADS_PER_GROUP,1) 
__global__ void
segmented_vector_reduce_kernel(const uint_fast64_t num_groups, const uint_fast64_t * __restrict__ nondeterministicChoiceIndices, ValueType * __restrict__ result, const ValueType * __restrict__ input, const ValueType minMaxInitializer)
{
    __shared__ volatile uint_fast64_t groups_pointers[GROUPS_PER_BLOCK][2];
    
    const uint_fast64_t THREADS_PER_BLOCK = GROUPS_PER_BLOCK * THREADS_PER_GROUP;

    const uint_fast64_t thread_id   = THREADS_PER_BLOCK * blockIdx.x + threadIdx.x;// global thread index
    const uint_fast64_t thread_lane = threadIdx.x & (THREADS_PER_GROUP - 1);       // thread index within the group
    const uint_fast64_t group_id   = thread_id   /  THREADS_PER_GROUP;             // global vector index
    const uint_fast64_t group_lane = threadIdx.x /  THREADS_PER_GROUP;             // vector index within the block
    const uint_fast64_t num_states = GROUPS_PER_BLOCK * gridDim.x;                 // total number of active groups

    for(uint_fast64_t row = group_id; row < num_groups; row += num_states) {
        if(thread_lane < 2)
            groups_pointers[group_lane][thread_lane] = nondeterministicChoiceIndices[row + thread_lane];

        const uint_fast64_t group_start = groups_pointers[group_lane][0];
        const uint_fast64_t group_end   = groups_pointers[group_lane][1];

        // initialize local Min/Max
        ValueType localMinMax = minMaxInitializer;

        if (THREADS_PER_GROUP == 32 && group_end - group_start > 32) {
            // ensure aligned memory access
            uint_fast64_t index = group_start - (group_start & (THREADS_PER_GROUP - 1)) + thread_lane;

            if(index >= group_start && index < group_end) {
				if(Maximize) { localMinMax = (localMinMax < input[index]) ? input[index] : localMinMax; } 
                else         { localMinMax = (localMinMax > input[index]) ? input[index] : localMinMax; }
			}
            // accumulate local sums
            for(index += THREADS_PER_GROUP; index < group_end; index += THREADS_PER_GROUP) {
                if(Maximize) { localMinMax = (localMinMax < input[index]) ? input[index] : localMinMax; } 
                else         { localMinMax = (localMinMax > input[index]) ? input[index] : localMinMax; }
            }
        } else {
            // accumulate local sums
            for(uint_fast64_t index = group_start + thread_lane; index < group_end; index += THREADS_PER_GROUP)
                if(Maximize) { localMinMax = (localMinMax < input[index]) ? input[index] : localMinMax; } 
                else         { localMinMax = (localMinMax > input[index]) ? input[index] : localMinMax; }
        }

        // reduce local min/max to row min/max
        localMinMax = (Maximize) ? maxSingleWarpReg<ValueType>(localMinMax, minMaxInitializer, THREADS_PER_GROUP) : 
                                   minSingleWarpReg<ValueType>(localMinMax, minMaxInitializer, THREADS_PER_GROUP) ;

        if (thread_lane == 0)
            result[row] = (localMinMax == minMaxInitializer) ? 0.0 : localMinMax;
    }
}

/*******************************************************************************/
/*                               HOST CODE                                     */
/*******************************************************************************/

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

    bool errorOccured = false;
    bool converged = false;
    iterationCount = 0;

    uint_fast64_t* device_columnIndices = nullptr;
    uint_fast64_t* device_rowStartIndices = nullptr; 
    uint_fast64_t* device_rowBlocks = nullptr;

    ValueType* device_x = nullptr;
    ValueType* device_xSwap = nullptr;
    ValueType* device_b = nullptr;
    ValueType* device_D = nullptr;
    ValueType* device_nnzValues = nullptr;

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

    // Device memory allocation
    CHECK_CUDA( cudaMalloc<uint_fast64_t>((&device_columnIndices), sizeof(uint_fast64_t) * columnIndices.size()) );
    CHECK_CUDA( cudaMalloc<uint_fast64_t>((&device_rowStartIndices), sizeof(uint_fast64_t) * (matrixRowCount + 1)) );
    
    CHECK_CUDA( cudaMalloc<ValueType>((&device_x), sizeof(ValueType) * matrixRowCount) );
    CHECK_CUDA( cudaMalloc<ValueType>((&device_xSwap), sizeof(ValueType) * matrixRowCount) );
    CHECK_CUDA( cudaMalloc<ValueType>((&device_b), sizeof(ValueType) * matrixRowCount) );
    CHECK_CUDA( cudaMalloc<ValueType>((&device_D), sizeof(ValueType) * matrixRowCount) );
    CHECK_CUDA( cudaMalloc<ValueType>((&device_nnzValues), sizeof(ValueType) * matrixNnzCount) );
#ifndef USE_CUSPARSE
    CHECK_CUDA( cudaMallocResult = cudaMalloc<uint_fast64_t>((&device_rowBlocks), sizeof(uint_fast64_t) * (matrixBlockCount + 1)) );
#endif

    // Memory allocated, copy data to device
    CHECK_CUDA( cudaMemcpy(device_columnIndices, columnIndices.data(), sizeof(uint_fast64_t) * columnIndices.size(), cudaMemcpyHostToDevice) );
    CHECK_CUDA( cudaMemcpy(device_rowStartIndices, rowStartIndices.data(), sizeof(uint_fast64_t) * (matrixRowCount + 1), cudaMemcpyHostToDevice) );
    
    CHECK_CUDA( cudaMemcpy(device_x, x.data(), sizeof(ValueType) * matrixRowCount, cudaMemcpyHostToDevice) );
    CHECK_CUDA( cudaMemset(device_xSwap, 0, sizeof(ValueType) * matrixRowCount) );
    CHECK_CUDA( cudaMemcpy(device_b, b.data(), sizeof(ValueType) * matrixRowCount, cudaMemcpyHostToDevice) );
    CHECK_CUDA( cudaMemcpy(device_D, D.data(), sizeof(ValueType) * matrixRowCount, cudaMemcpyHostToDevice) );
    CHECK_CUDA( cudaMemcpy(device_nnzValues, nnzValues.data(), sizeof(ValueType) * matrixNnzCount, cudaMemcpyHostToDevice) );
#ifndef USE_CUSPARSE
    CHECK_CUDA( cudaMemcpy(device_rowBlocks, rowBlocks.data(), sizeof(uint_fast64_t) * (matrixBlockCount + 1), cudaMemcpyHostToDevice) );
#endif

    // CUSPARSE settings
#ifdef USE_CUSPARSE
    CHECK_CUSPARSE( cusparseCreate(&handle) ); 
    CHECK_CUSPARSE( cusparseCreateCsr(&matA, matrixRowCount, matrixRowCount, matrixNnzCount, (void*)device_rowStartIndices, (void*)device_columnIndices, (void*)device_nnzValues, CUSPARSE_INDEX_64I, CUSPARSE_INDEX_64I, CUSPARSE_INDEX_BASE_ZERO, CUDA_DATATYPE) );
    CHECK_CUSPARSE( cusparseCreateDnVec(&vecX, matrixRowCount, (void*)device_x, CUDA_DATATYPE) );
    CHECK_CUSPARSE( cusparseCreateDnVec(&vecY, matrixRowCount, (void*)device_xSwap, CUDA_DATATYPE) );
    CHECK_CUSPARSE( cusparseSpMV_bufferSize(handle, CUSPARSE_OPERATION_NON_TRANSPOSE, &alpha, matA, vecX, &beta, vecY, CUDA_DATATYPE, CUSPARSE_CSRMV_ALG2, &bufferSize) ); 
    CHECK_CUDA( cudaMalloc(&dBuffer, bufferSize) ); 
#endif

    // Data is on device, start Kernel
    while (!converged && iterationCount < maxIterationCount) {
        // call kernels 
#ifdef USE_CUSPARSE        
        CHECK_CUSPARSE( cusparseSpMV(handle, CUSPARSE_OPERATION_NON_TRANSPOSE, &alpha, matA, vecX, &beta, vecY, CUDA_DATATYPE, CUSPARSE_CSRMV_ALG2, dBuffer) );
#else
        csr_spmv_adaptable_kernel<ValueType><<<matrixBlockCount, NNZ_PER_WG>>>(device_columnIndices, device_rowStartIndices, device_rowBlocks, device_nnzValues, device_x, device_xSwap); 
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
        CHECK_CUSPARSE( cusparseDnVecSetValues(vecX, (void*)device_x) );
        CHECK_CUSPARSE( cusparseDnVecSetValues(vecY, (void*)device_xSwap) );
#endif
    }

    if (!converged && (iterationCount == maxIterationCount)) {
		iterationCount = 0;
		errorOccured = true;
    }
    
    // Get x (result) back from the device
	CHECK_CUDA( cudaMemcpy(x.data(), device_x, sizeof(ValueType) * matrixRowCount, cudaMemcpyDeviceToHost) );

    // All code related to freeing memory and clearing up the device
    CHECK_CUDA( cudaFree(device_columnIndices) );
    CHECK_CUDA( cudaFree(device_rowStartIndices) );
    CHECK_CUDA( cudaFree(device_rowBlocks) );
    CHECK_CUDA( cudaFree(device_x) );
    CHECK_CUDA( cudaFree(device_xSwap) );
    CHECK_CUDA( cudaFree(device_b) );
    CHECK_CUDA( cudaFree(device_D) );
    CHECK_CUDA( cudaFree(device_nnzValues) );

#ifdef USE_CUSPARSE
    CHECK_CUSPARSE( cusparseDestroySpMat(matA) );
    CHECK_CUSPARSE( cusparseDestroyDnVec(vecX) );
    CHECK_CUSPARSE( cusparseDestroyDnVec(vecY) );
    CHECK_CUSPARSE( cusparseDestroy(handle) );
    CHECK_CUDA( cudaFree(dBuffer) );
#endif

    return !errorOccured;
}

template <typename ValueType, bool Maximize, unsigned int THREADS_PER_GROUP>
void __segmented_vector_reduce(const uint_fast64_t num_groups, const uint_fast64_t * nondeterministicChoiceIndices, ValueType * x, const ValueType * y)
{
	const ValueType minMaxInitializer = (Maximize) ? -std::numeric_limits<ValueType>::infinity() : std::numeric_limits<ValueType>::infinity();

    const size_t THREADS_PER_BLOCK  = 128;
    const size_t GROUPS_PER_BLOCK  = THREADS_PER_BLOCK / THREADS_PER_GROUP;
    const size_t NUM_BLOCKS = ceil(double(num_groups) / GROUPS_PER_BLOCK);

    segmented_vector_reduce_kernel<ValueType, GROUPS_PER_BLOCK, THREADS_PER_GROUP, Maximize> <<<NUM_BLOCKS, THREADS_PER_BLOCK>>> (num_groups, nondeterministicChoiceIndices, x, y, minMaxInitializer);
}

template <bool Maximize, typename ValueType>
void segmented_vector_reduce(const uint_fast64_t num_groups, const uint_fast64_t num_entries, const uint_fast64_t * nondeterministicChoiceIndices, ValueType * x, const ValueType * y)
{
    const uint_fast64_t threads_per_group = num_entries / num_groups;

    if (threads_per_group <=  2) { __segmented_vector_reduce<ValueType, Maximize, 2>(num_groups, nondeterministicChoiceIndices, x, y); return; }
    if (threads_per_group <=  4) { __segmented_vector_reduce<ValueType, Maximize, 4>(num_groups, nondeterministicChoiceIndices, x, y); return; }
    if (threads_per_group <=  8) { __segmented_vector_reduce<ValueType, Maximize, 8>(num_groups, nondeterministicChoiceIndices, x, y); return; }
    if (threads_per_group <= 16) { __segmented_vector_reduce<ValueType, Maximize,16>(num_groups, nondeterministicChoiceIndices, x, y); return; }
    
    __segmented_vector_reduce<ValueType, Maximize,32>(num_groups, nondeterministicChoiceIndices, x, y);
}

template <bool Maximize, bool Relative, typename ValueType, cudaDataType CUDA_DATATYPE>
bool valueIteration_solver(
                uint_fast64_t const maxIterationCount,
                ValueType const precision, 
                std::vector<uint_fast64_t> const& matrixRowIndices, 
                std::vector<uint_fast64_t> const& columnIndices, 
                std::vector<ValueType> const& nnzValues, 
                std::vector<ValueType> & x, 
                std::vector<ValueType> const& b, 
                std::vector<uint_fast64_t> const& nondeterministicChoiceIndices, 
                size_t& iterationCount, 
                bool const extractScheduler, 
                std::vector<uint_fast64_t>* choices) 
{

    bool errorOccured = false;
    bool converged = false;
    iterationCount = 0;

    uint_fast64_t* device_columnIndices = nullptr;
    uint_fast64_t* device_matrixRowIndices = nullptr;
    uint_fast64_t* device_nondeterministicChoiceIndices = nullptr;

    ValueType* device_nnzValues = nullptr;
    ValueType* device_x = nullptr;
    ValueType* device_xSwap = nullptr;
    ValueType* device_diff = nullptr;
    ValueType* device_b = nullptr;
	ValueType* device_multiplyResult = nullptr;

    const uint_fast64_t matrixRowCount = matrixRowIndices.size() - 1;
    const uint_fast64_t matrixColCount = nondeterministicChoiceIndices.size() - 1;
    const uint_fast64_t matrixNnzCount = nnzValues.size();

    // CUSPARSE APIs
    ValueType            alpha      = 1.0f;
    ValueType            beta       = 0.0f;
    cusparseHandle_t     handle     = NULL;
    cusparseSpMatDescr_t matA;
    cusparseDnVecDescr_t vecX, vecY;
    void*                dBuffer    = NULL;
    size_t               bufferSize = 0;
    
    // CUB APIs
    void     *dTempStorage = NULL;
    size_t   tempStorageBytes = 0;

    // Device memory allocation
    CHECK_CUDA( cudaMalloc<uint_fast64_t>((&device_columnIndices), sizeof(uint_fast64_t) * matrixNnzCount) );
    CHECK_CUDA( cudaMalloc<uint_fast64_t>((&device_matrixRowIndices), sizeof(uint_fast64_t) * (matrixRowCount + 1)) );
    CHECK_CUDA( cudaMalloc<uint_fast64_t>((&device_nondeterministicChoiceIndices), sizeof(uint_fast64_t) * (matrixColCount + 1)) );

    CHECK_CUDA( cudaMalloc<ValueType>((&device_nnzValues), sizeof(ValueType) * matrixNnzCount) );
    CHECK_CUDA( cudaMalloc<ValueType>((&device_x), sizeof(ValueType) * matrixColCount) );
    CHECK_CUDA( cudaMalloc<ValueType>((&device_xSwap), sizeof(ValueType) * matrixColCount) );
    CHECK_CUDA( cudaMalloc<ValueType>((&device_diff), sizeof(ValueType) * matrixColCount) );
    CHECK_CUDA( cudaMalloc<ValueType>((&device_b), sizeof(ValueType) * matrixRowCount) );
    CHECK_CUDA( cudaMalloc<ValueType>((&device_multiplyResult), sizeof(ValueType) * matrixRowCount) );

    // Memory allocated, copy data to device
    CHECK_CUDA( cudaMemcpy(device_columnIndices, columnIndices.data(), sizeof(uint_fast64_t) * matrixNnzCount, cudaMemcpyHostToDevice) );
    CHECK_CUDA( cudaMemcpy(device_matrixRowIndices, matrixRowIndices.data(), sizeof(uint_fast64_t) * (matrixRowCount + 1), cudaMemcpyHostToDevice) );
    CHECK_CUDA( cudaMemcpy(device_nondeterministicChoiceIndices, nondeterministicChoiceIndices.data(), sizeof(uint_fast64_t) * (matrixColCount + 1), cudaMemcpyHostToDevice) );

    CHECK_CUDA( cudaMemcpy(device_nnzValues, nnzValues.data(), sizeof(ValueType) * matrixNnzCount, cudaMemcpyHostToDevice) );
    CHECK_CUDA( cudaMemcpy(device_x, x.data(), sizeof(ValueType) * matrixColCount, cudaMemcpyHostToDevice) );
    CHECK_CUDA( cudaMemset(device_xSwap, 0, sizeof(ValueType) * matrixColCount) );
    CHECK_CUDA( cudaMemset(device_diff, 0, sizeof(ValueType) * matrixColCount) );
    CHECK_CUDA( cudaMemcpy(device_b, b.data(), sizeof(ValueType) * matrixRowCount, cudaMemcpyHostToDevice) );
    CHECK_CUDA( cudaMemset(device_multiplyResult, 0, sizeof(ValueType) * matrixRowCount) );

    // CUSPARSE settings
    CHECK_CUSPARSE( cusparseCreate(&handle) );
    CHECK_CUSPARSE( cusparseCreateCsr(&matA, matrixRowCount, matrixColCount, matrixNnzCount, (void*)device_matrixRowIndices, (void*)device_columnIndices, (void*)device_nnzValues, CUSPARSE_INDEX_64I, CUSPARSE_INDEX_64I, CUSPARSE_INDEX_BASE_ZERO, CUDA_DATATYPE) );
    CHECK_CUSPARSE( cusparseCreateDnVec(&vecX, matrixColCount, (void*)device_x, CUDA_DATATYPE) );
    CHECK_CUSPARSE( cusparseCreateDnVec(&vecY, matrixRowCount, (void*)device_multiplyResult, CUDA_DATATYPE) );
    CHECK_CUSPARSE( cusparseSpMV_bufferSize(handle, CUSPARSE_OPERATION_NON_TRANSPOSE, &alpha, matA, vecX, &beta, vecY, CUDA_DATATYPE, CUSPARSE_CSRMV_ALG2, &bufferSize) ); 
    CHECK_CUDA( cudaMalloc(&dBuffer, bufferSize) ); 

    // Thrust pointer initialization
    thrust::device_ptr<ValueType> devicePtrThrust_diff(device_diff);
    thrust::device_ptr<ValueType> devicePtrThrust_diff_end(device_diff + matrixColCount);
    thrust::device_ptr<ValueType> devicePtrThrust_b(device_b);
    thrust::device_ptr<ValueType> devicePtrThrust_multiplyResult(device_multiplyResult);

    // Data is on device, start Kernel
    while(!converged && iterationCount < maxIterationCount) {
        /* SPARSE MULT: transition matrix * x vector */
        CHECK_CUSPARSE( cusparseSpMV(handle, CUSPARSE_OPERATION_NON_TRANSPOSE, &alpha, matA, vecX, &beta, vecY, CUDA_DATATYPE, CUSPARSE_CSRMV_ALG2, dBuffer) );

        /* SAXPY: multiplyResult + b inplace to multiplyResult */
		thrust::transform(devicePtrThrust_multiplyResult, devicePtrThrust_multiplyResult + matrixRowCount, devicePtrThrust_b, devicePtrThrust_multiplyResult, thrust::plus<ValueType>());

        /* MAX/MIN_REDUCE: reduce multiplyResult to a new x vector */
        segmented_vector_reduce<Maximize, ValueType>(matrixColCount, matrixRowCount, device_nondeterministicChoiceIndices, device_xSwap, device_multiplyResult);
        
        /* INF_NORM: check for convergence */
        // Transform: diff = abs(x - xSwap)/ xSwap
		thrust::device_ptr<ValueType> devicePtrThrust_x(device_x);
		thrust::device_ptr<ValueType> devicePtrThrust_x_end(device_x + matrixColCount);
		thrust::device_ptr<ValueType> devicePtrThrust_xSwap(device_xSwap);
		thrust::transform(devicePtrThrust_x, devicePtrThrust_x_end, devicePtrThrust_xSwap, devicePtrThrust_diff, equalModuloPrecision<ValueType, Relative>());
		// Reduce: get Max over x and check for res < Precision
		ValueType maxX = thrust::reduce(devicePtrThrust_diff, devicePtrThrust_diff_end, -std::numeric_limits<ValueType>::max(), thrust::maximum<ValueType>());
		converged = (maxX < precision);
        ++iterationCount;

        // Swap pointers, device_x always contains the most current result
		std::swap(device_x, device_xSwap);
        CHECK_CUSPARSE( cusparseDnVecSetValues(vecX, (void*)device_x) );
    }

    if (!converged && (iterationCount == maxIterationCount)) {
		iterationCount = 0;
		errorOccured = true;
    }

    // repeat last iteration to extract scheduler
    if (extractScheduler) {
        /* SPARSE MULT: transition matrix * last x before convergence */
        CHECK_CUSPARSE( cusparseDnVecSetValues(vecX, (void*)device_xSwap) );
        CHECK_CUSPARSE( cusparseSpMV(handle, CUSPARSE_OPERATION_NON_TRANSPOSE, &alpha, matA, vecX, &beta, vecY, CUDA_DATATYPE, CUSPARSE_CSRMV_ALG2, dBuffer) );
        
        /* SAXPY: multiplyResult + b inplace to multiplyResult */
        thrust::transform(devicePtrThrust_multiplyResult, devicePtrThrust_multiplyResult + matrixRowCount, devicePtrThrust_b, devicePtrThrust_multiplyResult, thrust::plus<ValueType>());
        
        // CUB Memory allocation
        dTempStorage = NULL;
        tempStorageBytes = 0;

        std::vector<cub::KeyValuePair<int, ValueType>> host_choices(matrixColCount);
        thrust::device_vector<cub::KeyValuePair<int, ValueType>> device_choicesValues(matrixColCount);
        cub::KeyValuePair<int, ValueType>* device_choices = thrust::raw_pointer_cast(&device_choicesValues[0]);

        if (Maximize)   cub::DeviceSegmentedReduce::ArgMax(dTempStorage, tempStorageBytes, device_multiplyResult, device_choices, matrixColCount, device_nondeterministicChoiceIndices, device_nondeterministicChoiceIndices + 1);
        else            cub::DeviceSegmentedReduce::ArgMin(dTempStorage, tempStorageBytes, device_multiplyResult, device_choices, matrixColCount, device_nondeterministicChoiceIndices, device_nondeterministicChoiceIndices + 1); 
        CHECK_CUDA( cudaMalloc(&dTempStorage, tempStorageBytes) );
    
        /* MAX/MIN_REDUCE: reduce multiplyResult to a new [(choice,value),...] vector */
        (Maximize) ?
        cub::DeviceSegmentedReduce::ArgMax(dTempStorage, tempStorageBytes, device_multiplyResult, device_choices, matrixColCount, device_nondeterministicChoiceIndices, device_nondeterministicChoiceIndices + 1) :
        cub::DeviceSegmentedReduce::ArgMin(dTempStorage, tempStorageBytes, device_multiplyResult, device_choices, matrixColCount, device_nondeterministicChoiceIndices, device_nondeterministicChoiceIndices + 1) ; 
    
        /* Copy form device to host and set scheduler choices */
        thrust::copy(device_choicesValues.begin(), device_choicesValues.end(), host_choices.begin());
        for (int i = 0; i < host_choices.size(); i++) {
            choices->at(i) = host_choices[i].key;
        } 
    }

    // Get x (result) back from the device
    CHECK_CUDA( cudaMemcpy(x.data(), device_x, sizeof(ValueType) * matrixColCount, cudaMemcpyDeviceToHost) );

    // CUSPARSE free
    CHECK_CUSPARSE( cusparseDestroySpMat(matA) );
    CHECK_CUSPARSE( cusparseDestroyDnVec(vecX) );
    CHECK_CUSPARSE( cusparseDestroyDnVec(vecY) );
    CHECK_CUSPARSE( cusparseDestroy(handle) );

	// All code related to freeing memory and clearing up the device
    CHECK_CUDA( cudaFree(device_matrixRowIndices) );
    CHECK_CUDA( cudaFree(device_columnIndices) );
    CHECK_CUDA( cudaFree(device_nondeterministicChoiceIndices) );
    CHECK_CUDA( cudaFree(device_nnzValues) );
    CHECK_CUDA( cudaFree(device_x) );
    CHECK_CUDA( cudaFree(device_xSwap) );
    CHECK_CUDA( cudaFree(device_diff) );
    CHECK_CUDA( cudaFree(device_b) );
    CHECK_CUDA( cudaFree(device_multiplyResult) );
    CHECK_CUDA( cudaFree(dBuffer) );
    CHECK_CUDA( cudaFree(dTempStorage) );

    return !errorOccured;
}

template <bool Maximize, bool Relative, typename ValueType, cudaDataType CUDA_DATATYPE>
bool valueIteration_solver_multipleMDPs(
                size_t const schedulerSize,
                uint_fast64_t const maxIterationCount,
                ValueType const precision, 
                std::vector<uint_fast64_t> const& matrixRowIndices, 
                std::vector<uint_fast64_t> const& columnIndices, 
                std::vector<ValueType> const& nnzValues, 
                std::vector<ValueType> & x, 
                std::vector<ValueType> const& b, 
                std::vector<uint_fast64_t> const& nondeterministicChoiceIndices,
                std::vector<uint_fast64_t> const& choicesAsKeys,
                size_t& iterationCount, 
                bool const extractScheduler, 
                std::vector<uint_fast64_t>* choices) 
{

    bool errorOccured = false;
    bool converged = false;
    iterationCount = 0;

    uint_fast64_t* device_columnIndices = nullptr;
    uint_fast64_t* device_matrixRowIndices = nullptr;
    uint_fast64_t* device_nondeterministicChoiceIndices = nullptr;

    ValueType* device_nnzValues = nullptr;
    ValueType* device_x = nullptr;
    ValueType* device_xSwap = nullptr;
    ValueType* device_diff = nullptr;
    ValueType* device_b = nullptr;
	ValueType* device_multiplyResult = nullptr;

    const uint_fast64_t matrixRowCount = matrixRowIndices.size() - 1;
    const uint_fast64_t subfamiliesMatrixSize = nondeterministicChoiceIndices.size() - 1;
    const uint_fast64_t familiesCount = b.size() / matrixRowCount;
    const uint_fast64_t matrixColCount = x.size() / familiesCount;
    const uint_fast64_t matrixNnzCount = nnzValues.size();

    // CUSPARSE APIs (matC = matA * matB)
    ValueType            alpha      = 1.0f;
    ValueType            beta       = 0.0f;
    cusparseHandle_t     handle     = NULL;
    cusparseSpMatDescr_t matA;
    cusparseDnMatDescr_t matB, matC;
    // cusparseDnVecDescr_t vecX, vecY;
    void*                dBuffer    = NULL;
    size_t               bufferSize = 0;
    
    // CUB APIs
    void     *dTempStorage = NULL;
    size_t   tempStorageBytes = 0;

    // Device memory allocation
    CHECK_CUDA( cudaMalloc<uint_fast64_t>((&device_columnIndices), sizeof(uint_fast64_t) * matrixNnzCount) );
    CHECK_CUDA( cudaMalloc<uint_fast64_t>((&device_matrixRowIndices), sizeof(uint_fast64_t) * (matrixRowCount + 1)) );
    CHECK_CUDA( cudaMalloc<uint_fast64_t>((&device_nondeterministicChoiceIndices), sizeof(uint_fast64_t) * (subfamiliesMatrixSize + 1)) );

    CHECK_CUDA( cudaMalloc<ValueType>((&device_nnzValues), sizeof(ValueType) * matrixNnzCount) );
    CHECK_CUDA( cudaMalloc<ValueType>((&device_x), sizeof(ValueType) * subfamiliesMatrixSize) );
    CHECK_CUDA( cudaMalloc<ValueType>((&device_xSwap), sizeof(ValueType) * subfamiliesMatrixSize) );
    CHECK_CUDA( cudaMalloc<ValueType>((&device_diff), sizeof(ValueType) * subfamiliesMatrixSize) );
    CHECK_CUDA( cudaMalloc<ValueType>((&device_b), sizeof(ValueType) * matrixRowCount * familiesCount) );
    CHECK_CUDA( cudaMalloc<ValueType>((&device_multiplyResult), sizeof(ValueType) * matrixRowCount * familiesCount) );

    // Memory allocated, copy data to device
    CHECK_CUDA( cudaMemcpy(device_columnIndices, columnIndices.data(), sizeof(uint_fast64_t) * matrixNnzCount, cudaMemcpyHostToDevice) );
    CHECK_CUDA( cudaMemcpy(device_matrixRowIndices, matrixRowIndices.data(), sizeof(uint_fast64_t) * (matrixRowCount + 1), cudaMemcpyHostToDevice) );
    CHECK_CUDA( cudaMemcpy(device_nondeterministicChoiceIndices, nondeterministicChoiceIndices.data(), sizeof(uint_fast64_t) * (subfamiliesMatrixSize + 1), cudaMemcpyHostToDevice) );

    CHECK_CUDA( cudaMemcpy(device_nnzValues, nnzValues.data(), sizeof(ValueType) * matrixNnzCount, cudaMemcpyHostToDevice) );
    CHECK_CUDA( cudaMemcpy(device_x, x.data(), sizeof(ValueType) * subfamiliesMatrixSize, cudaMemcpyHostToDevice) );
    CHECK_CUDA( cudaMemset(device_xSwap, 0, sizeof(ValueType) * subfamiliesMatrixSize) );
    CHECK_CUDA( cudaMemset(device_diff, 0, sizeof(ValueType) * subfamiliesMatrixSize) );
    CHECK_CUDA( cudaMemcpy(device_b, b.data(), sizeof(ValueType) * matrixRowCount * familiesCount, cudaMemcpyHostToDevice) );
    CHECK_CUDA( cudaMemset(device_multiplyResult, 0, sizeof(ValueType) * matrixRowCount * familiesCount) );

    // CUSPARSE settings
    CHECK_CUSPARSE( cusparseCreate(&handle) );
    CHECK_CUSPARSE( cusparseCreateCsr(&matA, matrixRowCount, matrixColCount, matrixNnzCount, (void*)device_matrixRowIndices, (void*)device_columnIndices, (void*)device_nnzValues, CUSPARSE_INDEX_64I, CUSPARSE_INDEX_64I, CUSPARSE_INDEX_BASE_ZERO, CUDA_DATATYPE) );
    CHECK_CUSPARSE( cusparseCreateDnMat(&matB, matrixColCount, familiesCount, matrixColCount, device_x, CUDA_DATATYPE, CUSPARSE_ORDER_COL) );
    CHECK_CUSPARSE( cusparseCreateDnMat(&matC, matrixRowCount, familiesCount, matrixRowCount, device_multiplyResult, CUDA_DATATYPE, CUSPARSE_ORDER_COL) );
    CHECK_CUSPARSE( cusparseSpMM_bufferSize(handle, CUSPARSE_OPERATION_NON_TRANSPOSE,CUSPARSE_OPERATION_NON_TRANSPOSE, &alpha, matA, matB, &beta, matC, CUDA_DATATYPE, CUSPARSE_SPMM_ALG_DEFAULT, &bufferSize) ); 
    CHECK_CUDA( cudaMalloc(&dBuffer, bufferSize) ); 

    // Thrust pointer initialization
    thrust::device_ptr<ValueType> devicePtrThrust_diff(device_diff);
    thrust::device_ptr<ValueType> devicePtrThrust_diff_end(device_diff + subfamiliesMatrixSize);
    thrust::device_ptr<ValueType> devicePtrThrust_b(device_b);
    thrust::device_ptr<ValueType> devicePtrThrust_multiplyResult(device_multiplyResult);

    std::vector<ValueType> tmp(matrixRowCount * familiesCount);

    // Data is on device, start Kernel
    while(!converged && iterationCount < maxIterationCount) {
        /* SPARSE MULT: transition matrix * x vector */
        CHECK_CUSPARSE( cusparseSpMM(handle, CUSPARSE_OPERATION_NON_TRANSPOSE,CUSPARSE_OPERATION_NON_TRANSPOSE, &alpha, matA, matB, &beta, matC, CUDA_DATATYPE, CUSPARSE_SPMM_ALG_DEFAULT, dBuffer) );
        /* SAXPY: multiplyResult + b inplace to multiplyResult */
		thrust::transform(devicePtrThrust_multiplyResult, devicePtrThrust_multiplyResult + (matrixRowCount * familiesCount), devicePtrThrust_b, devicePtrThrust_multiplyResult, thrust::plus<ValueType>());
        /* MAX/MIN_REDUCE: reduce multiplyResult to a new x vector */
        segmented_vector_reduce<Maximize, ValueType>(subfamiliesMatrixSize, (matrixRowCount * familiesCount), device_nondeterministicChoiceIndices, device_xSwap, device_multiplyResult);
        /* INF_NORM: check for convergence */
        // Transform: diff = abs(x - xSwap)/ xSwap
		thrust::device_ptr<ValueType> devicePtrThrust_x(device_x);
		thrust::device_ptr<ValueType> devicePtrThrust_x_end(device_x + subfamiliesMatrixSize);
		thrust::device_ptr<ValueType> devicePtrThrust_xSwap(device_xSwap);
		thrust::transform(devicePtrThrust_x, devicePtrThrust_x_end, devicePtrThrust_xSwap, devicePtrThrust_diff, equalModuloPrecision<ValueType, Relative>());
		// Reduce: get Max over x and check for res < Precision
		ValueType maxX = thrust::reduce(devicePtrThrust_diff, devicePtrThrust_diff_end, -std::numeric_limits<ValueType>::max(), thrust::maximum<ValueType>());
		converged = (maxX < precision);
        ++iterationCount;

        // Swap pointers, device_x always contains the most current result
		std::swap(device_x, device_xSwap);
        CHECK_CUSPARSE( cusparseDnMatSetValues(matB, (void*)device_x) );
    }

    if (!converged && (iterationCount == maxIterationCount)) {
		iterationCount = 0;
		errorOccured = true;
    }

    // repeat last iteration to extract scheduler
    if (extractScheduler) {
        /* SPARSE MULT: transition matrix * last x before convergence */
        CHECK_CUSPARSE( cusparseDnMatSetValues(matB, (void*)device_xSwap) );
        CHECK_CUSPARSE( cusparseSpMM(handle, CUSPARSE_OPERATION_NON_TRANSPOSE,CUSPARSE_OPERATION_NON_TRANSPOSE, &alpha, matA, matB, &beta, matC, CUDA_DATATYPE, CUSPARSE_SPMM_ALG_DEFAULT, dBuffer) );
        
        /* SAXPY: multiplyResult + b inplace to multiplyResult */
		thrust::transform(devicePtrThrust_multiplyResult, devicePtrThrust_multiplyResult + (matrixRowCount * familiesCount), devicePtrThrust_b, devicePtrThrust_multiplyResult, thrust::plus<ValueType>());
        
        /* Find scheduler */
        thrust::device_vector<uint_fast64_t> keys(choicesAsKeys);
        // replace +-inf in order to recognize choices to be ignored
        if (Maximize) thrust::replace(thrust::device, devicePtrThrust_multiplyResult, devicePtrThrust_multiplyResult + (matrixRowCount * familiesCount), -std::numeric_limits<ValueType>::infinity(), ValueType(-1.0));
        else          thrust::replace(thrust::device, devicePtrThrust_multiplyResult, devicePtrThrust_multiplyResult + (matrixRowCount * familiesCount), std::numeric_limits<ValueType>::infinity(), ValueType(-1.0));
        // remove recognized keys and values
        thrust::device_vector<uint_fast64_t>::iterator newKeysEnd = thrust::remove_if(keys.begin(), keys.end(), devicePtrThrust_multiplyResult, is_minus_one<ValueType>());
        thrust::device_ptr<ValueType> newValuesEnd = thrust::remove(devicePtrThrust_multiplyResult, devicePtrThrust_multiplyResult + (matrixRowCount * familiesCount), ValueType(-1.0));
        thrust::device_vector<uint_fast64_t> rowGroups(schedulerSize + 1);
        rowGroups[0] = 0;
        // compute new groups without unwanted choices
        thrust::reduce_by_key(keys.begin(), newKeysEnd, thrust::make_constant_iterator<uint_fast64_t>(1), thrust::make_discard_iterator(), rowGroups.begin() + 1, thrust::equal_to<uint_fast64_t>(), thrust::plus<uint_fast64_t>());
        thrust::inclusive_scan(thrust::device, rowGroups.begin() + 1, rowGroups.begin() + schedulerSize + 1, rowGroups.begin() + 1);

        // CUB Memory allocation
        dTempStorage = NULL;
        tempStorageBytes = 0;

        std::vector<cub::KeyValuePair<int, ValueType>> host_choices(schedulerSize);
        thrust::device_vector<cub::KeyValuePair<int, ValueType>> device_choicesValues(schedulerSize);
        cub::KeyValuePair<int, ValueType>* device_choices = thrust::raw_pointer_cast(&device_choicesValues[0]);
        uint_fast64_t *cho = thrust::raw_pointer_cast(&rowGroups[0]);

        if (Maximize)   cub::DeviceSegmentedReduce::ArgMax(dTempStorage, tempStorageBytes, device_multiplyResult, device_choices, schedulerSize, cho, cho + 1);
        else            cub::DeviceSegmentedReduce::ArgMin(dTempStorage, tempStorageBytes, device_multiplyResult, device_choices, schedulerSize, cho, cho + 1); 
        CHECK_CUDA( cudaMalloc(&dTempStorage, tempStorageBytes) );
    
        /* MAX/MIN_REDUCE: reduce multiplyResult to a new [(choice,value),...] vector */
        (Maximize) ?
        cub::DeviceSegmentedReduce::ArgMax(dTempStorage, tempStorageBytes, device_multiplyResult, device_choices, schedulerSize, cho, cho + 1) :
        cub::DeviceSegmentedReduce::ArgMin(dTempStorage, tempStorageBytes, device_multiplyResult, device_choices, schedulerSize, cho, cho + 1) ; 
    
        /* Copy form device to host and set scheduler choices */
        thrust::copy(device_choicesValues.begin(), device_choicesValues.end(), host_choices.begin());
        for (int i = 0; i < host_choices.size(); i++) {
            choices->at(i) = host_choices[i].key;
        } 
    }

    // Get x (result) back from the device
    CHECK_CUDA( cudaMemcpy(x.data(), device_x, sizeof(ValueType) * subfamiliesMatrixSize, cudaMemcpyDeviceToHost) );

    // CUSPARSE free
    CHECK_CUSPARSE( cusparseDestroySpMat(matA) );
    CHECK_CUSPARSE( cusparseDestroyDnMat(matB) );
    CHECK_CUSPARSE( cusparseDestroyDnMat(matC) );
    CHECK_CUSPARSE( cusparseDestroy(handle) );

	// All code related to freeing memory and clearing up the device
    CHECK_CUDA( cudaFree(device_matrixRowIndices) );
    CHECK_CUDA( cudaFree(device_columnIndices) );
    CHECK_CUDA( cudaFree(device_nondeterministicChoiceIndices) );
    CHECK_CUDA( cudaFree(device_nnzValues) );
    CHECK_CUDA( cudaFree(device_x) );
    CHECK_CUDA( cudaFree(device_xSwap) );
    CHECK_CUDA( cudaFree(device_diff) );
    CHECK_CUDA( cudaFree(device_b) );
    CHECK_CUDA( cudaFree(device_multiplyResult) );
    CHECK_CUDA( cudaFree(dBuffer) );
    CHECK_CUDA( cudaFree(dTempStorage) );

    return !errorOccured;
}

/*******************************************************************************/
/*                    Jacobi Iteration API                                     */
/*******************************************************************************/

bool jacobiIteration_solver_double(uint_fast64_t const maxIterationCount, double const precision, uint_fast64_t const matrixRowCount, uint_fast64_t const matrixNnzCount, uint_fast64_t const matrixBlockCount, std::vector<double> & x, std::vector<double> const& b, std::vector<double> const& nnzValues, std::vector<double> const& D, std::vector<uint_fast64_t> const& columnIndices, std::vector<uint_fast64_t> const& rowStartIndices, std::vector<uint_fast64_t> const& rowBlocks, size_t& iterationCount, bool const relativePrecisionCheck) {
    if (relativePrecisionCheck) {
        return jacobiIteration_solver<true, double, CUDA_R_64F>(maxIterationCount, precision, matrixRowCount, matrixNnzCount, matrixBlockCount, x, b, nnzValues, D, columnIndices, rowStartIndices, rowBlocks, iterationCount);
    } else {
        return jacobiIteration_solver<false, double, CUDA_R_64F>(maxIterationCount, precision, matrixRowCount, matrixNnzCount, matrixBlockCount, x, b, nnzValues, D, columnIndices, rowStartIndices, rowBlocks, iterationCount);
    }
}

bool jacobiIteration_solver_float(uint_fast64_t const maxIterationCount, float const precision, uint_fast64_t const matrixRowCount, uint_fast64_t const matrixNnzCount, uint_fast64_t const matrixBlockCount, std::vector<float> & x, std::vector<float> const& b, std::vector<float> const& nnzValues, std::vector<float> const& D, std::vector<uint_fast64_t> const& columnIndices, std::vector<uint_fast64_t> const& rowStartIndices, std::vector<uint_fast64_t> const& rowBlocks, size_t& iterationCount, bool const relativePrecisionCheck) {
    if (relativePrecisionCheck) {
        return jacobiIteration_solver<true, float, CUDA_R_32F>(maxIterationCount, precision, matrixRowCount, matrixNnzCount, matrixBlockCount, x, b, nnzValues, D, columnIndices, rowStartIndices, rowBlocks, iterationCount);
    } else {
        return jacobiIteration_solver<false, float, CUDA_R_32F>(maxIterationCount, precision, matrixRowCount, matrixNnzCount, matrixBlockCount, x, b, nnzValues, D, columnIndices, rowStartIndices, rowBlocks, iterationCount);
    }
}

/*******************************************************************************/
/*                    Value Iteration API                                      */
/*******************************************************************************/

bool valueIteration_solver_uint64_double_minimize(size_t const schedulerSize, bool const solveMultipleInstances, uint_fast64_t const maxIterationCount,double const precision, bool const relativePrecisionCheck, std::vector<uint_fast64_t> const& matrixRowIndices, std::vector<uint_fast64_t> const& columnIndices, std::vector<double> const& nnzValues, std::vector<double>& x, std::vector<double> const& b, std::vector<uint_fast64_t> const& nondeterministicChoiceIndices, std::vector<uint_fast64_t> const& choicesAsKeys, size_t& iterationCount, bool const extractScheduler, std::vector<uint_fast64_t>* choices) {
    if (relativePrecisionCheck) {
        // <bool Maximize, bool Relative, typename ValueType, cudaDataType CUDA_DATATYPE>
        return (solveMultipleInstances) ?
                valueIteration_solver_multipleMDPs<false, true, double, CUDA_R_64F>(schedulerSize, maxIterationCount, precision, matrixRowIndices, columnIndices, nnzValues, x, b, nondeterministicChoiceIndices, choicesAsKeys, iterationCount, extractScheduler, choices)
               :valueIteration_solver<false, true, double, CUDA_R_64F>(maxIterationCount, precision, matrixRowIndices, columnIndices, nnzValues, x, b, nondeterministicChoiceIndices, iterationCount, extractScheduler, choices);  
    } else {
        // <bool Maximize, bool Relative, typename ValueType, cudaDataType CUDA_DATATYPE>
        return (solveMultipleInstances) ?
                valueIteration_solver_multipleMDPs<false, false, double, CUDA_R_64F>(schedulerSize, maxIterationCount, precision, matrixRowIndices, columnIndices, nnzValues, x, b, nondeterministicChoiceIndices, choicesAsKeys, iterationCount, extractScheduler, choices)
               :valueIteration_solver<false, false, double, CUDA_R_64F>(maxIterationCount, precision, matrixRowIndices, columnIndices, nnzValues, x, b, nondeterministicChoiceIndices, iterationCount, extractScheduler, choices);  
    }
}

bool valueIteration_solver_uint64_double_maximize(size_t const schedulerSize, bool const solveMultipleInstances, uint_fast64_t const maxIterationCount,double const precision, bool const relativePrecisionCheck, std::vector<uint_fast64_t> const& matrixRowIndices, std::vector<uint_fast64_t> const& columnIndices, std::vector<double> const& nnzValues, std::vector<double>& x, std::vector<double> const& b, std::vector<uint_fast64_t> const& nondeterministicChoiceIndices, std::vector<uint_fast64_t> const& choicesAsKeys, size_t& iterationCount, bool const extractScheduler, std::vector<uint_fast64_t>* choices) {
    if (relativePrecisionCheck) {
        // <bool Maximize, bool Relative, typename ValueType, cudaDataType CUDA_DATATYPE>
        return (solveMultipleInstances) ?
                valueIteration_solver_multipleMDPs<true, true, double, CUDA_R_64F>(schedulerSize, maxIterationCount, precision, matrixRowIndices, columnIndices, nnzValues, x, b, nondeterministicChoiceIndices, choicesAsKeys, iterationCount, extractScheduler, choices)
               :valueIteration_solver<true, true, double, CUDA_R_64F>(maxIterationCount, precision, matrixRowIndices, columnIndices, nnzValues, x, b, nondeterministicChoiceIndices, iterationCount, extractScheduler, choices);  
    } else {
        // <bool Maximize, bool Relative, typename ValueType, cudaDataType CUDA_DATATYPE>
        return (solveMultipleInstances) ?
                valueIteration_solver_multipleMDPs<true, false, double, CUDA_R_64F>(schedulerSize, maxIterationCount, precision, matrixRowIndices, columnIndices, nnzValues, x, b, nondeterministicChoiceIndices, choicesAsKeys, iterationCount, extractScheduler, choices)
               :valueIteration_solver<true, false, double, CUDA_R_64F>(maxIterationCount, precision, matrixRowIndices, columnIndices, nnzValues, x, b, nondeterministicChoiceIndices, iterationCount, extractScheduler, choices);  
    }
}

bool valueIteration_solver_uint64_float_minimize(size_t const schedulerSize, bool const solveMultipleInstances, uint_fast64_t const maxIterationCount,float const precision, bool const relativePrecisionCheck, std::vector<uint_fast64_t> const& matrixRowIndices, std::vector<uint_fast64_t> const& columnIndices, std::vector<float> const& nnzValues, std::vector<float>& x, std::vector<float> const& b, std::vector<uint_fast64_t> const& nondeterministicChoiceIndices, std::vector<uint_fast64_t> const& choicesAsKeys, size_t& iterationCount, bool const extractScheduler, std::vector<uint_fast64_t>* choices){
    if (relativePrecisionCheck) {
        // <bool Maximize, bool Relative, typename ValueType, cudaDataType CUDA_DATATYPE>
        return (solveMultipleInstances) ?
                valueIteration_solver_multipleMDPs<false, true, float, CUDA_R_32F>(schedulerSize, maxIterationCount, precision, matrixRowIndices, columnIndices, nnzValues, x, b, nondeterministicChoiceIndices, choicesAsKeys, iterationCount, extractScheduler, choices)
               :valueIteration_solver<false, true, float, CUDA_R_32F>(maxIterationCount, precision, matrixRowIndices, columnIndices, nnzValues, x, b, nondeterministicChoiceIndices, iterationCount, extractScheduler, choices);  
    } else {
        // <bool Maximize, bool Relative, typename ValueType, cudaDataType CUDA_DATATYPE>
        return (solveMultipleInstances) ?
                valueIteration_solver_multipleMDPs<false, false, float, CUDA_R_32F>(schedulerSize, maxIterationCount, precision, matrixRowIndices, columnIndices, nnzValues, x, b, nondeterministicChoiceIndices, choicesAsKeys, iterationCount, extractScheduler, choices)
               :valueIteration_solver<false, false, float, CUDA_R_32F>(maxIterationCount, precision, matrixRowIndices, columnIndices, nnzValues, x, b, nondeterministicChoiceIndices, iterationCount, extractScheduler, choices);  
    }
}

bool valueIteration_solver_uint64_float_maximize(size_t const schedulerSize, bool const solveMultipleInstances, uint_fast64_t const maxIterationCount,float const precision, bool const relativePrecisionCheck, std::vector<uint_fast64_t> const& matrixRowIndices, std::vector<uint_fast64_t> const& columnIndices, std::vector<float> const& nnzValues, std::vector<float>& x, std::vector<float> const& b, std::vector<uint_fast64_t> const& nondeterministicChoiceIndices, std::vector<uint_fast64_t> const& choicesAsKeys, size_t& iterationCount, bool const extractScheduler, std::vector<uint_fast64_t>* choices){
    if (relativePrecisionCheck) {
        // <bool Maximize, bool Relative, typename ValueType, cudaDataType CUDA_DATATYPE>
        return (solveMultipleInstances) ?
                valueIteration_solver_multipleMDPs<true, true, float, CUDA_R_32F>(schedulerSize, maxIterationCount, precision, matrixRowIndices, columnIndices, nnzValues, x, b, nondeterministicChoiceIndices, choicesAsKeys, iterationCount, extractScheduler, choices)
               :valueIteration_solver<true, true, float, CUDA_R_32F>(maxIterationCount, precision, matrixRowIndices, columnIndices, nnzValues, x, b, nondeterministicChoiceIndices, iterationCount, extractScheduler, choices);  
    } else {
        // <bool Maximize, bool Relative, typename ValueType, cudaDataType CUDA_DATATYPE>
        return (solveMultipleInstances) ?
                valueIteration_solver_multipleMDPs<true, false, float, CUDA_R_32F>(schedulerSize, maxIterationCount, precision, matrixRowIndices, columnIndices, nnzValues, x, b, nondeterministicChoiceIndices, choicesAsKeys, iterationCount, extractScheduler, choices)
               :valueIteration_solver<true, false, float, CUDA_R_32F>(maxIterationCount, precision, matrixRowIndices, columnIndices, nnzValues, x, b, nondeterministicChoiceIndices, iterationCount, extractScheduler, choices);  
    }
}