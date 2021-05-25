import sys
import logging

import stormpy

from dynasty.jani.quotient_container import ThresholdSynthesisResult
from dynasty.jani.jani_quotient_builder import JaniQuotientBuilder
from dynasty.family_checkers.familychecker import FamilyChecker


def setup_logger():
    """
    Setup routine for logging. 

    :param log_path: 
    :return: 
    """
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s %(threadName)s - %(name)s - %(levelname)s - %(message)s')

    handlers = []
   
    ch = logging.StreamHandler(sys.stdout)
    handlers.append(ch)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    for h in handlers:
        root.addHandler(h)
    return handlers

def load_mc_formulae(properties):
    mc_formulae = []
    mc_formulae_alt = []
    thresholds = []
    accept_if_above_list = []
    for p in properties:
        formula = p.raw_formula.clone()
        comparison_type = formula.comparison_type
        thresholds.append(formula.threshold)
        formula.remove_bound()
        alt_formula = formula.clone()
        if comparison_type in [stormpy.ComparisonType.LESS, stormpy.ComparisonType.LEQ]:
            formula.set_optimality_type(stormpy.OptimizationDirection.Minimize)
            alt_formula.set_optimality_type(stormpy.OptimizationDirection.Maximize)
            accept_if_above = False
        else:
            assert comparison_type in [stormpy.ComparisonType.GREATER, stormpy.ComparisonType.GEQ]
            formula.set_optimality_type(stormpy.OptimizationDirection.Maximize)
            alt_formula.set_optimality_type(stormpy.OptimizationDirection.Minimize)
            accept_if_above = True
        mc_formulae.append(formula)
        mc_formulae_alt.append(alt_formula)
        accept_if_above_list.append(accept_if_above)

    return mc_formulae, mc_formulae_alt, thresholds, accept_if_above_list


def mc_model_checking(model, formula_index, thresholds, quotient_container, accept_if_above):
    threshold = float(thresholds[formula_index])
    quotient_container.analyse(threshold, formula_index)
    mc_result = quotient_container.decided(threshold)
    if mc_result == ThresholdSynthesisResult.UNDECIDED:
        result = "UNDECIDED"
    else:
        result = "SAT" if (mc_result == ThresholdSynthesisResult.ABOVE) == accept_if_above else "UNSAT"
    return result, quotient_container.latest_result


def main(template, allowed, properties):
    setup_logger()

    family_checker = FamilyChecker()
    family_checker.load_sketch(template, properties)
    family_checker.load_template_definitions(allowed)
    quotient_builder = JaniQuotientBuilder(family_checker.sketch, family_checker.holes)
    quotient_container = quotient_builder.construct(family_checker.hole_options, remember=set())
    mc_formulae, mc_formulae_alt, thresholds, accept_if_above = load_mc_formulae(family_checker.properties)
    quotient_container.prepare(mc_formulae, mc_formulae_alt)
    mdp = quotient_container.mdp_handling.full_mdp

    result, latest_result = mc_model_checking(mdp, 0, thresholds, quotient_container, accept_if_above)
    print(f"MDP Model Checking Result: {result}")
    print(f"MDP Model Checking Bounds: {latest_result.absolute_min} -- {latest_result.absolute_max}")
    print(f"MDP Model Checking Time  : {quotient_container._mc_time}")


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
