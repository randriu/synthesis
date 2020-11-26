#include <algorithm>

#include "research.h"

#include "storm/research/Counterexample.h"

// Define python bindings
void define_research(py::module& m) {

    // String container
    // using FlatSetString = boost::container::flat_set<std::string, std::less<std::string>, boost::container::new_allocator<std::string>>;
    // py::class_<FlatSetString>(m, "FlatSetString", "Container of strings to pass to program")
    //         .def(py::init<>())
    //         .def(py::init<FlatSetString>(), "other"_a)
    //         .def("insert", [](FlatSetString& flatset, std::string value) {flatset.insert(value);})
    //         .def("is_subset_of", [](FlatSetString const& left, FlatSetString const& right) {return std::includes(right.begin(), right.end(), left.begin(), left.end()); })
    //         .def("insert_set", [](FlatSetString& left, FlatSetString const& additional) { for(auto const& i : additional) {left.insert(i);}})
    //         .def("__str__", [](FlatSetString const& set) { std::stringstream str; str << "["; for(auto const& i : set) { str << i << ", ";} str << "]"; return str.str(); })
    //         .def("__len__", [](FlatSetString const& set) { return set.size();})
    //         .def("__iter__", [](FlatSetString &v) {
    //             return py::make_iterator(v.begin(), v.end());
    //         }, py::keep_alive<0, 1>()) /* Keep vector alive while iterator is used */
    //         ;

    m.def("dtmc_from_mdp", [](
        storm::models::sparse::Mdp<double> const& mdp,
        storm::storage::FlatSet<uint_fast64_t> const& automataAndEdgeIndices
        )
            {return storm::research::DtmcFromMdp<>(mdp,automataAndEdgeIndices);},
            "Restrict an MDP to selected edge indices",
            py::arg("mdp"), py::arg("automata_and_edge_indices")
        );

    // Counterexample generation
    py::class_<storm::research::Counterexample<>>(
        m, "SynthesisResearchCounterexample", "[synthesis research] Counterexample generation"
    )
        .def(
            py::init<
                storm::models::sparse::Mdp<double> const&,
                uint_fast64_t,
                std::vector<std::set<uint_fast64_t>> const&,
                std::vector<std::shared_ptr<storm::logic::Formula const>> const&,
                std::vector<std::shared_ptr<storm::modelchecker::ExplicitQuantitativeCheckResult<double> const>> const&
            >(),
            "Preprocess the quotiendt MDP.",
            py::arg("quotient_mdp"), py::arg("hole_count"), py::arg("mdp_holes"), py::arg("formulae"), py::arg("mdp_bounds")
            )
        .def(
            "prepare_dtmc",
            &storm::research::Counterexample<>::prepareDtmc,
            "Prepare a DTMC for counterexample construction.",
            py::arg("dtmc"), py::arg("state_mdp")
            )
        .def(
            "construct_conflict",
            &storm::research::Counterexample<>::constructCounterexample,
            "Construct a counterexample to a prepared DTMC.",
            py::arg("formula_index"), py::arg("use_bounds") = true
        )
        .def_property_readonly(
            "stats",
            [](storm::research::Counterexample<> & counterexample) {
                return counterexample.stats();
            },
            "Read stats."
        );  
}
