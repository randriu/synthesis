import os
import pytest
import sys
import json

import stormpy

from paynt.sketch import Sketch
from paynt.jani.jani_quotient_builder import JaniQuotientBuilder
from paynt.jani.quotient_container import ThresholdSynthesisResult
from test_utils import PayntTestUtils

EXP_RESULTS = "/expected_results/"


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


def mdp_model_checking(model, formula_index, thresholds, quotient_container, accept_if_above):
    threshold = float(thresholds[formula_index])
    quotient_container.analyse(threshold, formula_index)
    mc_result = quotient_container.decided(threshold)
    if mc_result == ThresholdSynthesisResult.UNDECIDED:
        result = "UNDECIDED"
    else:
        result = "SAT" if (mc_result == ThresholdSynthesisResult.ABOVE) == accept_if_above else "UNSAT"
    return result, quotient_container.latest_result

mc_benchmark = [
    pytest.param("kydie", ""),
    pytest.param("dice/5", ""),
    pytest.param("dpm/demo", "CMAX=2"),
]

@pytest.mark.parametrize("project, constants_str", mc_benchmark)
def test_mdp_model_checking(project, constants_str):
    template = f"{PayntTestUtils.get_path_to_workspace_examples()}/{project}/sketch.templ"
    properties = f"{PayntTestUtils.get_path_to_workspace_examples()}/{project}/sketch.properties"
    sketch = Sketch(template, properties, constants_str)
    quotient_builder = JaniQuotientBuilder(sketch.jani, sketch.holes)
    quotient_container = quotient_builder.construct(sketch.hole_options, remember=set())
    mc_formulae, mc_formulae_alt, thresholds, accept_if_above = load_mc_formulae(sketch.properties)
    quotient_container.prepare(mc_formulae, mc_formulae_alt)
    mdp = quotient_container.mdp_handling.full_mdp

    with open(f"{os.path.abspath(os.path.dirname(__file__))}{EXP_RESULTS}mdp_model_checking.json", 'r') as json_file:
        expected_results = json.load(json_file)

    for idx, _ in enumerate(mc_formulae):
        result, latest_result = mdp_model_checking(mdp, idx, thresholds, quotient_container, accept_if_above)
        # assert result == expected_results[project][idx]["result"]
        # assert latest_result.absolute_min == expected_results[project][idx]["absolute_min"]
        # assert latest_result.absolute_max == expected_results[project][idx]["absolute_max"]

        print(f"MC Model Checking Result: {result}")
        print(f"MC Model Checking Bounds: {latest_result.absolute_min} -- {latest_result.absolute_max}")

if __name__ == '__main__':
    test_mdp_model_checking(sys.argv[1], sys.argv[2])