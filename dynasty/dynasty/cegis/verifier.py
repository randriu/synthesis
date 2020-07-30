import logging
import time

import stormpy
import stormpy.utility

import dynasty.cegis.stats


logger = logging.getLogger(__name__)

class Verifier:
    def __init__(self):
        self.nr_checks = 0
        self.sketch = None
        self._dont_care_set = None
        self.properties = None
        self.qualitative_properties = None
        self.stats = dynasty.cegis.stats.Stats()
        self.cex_options = stormpy.SMTCounterExampleGeneratorOptions()
        self._optimality = None
        self._opt_value = None
        self.sketch = None


    def initialise(self, sketch, properties, qualitative_properties, dont_care_set, add_cuts=True):
        self.properties = properties
        self.sketch = sketch
        self.qualitative_properties  = qualitative_properties
        self._dont_care_set = dont_care_set
        self._set_cex_options(add_cuts)

    def initialise_stats(self, holes):
        self.stats.initialize_properties_and_holes(self.properties, holes)

    def initialise_optimality(self, optimality_setting):
        self._optimality = optimality_setting

    @property
    def optimal_value(self):
        return self._opt_value

    def run(self, instance, all_conflicts, naive_deadlocks=True):
        """
        Run the verifier.
        
        :param instance: 
        :param all_conflicts: 
        :param naive_deadlocks: 
        :return: 
        """
        return self._naive_check(instance, all_conflicts, naive_deadlocks)

    def _naive_check(self, instance, all_conflicts, naive_deadlocks=True, check_conflicts=False):
        """
        Check the concrete program for the given assignments.

        :param assignments: 
        :return: 
        """
        self.nr_checks += 1
        logger.debug("Build DTMC....")
        model = self._build_model(instance)
        logger.debug("...done building DTMC (with {} states and {} transitions)".format(model.nr_states,
                                                                                        model.nr_transitions))
        # Analyse which properties hold.
        qualitative_conflicts_properties, quantitative_conflict_properties = self._naive_check_model(model,
                                                                                                     all_conflicts)
        if qualitative_conflicts_properties:
            # conflicts.add(tuple([c.name for c in self.sketch.used_constants()]))
            # TODO handling for qualitative conflicts can certainly be improved.
            return qualitative_conflicts_properties, set()

        # Construct the environment for the counterexample generator.
        env = stormpy.core.Environment()
        env.solver_environment.set_linear_equation_solver_type(stormpy.EquationSolverType.native)
        # env.solver_environment.set_force_sound()

        # We can sometimes merge properties into a single meta-property for conflict analysis.
        merged_conflict_props = self._merge_conflict_properties(quantitative_conflict_properties)

        conflicts = set()
        assert self._dont_care_set is not None
        for p, additional in merged_conflict_props.items():
            logger.debug("Conflict analysis for {} and {}".format(p.raw_formula, ",".join(
                [str(a[0]) + " " + str(a[1]) for a in additional])))
            conflict_analysis_timer = time.time()

            # Create input for the counterexample generation.
            symbolic_model = stormpy.SymbolicModelDescription(instance)
            cex_input = stormpy.core.SMTCounterExampleGenerator.precompute(env, symbolic_model, model, p.raw_formula)
            for a in additional:
                cex_input.add_reward_and_threshold(a[0], a[1])

            # Prepare execution of the counterexample generation
            cex_stats = stormpy.core.SMTCounterExampleGeneratorStats()
            # Generate the counterexample
            result = stormpy.core.SMTCounterExampleGenerator.build(env, cex_stats, symbolic_model, model, cex_input,
                                                                   self._dont_care_set, self.cex_options)
            # And put the counterexamples into a set.
            result = set(result)
            conflict_analysis_time = time.time() - conflict_analysis_timer

            logger.debug("Found {} counterexamples.".format(len(result)))

            # Translate the counterexamples into conflicts.
            analysed_conflicts = [self._conflict_analysis(conflict) for conflict in result]
            analysed_conflicts.sort()
            if check_conflicts:
                # Checking conflicts if for debugging purposes only.
                # We double check whether the counterexamples violate the properties.
                for cex in result:
                    test_model = self._build_model(instance.restrict_edges(cex), with_origins=False,
                                                   register_stats=False)
                    qualitative_conflicts_properties, quantitative_conflict_properties = self._naive_check_model(
                        test_model, all_conflicts)
                    assert len(quantitative_conflict_properties) > 0

            # And store details for benchmarking etc.
            self.stats.report_conflict_analysis_stats(cex_stats)
            self.stats.report_conflict_details(p, conflict_analysis_time, analysed_conflicts)

            # And update the list of found conflicts
            for ac in analysed_conflicts:
                conflicts.update([ac])

        return qualitative_conflicts_properties, conflicts

    def _build_model(self, instance, with_origins=True, register_stats=True):
        """
        Build a (sparse) model from the given prism program instance

        :param instance: A highlevel description of the model
        :param with_origins: If the model is to be analysed with highlevel counterex, then this flag should be true.
        :param register_stats: Should the stats for this model be registered. 
            Put to False, when the model is just build for debugging purposes.
        :return: The Markov chain.
        """
        start_mb = time.time()
        assert len(self.properties) + len(self.qualitative_properties) > 0 or self._optimality
        if with_origins:
            raw_formulae = [p.property.raw_formula for p in self.properties]
            if self._optimality:
                raw_formulae.append(self._optimality.criterion.raw_formula)
            options = stormpy.BuilderOptions(raw_formulae)
            options.set_build_with_choice_origins(True)
            options.set_add_overlapping_guards_label()
            model = stormpy.build_sparse_model_with_options(instance, options)
        else:
            model = stormpy.build_model(instance, [p.property for p in self.properties])

        self._print_overlapping_guards(model)

        model.reduce_to_state_based_rewards()
        building_time = time.time() - start_mb
        if register_stats:
            self.stats.report_model_building(building_time, model.nr_states)
        logger.debug("Build model with {} states in {} seconds".format(model.nr_states, building_time))
        assert len(model.initial_states) == 1
        #logger.debug(instance)
        return model

    def _naive_check_model(self, model, check_all, terminate_after_qualitative_violation = True):
        """
        Do the model checking of the properties

        :param model: the Markov chain
        :param check_all: Should we abort as soon as we have found a conflicting property?
        :param terminate_after_qualitative_violation: Should we abort after a qualitative conflict?
        :return: The set of qualitative conflict properties and the set of quantiative conflict properties
        """
        logger.info("Start Model Checking....")
        start_mc = time.time()
        violated = []
        qualitative_violation = False
        # for p in self.qualitative_properties:
        #     self.stats.qualitative_model_checking_calls += 1
        #     if not stormpy.model_checking(model, p).at(model.initial_states[0]):
        #         violated.append(p)
        #         qualitative_violation = True
        #         if not check_all or terminate_after_qualitative_violation:
        #             break
        logger.debug("Qualitative violations: {}".format(";".join([str(p.raw_formula) for p in violated])))
        self.stats.qualitative_model_checking_time += time.time() - start_mc
        if terminate_after_qualitative_violation and len(violated) > 0:
            return qualitative_violation, violated
        for p in self.properties:

            logger.debug("Consider..: {}".format(p.property))
            # First, we check some prerequisite properties, in case they exist.
            if p.prerequisite_property:
                logger.debug("Prerequisite checking..: {}".format(p.prerequisite_property))
                start_mc = time.time()
                mc_result = stormpy.model_checking(model, p.prerequisite_property).at(model.initial_states[0])
                logger.debug("MC result for prerequisite: {}".format(mc_result))
                logger.debug("model states: {}, transitions: {}".format(model.nr_states, model.nr_transitions))
                self.stats.report_model_checking(p.prerequisite_property, time.time() - start_mc, not mc_result)
                if not mc_result:
                    violated.append(p.prerequisite_property)
                    if not check_all:
                        break
                    else:
                        continue
            else:
                logger.debug("No prerequisite found!")

            start_mc = time.time()
            mc_result = stormpy.model_checking(model, p.property).at(model.initial_states[0])
            logger.debug("MC Result: {}".format(mc_result))
            logger.debug("model states: {}, transitions: {}".format(model.nr_states, model.nr_transitions))
            self.stats.report_model_checking(p.property, time.time() - start_mc, not mc_result)
            if not mc_result:
                violated.append(p.property)
                if not check_all:
                    break
        if self._optimality and len(violated) == 0:
            mc_result = stormpy.model_checking(model, self._optimality.criterion).at(model.initial_states[0])
            if self._optimality.is_improvement(mc_result, self._opt_value):
                logger.debug("Optimal value improved to {}.".format(mc_result))
                self._opt_value = mc_result
            else:
                logger.debug("Optimal value ({}) not improved, conflict analysis!".format(self._opt_value))
                violated.append(self._optimality.get_violation_property(self._opt_value, lambda x: self.sketch.expression_manager.create_rational(stormpy.Rational(x))))
        logger.info("Stop Model Checking")
        logger.debug(violated)
        return qualitative_violation, violated

    def is_jani(self):
        return type(self.sketch) == stormpy.storage.JaniModel


    def _set_cex_options(self, add_cuts):
        self.cex_options.maximum_counterexamples = 10000
        self.cex_options.continue_after_first_counterexample = 1 # was 1.
        self.cex_options.maximum_iterations_after_counterexample = 20
        self.cex_options.use_dynamic_constraints = True
        self.cex_options.add_backward_implication_cuts = True if int(add_cuts) > 0 else False
        self.cex_options.encode_reachability = False
        self.cex_options.check_threshold_feasible = False
        self.cex_options.silent = True



    def _conflict_analysis(self, result):
        applied_cex = self._restrict_sketch(result)
        conflict = tuple(self._used_constants(applied_cex))
        logger.debug("Conflict of size {}".format(len(conflict)))
        return conflict

    def _merge_conflict_properties(self, conflict_props):
        merged_conflict_props = dict()
        eliminated = set()
        for i, p in enumerate(conflict_props):
            if p in eliminated:
                continue
            merged_conflict_props[p] = list()
            for q in conflict_props[i + 1:]:
                if q in eliminated:
                    continue
                if str(p.raw_formula.subformula) == str(q.raw_formula.subformula):
                    assert q.raw_formula.has_reward_name()
                    eliminated.add(q)
                    merged_conflict_props[p].append((q.raw_formula.reward_name, q.raw_formula.threshold))
        return merged_conflict_props

    def _used_constants(self, model):
        if type(model) == stormpy.storage.JaniModel:
            vars = set()
            for automaton in model.automata:
                automaton_index = model.get_automaton_index(automaton.name)
                for edge_index, e in enumerate(automaton.edges):
                    vars.update(e.guard.get_variables())
                    for d in e.destinations:
                        for assignment in d.assignments:
                            vars.update(assignment.expression.get_variables())
                        vars.update(d.probability.get_variables())

            var_names = set([var.name for var in vars])
            constants = set()
            for c in model.constants:
                if c.name in var_names:
                    constants.add(c.name)
            return constants
        else:
            return [c.name for c in model.used_constants()]

    def _restrict_sketch(self, to):
        if self.is_jani():
            return self.sketch.restrict_edges(to)#.simplify()
        else:
            return self.sketch.restrict_commands(to).simplify()

    def _print_overlapping_guards(self, model):
        has_overlap_guards = model.labeling.get_states("overlap_guards")
        if has_overlap_guards.number_of_set_bits() == 0:
            return

        raise ValueError("Model has overlapping guards. This is not allowed")

        assert model.has_choice_origins()
        choice_origins = model.choice_origins
        conflicting_sets = []
        for state in model.states:
            if has_overlap_guards[state.id]:
                for action in state.actions:
                    conflicting_sets.append(choice_origins.get_edge_index_set(state.id + action.id))

        for cs in conflicting_sets:
            print(choice_origins.model.restrict_edges(cs))


