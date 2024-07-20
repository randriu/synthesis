#include "PosmgManager.h"

namespace synthesis {

    PosmgManager::PosmgManager(Posmg const& posmg)
        : posmg(posmg)
    {
        this->calculateObservationMap();
        this->calculateObservationSuccesors();


        this->optPlayerObservationMemorySize.resize(posmg.getP0ObservationCount(), 1);
        this->prototypeDuplicates.resize(posmg.getNumberOfStates());
    }

    std::vector<u_int64_t> PosmgManager::getObservationMapping()
    {
        return this->optPlayerObservationMap;
    }

    void PosmgManager::setObservationMemorySize(uint64_t observation, uint64_t memorySize)
    {
        this->optPlayerObservationMemorySize[observation] = memorySize;
    }


    void PosmgManager::calculateObservationMap()
    {
        this->optPlayerObservationMap.clear();

        auto stateCount = this->posmg.getNumberOfStates();
        auto observations = this->posmg.getObservations();

        for (uint64_t state = 0; state < stateCount; state++)
        {
            if (isOptPlayerState(state))
            {
                auto observation = observations[state];
                if (!contains(optPlayerObservationMap, observation))
                {
                    this->optPlayerObservationMap.push_back(observation);
                }
            }
        }
    }

    void PosmgManager::calculateObservationSuccesors()
    {
        auto transitionMat = this->posmg.getTransitionMatrix();
        auto stateCount = this->posmg.getNumberOfStates();
        auto rowGroupIndices = transitionMat.getRowGroupIndices();

        for (uint64_t state = 0; state < stateCount; state++)
        {
            if (isOptPlayerState(state))
            {
                auto observation = this->posmg.getObservation(state);
                for (size_t action = rowGroupIndices[state]; action < rowGroupIndices[state+1]; action++)
                {
                    auto row = transitionMat.getRow(action);
                    for (auto entry : row)
                    {
                        auto succesor = entry.getColumn();
                        this->succesors[observation].insert(succesor);
                    }
                }
            }
        }
    }

    void PosmgManager::calculateObservationActions()
    {
        for (uint64_t state = 0; state < this->posmg.getNumberOfStates(); state++)
        {
            if (isOptPlayerState(state))
            {
                auto observation = this->posmg.getObservation(state);
                auto actionCount = this->posmg.getTransitionMatrix().getRowGroupSize(state);
                this->optPlayerObservationActions[observation] = actionCount;
            }
        }
    }



    void PosmgManager::buildStateSpace()
    {
        auto prototypeCount = this->posmg.getNumberOfStates();
        this->stateDuplicateCount.resize(prototypeCount, 1); // je potreba resize???

        auto mat = this->posmg.getBackwardTransitions();

        // computing the number of needed duplicates for each state
        for (uint64_t prototype = 0; prototype < prototypeCount; prototype++) {
            if (isOptPlayerState(prototype)) {
                auto observation = this->posmg.getObservation(prototype);
                // retreive index of observation in optPlayerObservationMap
                auto optPlayerObservation = std::find(this->optPlayerObservationMap.begin(),
                                                      this->optPlayerObservationMap.end(),
                                                      observation) - this->optPlayerObservationMap.begin();
                auto memory = this->optPlayerObservationMemorySize[optPlayerObservation];
                this->stateDuplicateCount[prototype] = memory;

                // DFS to compute the needed memory for states of non-optimizing player
                std::stack<uint64_t> dfsStack;
                dfsStack.push(prototype);
                while (!dfsStack.empty()) {
                    auto currentState = dfsStack.top();
                    dfsStack.pop();
                    auto row = mat.getRow(currentState);
                    for (auto entry : row) {
                        auto dst = entry.getColumn();
                        if (!isOptPlayerState(dst) && this->stateDuplicateCount[dst] < memory) {
                            this->stateDuplicateCount[dst] = memory;
                            dfsStack.push(dst);
                        }
                    }
                }
            }
        }

        // calculate state count
        // create mapping between prototypes and duplicates
        this->stateCount = 0;
        this->statePrototype.clear();
        this->stateMemory.clear();
        for (uint64_t prototype = 0; prototype < prototypeCount; prototype++)
        {
            auto duplicateCount = stateDuplicateCount[prototype];
            this->prototypeDuplicates[prototype].clear();
            this->prototypeDuplicates[prototype].reserve(duplicateCount);
            for (uint64_t memory = 0; memory < duplicateCount; memory++)
            {
                this->prototypeDuplicates[prototype].push_back(this->stateCount);
                this->statePrototype.push_back(prototype);
                this->stateMemory.push_back(memory);
                this->stateCount++;
            }
        }
    }

    void PosmgManager::buildTransitionMatrixSpurious() {
        // calculate maxSuccesorDuplicateCount
        for (auto entry : this->succesors)
        {
            auto observation = entry.first;
            uint64_t maxDuplicateCount = 0;
            for (auto succesor : entry.second)
            {
                if (this->stateDuplicateCount[succesor] > maxDuplicateCount)
                {
                    maxDuplicateCount = this->stateDuplicateCount[succesor];
                }
            }
            this->maxSuccesorDuplicateCount[observation] = maxDuplicateCount;
        }

        this->rowGroups.resize(this->stateCount+1);
        this->rowPrototype.clear();
        this->rowMemory.clear();

        auto const& rowGroupIndices = this->posmg.getTransitionMatrix().getRowGroupIndices();

        for (uint64_t state = 0; state < this->stateCount; state++)
        {
            this->rowGroups[state] = this->rowPrototype.size();
            auto prototype = this->statePrototype[state];
            auto memory = this->stateMemory[state];
            auto observation = this->posmg.getObservation(prototype);
            for (uint64_t prototypeRow = rowGroupIndices[prototype];
                prototypeRow < rowGroupIndices[prototype + 1];
                prototypeRow++)
            {
                if (isOptPlayerState(prototype))
                {
                    auto maxDuplicateCount = this->maxSuccesorDuplicateCount[observation];
                    for (uint64_t dstMem = 0; dstMem < maxDuplicateCount; dstMem++)
                    {
                        this->rowPrototype.push_back(prototypeRow);
                        this->rowMemory.push_back(dstMem);
                    }
                }
                else
                {
                    this->rowPrototype.push_back(prototypeRow);
                    this->rowMemory.push_back(memory);
                }
            }
        }

        this->rowCount = rowPrototype.size();
        this->rowGroups[this->stateCount] = this->rowCount;
    }

    uint64_t PosmgManager::translateState(uint64_t prototype, uint64_t memory) {
        if(memory >= this->prototypeDuplicates[prototype].size()) {
            memory = 0;
        }
        return this->prototypeDuplicates[prototype][memory];
    }

    storm::storage::SparseMatrix<double> PosmgManager::constructTransitionMatrix()
    {
        storm::storage::SparseMatrixBuilder<double> builder(
            this->rowCount, this->stateCount, 0, true, true, this->stateCount
        );
        for (uint64_t state = 0; state < this->stateCount; state++)
        {
            builder.newRowGroup(this->rowGroups[state]);
            for (uint64_t row = this->rowGroups[state]; row < this->rowGroups[state+1]; row++)
            {
                auto prototypeRow = this->rowPrototype[row];
                auto dstMem = this->rowMemory[row];
                for (auto const &entry : this->posmg.getTransitionMatrix().getRow(prototypeRow))
                {
                    auto dst = this->translateState(entry.getColumn(), dstMem);
                    builder.addNextValue(row, dst, entry.getValue());
                }
            }
        }

        return builder.build();
    }

    storm::models::sparse::StateLabeling PosmgManager::constructStateLabeling()
    {
        storm::models::sparse::StateLabeling labeling(this->stateCount);
        for (auto const& label : this->posmg.getStateLabeling().getLabels())
        {
            storm::storage::BitVector labelFlags(this->stateCount, false);

            if (label == "init")
            {
                // init label is only assigned to states with the initial memory state
                for (auto const& prototype : this->posmg.getStateLabeling().getStates(label))
                {
                    labelFlags.set(translateState(prototype, 0));
                }
            }
            else
            {
                for (auto const& prototype : this->posmg.getStateLabeling().getStates(label))
                {
                    for (auto duplicate : this->prototypeDuplicates[prototype])
                    {
                        labelFlags.set(duplicate);
                    }
                }
            }
            labeling.addLabel(label, std::move(labelFlags));
        }

        return labeling;
    }

    void PosmgManager::resetDesignSpace()
    {
        // todo
    }

    void PosmgManager::buildDesignSpaceSpurious()
    {
        // todo
        // this->resetDesignSpace();

        // for (auto observation : this->optPlayerObservationMap)
        // {
        //     if (this->optPlayerObservationActions[observation] > 1)
        //     {
        //         for (uint64_t memory = 0; memory < this->optPlayerObservationMemorySize; memory++)
        //         {
        //             /* code */
        //         }

        //     }

        // }
    }

    std::shared_ptr<storm::models::sparse::Mdp<double>> PosmgManager::constructMdp()
    {
        this->buildStateSpace();
        this->buildTransitionMatrixSpurious();

        storm::storage::sparse::ModelComponents<double> components;
        components.transitionMatrix = this->constructTransitionMatrix();
        components.stateLabeling = this->constructStateLabeling();
        this->mdp = std::make_shared<storm::models::sparse::Mdp<double>>(std::move(components));

        this->buildDesignSpaceSpurious();

        return this->mdp;
    }

    bool PosmgManager::isOptPlayerState(uint64_t state){
        return this->posmg.getStatePlayerIndications()[state] == this->optimizingPlayer;
    }

    bool PosmgManager::contains(std::vector<uint64_t> v, uint64_t elem)
    {
        return std::find(v.begin(), v.end(), elem) != v.end();
    }

} // namespace synthesis