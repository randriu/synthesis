#include "synthesis.h"

#include "storm-synthesis/synthesis/Counterexample.h"

#include "storm-synthesis/pomdp/ExplicitPomdpMemoryUnfolder.h"
#include "storm-synthesis/pomdp/PomdpManager.h"

// Define python bindings
void define_synthesis(py::module& m) {

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
            {return storm::synthesis::DtmcFromMdp<>(mdp,automataAndEdgeIndices);},
            "Restrict an MDP to selected edge indices",
            py::arg("mdp"), py::arg("automata_and_edge_indices")
        );

    // Counterexample generation
    py::class_<storm::synthesis::Counterexample<>>(
        m, "SynthesisCounterexample", "Counterexample generation"
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
            "replace_formula_threshold",
            &storm::synthesis::Counterexample<>::replaceFormulaThreshold,
            "Replace the formula threshold as well as the corresponding MDP bound.",
            py::arg("formula_index"), py::arg("formula_threshold"), py::arg("mdp_bound")
            )
        .def(
            "prepare_dtmc",
            &storm::synthesis::Counterexample<>::prepareDtmc,
            "Prepare a DTMC for counterexample construction.",
            py::arg("dtmc"), py::arg("state_mdp")
            )
        .def(
            "construct_conflict",
            &storm::synthesis::Counterexample<>::constructCounterexample,
            "Construct a counterexample to a prepared DTMC.",
            py::arg("formula_index"), py::arg("use_bounds") = true
        )
        .def_property_readonly(
            "stats",
            [](storm::synthesis::Counterexample<> & counterexample) {
                return counterexample.stats();
            },
            "Read stats."
        );

    py::class_<storm::synthesis::ExplicitPomdpMemoryUnfolder<double>>(m, "ExplicitPomdpMemoryUnfolder", "Explicit memory unfolder for POMDPs")
        .def(py::init<storm::models::sparse::Pomdp<double> const&, storm::storage::PomdpMemory const&>(), "Constructor.", py::arg("pomdp"), py::arg("memory"))
        .def("transform", &storm::synthesis::ExplicitPomdpMemoryUnfolder<double>::transform, "Unfold memory into POMDP.")
        .def("state_to_state", &storm::synthesis::ExplicitPomdpMemoryUnfolder<double>::state_to_state, "TODO")
        .def("state_to_memory", &storm::synthesis::ExplicitPomdpMemoryUnfolder<double>::state_to_memory, "TODO")
        ;

    py::class_<storm::synthesis::PomdpManager<double>>(m, "PomdpManager", "POMDP manager")
        .def(py::init<storm::models::sparse::Pomdp<double> const&>(), "Constructor.", py::arg("pomdp"))
        .def("construct_mdp", &storm::synthesis::PomdpManager<double>::constructMdp, "Unfold POMDP into MDP.")
        .def("inject_memory", &storm::synthesis::PomdpManager<double>::injectMemory, "Inject 1 state into a selected observation.", py::arg("observation"))
        ; 
}

// STANDARD, SIMPLE_LINEAR, SIMPLE_LINEAR_INVERSE, SIMPLE_LOG, FULL
void define_transformations(py::module &m) {
    /*py::class_<storm::transformer::ExplicitPomdpMemoryUnfolder<double>>(m, "ExplicitPomdpMemoryUnfolder", "Explicit memory unfolder for POMDPs")
        .def(py::init<storm::models::sparse::Pomdp<double> const&, storm::storage::PomdpMemory const&>(), "Constructor.", py::arg("pomdp"), py::arg("memory"))
        .def("transform", &storm::transformer::ExplicitPomdpMemoryUnfolder<double>::transform, "Unfold memory into POMDP.")
        .def("state_to_state", &storm::transformer::ExplicitPomdpMemoryUnfolder<double>::state_to_state, "TODO")
        .def("state_to_memory", &storm::transformer::ExplicitPomdpMemoryUnfolder<double>::state_to_memory, "TODO")
        // .def("action_map", &storm::transformer::ExplicitPomdpMemoryUnfolder<double>::action_map, "TODO")
        // .def("memory_map", &storm::transformer::ExplicitPomdpMemoryUnfolder<double>::memory_map, "TODO")
        ;*/
}
