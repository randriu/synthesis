#include "StochasticGame.h"


namespace synthesis {


    StochasticGame::StochasticGame(storm::models::sparse::Pomdp<double> const& pomdp) : pomdp(pomdp) {

    }


    std::shared_ptr<storm::models::sparse::Smg<double>> StochasticGame::buildGame() {
        storm::storage::sparse::ModelComponents<double> components;
        components.transitionMatrix = this->pomdp.getTransitionMatrix();
        components.stateLabeling = this->pomdp.getStateLabeling();
        components.rewardModels = this->pomdp.getRewardModels();

        std::vector<uint64_t> statePlayerIndications;
        for (uint64_t state = 0; state < this->pomdp.getNumberOfStates(); state++) {
            bool has_p1_label = pomdp.getStateLabeling().getStateHasLabel("__player_1_state__", state);
            if (has_p1_label) {
                statePlayerIndications.push_back(1);
            } else {
                statePlayerIndications.push_back(2);
            }
        }
        components.statePlayerIndications = statePlayerIndications;

        auto myGame = std::make_shared<storm::models::sparse::Smg<double>>(std::move(components));

        return myGame;
    }


    void StochasticGame::checkGame(std::shared_ptr<storm::models::sparse::Smg<double>> const& model) {

        std::vector<std::shared_ptr<storm::logic::Formula const>> formulas =
        storm::api::extractFormulasFromProperties(storm::api::parseProperties("<<1>> Rmax=? [ S ]"));

        // auto formulas = storm::api::parseProperties("<<1>> Pmax=? [F \"goal\"]");
        auto task = storm::api::createTask<double>(formulas[0], false);

        storm::logic::Formula const& formula = task.getFormula();
        std::cout << "Formula in rPATL: " << formula.isInFragment(storm::logic::rpatl()) << std::endl;

        storm::Environment env;

        auto result = storm::api::verifyWithSparseEngine<double>(env, model, task);

        if (result == nullptr) {
            std::cout << "NULL" << std::endl;
        } else {
            std::cout << result->hasScheduler() << std::endl;
        }


    }



}