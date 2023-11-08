import stormpy.synthesis

import paynt.quotient.holes
import paynt.quotient.models
import paynt.synthesizer.synthesizer

import logging
logger = logging.getLogger(__name__)


class MdpFamilyResult:
    def __init__(self):
        # if True, then all family is sat; if False, then all family is UNSAT; otherwise it is None
        self.sat = None
        # if not None, then contains a satisfying policy for all MDPs in the family
        self.satisfying_policy = None

        self.scheduler_choices = None
        self.hole_selection = None

    def __str__(self):
        return str(self.sat)



class SynthesizerMetaPolicy(paynt.synthesizer.synthesizer.Synthesizer):

    @property
    def method_name(self):
        return "meta-policy AR"


    def verify_family(self, family, game_solver, prop):
        self.quotient.build(family)

        self.stat.iteration_mdp(family.mdp.states)

        mdp_family_result = MdpFamilyResult()


        if family.size == 1:
            primary_primary_result = family.mdp.model_check_property(prop)
            logger.debug("primary-primary direction solved, value is {}".format(primary_primary_result.value))
            mdp_family_result.sat = primary_primary_result.sat
            if primary_primary_result.sat:
                # TODO extract policy
                mdp_family_result.satisfying_policy = "TODO"
            return mdp_family_result


        # construct and solve the game abstraction
        logger.debug("solving the game...")
        game_solver.solve(family.selected_actions_bv, prop.maximizing, prop.minimizing)
        logger.debug("game solved, value is {}".format(game_solver.solution_value))
        game_result_sat = prop.satisfies_threshold(game_solver.solution_value)
        
        if True:
            model,state_map,choice_map = self.quotient.restrict_mdp(self.quotient.quotient_mdp, game_solver.solution_reachable_choices)
            assert(model.nr_states == model.nr_choices)
            dtmc = paynt.quotient.models.DTMC(model, self.quotient, state_map, choice_map)
            dtmc_result = dtmc.model_check_property(prop)
            # print("double-checking game value: ", game_solver.solution_value, dtmc_result)
            if abs(dtmc_result.value-game_solver.solution_value) > 0.01:
                raise ValueError("game solution is {}, but DTMC model checker yielded {}".format(game_solver.solution_value,dtmc_result.value))

        if game_result_sat:
            logger.debug("verifying game policy...")
            mdp_family_result.sat = True
            # apply player 1 actions to the quotient
            policy = game_solver.solution_state_to_player1_action
            policy_result = self.verify_policy(family,prop,policy)
            if policy_result.sat:
                # this scheduler is good for all MDPs in the family
                mdp_family_result.satisfying_policy = policy
                return mdp_family_result
        else:
            logger.debug("solving primary-primary direction...")
            # solve primary-primary direction for the family
            primary_primary_result = family.mdp.model_check_property(prop)
            logger.debug("primary-primary direction solved, value is {}".format(primary_primary_result.value))
            if not primary_primary_result.sat:
                mdp_family_result.sat = False
                return mdp_family_result
        
        # undecided: prepare to split
        scheduler_choices = game_solver.solution_reachable_choices
        ev = self.quotient.expected_visits(self.quotient.quotient_mdp, prop, scheduler_choices)
        for choice in scheduler_choices:
            assert choice in family.selected_actions_bv

        # map scheduler choices to hole options and check consistency
        hole_selection = [set() for hole_index in self.quotient.design_space.hole_indices]
        for choice in scheduler_choices:
            choice_options = self.quotient.coloring.action_to_hole_options[choice]
            for hole_index,option in choice_options.items():
                hole_selection[hole_index].add(option)
        hole_selection = [list(options) for options in hole_selection]

        print([hole.options for hole in family])
        print(hole_selection)
        for hole_index,options in enumerate(hole_selection):
            assert all([option in family[hole_index].options for option in options])
        mdp_family_result.scheduler_choices = scheduler_choices
        mdp_family_result.hole_selection = hole_selection
        return mdp_family_result


    def verify_policy(self, family, prop, policy):
        mdp = self.quotient.keep_actions(family, policy)
        return mdp.model_check_property(prop, alt=True)



    def split(self, family, prop, scheduler_choices, state_values, hole_selection):
        splitter = None
        print(hole_selection)
        inconsistent_assignments = {hole_index:options for hole_index,options in enumerate(hole_selection) if len(options) > 1}
        if len(inconsistent_assignments)==0:
            for hole_index,hole in enumerate(family):
                if hole.size > 1:
                    splitter = hole_index
                    break
        elif len(inconsistent_assignments)==1:
            for hole_index in inconsistent_assignments.keys():
                splitter = hole_index
                break
        else:
            # compute scores for inconsistent holes
            mdp = self.quotient.quotient_mdp
            choice_values = self.quotient.choice_values(mdp, prop, state_values)
            expected_visits = self.quotient.expected_visits(mdp, prop, scheduler_choices)
            quotient_mdp_wrapped = self.quotient.design_space.mdp
            scores = self.quotient.estimate_scheduler_difference(quotient_mdp_wrapped, inconsistent_assignments, choice_values, expected_visits)
            splitters = self.quotient.holes_with_max_score(scores)
            splitter = splitters[0]
        
        # split the hole
        assert splitter is not None
        print(splitter)
        used_options = hole_selection[splitter]
        if len(used_options) > 1:
            core_suboptions = [[option] for option in used_options]
            other_suboptions = [option for option in family[splitter].options if option not in used_options]
        else:
            assert len(family[splitter].options) > 1
            options = family[splitter].options
            half = len(options) // 2
            core_suboptions = [options[:half], options[half:]]
            other_suboptions = []

        if len(other_suboptions) == 0:
            suboptions = core_suboptions
        else:
            suboptions = [other_suboptions] + core_suboptions  # DFS solves core first
        
        print(used_options, suboptions)
        # construct corresponding design subspaces
        subfamilies = []
        family.splitter = splitter
        new_design_space = family.copy()
        for suboption in suboptions:
            subholes = new_design_space.subholes(splitter, suboption)
            subfamily = paynt.quotient.holes.DesignSpace(subholes)
            subfamily.assume_hole_options(splitter, suboption)
            subfamilies.append(subfamily)

        print(family, family.size)
        print([str(f) for f in subfamilies])
        print([f.size for f in subfamilies])
        return subfamilies
        


    def synthesize_metapolicy(self, family):

        members_satisfied = 0
        members_total = family.size
        members_verified = 0
        metapolicy = []

        prop = self.quotient.specification.constraints[0]
        game_solver = self.quotient.build_game_abstraction_solver(prop)

        families = [family]
        while families:
            family = families.pop(-1)
            print("investigating family of size ", family.size)
            if family.size == 1:
                members_verified += 1
            result = self.verify_family(family,game_solver,prop)
            # print(result)

            if result.sat == False:
                # unsat
                # unsatisfiable_family = self.quotient.design_space.assume_options_copy(result.hole_selection)
                unsatisfiable_family = family
                logger.info("satisfying scheduler cannot be obtained for the following family {}".format(unsatisfiable_family))
                self.explore(family)
                if unsatisfiable_family.size > family.size:
                    logger.info("Can reject a larger family than the one that is being explored???")
                continue

            if result.satisfying_policy is not None:
                logger.debug("found policy for family of size {}".format(family.size))
                members_satisfied += family.size
                metapolicy += [(family,result.satisfying_policy)]
                self.explore(family)
                continue

            # refine
            subfamilies = self.split(
                family, prop, game_solver.solution_reachable_choices, game_solver.solution_state_values, result.hole_selection
            )
            families = families + subfamilies
            print([f.size for f in subfamilies])

        satisfied_percentage = round(members_satisfied/members_total*100,0)
        logger.info("all families are explored")
        logger.info("individual MDPs verified: {}".format(members_verified))
        logger.info("found satisfying policies for {}/{} family members ({}%)".format(members_satisfied,members_total,satisfied_percentage))
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
    