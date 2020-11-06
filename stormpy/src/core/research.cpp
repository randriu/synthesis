#include <algorithm>

#include "research.h"

#include "storm/research/Counterexample.h"

// Define python bindings
void define_research(py::module& m) {

    // String container
    using FlatSetString = boost::container::flat_set<std::string, std::less<std::string>, boost::container::new_allocator<std::string>>;
    py::class_<FlatSetString>(m, "FlatSetString", "Container of strings to pass to program")
            .def(py::init<>())
            .def(py::init<FlatSetString>(), "other"_a)
            .def("insert", [](FlatSetString& flatset, std::string value) {flatset.insert(value);})
            .def("is_subset_of", [](FlatSetString const& left, FlatSetString const& right) {return std::includes(right.begin(), right.end(), left.begin(), left.end()); })
            .def("insert_set", [](FlatSetString& left, FlatSetString const& additional) { for(auto const& i : additional) {left.insert(i);}})
            .def("__str__", [](FlatSetString const& set) { std::stringstream str; str << "["; for(auto const& i : set) { str << i << ", ";} str << "]"; return str.str(); })
            .def("__len__", [](FlatSetString const& set) { return set.size();})
            .def("__iter__", [](FlatSetString &v) {
                return py::make_iterator(v.begin(), v.end());
            }, py::keep_alive<0, 1>()) /* Keep vector alive while iterator is used */
            ;

    // Counterexample generation
    py::class_<storm::research::Counterexample<>>(
        m, "SynthesisResearchCounterexample", "[synthesis research] Counterexample generation"
    )
        .def(
            py::init<
                storm::jani::Model const&,
                storm::storage::FlatSet<std::string> const&,
                storm::logic::Formula const&,
                storm::models::sparse::Mdp<double> const&,
                storm::modelchecker::ExplicitQuantitativeCheckResult<double> const&
            >(),
            "Preprocess the quotiendt MDP.",
            py::arg("program"), py::arg("relevant_holes"), py::arg("formula"), py::arg("mdp"), py::arg("mdp_result")
        )
        // .def(
        //     "construct_via_states",
        //     &storm::research::Counterexample<>::constructViaStates,
        //     "Construct a counterexample to a given DTMC via state exploration.",
        //     py::arg("dtmc"), py::arg("dtmc_result"), py::arg("expanded_per_iter"), py::arg("subchains_checked_limit")
        // )
        .def(
            "construct_via_holes",
            &storm::research::Counterexample<>::constructViaHoles,
            "Construct a counterexample to a given DTMC via holes exploration.",
            py::arg("dtmc"), py::arg("use_bounds")
        )
        .def_property_readonly(
            "stats",
            [](storm::research::Counterexample<> & counterexample) {
                return counterexample.stats();
            },
            "Read stats."
        );  
}
