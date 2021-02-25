#ifndef STORM_CUDAFORSTORM_JACOBIITERATION_H_
#define STORM_CUDAFORSTORM_JACOBIITERATION_H_

#include <vector>
#include <cstdint>

#include "cudaForStorm.h"

#define NNZ_PER_WG 128

/**
 * @brief 
 * 
 * @param maxIterationCount 
 * @param precision 
 * @param matrixRowCount 
 * @param matrixNnzCount 
 * @param matrixBlockCount 
 * @param x 
 * @param b 
 * @param nnzValues 
 * @param D 
 * @param columnIndices 
 * @param rowStartIndices 
 * @param rowBlocks 
 * @param iterationCount 
 * @param relativePrecisionCheck 
 * @return true 
 * @return false 
 */
bool jacobiIteration_solver_double(uint_fast64_t const maxIterationCount, double const precision, uint_fast64_t const matrixRowCount, uint_fast64_t const matrixNnzCount, uint_fast64_t const matrixBlockCount, std::vector<double> & x, std::vector<double> const& b, std::vector<double> const& nnzValues, std::vector<double> const& D, std::vector<uint_fast64_t> const& columnIndices, std::vector<uint_fast64_t> const& rowStartIndices, std::vector<uint_fast64_t> const& rowBlocks, size_t& iterationCount, bool const relativePrecisionCheck);
bool jacobiIteration_solver_float(uint_fast64_t const maxIterationCount, float const precision, uint_fast64_t const matrixRowCount, uint_fast64_t const matrixNnzCount, uint_fast64_t const matrixBlockCount, std::vector<float> & x, std::vector<float> const& b, std::vector<float> const& nnzValues, std::vector<float> const& D, std::vector<uint_fast64_t> const& columnIndices, std::vector<uint_fast64_t> const& rowStartIndices, std::vector<uint_fast64_t> const& rowBlocks, size_t& iterationCount, bool const relativePrecisionCheck);

/**
 * @brief 
 * 
 * @param maxIterationCount 
 * @param precision 
 * @param relativePrecisionCheck 
 * @param matrixRowIndices 
 * @param columnIndices 
 * @param nnzValues 
 * @param x 
 * @param b 
 * @param nondeterministicChoiceIndices 
 * @param iterationCount 
 * @return true 
 * @return false 
 */
bool valueIteration_solver_uint64_double_minimize(uint_fast64_t const maxIterationCount,double const precision, bool const relativePrecisionCheck, std::vector<uint_fast64_t> const& matrixRowIndices, std::vector<uint_fast64_t> const& columnIndices, std::vector<double> const& nnzValues, std::vector<double> x, std::vector<double> const& b, std::vector<uint_fast64_t> const& nondeterministicChoiceIndices, size_t& iterationCount);
bool valueIteration_solver_uint64_double_maximize(uint_fast64_t const maxIterationCount,double const precision, bool const relativePrecisionCheck, std::vector<uint_fast64_t> const& matrixRowIndices, std::vector<uint_fast64_t> const& columnIndices, std::vector<double> const& nnzValues, std::vector<double> x, std::vector<double> const& b, std::vector<uint_fast64_t> const& nondeterministicChoiceIndices, size_t& iterationCount);
bool valueIteration_solver_uint64_float_minimize(uint_fast64_t const maxIterationCount,float const precision, bool const relativePrecisionCheck, std::vector<uint_fast64_t> const& matrixRowIndices, std::vector<uint_fast64_t> const& columnIndices, std::vector<float> const& nnzValues, std::vector<float> x, std::vector<float> const& b, std::vector<uint_fast64_t> const& nondeterministicChoiceIndices, size_t& iterationCount);
bool valueIteration_solver_uint64_float_maximize(uint_fast64_t const maxIterationCount,float const precision, bool const relativePrecisionCheck, std::vector<uint_fast64_t> const& matrixRowIndices, std::vector<uint_fast64_t> const& columnIndices, std::vector<float> const& nnzValues, std::vector<float> x, std::vector<float> const& b, std::vector<uint_fast64_t> const& nondeterministicChoiceIndices, size_t& iterationCount);

#endif // STORM_CUDAFORSTORM_JACOBIITERATION_H_
