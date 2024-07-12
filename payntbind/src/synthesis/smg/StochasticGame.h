#pragma once

#include <storm/adapters/RationalNumberAdapter.h>
#include <storm/models/sparse/Smg.h>
#include <storm/models/sparse/Pomdp.h>
#include <storm-parsers/api/storm-parsers.h>
#include <storm/api/verification.h>
#include <storm/api/storm.h>

namespace synthesis {

    class StochasticGame {

    public:

        StochasticGame(storm::models::sparse::Pomdp<double> const& pomdp);

        std::shared_ptr<storm::models::sparse::Smg<double>> buildGame();

        void checkGame(std::shared_ptr<storm::models::sparse::Smg<double>> const& model);

    private:

        storm::models::sparse::Pomdp<double> const& pomdp;
    };
}