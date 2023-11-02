import stormpy.synthesis

import paynt.quotient.holes
import paynt.quotient.models
import paynt.synthesizer.synthesizer

import logging
logger = logging.getLogger(__name__)


class GameResult:
    def __init__(self):
        self.sat = None
        self.scheduler_choices = None
        self.hole_selection = None

    @property
    def scheduler_consistent(self):
        return all([len(options)<=1 for options in self.hole_selection])

    def __str__(self):
        return str(self.sat)



class SynthesizerMetaPolicy(paynt.synthesizer.synthesizer.Synthesizer):

    @property
    def method_name(self):
        return "meta-policy AR"

    
    def verify_family(self, family, game_solver, prop):
        self.quotient.build(family)

        self.stat.iteration_mdp(family.mdp.states)

        # solve primary-secondary direction via a game
        print("solving...")
        game_solver.solve(family.selected_actions_bv, prop.maximizing, prop.minimizing)
        print("solved")
        game_result = GameResult()
        game_result.sat = prop.satisfies_threshold(game_solver.solution_value)
        game_result.scheduler_choices = game_solver.solution_choices
        print(game_solver.solution_value)
        print(game_solver.solution_state_values)
        print(game_solver.solution_choices)

        if True:
            model,state_map,choice_map = self.quotient.restrict_mdp(self.quotient.quotient_mdp, game_result.scheduler_choices)
            dtmc = paynt.quotient.models.DTMC(model, self.quotient, state_map, choice_map)
            dtmc_result = dtmc.model_check_property(prop)
            print("double-checking game value: ", game_solver.solution_value, dtmc_result)
            if abs(dtmc_result.value-game_solver.solution_value) > 0.1:
                exit()
        
        if game_result.sat:
            return game_result

        print(self.quotient.action_labels)
        print(self.quotient.state_to_actions)
        # for choice in range(self.quotient.quotient_mdp.nr_choices):
        #     choice_options = self.quotient.coloring.action_to_hole_options[choice]
        #     print(choice_options)

        # map scheduler choices to hole options and check consistency
        hole_selection = [set() for hole_index in self.quotient.design_space.hole_indices]
        for choice in game_result.scheduler_choices:
            choice_options = self.quotient.coloring.action_to_hole_options[choice]
            print(choice_options)
            print(self.quotient.quotient_mdp.transition_matrix.get_row(choice))
            for hole_index,option in choice_options.items():
                hole_selection[hole_index].add(option)
        game_result.hole_selection = [list(options) for options in hole_selection]
        return game_result



    def split(self, family, prop, scheduler_choices, state_values, hole_selection):
        # compute scores for inconsistent holes
        mdp = self.quotient.quotient_mdp
        choice_values = self.quotient.choice_values(mdp, prop, state_values)
        inconsistent_assignments = {hole_index:options for hole_index,options in enumerate(hole_selection) if len(options) > 1 }
        expected_visits = self.quotient.expected_visits(mdp, prop, scheduler_choices)
        quotient_mdp_wrapped = self.quotient.design_space.mdp
        scores = self.quotient.estimate_scheduler_difference(quotient_mdp_wrapped, inconsistent_assignments, choice_values, expected_visits)
        
        # split the hole
        splitters = self.quotient.holes_with_max_score(scores)
        splitter = splitters[0]
        used_options = hole_selection[splitter]
        if len(used_options) > 1:
            core_suboptions = [[option] for option in used_options]
            other_suboptions = [option for option in family[splitter].options if option not in used_options]
        else:
            assert len(family[splitter].options) > 1
            options = family.options
            half = len(options) // 2
            core_suboptions = [options[:half], options[half:]]
            other_suboptions = []

        if len(other_suboptions) == 0:
            suboptions = core_suboptions
        else:
            suboptions = [other_suboptions] + core_suboptions  # DFS solves core first
        
        # construct corresponding design subspaces
        subfamilies = []
        family.splitter = splitter
        new_design_space = family.copy()
        for suboption in suboptions:
            subholes = new_design_space.subholes(splitter, suboption)
            subfamily = paynt.quotient.holes.DesignSpace(subholes)
            subfamily.assume_hole_options(splitter, suboption)
            subfamilies.append(subfamily)

        return subfamilies
        


    def synthesize_metapolicy(self, family):
        metapolicy = []

        prop = self.quotient.specification.constraints[0]
        game_solver = self.quotient.build_game_abstraction_solver(prop)

        families = [family]
        while families:
            family = families.pop(-1)
            print("trying family of size ", family.size)
            result = self.verify_family(family,game_solver,prop)
            if result.sat:
                logger.debug("found policy for family of size {}".format(family.size))
                metapolicy += [(family,result.scheduler_choices)]
                self.explore(family)
                continue

            # unsat
            if result.scheduler_consistent:
                unsatisfiable_family = self.quotient.design_space.assume_options_copy(result.hole_selection)
                logger.info("satisfying scheduler cannot be obtained for the following family {}".format(unsatisfiable_family))
                self.explore(family)
                if unsatisfiable_family.size > family.size:
                    logger.info("can reject a larger family than the one that is being explored???")
                continue

            # refine
            subfamilies = self.split(
                family, prop, game_solver.solution_choices, game_solver.solution_state_values, result.hole_selection
            )
            print([f.size for f in subfamilies])
            # exit()
            families = families + subfamilies

        return metapolicy

    

    def synthesize(self, family = None):
        if family is None:
            family = self.quotient.design_space
        self.stat.start()
        logger.info("synthesis initiated, design space: {}".format(family.size))
        metapolicy = self.synthesize_metapolicy(family)
        self.stat.finished(metapolicy)
        return metapolicy

    
    def run(self):
        ''' Synthesize meta-policy that satisfies all family members. '''
        self.quotient.design_space.constraint_indices = self.quotient.specification.all_constraint_indices()

        spec = self.quotient.specification
        assert not spec.has_optimality and spec.num_properties == 1 and not spec.constraints[0].reward, \
            "expecting a single reachability probability constraint"
        
        metapolicy = self.synthesize()
        self.stat.print()
    