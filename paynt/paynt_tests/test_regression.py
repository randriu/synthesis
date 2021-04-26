import os.path
import pytest
import logging
import click.testing

import paynt
import paynt.cli
logger = logging.getLogger(__name__)
paynt.cli.setup_logger("paynt_tests.log")


benchmarks_feasibility = [
    pytest.param("examples/grid", "4x4grid_sl.templ", "CMAX=11,T_EXP=10.0,T_SLOW=10.0,T_FAST=0.7", "4x4grid_sl.allowed", "single.properties",  "none.restrictions"),
    pytest.param("examples/grid", "4x4grid_sl.templ", "CMAX=11,T_EXP=10.0,T_SLOW=10.0,T_FAST=0.9", "4x4grid_sl.allowed",
                 "single.properties", "none.restrictions"),
    ## pytest.param("brp", "brp", "N=16,MAX=2", "property1", "stormpy", marks=[require_stormpy()]),
]

methods_feasibility = [
    "lift",
    "cschedenum",
    "cegis"
]

@pytest.mark.parametrize("project,sketch,constants,allowed,properties,restrictions", benchmarks_feasibility)
@pytest.mark.parametrize("method", methods_feasibility)
def test_feasibility_script(project, sketch, constants, allowed, properties, restrictions, method):
    command = ["--project",
               project,
               "--sketch",
               sketch,
               "--constants",
               constants,
               "--allowed",
               allowed,
               "--properties",
               properties,
               "--restrictions",
               restrictions,
               method
               ]
    runner = click.testing.CliRunner()
    logger.info("paynt.py " + " ".join(command))
    result = runner.invoke(paynt.cli.paynt, command)
    assert result.exit_code == 0, result.output
#    assert os.path.isfile(target_file)
#    os.remove(target_file)


benchmarks_optimal_feasibility = [
    pytest.param("examples/grid", "4x4grid_sl.templ", "CMAX=11,T_EXP=10.0,T_SLOW=10.0,T_FAST=0.7", "4x4grid_sl.allowed", "none.properties",  "none.restrictions", "fast_to_target.optimal"),
    ## pytest.param("brp", "brp", "N=16,MAX=2", "property1", "stormpy", marks=[require_stormpy()]),
]

methods_optimal_feasibility = methods_feasibility

@pytest.mark.parametrize("project,sketch,constants,allowed,properties,restrictions,optimal", benchmarks_optimal_feasibility)
@pytest.mark.parametrize("method", methods_optimal_feasibility)
def test_optimal_feasibility_script(project, sketch, constants, allowed, properties, restrictions,optimal, method):
    command = ["--project",
               project,
               "--sketch",
               sketch,
               "--constants",
               constants,
               "--allowed",
               allowed,
               "--properties",
               properties,
               "--restrictions",
               restrictions,
               "--optimality",
               optimal,
               method
               ]
    runner = click.testing.CliRunner()
    logger.info("paynt.py " + " ".join(command))
    result = runner.invoke(paynt.cli.paynt, command)
    assert result.exit_code == 0, result.output
#    assert os.path.isfile(target_file)
#    os.remove(target_file)
