#pragma once

/* 
 * code in this file was taken from TEMPEST (https://github.com/PrangerStefan/TempestSynthesis)
 */

#include <storm/storage/SparseMatrix.h>
#include <storm/solver/LinearEquationSolver.h>
#include <storm/solver/MinMaxLinearEquationSolver.h>
#include <storm/storage/Scheduler.h>

#include "Multiplier.h"

namespace synthesis {

    template <typename ValueType>
    class GameViHelper {
    public:
        GameViHelper(storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::BitVector statesOfCoalition);

        void prepareSolversAndMultipliers(const storm::Environment& env);

        /*!
            * Perform value iteration until convergence
            */
        void performValueIteration(storm::Environment const& env, std::vector<ValueType>& x, std::vector<ValueType> b, storm::solver::OptimizationDirection const dir, std::vector<ValueType>& constrainedChoiceValues);

        /*!
            * Sets whether an optimal scheduler shall be constructed during the computation
            */
        void setProduceScheduler(bool value);

        /*!
            * @return whether an optimal scheduler shall be constructed during the computation
            */
        bool isProduceSchedulerSet() const;

        /*!
            * Sets whether an optimal scheduler shall be constructed during the computation
            */
        void setShieldingTask(bool value);

        /*!
            * @return whether an optimal scheduler shall be constructed during the computation
            */
        bool isShieldingTask() const;

        /*!
            * Changes the transitionMatrix to the given one.
            */
        void updateTransitionMatrix(storm::storage::SparseMatrix<ValueType> newTransitionMatrix);

        /*!
            * Changes the statesOfCoalition to the given one.
            */
        void updateStatesOfCoalition(storm::storage::BitVector newStatesOfCoalition);

        storm::storage::Scheduler<ValueType> extractScheduler() const;

        void getChoiceValues(storm::Environment const& env, std::vector<ValueType> const& x, std::vector<ValueType>& choiceValues);

        /*!
            * Fills the choice values vector to the original size with zeros for ~psiState choices.
            */
        void fillChoiceValuesVector(std::vector<ValueType>& choiceValues, storm::storage::BitVector psiStates, std::vector<storm::storage::SparseMatrix<double>::index_type> rowGroupIndices);

    private:
        /*!
            * Performs one iteration step for value iteration
            */
        void performIterationStep(storm::Environment const& env, storm::solver::OptimizationDirection const dir, std::vector<uint64_t>* choices = nullptr);

        /*!
            * Checks whether the curently computed value achieves the desired precision
            */
        bool checkConvergence(ValueType precision) const;

        std::vector<ValueType>& xNew();
        std::vector<ValueType> const& xNew() const;

        std::vector<ValueType>& xOld();
        std::vector<ValueType> const& xOld() const;
        bool _x1IsCurrent;

        /*!
            * @pre before calling this, a computation call should have been performed during which scheduler production was enabled.
            * @return the produced scheduler of the most recent call.
            */
        std::vector<uint64_t> const& getProducedOptimalChoices() const;

        /*!
            * @pre before calling this, a computation call should have been performed during which scheduler production was enabled.
            * @return the produced scheduler of the most recent call.
            */
        std::vector<uint64_t>& getProducedOptimalChoices();

        storm::storage::SparseMatrix<ValueType> _transitionMatrix;
        storm::storage::BitVector _statesOfCoalition;
        std::vector<ValueType> _x, _x1, _x2, _b;
        std::unique_ptr<synthesis::Multiplier<ValueType>> _multiplier;

        bool _produceScheduler = false;
        bool _shieldingTask = false;
        boost::optional<std::vector<uint64_t>> _producedOptimalChoices;
    };
}
