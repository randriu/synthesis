#include "SynthesisMatrix.h"


namespace synthesis {

    SynthesisMatrix::SynthesisMatrix(storm::storage::SparseMatrix<double> const& other) : storm::storage::SparseMatrix<double>(other) {
        this->rowIndications.reserve(other.getRowCount() + 1);
        this->rowIndications.push_back(0);
        storm::storage::sparse::state_type indicationCounter = 0;
        for (index_type row = 0; row < other.getRowCount(); row++) {
            for (auto const &entry: other.getRow(row)) {
                indicationCounter++;
            }
            this->rowIndications.push_back(indicationCounter);
        }
    }

    std::vector<storm::storage::sparse::state_type> SynthesisMatrix::getRowIndications() {
        return this->rowIndications;
    }

}