#include "storm-synthesis/pomdp/PomdpManager.h"

#include "storm/exceptions/InvalidArgumentException.h"
#include "storm/exceptions/NotSupportedException.h"
#include "storm/storage/sparse/ModelComponents.h"
#include "storm/storage/SparseMatrix.h"
#include "storm/models/sparse/StandardRewardModel.h"

namespace storm {
    namespace synthesis {

            
            template<typename ValueType>
            PomdpManager<ValueType>::PomdpManager(storm::models::sparse::Pomdp<ValueType> const& pomdp)
            : pomdp(pomdp) {
                STORM_LOG_THROW(pomdp.isCanonic() , storm::exceptions::InvalidArgumentException, "POMDP must be canonic");

                // auto num_states = pomdp.getNumberOfStates();
                auto num_observations = pomdp.getNumberOfStates();
                this->observation_memory_size.resize(num_observations, 1);
                this->buildStateSpace();

                /*this->prototypes_with_observation.resize(num_observations);
                for(uint64_t state = 0; state < num_states; state++) {
                    auto obs = pomdp.getObservation(state);
                    this->prototypes_with_observation[obs].push_back(state);
                }*/
            }

            template<typename ValueType>
            void PomdpManager<ValueType>::buildStateSpace() {
                this->state_prototype.clear();
                this->state_memory.clear();
                this->num_states = 0;
                for(uint64_t prototype = 0; prototype < this->pomdp.getNumberOfStates(); prototype++) {
                    auto obs = this->pomdp.getObservation(prototype);
                    auto memory_size = this->observation_memory_size[obs];
                    this->state_duplicates[prototype] = std::vector<uint64_t>(memory_size);
                    for(uint64_t memory = 0; memory < memory_size; memory++) {
                        this->state_duplicates[memory].push_back(this->num_states);
                        this->state_prototype.push_back(prototype);
                        this->state_memory.push_back(memory);
                        this->num_states++;
                    }
                }
            }

            template<typename ValueType>
            uint64_t PomdpManager<ValueType>::translateState(uint64_t prototype, uint64_t memory) {
                if(memory >= this->state_duplicates[prototype].size()) {
                    memory = 0;
                }
                return this->state_duplicates[prototype][memory];
            }

            template<typename ValueType>
            std::shared_ptr<storm::models::sparse::Mdp<ValueType>> PomdpManager<ValueType>::constructMdp() {

                storm::storage::sparse::ModelComponents<ValueType> components;


                components.transitionMatrix = buildTransitionMatrix();
                components.stateLabeling = buildStateLabeling();

                // TODO remove unreachable states

                // build the remaining components
                /*components.observabilityClasses = transformObservabilityClasses(reachableStates);*/
                for (auto const& reward_model : pomdp.getRewardModels()) {
                    components.rewardModels.emplace(reward_model.first, buildRewardModel(reward_model.second));
                }
                components.rewardModels = pomdp.getRewardModels();

                this->mdp = std::make_shared<storm::models::sparse::Mdp<ValueType>>(std::move(components));


                std::cout << "success" << std::endl << std::flush;
                exit(0);

                return this->mdp;
            }

            template<typename ValueType>
            storm::models::sparse::StateLabeling PomdpManager<ValueType>::buildStateLabeling() {
                storm::models::sparse::StateLabeling labeling(this->num_states);
                for (auto const& label : pomdp.getStateLabeling().getLabels()) {
                    storm::storage::BitVector label_flags(this->num_states, false);
                    
                    if (label == "init") {
                        // init label is only assigned to states with the initial memory state
                        for (auto const& prototype : pomdp.getStateLabeling().getStates(label)) {
                            label_flags.set(translateState(prototype, 0));
                        }
                    } else {
                        for (auto const& prototype : pomdp.getStateLabeling().getStates(label)) {
                            for(auto duplicate: this->state_duplicates[prototype]) {
                                label_flags.set(duplicate);
                            }
                        }
                    }
                    labeling.addLabel(label, std::move(label_flags));
                }
                return labeling;
            }



            template<typename ValueType>
            storm::storage::SparseMatrix<ValueType> PomdpManager<ValueType>::buildTransitionMatrix() {

                // for each row, identify maximum memory size among all destinations
                // this will define the number of copies we need to make of each row
                std::vector<uint64_t> row_copies_needed(this->pomdp.getNumberOfChoices());
                for (uint64_t prototype_row = 0; prototype_row < this->pomdp.getNumberOfChoices(); prototype_row++) {
                    uint64_t max_memory_size = 0;
                    for(auto const &entry: this->pomdp.getTransitionMatrix().getRow(prototype_row)) {
                        auto dst = entry.getColumn();
                        auto obs = this->pomdp.getObservation(dst);
                        auto memory_size = this->observation_memory_size[obs];
                        if(memory_size > max_memory_size) {
                            max_memory_size = memory_size;
                        } 
                    }
                    row_copies_needed[prototype_row] = max_memory_size;
                }

                // for each
                // TODO compute number of entries
                std::vector<uint64_t> row_groups(this->num_states+1);
                this->row_prototype.clear();
                this->row_memory.clear();
                // uint64_t num_entries = 0;
                
                for(uint64_t state = 0; state < num_states; state++) {
                    row_groups.push_back(this->row_prototype.size());
                    
                    // get the prototype state
                    auto prototype_state = this->state_prototype[state];

                    auto const& row_group_indices = this->pomdp.getTransitionMatrix().getRowGroupIndices();
                    for (
                        uint64_t prototype_row = row_group_indices[prototype_state];
                        prototype_row < row_group_indices[prototype_state + 1];
                        prototype_row++
                    ) {
                        // creat the required number of copies of this row
                        // each transition will lead to the corresponding memory update
                        // if the destination is not resized for the memory update, default to 0
                        for(uint64_t dst_mem = 0; dst_mem < row_copies_needed[prototype_row]; dst_mem++) {
                            this->row_prototype.push_back(prototype_row);
                            this->row_memory.push_back(dst_mem);
                        }
                    }
                }
                this->num_rows = this->row_prototype.size();
                
                // create choices for each state
                storm::storage::SparseMatrixBuilder<ValueType> builder(
                    this->num_rows, this->num_states, 0, true, true, this->num_states
                );
                for(uint64_t state = 0; state < num_states; state++) {
                    builder.newRowGroup(row_groups[state]);
                    for (uint64_t row = row_groups[state]; row < row_groups[state+1]; row++) {
                        auto prototype_row = this->row_prototype[row];
                        auto dst_mem = this->row_memory[row];
                        for(auto const &entry: this->pomdp.getTransitionMatrix().getRow(prototype_row)) {
                            auto dst = this->translateState(entry.getColumn(),dst_mem);
                            builder.addNextValue(row, dst, entry.getValue());
                        }
                    }
                }

                std::cout << "success" << std::endl << std::flush;
                exit(0);

                return builder.build();
            }


            template<typename ValueType>
            storm::models::sparse::StandardRewardModel<ValueType> PomdpManager<ValueType>::buildRewardModel(storm::models::sparse::StandardRewardModel<ValueType> const& rewardModel) {
                boost::optional<std::vector<ValueType>> state_rewards, action_rewards;
                if (rewardModel.hasStateRewards()) {
                    state_rewards = std::vector<ValueType>();
                    state_rewards->reserve(this->num_states);
                    for(uint64_t state = 0; state < this->num_states; state++) {
                        auto prototype = this->state_prototype[state];
                        auto reward = rewardModel.getStateReward(prototype);
                        state_rewards->push_back(reward);
                    }
                }
                if (rewardModel.hasStateActionRewards()) {
                    action_rewards = std::vector<ValueType>();
                    for(uint64_t row = 0; row < this->num_rows; row++) {
                        auto prototype = this->row_prototype[row];
                        auto reward = rewardModel.getStateActionReward(prototype);
                        action_rewards->push_back(reward);
                    }
                }
                STORM_LOG_THROW(!rewardModel.hasTransitionRewards(), storm::exceptions::NotSupportedException, "Transition rewards are currently not supported.");
                return storm::models::sparse::StandardRewardModel<ValueType>(std::move(state_rewards), std::move(action_rewards));
            }


            

            template<typename ValueType>
            void PomdpManager<ValueType>::injectMemory(uint_fast64_t observation) {
                std::cout << "injecting memory into observation " << observation << std::endl;
                
                this->observation_memory_size[observation]++;
                this->buildStateSpace();
            }

            

            


            

            /*template<typename ValueType>
            void PomdpManager<ValueType>::copyRow(storm::storage::SparseMatrixBuilder<ValueType> builder, uint64_t prototype_row) {
                
            }*/


            template class PomdpManager<double>;

    }
}