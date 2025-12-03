#include "../synthesis.h"
#include "SubPomdpBuilder.h"

#include "src/synthesis/translation/componentTranslations.h"
#include "src/synthesis/translation/choiceTransformation.h"
#include <storm/adapters/RationalNumberAdapter.h>
#include <storm/storage/SparseMatrix.h>

namespace synthesis {
template <typename ValueType>
std::shared_ptr<storm::models::sparse::Mdp<ValueType>> createMdpFromVectorMatrix(storm::models::sparse::Mdp<ValueType> mdp, std::vector<std::vector<std::vector<storm::storage::MatrixEntry<uint_fast64_t, ValueType>>>> vectorMatrix) {

    uint64_t row_count = 0;
    for (const auto& v : vectorMatrix) {
        row_count += v.size();
    }

    storm::storage::sparse::ModelComponents<ValueType> components;

    storm::storage::SparseMatrixBuilder<ValueType> builder(
        row_count, vectorMatrix.size(), 0, false, true, vectorMatrix.size()
    );
    
    uint64_t current_row = 0;
    for (const auto& rowGroupVector : vectorMatrix) {
        builder.newRowGroup(current_row);
        for (const auto& row : rowGroupVector) {
            for (const auto& entry : row) {
                builder.addNextValue(current_row, entry.getColumn(), entry.getValue());
            }
            ++current_row;
        }
    }

    components.transitionMatrix =  builder.build();

    components.stateLabeling = mdp.getStateLabeling();

    return std::make_shared<storm::models::sparse::Mdp<ValueType>>(std::move(components));
}

template <typename ValueType>
std::vector<std::vector<std::vector<storm::storage::MatrixEntry<uint_fast64_t, ValueType>>>> getVectorFromMatrix(storm::storage::SparseMatrix<ValueType> matrix) {

    uint64_t stateCount = matrix.getRowGroupCount(); 
    std::vector<std::vector<std::vector<storm::storage::MatrixEntry<uint_fast64_t, ValueType>>>> resultVector(stateCount);
    const auto rowGroupIndices = matrix.getRowGroupIndices();

    for (uint64_t state = 0; state < stateCount; ++state) {
        resultVector[state].resize(rowGroupIndices[state+1] - rowGroupIndices[state]);
        uint64_t startRow = rowGroupIndices[state];
        for (uint64_t row = rowGroupIndices[state]; row < rowGroupIndices[state+1]; row++) {
            auto rowData = matrix.getRow(row);
            resultVector[state][row - startRow].resize(rowData.getNumberOfEntries());
            for (const auto &entry : rowData) {
                resultVector[state][row - startRow].push_back(entry);
            }
        }
    }

    return resultVector;
}

template <typename ValueType>
std::vector<storm::storage::MatrixEntry<uint_fast64_t, ValueType>> createCombinationOfRows(std::vector<std::vector<storm::storage::MatrixEntry<uint_fast64_t, ValueType>>> rows, std::vector<ValueType> distribution) {
    // Use a map to accumulate values for each column
    std::map<uint_fast64_t, ValueType> columnSums;
    for (size_t i = 0; i < rows.size(); ++i) {
        for (const auto& entry : rows[i]) {
            columnSums[entry.getColumn()] += entry.getValue() * distribution[i];
        }
    }

    std::vector<storm::storage::MatrixEntry<uint_fast64_t, ValueType>> combinedEntries;
    for (const auto& [column, value] : columnSums) {
        combinedEntries.emplace_back(column, value);
    }

    return combinedEntries;
}

}

template <typename ValueType>
void bindings_translation_vt(py::module& m, std::string const& vtSuffix) {

    m.def(("computeChoiceDestinations" + vtSuffix).c_str(), &synthesis::computeChoiceDestinations<ValueType>);
    m.def(("addMissingChoiceLabels" + vtSuffix).c_str(), &synthesis::addMissingChoiceLabelsModel<ValueType>);
    m.def(("assertChoiceLabelingIsCanonic" + vtSuffix).c_str(), &synthesis::assertChoiceLabelingIsCanonic);
    m.def(("extractActionLabels" + vtSuffix).c_str(), &synthesis::extractActionLabels<ValueType>);
    m.def(("enableAllActions" + vtSuffix).c_str(), py::overload_cast<storm::models::sparse::Model<ValueType> const&>(&synthesis::enableAllActions<ValueType>));
    m.def(("restoreActionsInAbsorbingStates" + vtSuffix).c_str(), &synthesis::restoreActionsInAbsorbingStates<ValueType>);
    m.def(("addDontCareAction" + vtSuffix).c_str(), &synthesis::addDontCareAction<ValueType>);
    m.def(("createModelUnion" + vtSuffix).c_str(), &synthesis::createModelUnion<ValueType>);

    m.def(("createMdpFromVectorMatrix" + vtSuffix).c_str(), &synthesis::createMdpFromVectorMatrix<ValueType>);
    m.def(("getVectorFromMatrix" + vtSuffix).c_str(), &synthesis::getVectorFromMatrix<ValueType>);
    m.def(("createCombinationOfRows" + vtSuffix).c_str(), &synthesis::createCombinationOfRows<ValueType>);

    m.def(("get_matrix_rows" + vtSuffix).c_str(), [](storm::storage::SparseMatrix<ValueType>& matrix, std::vector<typename storm::storage::SparseMatrix<ValueType>::index_type> rows) {
        std::vector<typename storm::storage::SparseMatrix<ValueType>::rows> result;
        for (const auto& row : rows) {
            result.push_back(matrix.getRows(row, row+1));
        }
        return result;
    }, py::arg("matrix"), py::arg("rows"), "Get multiple rows from a sparse matrix");

    py::class_<synthesis::SubPomdpBuilder<ValueType>, std::shared_ptr<synthesis::SubPomdpBuilder<ValueType>>>(m, ("SubPomdpBuilder" + vtSuffix).c_str())
        .def(py::init<storm::models::sparse::Pomdp<ValueType> const&>())
        .def("start_from_belief", &synthesis::SubPomdpBuilder<ValueType>::startFromBelief)
        .def_property_readonly("state_sub_to_full", [](synthesis::SubPomdpBuilder<ValueType>& b) {return b.state_sub_to_full;} )
        ;
}

void bindings_translation(py::module& m) {
    bindings_translation_vt<double>(m, "");
    bindings_translation_vt<storm::RationalNumber>(m, "Exact");
}
