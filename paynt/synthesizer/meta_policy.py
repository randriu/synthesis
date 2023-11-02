import stormpy.synthesis

import paynt.quotient.models
import paynt.synthesizer.synthesizer

import logging
logger = logging.getLogger(__name__)


class GameResult:
    def __init__(self):
        self.sat = None
        self.scheduler_choices = None
        self.scheduler_selection = None
        self.scheduler_consistent = None

    def __str__(self):
        return str(self.sat)



class SynthesizerMetaPolicy(paynt.synthesizer.synthesizer.Synthesizer):

    @property
    def method_name(self):
        return "meta-policy AR"

    
    def verify_family(self, family, game_solver, prop):
        self.quotient.build(family)

        # solve primary-secondary direction via a game
        game_solver.solve(family.selected_actions_bv, prop.maximizing, prop.minimizing)
        game_result = GameResult()
        game_result.sat = prop.satisfies_threshold(game_solver.solution_value)
        game_result.scheduler_choices = game_solver.solution_choices

        print("game value: {} ({})".format(game_solver.solution_value,game_result.sat))

        model,state_map,choice_map = self.quotient.restrict_mdp(self.quotient.quotient_mdp, game_result.scheduler_choices)
        assert model.nr_states == model.nr_choices
        dtmc = paynt.quotient.models.DTMC(model, self.quotient, state_map, choice_map)
        dtmc_result = dtmc.model_check_property(prop)
        print("double-checking game value: ", dtmc_result)
        
        if game_result.sat:
            return game_result

        # map reachable choices to hole options and check consistency
        selection = [set() for hole_index in self.quotient.design_space.hole_indices]
        for choice in game_result.scheduler_choices:
            choice_options = self.quotient.coloring.action_to_hole_options[choice]
            for hole_index,option in choice_options.items():
                selection[hole_index].add(option)
        selection = [list(options) for options in selection]
        game_result.scheduler_selection = selection
        game_result.scheduler_consistent = all([len(options)<=1 for options in selection])

        return game_result
        


    def synthesize_metapolicy(self, family):
        metapolicy = []

        prop = self.quotient.specification.constraints[0]
        game_solver = self.quotient.build_game_abstraction_solver(prop)

        families = [family]
        while families:
            family = families.pop(-1)
            result = self.verify_family(family,game_solver,prop)
            if result.sat:
                logger.debug("found policy for family of size {}".format(family.size))
                # TODO assign policy to family
                metapolicy += [(family,result.scheduler_choices)]
                self.explore(family)
                continue

            # unsat
            if result.scheduler_consistent:
                # unsatisfiable_family = result.scheduler_selection
                unsatisfiable_family = self.quotient.design_space.assume_options_copy(result.scheduler_selection)
                logger.info("satisfying scheduler cannot be obtained for the following family {}".format(unsatisfiable_family))
                self.explore(family)
                if unsatisfiable_family.size > family.size:
                    logger.info("can reject a larger family than the one that is being explored???")
                continue

            # refine
            raise NotImplementedError("family splitting is not yet implemented for game abstractions")
            subfamilies = self.quotient.split(family, Synthesizer.incomplete_search)
            families = families + subfamilies

        return metapolicy

    

    def synthesize(self, family = None):
        self.stat.start()
        if not self.stat.whole_synthesis_timer.running:
            self.stat.whole_synthesis_timer.start()

        if family is None:
            family = self.quotient.design_space
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

        metapolicy = self.synthesize(self.quotient.design_space)

        if metapolicy is not None:
            logger.info("Printing synthesized meta-policy below:")
            logger.info("{}".format(metapolicy))
        
        self.print_stats()
    