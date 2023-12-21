#include "JaniChoices.h"

#include <storm/models/sparse/Mdp.h>
#include <storm/storage/jani/Model.h>
#include <storm/storage/sparse/JaniChoiceOrigins.h>
#include <storm/storage/sparse/ModelComponents.h>

namespace synthesis {
    
    template<typename ValueType>
    storm::models::sparse::ChoiceLabeling reconstructChoiceLabelsFromJani(
        storm::models::sparse::Model<ValueType> const& model
    ) {
        uint64_t num_choices = model.getNumberOfChoices();
        auto const& co = model.getChoiceOrigins()->asJaniChoiceOrigins();
        auto const& jani = co.getModel();

        storm::models::sparse::ChoiceLabeling choice_labeling(num_choices);
        for (auto const& action : jani.getActions()) {
            choice_labeling.addLabel(action.getName(), storm::storage::BitVector(num_choices,false));
        }
        
        for(uint64_t choice = 0; choice < num_choices; choice++) {
            for(auto const& aut_edge: co.getEdgeIndexSet(choice)) {
                auto [aut_index,edge_index] = jani.decodeAutomatonAndEdgeIndices(aut_edge);
                auto action_index = jani.getAutomaton(aut_index).getEdge(edge_index).getActionIndex();
                choice_labeling.addLabelToChoice(jani.getAction(action_index).getName(), choice);
            }
        }
        
        return choice_labeling;
    }

    /**
     * Given model and its choice labeling, remove unused labels and make sure that all choices have at most 1 label.
     * If the choice does not have a label, label it with the label derived from the provided prefix.
     * Make sure that for each state of the MDP, either all its rows have no labels or all its rows have exactly one
     */
    template<typename ValueType>
    void makeChoiceLabelingCanonic(
        storm::models::sparse::Model<ValueType> const& model,
        storm::models::sparse::ChoiceLabeling& choice_labeling,
        std::string const& no_label_prefix
    ) {
        for(auto const& label: choice_labeling.getLabels()) {
            if(choice_labeling.getChoices(label).empty()) {
                choice_labeling.removeLabel(label);
            }
        }
        storm::storage::BitVector no_label_labeling(model.getNumberOfChoices());
        for(uint64_t choice = 0; choice < model.getNumberOfChoices(); choice++) {
            uint64_t choice_num_labels = choice_labeling.getLabelsOfChoice(choice).size();
            if(choice_num_labels > 1) {
                throw std::invalid_argument("A choice of the model contains multiple labels.");
            }
            if(choice_num_labels == 0) {
                no_label_labeling.set(choice,true);
            }
        }
        std::string empty_label = choice_labeling.addUniqueLabel(no_label_prefix, no_label_labeling);
    }

    template<typename ValueType>
    std::shared_ptr<storm::models::sparse::Model<ValueType>> addChoiceLabelsFromJani(storm::models::sparse::Model<ValueType> const& model) {
        storm::storage::sparse::ModelComponents<ValueType> components;
        components.transitionMatrix = model.getTransitionMatrix();
        components.stateLabeling = model.getStateLabeling();
        if(model.hasStateValuations()) {
            components.stateValuations = model.getStateValuations();
        }
        storm::models::sparse::ChoiceLabeling choice_labeling = reconstructChoiceLabelsFromJani(model);
        makeChoiceLabelingCanonic(model,choice_labeling,"empty_label");
        components.choiceLabeling = choice_labeling;
        components.rewardModels = model.getRewardModels();
        return std::make_shared<storm::models::sparse::Mdp<ValueType>>(std::move(components));
    }
    

    template std::shared_ptr<storm::models::sparse::Model<double>> addChoiceLabelsFromJani(storm::models::sparse::Model<double> const& model);
}
