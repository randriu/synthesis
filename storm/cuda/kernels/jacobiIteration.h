#ifndef STORM_CUDAFORSTORM_JACOBIITERATION_H_
#define STORM_CUDAFORSTORM_JACOBIITERATION_H_

#include <vector>
#include <cstdint>

#include "cudaForStorm.h"

#define NNZ_PER_WG 32

bool jacobiIteration_solver_double(
                uint_fast64_t const maxIterationCount, 
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
                bool const relativePrecisionCheck);

bool jacobiIteration_solver_float(
                uint_fast64_t const maxIterationCount, 
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
                bool const relativePrecisionCheck);

#endif // STORM_CUDAFORSTORM_JACOBIITERATION_H_
