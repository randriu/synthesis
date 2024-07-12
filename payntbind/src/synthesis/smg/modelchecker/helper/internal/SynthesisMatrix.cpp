#include "SynthesisMatrix.h"


namespace synthesis {

    SynthesisMatrix::SynthesisMatrix(storm::storage::SparseMatrix<double> const& other) : storm::storage::SparseMatrix<double>(other) {
        // left intentionally empty
    }

    std::vector<storm::storage::sparse::state_type> SynthesisMatrix::getRowIndications() {
        return this->rowIndications;
    }

}