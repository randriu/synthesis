import stormpy
import payntbind

import logging
logger = logging.getLogger(__name__)

class AllInOne:

    def __init__(self, all_in_one_program, specification, approach):

        self.properties = specification.all_properties()
        self.approach = approach

        if self.approach == 'bdd':
            print(all_in_one_program)
            self.model = stormpy.build_symbolic_model(all_in_one_program)
            self.filter = stormpy.create_filter_initial_states_symbolic(self.model)
        elif self.approach == "sparse":
            build_options = stormpy.BuilderOptions([p.property.raw_formula for p in self.properties])
            build_options.set_build_state_valuations()
            self.model = stormpy.build_sparse_model_with_options(all_in_one_program, build_options)
            self.filter = stormpy.create_filter_initial_states_sparse(self.model)
        else:
            logger.error("Unknown all in one approach!")
            exit(1)


    def run(self):

        if self.approach == 'bdd':
            result = stormpy.check_model_dd(self.model, self.properties[0].property, only_initial_states=True)
            result.filter(self.filter)
        elif self.approach == "sparse":
            result = stormpy.check_model_sparse(self.model, self.properties[0].property, extract_scheduler=True, only_initial_states=True)
            result.filter(self.filter)


