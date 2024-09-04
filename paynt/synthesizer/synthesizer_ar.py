import paynt.synthesizer.synthesizer
import paynt.quotient.pomdp
import paynt.verification.property_result
import paynt.utils.profiler

import logging
logger = logging.getLogger(__name__)

class SynthesizerAR(paynt.synthesizer.synthesizer.Synthesizer):

    @property
    def method_name(self):
        return "AR"

    def check_specification_for_mdp(self, family):
        mdp = family.mdp
        self.stat.iteration(mdp)

        # check constraints
        spec = self.quotient.specification
        if family.constraint_indices is None:
            family.constraint_indices = spec.all_constraint_indices()
        results = [None for _ in spec.constraints]
        for index in family.constraint_indices:
            constraint = spec.constraints[index]
            result = paynt.verification.property_result.MdpPropertyResult(constraint)

            # check primary direction
            result.primary = mdp.model_check_property(constraint)

            # no need to check secondary direction if primary direction yields UNSAT
            if not result.primary.sat:
                result.sat = False
            else:
                # check secondary direction
                result.secondary = mdp.model_check_property(constraint, alt=True)
                if mdp.is_deterministic and result.primary.value != result.secondary.value:
                    logger.warning("WARNING: model is deterministic but min<max")
                if result.secondary.sat:
                    result.sat = True

            # primary direction is SAT
            if result.sat is None:
                # check if the primary scheduler is consistent
                result.primary_selection,_ = self.quotient.scheduler_is_consistent(mdp, constraint, result.primary.result)
            results[index] = result
            if result.sat is False:
                break
        spec_result = paynt.verification.property_result.MdpSpecificationResult()
        spec_result.constraints_result = paynt.verification.property_result.ConstraintsResult(results)

        # check optimality
        if spec.has_optimality and not spec_result.constraints_result.sat is False:
            opt = spec.optimality
            result = paynt.verification.property_result.MdpOptimalityResult(opt)

            # check primary direction
            result.primary = mdp.model_check_property(opt)
            if not result.primary.improves_optimum:
                # OPT <= LB
                result.can_improve = False
            else:
                # LB < OPT, check if LB is tight
                result.primary_selection,consistent = self.quotient.scheduler_is_consistent(mdp, opt, result.primary.result)
                result.can_improve = True
                if consistent:
                    # LB < OPT and it's tight, double-check the constraints and the value on the DTMC
                    result.can_improve = False
                    assignment = family.assume_options_copy(result.primary_selection)
                    dtmc = self.quotient.build_assignment(assignment)
                    res = dtmc.check_specification(self.quotient.specification)
                    if res.constraints_result.sat and spec.optimality.improves_optimum(res.optimality_result.value):
                        result.improving_assignment = assignment
                        result.improving_value = res.optimality_result.value
            spec_result.optimality_result = result

        spec_result.evaluate(family)
        family.analysis_result = spec_result


    def verify_family(self, family):
        self.quotient.build(family)
        self.check_specification_for_mdp(family)


    def update_optimum(self, family):
        ia = family.analysis_result.improving_assignment
        iv = family.analysis_result.improving_value
        if iv is not None and self.quotient.specification.optimality.improves_optimum(iv):
            self.quotient.specification.optimality.update_optimum(iv)
            self.best_assignment = ia
            # logger.info(f"new optimum achieved: {iv}")
            if isinstance(self.quotient, paynt.quotient.pomdp.PomdpQuotient):
                self.stat.new_fsc_found(family.analysis_result.improving_value, ia, self.quotient.policy_size(ia))


    def synthesize_one(self, family):
        # return self.synthesize_one_experimental(family)
        families = [family]
        while families:
            if paynt.utils.profiler.GlobalTimeoutTimer.timeout_reached():
                logger.info("timeout reached, aborting...")
                break
            family = families.pop(-1)
            self.verify_family(family)
            self.update_optimum(family)
            if family.analysis_result.can_improve is False:
                self.explore(family)
                continue
            # undecided
            subfamilies = self.quotient.split(family)
            families = families + subfamilies
        return self.best_assignment
