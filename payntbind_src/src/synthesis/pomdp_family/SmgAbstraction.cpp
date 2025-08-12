#include "SmgAbstraction.h"

#include "src/synthesis/translation/componentTranslations.h"
#include "src/synthesis/translation/ItemKeyTranslator.h"
#include "src/synthesis/posmg/Posmg.h"

#include <storm/storage/PlayerIndex.h>
#include <storm/utility/builder.h>

#include <queue>

namespace synthesis {

    template<typename ValueType>
    SmgAbstraction<ValueType>::SmgAbstraction(
        storm::models::sparse::Model<ValueType> const& quotient,
        uint64_t quotient_num_actions,
        std::vector<uint64_t> const& choice_to_action,
        storm::storage::BitVector const& quotient_choice_mask
    ) {
        uint64_t quotient_num_states = quotient.getNumberOfStates();
        uint64_t quotient_initial_state = *(quotient.getInitialStates().begin());
        uint64_t quotient_num_choices = quotient.getNumberOfChoices();
        auto const& quotient_row_groups = quotient.getTransitionMatrix().getRowGroupIndices();

        ItemKeyTranslator<uint64_t> state_action_to_game_state(quotient_num_states);
        // for Player 1 states, contains available actions; for Player 2 states, contains enabled choices
        std::vector<std::vector<uint64_t>> game_state_to_choices;

        std::queue<uint64_t> unexplored_states;
        storm::storage::BitVector state_is_encountered(quotient_num_states,false);
        unexplored_states.push(quotient_initial_state);
        state_is_encountered.set(quotient_initial_state,true);
        std::vector<std::vector<uint64_t>> state_enabled_actions(quotient_num_states);
        std::vector<std::vector<uint64_t>> state_action_choice(quotient_num_states);
        while(not unexplored_states.empty()) {
            uint64_t state = unexplored_states.front();
            unexplored_states.pop();
            std::set<uint64_t> enabled_actions;
            state_action_choice[state] = std::vector(quotient_num_actions,quotient_num_choices);
            uint64_t player1_state = state_action_to_game_state.translate(state,quotient_num_actions);
            game_state_to_choices.resize(state_action_to_game_state.numTranslations());
            for(uint64_t choice = quotient_row_groups[state]; choice < quotient_row_groups[state+1]; ++choice) {
                if(not quotient_choice_mask[choice]) {
                    continue;
                }
                uint64_t action = choice_to_action[choice];
                enabled_actions.insert(action);
                state_action_choice[state][action] = choice;
                uint64_t player2_state = state_action_to_game_state.translate(state,action);
                game_state_to_choices.resize(state_action_to_game_state.numTranslations());
                game_state_to_choices[player2_state].push_back(choice);
                for(auto const &entry: quotient.getTransitionMatrix().getRow(choice)) {
                    uint64_t state_dst = entry.getColumn();
                    if(state_is_encountered[state_dst]) {
                        continue;
                    }
                    unexplored_states.push(state_dst);
                    state_is_encountered.set(state_dst,true);
                }
            }
            state_enabled_actions[state] = std::vector(enabled_actions.begin(),enabled_actions.end());
        }

        uint64_t game_num_states = state_action_to_game_state.numTranslations();
        storm::storage::SparseMatrixBuilder<ValueType> game_matrix_builder(0,0,0,false,true);
        uint64_t game_num_choices = 0;
        // for Player 1, contains a representative choice with the appropriate label; for Player 2, contains the corresponding choice
        std::vector<uint64_t> game_choice_to_quotient_choice;
        std::vector<bool> game_choice_is_player1;

        for(uint64_t game_state = 0; game_state < game_num_states; ++game_state) {
            auto [state,state_action] = state_action_to_game_state.retrieve(game_state);
            game_matrix_builder.newRowGroup(game_num_choices);
            if(state_action == quotient_num_actions) {
                // Player 1 state
                for(uint64_t action: state_enabled_actions[state]) {
                    uint64_t player2_state = state_action_to_game_state.translate(state,action);
                    game_matrix_builder.addNextValue(game_num_choices,player2_state,1);
                    // game_state_to_choices[player1_state].push_back(action);
                    game_choice_to_quotient_choice.push_back(state_action_choice[state][action]);
                    game_choice_is_player1.push_back(true);
                    game_num_choices++;
                }
            } else {
                // Player 2 state
                uint64_t player2_state = game_state;
                for(uint64_t choice: game_state_to_choices[game_state]) {
                    for(auto const& entry: quotient.getTransitionMatrix().getRow(choice)) {
                        uint64_t state_dst = entry.getColumn();
                        uint64_t game_state_dst = state_action_to_game_state.translate(state_dst,quotient_num_actions);
                        game_matrix_builder.addNextValue(game_num_choices,game_state_dst,entry.getValue());
                    }
                    game_choice_to_quotient_choice.push_back(choice);
                    game_choice_is_player1.push_back(false);
                    game_num_choices++;
                }
            }
        }

        storm::storage::sparse::ModelComponents<ValueType> components;
        components.transitionMatrix =  game_matrix_builder.build();
        uint64_t game_initial_state = state_action_to_game_state.translate(quotient_initial_state,quotient_num_actions);

        components.stateLabeling = synthesis::translateStateLabeling(quotient,state_action_to_game_state.translationToItem(),game_initial_state);
        std::vector<storm::storage::PlayerIndex> game_state_to_player;
        for(auto [_,action]: state_action_to_game_state.translationToItemKey()) {
            uint64_t player = action == quotient_num_actions ? 0 : 1;
            game_state_to_player.push_back(player);
        }
        components.statePlayerIndications = std::move(game_state_to_player);
        // skipping state valuations

        storm::storage::BitVector game_choice_mask(game_num_choices,true);
        storm::storage::BitVector player1_choice_mask(game_num_choices);
        for(uint64_t game_choice = 0; game_choice < game_num_choices; ++game_choice) {
            player1_choice_mask.set(game_choice_is_player1[game_choice]);
        }
        components.choiceLabeling = synthesis::translateChoiceLabeling(quotient,game_choice_to_quotient_choice,game_choice_mask);
        components.rewardModels = synthesis::translateRewardModels(quotient,game_choice_to_quotient_choice,player1_choice_mask);
        // skipping choice origins

        if (quotient.getType() == storm::models::ModelType::Pomdp) {
            components.observabilityClasses = synthesis::translateObservabilityClasses(quotient,state_action_to_game_state.translationToItem());
            // skipping observation valuations
            this->smg = std::make_shared<synthesis::Posmg<ValueType>>(std::move(components));
        } else {
            this->smg = std::make_shared<storm::models::sparse::Smg<ValueType>>(std::move(components));
        }

        this->state_to_quotient_state_action = state_action_to_game_state.translationToItemKey();
        this->choice_to_quotient_choice = std::move(game_choice_to_quotient_choice);
    }

    template class SmgAbstraction<double>;
}