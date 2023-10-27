import paynt.synthesizer.synthesizer

import stormpy.synthesis

import logging
logger = logging.getLogger(__name__)


class GameResult:
    def __init__(self):
        self.sat = None
        self.player1_choices = None
        self.player2_choices = None

    def __str__(self):
        return str(self.sat)


class MetaSchedulerFamilyAnalysisResult:

    def __init__(self):
        self.primary_secondary_result = None
        self.primary_primary_result = None
        self.sat = None
        self.should_refine = None
        
    def evaluate(self):
        self.sat = None
        self.should_refine = None
        if self.primary_secondary_result.sat:
            self.sat = True
            self.should_refine = False
            return
        if self.primary_primary_result is None:
            return
        self.sat = False
        self.should_refine = self.primary_primary_result.sat

    def __str__(self):
        return str(self.primary_secondary_result) + " - " + str(self.primary_secondary_result)


class SynthesizerMetaScheduler(paynt.synthesizer.synthesizer.Synthesizer):

    @property
    def method_name(self):
        return "Meta-scheduler AR"

    
    def verify_family(self, family, game_solver, prop):
        self.quotient.build(family)

        res = MetaSchedulerFamilyAnalysisResult()


        # solve primary-secondary direction via a game
        game_solver.solve(family.selected_actions_bv, prop.maximizing, prop.minimizing)
        res.primary_secondary_result = GameResult()
        primary_secondary_value = game_solver.player1_state_values[0]
        res.primary_secondary_result.sat = prop.satisfies_threshold(primary_secondary_value)
        res.primary_secondary_result.player1_choices = game_solver.player1_choices
        res.primary_secondary_result.player2_choices = game_solver.player2_choices
        res.evaluate()
        if res.sat is not None:
            # decided
            return res

        # undecided, solve PP
        res.primary_primary_result = family.mdp.model_check_property(prop)
        res.evaluate()
        return res
        


    def synthesize_metascheduler(self, family):
        metascheduler = {}

        prop = self.quotient.specification.constraints[0]
        game_solver = self.quotient.build_game_abstraction_solver(prop)

        families = [family]
        while families:
            family = families.pop(-1)
            result = self.verify_family(family,game_solver,prop)
            if result.sat:
                logger.debug("found scheduler for family of size {}".format(family.size))
                metascheduler[family] = result.primary_secondary_result.player1_choices
            if not result.should_refine:
                self.explore(family)
                continue

            # refine
            raise NotImplementedError("family splitting is not yet implemented for game abstractions")
            subfamilies = self.quotient.split(family, Synthesizer.incomplete_search)
            families = families + subfamilies

        return metascheduler

    

    def synthesize(self, family = None):
        self.stat.start()
        if not self.stat.whole_synthesis_timer.running:
            self.stat.whole_synthesis_timer.start()

        if family is None:
            family = self.quotient.design_space
        logger.info("synthesis initiated, design space: {}".format(family.size))
        
        metascheduler = self.synthesize_metascheduler(family)

        self.stat.finished(metascheduler)
        return metascheduler

    
    def run(self):
        ''' Synthesize (meta-)scheduler that satisfies all family members. '''
        self.quotient.design_space.constraint_indices = self.quotient.specification.all_constraint_indices()

        spec = self.quotient.specification
        assert not spec.has_optimality and spec.num_properties == 1 and not spec.constraints[0].reward, \
            "expecting a single reachability probability constraint"

        metascheduler = self.synthesize(self.quotient.design_space)

        if metascheduler is not None:
            logger.info("Printing synthesized meta-scheduler below:")
            logger.info("{}".format(metascheduler))
        
        self.print_stats()
    