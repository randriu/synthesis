#include "../synthesis.h"

#include "DecPomdp.h"

void bindings_decpomdp(py::module& m) {

    py::class_<synthesis::DecPomdp>(m, "DecPomdp", "dec-POMDP")
        // .def(py::init<std::string const&>(), "constructor.", py::arg("filename"));
        .def("construct_mdp", &synthesis::DecPomdp::constructMdp)
        .def("construct_pomdp", &synthesis::DecPomdp::constructPomdp)
        .def_property_readonly("num_agents", [](synthesis::DecPomdp& decpomdp) {return decpomdp.num_agents;})
        .def_property_readonly("joint_observations", [](synthesis::DecPomdp& decpomdp) {return decpomdp.joint_observations;})
        .def_property_readonly("agent_observation_labels", [](synthesis::DecPomdp& decpomdp) {return decpomdp.agent_observation_labels;})
        
        .def_property_readonly("reward_model_name", [](synthesis::DecPomdp& decpomdp) {return decpomdp.reward_model_name;})
        .def_property_readonly("reward_minimizing", [](synthesis::DecPomdp& decpomdp) {return decpomdp.reward_minimizing;})
        .def_property_readonly("discount_factor", [](synthesis::DecPomdp& decpomdp) {return decpomdp.discount_factor;})
        
        .def("apply_discount_factor_transformation", &synthesis::DecPomdp::applyDiscountFactorTransformation)
        .def_property_readonly("discount_sink_label", [](synthesis::DecPomdp& decpomdp) {return decpomdp.discount_sink_label;})
        ;

    m.def("parse_decpomdp", &synthesis::parseDecPomdp,  py::arg("filename"));

}
