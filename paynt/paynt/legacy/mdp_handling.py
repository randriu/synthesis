import stormpy

import logging
import os
import math
import subprocess


logger = logging.getLogger(__name__)


def always_true(_, __):
    return True


class SymbolicMCResult:
    def __init__(self, absolute_min, absolute_max):
        self.absolute_min = absolute_min
        self.absolute_max = absolute_max


class ExplicitMCResult:
    def __init__(self, result, alt_result, maximising=True, absolute_min=None, absolute_max=None):
        self.result = result
        self.alt_result = alt_result
        self.maximising = maximising
        self.absolute_min = absolute_min
        self.absolute_max = absolute_max

    @property
    def scheduler(self):
        return self.result.scheduler

    @property
    def alt_scheduler(self):
        return self.alt_result.scheduler

    @property
    def lower_bound_result(self):
        return self.alt_result if self.maximising else self.result

    @property
    def upper_bound_result(self):
        return self.result if self.maximising else self.alt_result


class ModelHandling:
    """
    Takes an lifted MDP, which may be restricted and then checked.
    """

    def __init__(self):
        self._model = None  # Last mdp that has been built.
        self._formulae = None
        self._alt_formulae = None
        self._expression_manager = None
        self._submodel = None
        self._mapping_to_original = None

        self._color_0_actions = None

        self._restrict_time = 0
        self._mc_dtmc_calls = 0
        self._mc_mdp_calls = 0
        self._mc_mdp_executions = 0

    def reset(self):
        self._model = None
        self._submodel = None
        self._color_0_actions = None

    def display_model(self):
        """
        For debugging purposes
        
        :return: 
        """
        logger.debug("Display model")
        model = self._submodel
        dot_string = model.to_dot()
        # TODO make graphviz optional.
        import pygraphviz as pgv
        logger.debug("rendering...")
        graph = pgv.AGraph(dot_string)
        graph.layout(prog='neato')
        location = os.path.join("model.ps")
        graph.draw(location)
        subprocess.call(["open", location])

    @property
    def full_mdp(self):
        return self._model

    @property
    def mdp(self):
        return self._submodel

    @property
    def mapping_to_original(self):
        return self._mapping_to_original

    def has_reward_model(self, index=0):
        """
        Do we need a reward model for the formula at the given index 
        :param index: 
        :return: 
        """
        return self._formulae[index].is_reward_operator()

    def submodel_is_dtmc(self):
        """
        Is the model that we are handling a dtmc?
        :return: 
        """
        return self._submodel.nr_choices == self._submodel.nr_states

    def get_reward_model(self, index=0):
        logger.debug(f"Get reward model for formulae with index {index}")
        assert self._formulae[index].has_reward_name()
        reward_model_name = self._formulae[index].get_reward_name()
        logger.debug(f"Reward model name requires is {reward_model_name}")
        return self.mdp.reward_models[reward_model_name]

    def build_symbolic_model(self, jani_program, formulae, alt_formulae):
        if self._model:
            logger.warning("Rebuilding a model...")
        logger.info("Build model (with dd engine)...")

        self._formulae = formulae
        self._alt_formulae = alt_formulae
        self._expression_manager = jani_program.expression_manager
        jani_program.substitute_functions()
        result = stormpy.build_symbolic_model(jani_program, self._formulae)
        logger.info(
            f"done. Model has {result.nr_states} states, "
            f"{result.nr_choices} actions and {result.nr_transitions} transitions"
        )
        self._model = result
        self._submodel = result
        return self._model

    def build_model(self, jani_program, formulae, alt_formulae):
        if self._model:
            logger.warning("Rebuilding a model...")
        logger.info("Build model...")
        options = stormpy.BuilderOptions(formulae)
        options.set_build_with_choice_origins(True)
        options.set_build_state_valuations(True)  # +

        options.set_add_overlapping_guards_label()
        self._formulae = formulae
        self._alt_formulae = alt_formulae
        self._expression_manager = jani_program.expression_manager
        result = stormpy.build_sparse_model_with_options(jani_program, options)
        logger.info(
            f"done. Model has {result.nr_states} states, "
            f"{result.nr_choices} actions and {result.nr_transitions} transitions"
        )
        self._model = result
        self._submodel = self._model
        self._print_overlapping_guards(self._model)
        return self._model

    @staticmethod
    def _print_overlapping_guards(model):
        """
        This method is purely for model debugging purposes.
        
        :param model: 
        :return: 
        """
        has_overlap_guards = model.labeling.get_states("overlap_guards")
        if has_overlap_guards.number_of_set_bits() == 0:
            return

        print("OVERLAP!")
        print(has_overlap_guards)

        assert model.has_choice_origins()
        choice_origins = model.choice_origins
        conflicting_sets = []
        for state in model.states:
            if has_overlap_guards[state.id]:
                for action in state.actions:
                    conflicting_sets.append(choice_origins.get_edge_index_set(state.id + action.id))

        for cs in conflicting_sets:
            print(choice_origins.model.restrict_edges(cs))
            exit(1)

    def restrict(self, edge_indices, edge_0_indices):
        logger.debug("select mask for submodel construction...")
        all_states = stormpy.BitVector(self._model.nr_states, True)
        if self._color_0_actions is None:
            self._color_0_actions = stormpy.BitVector(self._model.nr_choices, False)
            for act_index in range(0, self._model.nr_choices):

                if self._model.choice_origins.get_edge_index_set(act_index).is_subset_of(edge_0_indices):
                    assert self._model.choice_origins.get_edge_index_set(act_index).is_subset_of(edge_indices)
                    self._color_0_actions.set(act_index)
        selected_actions = stormpy.BitVector(self._color_0_actions)

        for act_index in range(0, self._model.nr_choices):
            if selected_actions.get(act_index):
                continue
            # TODO many actions are always taken. We should preprocess these.

            if self._model.choice_origins.get_edge_index_set(act_index).is_subset_of(edge_indices):
                selected_actions.set(act_index)

        keep_unreachable_states = False
        logger.debug("Construct submodel...")
        subsystem_options = stormpy.SubsystemBuilderOptions()
        subsystem_options.build_action_mapping = True
        # subsystem_options.build_state_mapping = True #+
        submodel_construction = stormpy.construct_submodel(
            self._model, all_states, selected_actions, keep_unreachable_states, subsystem_options
        )
        assert (not keep_unreachable_states) or submodel_construction.kept_actions == selected_actions, \
            f"kept: {submodel_construction.kept_actions} vs selected: {selected_actions}"
        self._submodel = submodel_construction.model
        self._mapping_to_original = submodel_construction.new_to_old_action_mapping
        assert len(self._mapping_to_original) == self._submodel.nr_choices, \
            f"mapping contains {len(self._mapping_to_original)} actions, " \
            f"but model has {self._submodel.nr_choices} actions"
        assert self._submodel.has_choice_origins()
        return self._submodel

    def get_original_action(self, new_action):
        if self._mapping_to_original is None:
            return new_action
        return self._mapping_to_original[new_action]

    def compute_no_further_reward(self, index=0):
        assert self._expression_manager is not None
        assert self._formulae[index].is_reward_operator

        rew0_formula = self._formulae[index].clone()
        rew0_formula.set_optimality_type(stormpy.OptimizationDirection.Maximize)
        rew0_formula.set_bound(stormpy.ComparisonType.LEQ, self._expression_manager.create_integer(0))
        result = stormpy.model_checking(self._model, rew0_formula, only_initial_states=False, extract_scheduler=True)
        return result

    def mc_model_hybrid(self, index=0):
        _ = stormpy.check_model_hybrid(self._submodel, self._formulae[index])
        # TODO do something with this result

    def mc_model_symbolic(self, index=0):
        internal_res = stormpy.check_model_dd(self._submodel, self._formulae[index])
        internal_res.filter(stormpy.create_filter_initial_states_symbolic(self._submodel))
        return SymbolicMCResult(internal_res.min, internal_res.max)

    def mc_model(self, index=0, compute_action_values=False, check_dir_2=always_true):
        """

        :param index:
        :param compute_action_values:
        :param check_dir_2:
        :return:
        """
        assert len(self._formulae) > index
        assert not compute_action_values
        is_dtmc = False
        extract_scheduler = True

        if self._submodel.nr_choices == self._submodel.nr_states:
            is_dtmc = True
            self._mc_dtmc_calls += 1
            extract_scheduler = False
        else:
            self._mc_mdp_calls += 1
            self._mc_mdp_executions += 1

        # TODO set from the outside.
        env = stormpy.Environment()
        env.solver_environment.minmax_solver_environment.precision = stormpy.Rational(0.0000000001)  # +
        if is_dtmc:
            env.solver_environment.minmax_solver_environment.method = stormpy.MinMaxMethod.policy_iteration
        else:
            env.solver_environment.minmax_solver_environment.method = stormpy.MinMaxMethod.value_iteration

        # assert not self._formulae[index].has_bound

        logger.info(f"Start checking direction 1: {self._formulae[index]}")
        # TODO allow qualitative model checking with scheduler extraction.
        prime_result = stormpy.model_checking(
            self._submodel, self._formulae[index], only_initial_states=False,
            extract_scheduler=extract_scheduler, environment=env
        )

        if is_dtmc:
            maximise = True
            absolute_min = min([prime_result.at(x) for x in self._submodel.initial_states])
            absolute_max = max([prime_result.at(x) for x in self._submodel.initial_states])
            logger.info(f"Done DTMC Checking. Result for initial state is: {absolute_min} -- {absolute_max}")

            return ExplicitMCResult(
                prime_result, prime_result, maximise, absolute_min=absolute_min, absolute_max=absolute_max
            )

        absolute_min = -math.inf
        absolute_max = math.inf
        second_result = None

        if self._formulae[index].optimality_type == stormpy.OptimizationDirection.Maximize:
            maximise = True
            upper_result = prime_result
            absolute_max = max([upper_result.at(x) for x in self._submodel.initial_states])

        else:
            assert (self._formulae[index].optimality_type == stormpy.OptimizationDirection.Minimize)
            maximise = False
            lower_result = prime_result
            absolute_min = min([lower_result.at(x) for x in self._submodel.initial_states])

        if check_dir_2(absolute_min, absolute_max):
            self._mc_mdp_executions += 1
            logger.info(f"Start checking direction 2: {self._alt_formulae[index]}")
            second_result = stormpy.model_checking(
                self._submodel, self._alt_formulae[index], only_initial_states=False,
                extract_scheduler=extract_scheduler, environment=env
            )

            if maximise:
                lower_result = second_result
                absolute_min = min([lower_result.at(x) for x in self._submodel.initial_states])
            else:
                assert not maximise
                upper_result = second_result
                absolute_max = max([upper_result.at(x) for x in self._submodel.initial_states])

        logger.info(f"Done Checking. Result for initial state is: {absolute_min} -- {absolute_max}")

        return ExplicitMCResult(
            prime_result, second_result, maximise, absolute_min=absolute_min, absolute_max=absolute_max
        )
