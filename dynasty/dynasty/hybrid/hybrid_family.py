import logging
import z3

import stormpy

from ..family_checkers.familychecker import HoleOptions
from ..model_handling.mdp_handling import MC_ACCURACY_THRESHOLD
from ..profiler import Profiler
from .helpers import check_dtmc
from .family import Family

logger = logging.getLogger(__name__)


class FamilyHybrid(Family):
    """ Family adopted for CEGAR-CEGIS analysis. """

    # TODO: more efficient state-hole mapping?

    _choice_to_hole_indices = {}

    def __init__(self, *args):
        super().__init__(*args)

        self._state_to_hole_indices = None  # evaluated on demand

        # dtmc corresponding to the constructed assignment
        self.dtmc = None
        self.dtmc_state_map = None
        self.param_dtmc = None
        self.instantiator = None
        self.points = None
        self.violated_formulae_indices = None

    def initialize(*args):
        Family.initialize(*args)

        # map edges of a quotient container to hole indices
        jani = Family._quotient_container.jani_program
        _edge_to_hole_indices = dict()
        for aut_index, aut in enumerate(jani.automata):
            for edge_index, edge in enumerate(aut.edges):
                if edge.color == 0:
                    continue
                index = jani.encode_automaton_and_edge_index(aut_index, edge_index)
                assignment = Family._quotient_container.edge_coloring.get_hole_assignment(edge.color)
                hole_indices = [index for index, value in enumerate(assignment) if value is not None]
                _edge_to_hole_indices[index] = hole_indices

        # map actions of a quotient MDP to hole indices
        FamilyHybrid._choice_to_hole_indices = []
        choice_origins = Family._quotient_mdp.choice_origins
        matrix = Family._quotient_mdp.transition_matrix
        for state in range(Family._quotient_mdp.nr_states):
            for choice_index in range(matrix.get_row_group_start(state), matrix.get_row_group_end(state)):
                choice_hole_indices = set()
                for index in choice_origins.get_edge_index_set(choice_index):
                    hole_indices = _edge_to_hole_indices.get(index, set())
                    choice_hole_indices.update(hole_indices)
                FamilyHybrid._choice_to_hole_indices.append(choice_hole_indices)

    def split(self):
        assert self.split_ready
        return [FamilyHybrid(self, sub_option) for sub_option in self.suboptions]

    @property
    def state_to_hole_indices(self):
        """
        Identify holes relevant to the states of the MDP and store only significant ones.
        """
        # if someone (i.e., CEGIS) asks for state indices, the model should already be analyzed
        assert self.constructed and self.analyzed

        # lazy evaluation
        if self._state_to_hole_indices is not None:
            return self._state_to_hole_indices

        Profiler.start("is - MDP holes (edges)")
        # logger.debug("Constructing state-holes mapping via edge-holes mapping.")

        self._state_to_hole_indices = []
        matrix = self.mdp.transition_matrix
        for state in range(self.mdp.nr_states):
            state_hole_indices = set()
            for choice_index in range(matrix.get_row_group_start(state), matrix.get_row_group_end(state)):
                state_hole_indices.update(FamilyHybrid._choice_to_hole_indices[self.choice_map[choice_index]])
            state_hole_indices = set(
                [index for index in state_hole_indices if len(self.options[Family.hole_list[index]]) > 1]
            )
            self._state_to_hole_indices.append(state_hole_indices)

        Profiler.stop()
        return self._state_to_hole_indices

    @property
    def state_to_hole_indices_choices(self):
        """
        Identify holes relevant to the states of the MDP and store only significant ones.
        """
        # if someone (i.e., CEGIS) asks for state indices, the model should already be analyzed
        assert self.constructed and self.analyzed

        # lazy evaluation
        if self._state_to_hole_indices is not None:
            return self._state_to_hole_indices

        Profiler.start("is - MDP holes (choices)")
        logger.debug("Constructing state-holes mapping via choice-holes mapping.")

        self._state_to_hole_indices = []
        matrix = self.mdp.transition_matrix
        for state in range(self.mdp.nr_states):
            state_hole_indices = set()
            for choice_index in range(matrix.get_row_group_start(state), matrix.get_row_group_end(state)):
                quotient_choice_index = self.choice_map[choice_index]
                choice_hole_indices = FamilyHybrid._choice_to_hole_indices[quotient_choice_index]
                state_hole_indices.update(choice_hole_indices)
            state_hole_indices = set(
                [index for index in state_hole_indices if len(self.options[Family.hole_list[index]]) > 1])
            self._state_to_hole_indices.append(state_hole_indices)
        Profiler.stop()
        return self._state_to_hole_indices

    def pick_member(self):
        # pick hole assignment

        self.pick_assignment()
        if self.member_assignment is not None:

            # collect edges relevant for this assignment
            indexed_assignment = Family._hole_options.index_map(self.member_assignment, self._parameters)
            subcolors = Family._quotient_container.edge_coloring.subcolors(indexed_assignment)
            collected_edge_indices = stormpy.FlatSet(
                Family._quotient_container.color_to_edge_indices.get(0, stormpy.FlatSet())
            )
            for c in subcolors:
                collected_edge_indices.insert_set(Family._quotient_container.color_to_edge_indices.get(c))

            # construct the DTMC by exploring the quotient MDP for this subfamily
            if isinstance(self.mdp, stormpy.storage.SparseParametricMdp):
                self.dtmc, self.dtmc_state_map = stormpy.synthesis.dtmc_from_param_mdp(self.mdp, collected_edge_indices)
            else:
                self.dtmc, self.dtmc_state_map = stormpy.synthesis.dtmc_from_mdp(self.mdp, collected_edge_indices)
            Family._dtmc_stats = (Family._dtmc_stats[0] + self.dtmc.nr_states, Family._dtmc_stats[1] + 1)
            logger.debug(f"Constructed DTMC of size {self.dtmc.nr_states}.")

            self.points = {}
            if isinstance(self.dtmc, stormpy.storage.SparseParametricDtmc):
                for p in self.dtmc.collect_probability_parameters():
                    assert len(self.member_assignment[p.name[:-2]]) == 1
                    self.points[p] = stormpy.RationalRF(self.member_assignment[p.name[:-2]][0].evaluate_as_double())
                self.instantiator = stormpy.pars.ModelInstantiator(self.dtmc)
                self.param_dtmc = self.dtmc
                self.dtmc = self.instantiator.instantiate(self.points)

            # assert absence of deadlocks or overlapping guards
            assert self.dtmc.labeling.get_states("deadlock").number_of_set_bits() == 0
            assert self.dtmc.labeling.get_states("overlap_guards").number_of_set_bits() == 0
            assert len(self.dtmc.initial_states) == 1  # to avoid ambiguity

        # success
        return self.member_assignment

    def construct_and_check_mdp(self, prob_params, hole_options, epsilons, construct=False):
        for param in prob_params:
            param_value = self.member_assignment[param.name[:-2]][0].evaluate_as_double()
            hole_options[param.name[:-2]] = [
                self._sketch.expression_manager.create_rational(stormpy.Rational(param_value - epsilons[param.name])),
                self._sketch.expression_manager.create_rational(stormpy.Rational(param_value + epsilons[param.name])),
            ]
        self.options = hole_options
        if construct:
            indexed_options = Family._hole_options.index_map(self.options, self._parameters)
            Family._quotient_container.consider_subset(self.options, indexed_options)

        absolute_diff = 0.0
        unsat = False
        for formula_index in self.violated_formulae_indices:
            Family.mdp_checks_inc()
            unsat, _ = self.model_check_formula(formula_index)
            if unsat:
                absolute_diff = self._quotient_container.latest_result.absolute_max - \
                    self._quotient_container.latest_result.absolute_min
                break
        return unsat, absolute_diff

    def get_parameter_bounds(self, hole_options):
        eps = 1.0e-9
        last_ref_eps = 0
        # TODO: Is right collecting params from param_dtmc or mdp?
        prob_params = self.mdp.collect_probability_parameters()
        epsilons = {param.name: eps for param in prob_params}
        saved_orig_options = self.options
        exists_sat, absolute_diff = self.construct_and_check_mdp(prob_params, hole_options, epsilons, construct=True)
        while exists_sat and absolute_diff <= MC_ACCURACY_THRESHOLD:
            epsilons = {k: v / 2 for idx, (k, v) in enumerate(epsilons.items()) if idx == last_ref_eps}
            last_ref_eps = last_ref_eps + 1 if last_ref_eps + 1 < len(epsilons.keys()) else 0
            exists_sat = self.construct_and_check_mdp(prob_params, hole_options, epsilons, construct=True)
        lower_bounds, upper_bounds = {}, {}
        for param in prob_params:
            assert len(self.options[param.name[:-2]]) == 2
            lower_bounds[param.name[:-2]] = self.options[param.name[:-2]][0].evaluate_as_double()
            upper_bounds[param.name[:-2]] = self.options[param.name[:-2]][1].evaluate_as_double()
        self.options = saved_orig_options
        return lower_bounds, upper_bounds

    def construct_parametric_clauses(self, cex_clauses, lower_bounds, upper_bounds):
        for var, hole in Family._solver_meta_vars.items():
            if hole in self.mdp.collect_probability_parameters():
                cex_clauses[hole] = z3.And(var >= lower_bounds[hole], var <= upper_bounds[hole])
        return cex_clauses

    def exclude_member(self, conflicts):
        """
        Exclude the subfamily induced by the selected assignment and a set of conflicts.
        """
        assert self.member_assignment is not None

        for conflict in conflicts:
            # if set(conflict).intersection(set(Family._parameters)):
                # print(f"CONFLICT: {conflict}")
                # exit(1)
            cex_clauses = dict()
            hole_options = HoleOptions()
            for var, hole in Family._solver_meta_vars.items():
                if hole in Family._parameters:
                    hole_options[hole] = [None]
                elif Family._hole_indices[hole] in conflict:
                    assert len(self.member_assignment[hole]) == 1
                    hole_options[hole] = self.member_assignment[hole]
                    option_index = Family._hole_option_indices[hole][self.member_assignment[hole][0]]
                    cex_clauses[hole] = (var == option_index)
                else:
                    hole_options[hole] = self.options[hole]
                    all_options = [var == Family._hole_option_indices[hole][option] for option in self.options[hole]]
                    cex_clauses[hole] = z3.Or(all_options)
            if Family._parameters:
                lower_bounds, upper_bounds = self.get_parameter_bounds(hole_options)
                cex_clauses = self.construct_parametric_clauses(cex_clauses, lower_bounds, upper_bounds)
            counterexample_encoding = z3.Not(z3.And(list(cex_clauses.values())))
            Family._solver.add(counterexample_encoding)
        self.member_assignment = None

    def analyze_member(self, formula_index):
        assert self.dtmc is not None
        sat, result = check_dtmc(self.dtmc, Family._formulae[formula_index], quantitative=True)
        return sat, result

    def print_member(self):
        print("> DTMC info:")
        dtmc = self.dtmc
        tm = dtmc.transition_matrix
        for state in range(dtmc.nr_states):
            row = tm.get_row(state)
            print("> ", str(row))

    def conflict_covers_interesting(self, conflict):
        generalized_options = self.options.copy()
        for hole in conflict:
            generalized_options[hole] = self.member_assignment[hole]
        return Family.is_in_family(Family.interesting_assignment, generalized_options)
