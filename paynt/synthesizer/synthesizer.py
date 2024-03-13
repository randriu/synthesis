import paynt.synthesizer.statistic

import logging
logger = logging.getLogger(__name__)


class FamilyEvaluation:
    '''Result associated with a family after its evaluation. '''
    def __init__(self, family, value, sat, policy):
        self.family = family
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

    def export_evaluation_result(self, evaluations, export_filename_base):
        ''' to be overridden '''
        pass

    def evaluate(self, family=None, prop=None, keep_value_only=False, print_stats=True, export_filename_base=None):
        '''
        Evaluate each member of the family wrt the given property.
        :param family if None, then the design space of the quotient will be used
        :param prop if None, then the default property of the quotient will be used
            (assuming single-property specification)
        :param keep_value_only if True, only value will be associated with the family
        :param print_stats if True, synthesis statistic will be printed
        :param export_filename_base base filename used to export the evaluation results
        :returns a list of (family,evaluation) pairs
        '''
        if family is None:
            family = self.quotient.design_space
        if prop is None:
            prop = self.quotient.get_property()

        logger.info("evaluation initiated, design space: {}".format(family.size))
        self.stat.start(family)
        evaluations = self.evaluate_all(family, prop, keep_value_only)
        self.stat.finished_evaluation(evaluations)
        logger.info("evaluation finished")

        if export_filename_base is not None:
            self.export_evaluation_result(evaluations, export_filename_base)

        if print_stats:
            self.stat.print()
        
        return evaluations

    
    def synthesize_one(self, family):
        ''' to be overridden '''
        pass

    def synthesize(self, family=None, optimum_threshold=None, keep_optimum=False, return_all=False, print_stats=True):
        '''
        :param family family of assignment to search in
        :param optimum_threshold known bound on the optimum value
        :param keep_optimum if True, the optimality specification will not be reset upon finish
        :param return_all if True and the synthesis returns a family, all assignments will be returned instead of an
            arbitrary one
        :param print_stats if True, synthesis stats will be printed upon completion
        '''
        if family is None:
            family = self.quotient.design_space
        if family.constraint_indices is None:
            family.constraint_indices = list(range(len(self.quotient.specification.constraints)))
        
        if optimum_threshold is not None:
            self.quotient.specification.optimality.update_optimum(optimum_threshold)
            logger.debug(f"optimality threshold set to {optimum_threshold}")
        
        logger.info("synthesis initiated, design space: {}".format(family.size_or_order))
        self.quotient.discarded = 0
        self.stat.start(family)
        assignment = self.synthesize_one(family)
        if assignment is not None and assignment.size > 1 and not return_all:
            assignment = assignment.pick_any()
        self.stat.finished_synthesis(assignment)
        logger.info("synthesis finished, printing synthesized assignment below:")
        logger.info(assignment)

        if assignment is not None and assignment.size == 1:
            model = self.quotient.build_assignment(assignment)
            mc_result = model.check_specification(self.quotient.specification)
            logger.info(f"double-checking specification satisfiability: {mc_result}")

        if print_stats:
            self.stat.print()

        if not keep_optimum:
            self.quotient.specification.reset()

        return assignment

    
    def run(self, optimum_threshold=None, export_evaluation=None):
        if isinstance(self.quotient, paynt.quotient.mdp_family.MdpFamilyQuotient):
            self.evaluate(export_filename_base=export_evaluation)
        else:
            self.synthesize(optimum_threshold=optimum_threshold)
