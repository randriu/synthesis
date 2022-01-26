#include "storm-synthesis/synthesis/Hole.h"

namespace storm {
    namespace synthesis {

        Hole::Hole(
            std::string name,
            std::vector<int> option_labels,
            std::vector<int> options
        ) {
            this->name = name;
            this->option_labels = option_labels;
            this->options = options;
        };
    }
}