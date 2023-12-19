import paynt.synthesizer.statistic

import logging
logger = logging.getLogger(__name__)


class FamilyEvaluation:
    '''Result associated with a family after its evaluation. '''
    def __init__(self, value, sat, policy):
        self.value = value
        self.sat = sat
        self.policy = policy


class Synthesizer:

    # if True, some subfamilies can be discarded and some holes can be generalized
    incomplete_search = False

    @staticmethod
    def choose_synthesizer(quotient, method, fsc_synthesis, storm_control):

        # hiding imports here to avoid mutual top-level imports
        import paynt.quotient.pomdp
        import paynt.quotient.mdp_family
        import paynt.synthesizer.synthesizer_onebyone
        import paynt.synthesizer.synthesizer_ar
        import paynt.synthesizer.synthesizer_cegis
        import paynt.synthesizer.synthesizer_hybrid
        import paynt.synthesizer.synthesizer_multicore_ar
        import paynt.synthesizer.synthesizer_pomdp
        import paynt.synthesizer.policy_tree

        if isinstance(quotient, paynt.quotient.pomdp_family.PomdpFamilyQuotient):
            logger.info("nothing to do with the POMDP sketch, aborting...")
            exit(0)
        if isinstance(quotient, paynt.quotient.pomdp.PomdpQuotient) and fsc_synthesis:
            return paynt.synthesizer.synthesizer_pomdp.SynthesizerPOMDP(quotient, method, storm_control)
        if isinstance(quotient, paynt.quotient.mdp_family.MdpFamilyQuotient):
            if method == "onebyone":
                return paynt.synthesizer.synthesizer_onebyone.SynthesizerOneByOne(quotient)
            else:
                return paynt.synthesizer.policy_tree.SynthesizerPolicyTree(quotient)
        if method == "onebyone":
            return paynt.synthesizer.synthesizer_onebyone.SynthesizerOneByOne(quotient)
        if method == "ar":
            return paynt.synthesizer.synthesizer_ar.SynthesizerAR(quotient)
        if method == "cegis":
            return paynt.synthesizer.synthesizer_cegis.SynthesizerCEGIS(quotient)
        if method == "hybrid":
            return paynt.synthesizer.synthesizer_hybrid.SynthesizerHybrid(quotient)
        if method == "ar_multicore":
            return paynt.synthesizer.synthesizer_multicore_ar.SynthesizerMultiCoreAR(quotient)
        raise ValueError("invalid method name")
    
    
    def __init__(self, quotient):
        self.quotient = quotient
        self.stat = paynt.synthesizer.statistic.Statistic(self)
        self.explored = 0
    
    @property
    def method_name(self):
        ''' to be overridden '''
        pass
    
    def explore(self, family):
        self.explored += family.size


    def evaluate_all(self, family, prop, keep_value_only=False):
        ''' to be overridden '''
        pass

    def evaluate(self, family=None, prop=None, keep_value_only=False, print_stats=True):
        '''
        Evaluate each member of the family wrt the given property.
        :param family if None, then the design space of the quotient will be used
        :param prop if None, then the default property of the quotient will be used
            (assuming single-property specification)
        :param keep_value_only if True, only value will be associated with the family
        :param print_stats if True, synthesis statistic will be printed
        :returns a list of (family,evaluation) pairs
        '''
        if family is None:
            family = self.quotient.design_space
        if prop is None:
            prop = self.quotient.get_property()

        logger.info("evaluation initiated, design space: {}".format(family.size))
        self.stat.start(family)
        family_to_evaluation = self.evaluate_all(family, prop, keep_value_only)
        self.stat.finished_evaluation(family_to_evaluation)
        logger.info("evaluation finished")

        if print_stats:
            self.stat.print()
        return family_to_evaluation

    
    def synthesize_one(self, family):
        ''' to be overridden '''
        pass

    def synthesize(self, family=None, optimum_threshold=None, print_stats=True):
        if family is None:
            family = self.quotient.design_space
        family.constraint_indices = self.quotient.specification.all_constraint_indices()
        
        if optimum_threshold is not None:
            self.quotient.specification.optimality.update_optimum(optimum_threshold)
            logger.debug(f"optimality threshold set to {optimum_threshold}")
        
        logger.info("synthesis initiated, design space: {}".format(family.size))
        self.stat.start(family)
        assignment = self.synthesize_one(family)
        if assignment is not None and assignment.size > 1:
            assignment = assignment.pick_any()
        self.stat.finished_synthesis(assignment)
        logger.info("synthesis finished")

        if assignment is not None:
            logger.info("printing synthesized assignment below:")
            logger.info(assignment)
            model = self.quotient.build_assignment(assignment)
            mc_result = model.check_specification(self.quotient.specification)
            logger.info(f"double-checking specification satisfiability: {mc_result}")
        
        if print_stats:
            self.stat.print()
        return assignment

    
    def run(self, optimum_threshold=None):
        if isinstance(self.quotient, paynt.quotient.mdp_family.MdpFamilyQuotient):
            self.evaluate()
        else:
            self.synthesize(optimum_threshold=optimum_threshold)
