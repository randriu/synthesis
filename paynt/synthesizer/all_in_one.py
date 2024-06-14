import stormpy
import payntbind

import paynt.utils.profiler

import logging
logger = logging.getLogger(__name__)

class AllInOne:

    def __init__(self, all_in_one_program, specification, approach, memory_limit_mb, family):

        self.properties = specification.all_properties()
        self.threshold = self.properties[0].threshold
        logger.info("changing constraints into optimality") # TODO check if the properties are optimality or not
        self.transformed_properties = [x.transform_to_optimality_formula(all_in_one_program) for x in self.properties]
        self.approach = approach
        self.family = family

        build_timer = paynt.utils.profiler.Timer()
        logger.info(f"building {self.approach} all in one MDP")

        build_timer.start()
        if self.approach == 'bdd':
            stormpy.set_settings(["--sylvan:maxmem", str(memory_limit_mb)]) # set memory usage by the symbolic approach
            self.model = stormpy.build_symbolic_model(all_in_one_program)
            self.filter = stormpy.create_filter_initial_states_symbolic(self.model)
        elif self.approach == 'sparse':
            build_options = stormpy.BuilderOptions([p.raw_formula for p in self.transformed_properties])
            build_options.set_build_state_valuations()
            self.model = stormpy.build_sparse_model_with_options(all_in_one_program, build_options)
            self.filter = stormpy.create_filter_initial_states_sparse(self.model)
        else:
            logger.error("Unknown all in one approach!")
            exit(1)
        build_timer.stop()

        logger.info(f"build finished in {round(build_timer.read(),1)}s")
        logger.info(f"constructed all in one MDP having {self.model.nr_states} states and {self.model.nr_choices} actions")


    def run(self):

        all_in_one_timer = paynt.utils.profiler.Timer()
        logger.info(f"starting all in one analysis")

        all_in_one_timer.start()
        if self.approach == 'bdd':
            result = stormpy.check_model_dd(self.model, self.transformed_properties[0], only_initial_states=True)
            result.filter(self.filter)
            all_in_one_timer.stop()

            members_sat = 0
            result_values = result.get_values()
            for valuation, mc_result in result_values:
                # 'valuation' can be used to obtain hole assignments for a give result 
                if self.properties[0].satisfies_threshold(mc_result):
                    members_sat += 1
                    
        elif self.approach == 'sparse':
            result = stormpy.check_model_sparse(self.model, self.transformed_properties[0], extract_scheduler=True, only_initial_states=True)
            result.filter(self.filter)
            all_in_one_timer.stop()
        
        members_total = self.family.size
        members_sat_percentage = int(round(members_sat/members_total*100,0))
        print(f"satisfied {members_sat}/{members_total} members ({members_sat_percentage}%)")

        time_elapsed = round(all_in_one_timer.read(),1)
        logger.info(f"all in one analysis finished in {time_elapsed}s")


