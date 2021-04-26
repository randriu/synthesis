import sys
import logging
import click
import os

from dynasty import version
from dynasty.family_checkers.familychecker import FamilyCheckMethod

from dynasty.sketch import Sketch
from dynasty.hybrid.enumeration import EnumerationChecker
from dynasty.hybrid.cegis import CEGISChecker
from dynasty.hybrid.ar import ARChecker
from dynasty.hybrid.integrated_checker import IntegratedChecker

logger = logging.getLogger(__name__)

STAGE_SCORE_LIMIT = 99999

def setup_logger(log_path):
    """
    Setup routine for logging. 

    :param log_path: 
    :return: 
    """
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s %(threadName)s - %(name)s - %(levelname)s - %(message)s')

    handlers = []
    if log_path:
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        handlers.append(fh)
    ch = logging.StreamHandler(sys.stdout)
    handlers.append(ch)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    for h in handlers:
        root.addHandler(h)
    return handlers

# def dump_stats_to_file(path, keyword, constants, description, *args):
#     logger.debug("Storing stats...")
#     pickle.dump((keyword, constants, description, *args), open(path, "wb"))
#     logger.info("Stored stats at {}".format(path))

@click.command()
@click.option('--project', help="root", required=True)
@click.option('--sketch', help="the sketch", required=False, default="sketch.templ")
@click.option('--allowed', help="for each hole the options", required=False, default="sketch.allowed")
@click.option('--properties', help="the properties", required=False, default="sketch.properties")
@click.option("--constants", default="")
@click.option('--short-summary', '-ss', help="Print also short synthesis summary", is_flag=True, default=False)
@click.option('--ce-quality', '-ceq', help="Compute counter-examples qualities.", is_flag=True, default=False)
@click.option('--ce-maxsat', '-cem', help="Compute quality of maxsat counter-examples.", is_flag=True, default=False)
@click.argument("method", type=click.Choice(['cegar', 'cschedenum', 'allinone', 'onebyone', 'cegis', 'hybrid']))  # +
def dynasty(
        project, sketch, allowed, properties, constants, method, short_summary, ce_quality, ce_maxsat
):
    print("This is Dynasty version {}.".format(version()))
    
    # parse sketch
    if not os.path.isdir(project):
        raise ValueError(f"The project folder {project} is not a directory")
    sketch_path = os.path.join(project, sketch)
    allowed_path = os.path.join(project, allowed)
    properties_path = os.path.join(project, properties)
    sketch = Sketch(sketch_path, allowed_path, properties_path, constants)

    # choose method
    # FIXME: differentiate between solvers
    approach = FamilyCheckMethod.from_string(method)
    assert approach == FamilyCheckMethod.Hybrid
    
    # FIXME: set hybrid parameters
    # FIXME: set the stage score limit
    # RA: do we need a stage score limit? hybrid method seems to behave well without one
    IntegratedChecker.ce_quality = ce_quality
    IntegratedChecker.ce_maxsat = ce_maxsat
    IntegratedChecker.stage_score_limit = STAGE_SCORE_LIMIT

    if FamilyCheckMethod.regime == 0:
        algorithm = EnumerationChecker(sketch)
    elif FamilyCheckMethod.regime == 1:
        algorithm = CEGISChecker(sketch)
    elif FamilyCheckMethod.regime == 2:
        algorithm = ARChecker(sketch)
    elif FamilyCheckMethod.regime == 3:
        algorithm = IntegratedChecker(sketch)
    else:
        assert None

    algorithm.initialise()
    algorithm.run(short_summary)
    print(algorithm.statistic)

    # logging (deprecated?)
    #     if result is not None:
    #         sat, solution, optimal_value = result
    #         if sat:
    #             print("Satisfiable!")
    #             if solution is not None:
    #                 print("using " + ", ".join([str(k) + ": " + str(v) for k, v in solution.items()]))
    #             if optimal_value is not None:
    #                 print("and induces a value of {}".format(optimal_value))
    #             # print(algorithm.build_instance(solution))
    #         else:
    #             print("Unsatisfiable!")
    #     else:
    #         print("Solver finished without a result provided.")

    # logger.info("Finished after {} seconds.".format(end_time - start_time))

    # if print_stats:
    #     algorithm.print_stats()

    # description = "-".join([str(x) for x in
    #                         [project, sketch, allowed, restrictions, optimality, properties, check_prerequisites,
    #                          backward_cuts, "sat" if result is not None else "unsat"]])
    # dump_stats_to_file(stats, algorithm.stats_keyword, constants, description, algorithm.store_in_statistics())


def main():
    setup_logger("dynasty.log")
    dynasty()

if __name__ == "__main__":
    main()
