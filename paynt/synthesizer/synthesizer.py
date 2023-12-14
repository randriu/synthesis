import paynt.synthesizer.statistic

import logging
logger = logging.getLogger(__name__)


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
    
    def synthesize(self, family = None):
        self.stat.start()
        if not self.stat.whole_synthesis_timer.running:
            self.stat.whole_synthesis_timer.start()

        if family is None:
            family = self.quotient.design_space
        logger.info("synthesis initiated, design space: {}".format(family.size))
        assignment = self.synthesize_assignment(family)
        self.stat.finished(assignment)
        return assignment

    
    def synthesize_assignment(self,family):
        pass

    def synthesize_families(self,family):
        pass
    
    def explore(self, family):
        self.explored += family.size

    def print_stats(self):
        self.stat.print()
    
    def run(self):
        # self.quotient.specification.optimality.update_optimum(0.9)
        self.quotient.design_space.constraint_indices = self.quotient.specification.all_constraint_indices()
        assignment = self.synthesize(self.quotient.design_space)
        if assignment is not None and assignment.size > 1:
            assignment = assignment.pick_any()

        print("")
        if assignment is not None:
            logger.info("Printing synthesized assignment below:")
            logger.info(assignment)
            chain = self.quotient.build_chain(assignment)
            result = chain.check_specification(self.quotient.specification)
            logger.info("Double-checking specification satisfiability: {}".format(result))
            if self.quotient.export_optimal_result:
                self.quotient.export_result(dtmc, result)
        
        self.print_stats()
    
    

