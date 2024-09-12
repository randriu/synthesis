#pragma once

/* 
 * code in this file was taken from TEMPEST (https://github.com/PrangerStefan/TempestSynthesis)
 */

#include <storm/modelchecker/helper/infinitehorizon/SparseInfiniteHorizonHelper.h>
#include <storm/storage/BitVector.h>
#include <storm/storage/Scheduler.h>

namespace synthesis {

    // namespace storage {
    //     template <typename VT> class Scheduler;
    // }

    // namespace modelchecker {
    //     namespace helper {

    /*!
        * Helper class for model checking queries that depend on the long run behavior of the (nondeterministic) system with different players choices.
        * @tparam ValueType the type a value can have
        */
    template <typename ValueType>
    class SparseNondeterministicGameInfiniteHorizonHelper : public storm::modelchecker::helper::SparseInfiniteHorizonHelper<ValueType, true> {

    public:

        /*!
            * Function mapping from indices to values
            */
        typedef typename storm::modelchecker::helper::SparseInfiniteHorizonHelper<ValueType, true>::ValueGetter ValueGetter;

        /*!
            * Initializes the helper for a discrete time model with different players (i.e. SMG)
            */
        SparseNondeterministicGameInfiniteHorizonHelper(storm::storage::SparseMatrix<ValueType> const& transitionMatrix, storm::storage::BitVector statesOfCoalition);

        /*! TODO
            * Computes the long run average value given the provided state and action based rewards
            * @param stateValuesGetter a function returning a value for a given state index
            * @param actionValuesGetter a function returning a value for a given (global) choice index
            * @return a value for each state
            */
        std::vector<ValueType> computeLongRunAverageValues(storm::Environment const& env, ValueGetter const& stateValuesGetter,  ValueGetter const& actionValuesGetter);

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

        /*!
            * @pre before calling this, a computation call should have been performed during which scheduler production was enabled.
            * @return a new scheduler containing optimal choices for each state that yield the long run average values of the most recent call.
            */
        storm::storage::Scheduler<ValueType> extractScheduler() const;

        /*!
            * @return the computed choice values for the states.
            */
        std::vector<ValueType> getChoiceValues() const;

        ValueType computeLraForComponent(storm::Environment const& env, ValueGetter const& stateValuesGetter,  ValueGetter const& actionValuesGetter, storm::storage::MaximalEndComponent const& component);

        ValueType computeLraVi(storm::Environment const& env, ValueGetter const& stateValuesGetter, ValueGetter const& actionValuesGetter, storm::storage::MaximalEndComponent const& mec);

        void createDecomposition();
        std::vector<ValueType> buildAndSolveSsp(storm::Environment const& env, std::vector<ValueType> const& mecLraValues);

        /*!
        * Sets whether all choice values shall be computed
        */
        void setProduceChoiceValues(bool value);

        /*!
        * @return whether all choice values shall be computed
        */
        bool isProduceChoiceValuesSet() const;

    private:
        storm::storage::BitVector statesOfCoalition;

    protected:
        boost::optional<std::vector<ValueType>> _choiceValues;
        bool _produceChoiceValues;
    };

}
