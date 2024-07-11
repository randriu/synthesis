#include <storm/storage/SparseMatrix.h>
#include <storm/storage/sparse/StateType.h>


namespace synthesis
{

    class SynthesisMatrix : public storm::storage::SparseMatrix<double> {

       public:

        SynthesisMatrix(storm::storage::SparseMatrix<double> const& other);
        std::vector<storm::storage::sparse::state_type> getRowIndications();

       private:
        std::vector<index_type> rowIndications;
        
    };
}