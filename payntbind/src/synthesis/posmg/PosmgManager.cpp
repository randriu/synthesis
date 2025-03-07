#include "PosmgManager.h"

namespace synthesis {

    template<typename ValueType>
    PosmgManager<ValueType>::PosmgManager(Posmg<ValueType> const& posmg, uint64_t optimizingPlayer)
        : posmg(posmg), optimizingPlayer(optimizingPlayer)
    {
        this->calculateObservationMap();
        this->calculateObservationSuccesors();
        this->calculatePrototypeActionCount();
        this->calculateObservationActions();
        this->calculatePrototypeRowIndex();


        //this->optPlayerObservationMemorySize.resize(posmg.getP0ObservationCount(), 1);
        this->prototypeDuplicates.resize(posmg.getNumberOfStates());
    }

    template<typename ValueType>
    std::vector<uint64_t> PosmgManager<ValueType>::getObservationMapping()
    {
        return this->optPlayerObservationMap;
    }

    template<typename ValueType>
    void PosmgManager<ValueType>::setObservationMemorySize(uint64_t observation, uint64_t memorySize)
    {
        this->optPlayerObservationMemorySize[observation] = memorySize;
    }

    template<typename ValueType>
    std::vector<uint64_t> PosmgManager<ValueType>::getStatePlayerIndications()
    {
        std::vector<uint64_t> statePlayerIndications(this->stateCount);
        for (uint64_t state = 0; state < this->stateCount; state++)
        {
            auto prototype = this->statePrototype[state];
            statePlayerIndications[state] = this->posmg.getStatePlayerIndications()[prototype];
        }

        return statePlayerIndications;
    }

    template<typename ValueType>
    void PosmgManager<ValueType>::calculateObservationMap()
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

    template<typename ValueType>
    void PosmgManager<ValueType>::calculateObservationSuccesors()
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

    template<typename ValueType>
    void PosmgManager<ValueType>::calculatePrototypeActionCount()
    {
        auto prototypeCount = this->posmg.getNumberOfStates();
        this->prototypeActionCount.resize(prototypeCount);

        for (uint64_t prototype = 0; prototype < prototypeCount; prototype++)
        {
            auto actionCount = this->posmg.getTransitionMatrix().getRowGroupSize(prototype);
            this->prototypeActionCount[prototype] = actionCount;
        }
    }

    template<typename ValueType>
    void PosmgManager<ValueType>::calculateObservationActions()
    {
        for (uint64_t prototype = 0; prototype < this->posmg.getNumberOfStates(); prototype++)
        {
            if (isOptPlayerState(prototype))
            {
                auto observation = this->posmg.getObservation(prototype);
                auto actionCount = this->prototypeActionCount[prototype];
                this->optPlayerObservationActions[observation] = actionCount;
            }
        }
    }

    template<typename ValueType>
    void PosmgManager<ValueType>::calculatePrototypeRowIndex()
    {
        this->prototypeRowIndex.resize(this->posmg.getTransitionMatrix().getRowCount());

        auto prototypeCount = this->posmg.getNumberOfStates();
        auto rowGroupIndices = this->posmg.getTransitionMatrix().getRowGroupIndices();
        for (uint64_t state = 0; state < prototypeCount; state++)
        {
            uint64_t index = 0;
            for (uint64_t row = rowGroupIndices[state]; row < rowGroupIndices[state+1]; row++)
            {
                this->prototypeRowIndex[row] = index;
                index++;
            }
        }
    }

    template<typename ValueType>
    void PosmgManager<ValueType>::buildStateSpace()
    {
        auto prototypeCount = this->posmg.getNumberOfStates();
        this->stateDuplicateCount.resize(prototypeCount, 1); // je potreba resize???

        auto mat = this->posmg.getBackwardTransitions();

        // computing the number of needed duplicates for each state
        for (uint64_t prototype = 0; prototype < prototypeCount; prototype++) {
            if (isOptPlayerState(prototype)) {
                auto observation = this->posmg.getObservation(prototype);
                // retreive index of observation in optPlayerObservationMap
                // auto optPlayerObservation = std::find(this->optPlayerObservationMap.begin(),
                //                                       this->optPlayerObservationMap.end(),
                //                                       observation) - this->optPlayerObservationMap.begin();
                // auto memory = this->optPlayerObservationMemorySize[optPlayerObservation];
                auto memory = this->optPlayerObservationMemorySize.at(observation);
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

    template<typename ValueType>
    void PosmgManager<ValueType>::buildTransitionMatrixSpurious() {
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
                    auto maxDuplicateCount = this->maxSuccesorDuplicateCount.at(observation);
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

    template<typename ValueType>
    uint64_t PosmgManager<ValueType>::translateState(uint64_t prototype, uint64_t memory) {
        if(memory >= this->prototypeDuplicates[prototype].size()) {
            memory = 0;
        }
        return this->prototypeDuplicates[prototype][memory];
    }

    template<typename ValueType>
    storm::storage::SparseMatrix<ValueType> PosmgManager<ValueType>::constructTransitionMatrix()
    {
        storm::storage::SparseMatrixBuilder<ValueType> builder(
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

    template<typename ValueType>
    storm::models::sparse::StateLabeling PosmgManager<ValueType>::constructStateLabeling()
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

    template<typename ValueType>
    void PosmgManager<ValueType>::resetDesignSpace()
    {
        this->holeCount = 0;
        this->actionHoles.clear();
        this->memoryHoles.clear();
        this->holeOptionCount.clear();

        this->rowActionHole.clear();
        this->rowActionHole.resize(this->rowCount);
        this->rowActionOption.clear();
        this->rowActionOption.resize(this->rowCount);

        this->rowMemoryHole.clear();
        this->rowMemoryHole.resize(this->rowCount);
        this->rowMemoryOption.clear();
        this->rowMemoryOption.resize(this->rowCount);
    }

    // version where each state of non optimising players has it's own action hole
    template<typename ValueType>
    void PosmgManager<ValueType>::buildDesignSpaceSpurious()
    {
        this->resetDesignSpace();

        // create action and memory holes for each optimizing player observation
        // store number of available options at each hole
        for (auto observation : this->optPlayerObservationMap)
        {
            if (this->optPlayerObservationActions.at(observation) > 1)
            {
                for (uint64_t memory = 0; memory < this->optPlayerObservationMemorySize.at(observation); memory++)
                {
                    this->actionHoles[observation].push_back(this->holeCount);
                    // this->holeOptionCount.push_back(this->optPlayerObservationActions.at(observation));
                    this->holeCount++;
                }
            }
            if (this->maxSuccesorDuplicateCount.at(observation) > 1)
            {
                for (uint64_t memory = 0; memory < this->optPlayerObservationMemorySize.at(observation); memory++)
                {
                    this->memoryHoles[observation].push_back(this->holeCount);
                    // this->holeOptionCount.push_back(this->optPlayerObservationActions.at(observation));
                    this->holeCount++;
                }
            }
        }

        // create acton holes for each other player state
        for (uint64_t state = 0; state < this->stateCount; state++)
        {
            auto prototype = this->statePrototype[state];

            if (!isOptPlayerState(prototype) && this->posmg.getTransitionMatrix().getRowGroupSize(prototype) > 1)
            {
                this->nonOptActionHoles[state] = this->holeCount;
                this->holeCount++;
            }
        }


        for (uint64_t state = 0; state < this->stateCount; state++)
        {
            auto prototype = this->statePrototype[state];
            auto observation = this->posmg.getObservation(prototype);
            auto memory = this->stateMemory[state];
            for (uint64_t row = this->rowGroups[state]; row < this->rowGroups[state+1]; row++)
            {
                if (isOptPlayerState(prototype) && this->optPlayerObservationActions.at(observation) > 1)
                {
                    auto actionHole = this->actionHoles.at(observation).at(memory);
                    this->rowActionHole[row] = actionHole;

                    auto prototypeRow = this->rowPrototype[row];
                    auto rowIndex = this->prototypeRowIndex[prototypeRow];
                    this->rowActionOption[row] = rowIndex;
                }
                else if (!isOptPlayerState(prototype) && this->posmg.getTransitionMatrix().getRowGroupSize(prototype) > 1)
                {
                    auto actionHole = this->nonOptActionHoles.at(state);
                    this->rowActionHole[row] = actionHole;

                    auto prototypeRow = this->rowPrototype[row];
                    auto rowIndex = this->prototypeRowIndex[prototypeRow];
                    this->rowActionOption[row] = rowIndex;
                }
                else // only one action
                {
                    this->rowActionHole[row] = this->holeCount;
                }
                if (isOptPlayerState(prototype) && this->maxSuccesorDuplicateCount.at(observation) > 1)
                {
                    auto memoryHole = this->memoryHoles.at(observation).at(memory);
                    rowMemoryHole[row] = memoryHole;

                    auto rowMem = rowMemory[row];
                    this->rowMemoryOption[row] = rowMem;
                }
                else // other player or successor has only one memory
                {
                    this->rowMemoryHole[row] = this->holeCount;
                }
            }
        }

    }

    template<typename ValueType>
    std::shared_ptr<storm::models::sparse::Mdp<ValueType>> PosmgManager<ValueType>::constructMdp()
    {
        this->buildStateSpace();
        this->buildTransitionMatrixSpurious();

        storm::storage::sparse::ModelComponents<ValueType> components;
        components.transitionMatrix = this->constructTransitionMatrix();
        components.stateLabeling = this->constructStateLabeling();
        this->mdp = std::make_shared<storm::models::sparse::Mdp<ValueType>>(std::move(components));

        this->buildDesignSpaceSpurious();

        return this->mdp;
    }

    template<typename ValueType>
    bool PosmgManager<ValueType>::isOptPlayerState(uint64_t state){
        return this->posmg.getStatePlayerIndications()[state] == this->optimizingPlayer;
    }

    template<typename ValueType>
    uint64_t PosmgManager<ValueType>::getActionCount(uint64_t state)
    {
        auto prototype = this->statePrototype[state];
        return this->prototypeActionCount[prototype];
    }

    template<typename ValueType>
    bool PosmgManager<ValueType>::contains(std::vector<uint64_t> v, uint64_t elem)
    {
        return std::find(v.begin(), v.end(), elem) != v.end();
    }

    template class PosmgManager<double>;
    template class PosmgManager<storm::RationalNumber>;

} // namespace synthesis