from .synthesizer import Synthesizer

import logging
logger = logging.getLogger(__name__)


class SynthesizerOneByOne(Synthesizer):
    
    @property
    def method_name(self):
        return "1-by-1"

    def synthesize_assignment(self, family):
        
        satisfying_assignment = None
        for hole_combination in family.all_combinations():
            
            assignment = family.construct_assignment(hole_combination)
            chain = self.quotient.build_chain(assignment)
            self.stat.iteration_dtmc(chain.states)
            result = chain.check_specification(self.quotient.specification, short_evaluation = True)
            self.explore(assignment)

            accepting,improving_value = result.accepting_dtmc(self.quotient.specification)
            if accepting:
                satisfying_assignment = assignment
            if improving_value is not None:
                self.quotient.specification.optimality.update_optimum(improving_value)
            if accepting and not self.quotient.specification.can_be_improved:
                return accepting_assignment

        return satisfying_assignment

    def evaluate_all_wrt_property(self, family=None, prop=None, keep_value_only=False):
        '''
        Model check each member of the family wrt the given property.
        :param family if None, then the design space of the quotient will be used
        :param prop if None, then the default property of the quotient will be used
        :param keep_value_only if True, then, instead of property result, only the corresponding value will be
            associated with the member
        :returns a list of (family,property result) pairs where family is neceesarily a singleton
        '''
        if family is None:
            family = self.quotient.design_space
        if prop is None:
            prop = self.quotient.get_property()
        assignment_evaluation = []
        for hole_combination in family.all_combinations():
            assignment = family.construct_assignment(hole_combination)
            chain = self.quotient.build_chain(assignment)
            self.stat.iteration_dtmc(chain.states)
            evaluation = chain.model_check_property(prop)
            if keep_value_only:
                evaluation = evaluation.value
            assignment_evaluation.append( (assignment,evaluation) )
            self.explore(assignment)
        return assignment_evaluation
