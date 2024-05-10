// Contributions of MASTER'S THESIS 
// INDUCTIVE SYNTHESIS OF FINITE STATE CONTROLLERS FOR DECENTRALIZED POMDPS
// by Vojtech Hranicka

// Added majority of bindings
#include "../synthesis.h"

#include "DecPomdp.h"

void bindings_decpomdp(py::module& m) {

    py::class_<synthesis::DecPomdp>(m, "DecPomdp", "dec-POMDP")
        // .def(py::init<std::string const&>(), "constructor.", py::arg("filename"));
        .def("construct_quotient_mdp", &synthesis::DecPomdp::constructQuotientMdp)
        .def("construct_mdp", &synthesis::DecPomdp::constructMdp)
        .def("construct_pomdp", &synthesis::DecPomdp::constructPomdp)
        .def("set_global_memory_size", &synthesis::DecPomdp::setGlobalMemorySize, py::arg("memory_size"))
        .def_property_readonly("observation_memory_size", [](synthesis::DecPomdp& decpomdp) {return decpomdp.observation_memory_size;})
        .def_property_readonly("num_agents", [](synthesis::DecPomdp& decpomdp) {return decpomdp.num_agents;})
        .def_property_readonly("num_quotient_rows", [](synthesis::DecPomdp& decpomdp) {return decpomdp.num_quotient_rows;})
        .def_property_readonly("joint_observations", [](synthesis::DecPomdp& decpomdp) {return decpomdp.joint_observations;})
        .def_property_readonly("agent_observation_labels", [](synthesis::DecPomdp& decpomdp) {return decpomdp.agent_observation_labels;})
        
        .def_property_readonly("reward_model_name", [](synthesis::DecPomdp& decpomdp) {return decpomdp.reward_model_name;})
        .def_property_readonly("reward_minimizing", [](synthesis::DecPomdp& decpomdp) {return decpomdp.reward_minimizing;})
        .def_property_readonly("discount_factor", [](synthesis::DecPomdp& decpomdp) {return decpomdp.discount_factor;})
        .def_property_readonly("discounted", [](synthesis::DecPomdp& decpomdp) {return decpomdp.discounted;})
        
        .def("apply_discount_factor_transformation", &synthesis::DecPomdp::applyDiscountFactorTransformation)
        .def_property_readonly("discount_sink_label", [](synthesis::DecPomdp& decpomdp) {return decpomdp.discount_sink_label;})

        .def_property_readonly("row_joint_action", [](synthesis::DecPomdp& decpomdp) {return decpomdp.row_joint_action;}, "row_joint_action")
        .def_property_readonly("state_joint_observation", [](synthesis::DecPomdp& decpomdp) {return decpomdp.state_joint_observation;},"state_joint_observation")
        .def_property_readonly("joint_actions", [](synthesis::DecPomdp& decpomdp) {return decpomdp.joint_actions;})
        .def_property_readonly("agent_action_labels", [](synthesis::DecPomdp& decpomdp) {return decpomdp.agent_action_labels;})
        .def_property_readonly("max_successor_memory_size", [](synthesis::DecPomdp& decpomdp) {return decpomdp.max_successor_memory_size;})

        .def_property_readonly("row_action_hole", [](synthesis::DecPomdp& decpomdp) {return decpomdp.row_action_hole;})
        .def_property_readonly("row_action_option", [](synthesis::DecPomdp& decpomdp) {return decpomdp.row_action_option;})
        .def_property_readonly("row_memory_hole", [](synthesis::DecPomdp& decpomdp) {return decpomdp.row_memory_hole;})
        .def_property_readonly("row_memory_option", [](synthesis::DecPomdp& decpomdp) {return decpomdp.row_memory_option;})
        .def_property_readonly("num_holes", [](synthesis::DecPomdp& decpomdp) {return decpomdp.num_holes;})
        .def_property_readonly("transition_matrix", [](synthesis::DecPomdp& decpomdp) {return decpomdp.transition_matrix;}, "transition matrix")

        .def_property_readonly("agent_max_successor_memory_size", [](synthesis::DecPomdp& decpomdp) {return decpomdp.agent_max_successor_memory_size;})
        .def_property_readonly("memory_joint_observation", [](synthesis::DecPomdp& decpomdp) {return decpomdp.memory_joint_observation;})
        .def_property_readonly("action_to_memory_joint_observation", [](synthesis::DecPomdp& decpomdp) {return decpomdp.action_to_memory_joint_observation;})
        .def_property_readonly("state_to_memory_joint_observation", [](synthesis::DecPomdp& decpomdp) {return decpomdp.state_to_memory_joint_observation;})
        .def_property_readonly("nr_memory_joint_observations", [](synthesis::DecPomdp& decpomdp) {return decpomdp.nr_memory_joint_observations;})
        .def("set_target_state", &synthesis::DecPomdp::setTargetState, py::arg("state"))
        .def_property_readonly("target_label", [](synthesis::DecPomdp& decpomdp) {return decpomdp.target_label;})
        
        



        //new
        // .def("set_observation_memory_size", &storm::synthesis::DecPomdp::setObservationMemorySize, "Set memory size to a selected observation.", py::arg("observation"), py::arg("memory_size"))
        // // .def_property_readonly("num_states", [](storm::synthesis::DecPomdp& decpomdp) {return decpomdp.num_states();}, "number of states")
        // // .def_property_readonly("transition_matrix", [](storm::synthesis::DecPomdp& decpomdp) {return decpomdp.transition_matrix;}, "transition matrix")
        // // .def_property_readonly("row_reward", [](storm::synthesis::DecPomdp& decpomdp) {return decpomdp.row_reward;}, "for each row group, a list of row rewards")

        // .def_property_readonly("reward_model_name", [](storm::synthesis::DecPomdp& decpomdp) {return decpomdp.reward_model_name;})
        // .def_property_readonly("reward_minimizing", [](storm::synthesis::DecPomdp& decpomdp) {return decpomdp.reward_minimizing;})
        // .def_property_readonly("discount_factor", [](storm::synthesis::DecPomdp& decpomdp) {return decpomdp.discount_factor;})
        
        // .def("apply_discount_factor_transformation", &storm::synthesis::DecPomdp::applyDiscountFactorTransformation)
        // .def_property_readonly("discount_sink_label", [](storm::synthesis::DecPomdp& decpomdp) {return decpomdp.discount_sink_label;})

        // .def_property_readonly("num_holes", [](storm::synthesis::DecPomdp& decpomdp) {return decpomdp.num_holes;})

        // .def_property_readonly("row_prototype", [](storm::synthesis::DecPomdp& decpomdp) {return decpomdp.row_prototype;})
        // .def_property_readonly("state_prototype", [](storm::synthesis::DecPomdp& decpomdp) {return decpomdp.state_prototype;})
        // .def_property_readonly("state_memory", [](storm::synthesis::DecPomdp& decpomdp) {return decpomdp.state_memory;})
        // .def_property_readonly("row_groups", [](storm::synthesis::DecPomdp& decpomdp) {return decpomdp.row_groups;})
        // .def_property_readonly("num_states_mdp", [](storm::synthesis::DecPomdp& decpomdp) {return decpomdp.num_states_mdp;})
        // .def_property_readonly("prototype_row_index", [](storm::synthesis::DecPomdp& decpomdp) {return decpomdp.prototype_row_index;})

//unused:
        // .def("num_rows", &storm::synthesis::DecPomdp::num_rows)
        // .def_property_readonly("num_states", [](storm::synthesis::DecPomdp& decpomdp) {return decpomdp.num_states();}, "number of states")
        
        // .def_property_readonly("row_reward", [](storm::synthesis::DecPomdp& decpomdp) {return decpomdp.row_reward;}, "for each row group, a list of row rewards")
        // .def_property_readonly("row_joint_action", [](storm::synthesis::DecPomdp& decpomdp) {return decpomdp.row_joint_action;}, "row_joint_action")
        // .def_property_readonly("agent_observation_labels", [](storm::synthesis::DecPomdp& decpomdp) {return decpomdp.agent_observation_labels;})
        ;


    m.def("parse_decpomdp", &synthesis::parseDecPomdp,  py::arg("filename"));

}
