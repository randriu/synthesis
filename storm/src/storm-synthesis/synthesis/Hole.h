#include <string>
#include <vector>

namespace storm {
    namespace synthesis {

        class Hole {
        public:
            // instance variables
            std::string name;
            std::vector<int> option_labels;
            std::vector<int> options;

            /*!
               Constructor of Hole instance.
             */
            Hole(std::string name,
                std::vector<int> option_labels,
                std::vector<int> options
            );
        };
    }
}