import sys
import logging
import pickle
import click
import os
import time

from dynasty.family_checkers.familychecker import FamilyCheckMethod
from dynasty.family_checkers.quotientbased import LiftingChecker, AllInOneChecker,OneByOneChecker,ConsistentSchedChecker
from dynasty.family_checkers.cegis import Synthesiser
from dynasty import version
from dynasty.jani.quotient_container import Engine


logger = logging.getLogger(__name__)

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

def dump_stats_to_file(path, keyword, constants, description, *args):
    logger.debug("Storing stats...")
    pickle.dump((keyword,constants, description,*args), open(path, "wb"))
    logger.info("Stored stats at {}".format(path))


@click.command()
@click.option('--project', help="root", required=True)
@click.option('--sketch', help="the sketch", required=True)
@click.option('--allowed', help="for each hole the options", required=True)
@click.option('--properties', help="the properties", required=True)
@click.option('--optimality', help="optimality criterion")
@click.option('--restrictions', help="restrictions")
@click.option("--constants", default="")
@click.option("--stats", default="stats.out")
@click.option('--engine', help="What engine to use",type=click.Choice(['dd', 'sparse']), default="sparse")
@click.option("--print-stats", is_flag=True)
@click.option('--check-prerequisites', help="should prerequisites be checked", is_flag=True)
@click.option('--partitioning', help="Run partitioning instead of feasibility", is_flag=True)
@click.argument("method",  type=click.Choice(['lift', 'cschedenum', 'allinone', 'onebyone', 'cegis']))
def dynasty(project, sketch, allowed, properties, optimality, restrictions, constants, stats, engine, print_stats, check_prerequisites, partitioning, method):
    print("This is Dynasty version {}.".format(version()))
    approach = FamilyCheckMethod.from_string(method)
    selected_engine = Engine.Sparse if engine == "sparse" else Engine.Dd
    assert approach is not None
    backward_cuts = 1 # Only used for cegis.

    if optimality:
        if partitioning:
            raise RuntimeError("It does not make sense to combine partitioning and optimality")

    if selected_engine == Engine.Dd and approach != FamilyCheckMethod.AllInOne:
        raise RuntimeError("DD engine is currently only supported with the all-in-one approach")

    if approach == FamilyCheckMethod.Lifting:
        algorithm = LiftingChecker()
    elif approach == FamilyCheckMethod.AllInOne:
        algorithm = AllInOneChecker(engine=selected_engine)
    elif approach == FamilyCheckMethod.DtmcIteration:
        algorithm = OneByOneChecker()
    elif approach == FamilyCheckMethod.SchedulerIteration:
        algorithm = ConsistentSchedChecker()
    elif approach == FamilyCheckMethod.CEGIS:
        algorithm = Synthesiser(threads=1, check_prerequisites=check_prerequisites,
                              add_cuts=backward_cuts)
    else:
        assert None


    if not os.path.isdir(project):
        raise ValueError(f"The project folder {project} is not a directory")

    sketch_path = os.path.join(project, sketch)
    allowed_path = os.path.join(project, allowed)
    if restrictions:
        restriction_path = os.path.join(project, restrictions)
    property_path = os.path.join(project, properties)
    if optimality:
        optimality_path = os.path.join(project, optimality)
    else:
        optimality_path = None

    algorithm.load_sketch(sketch_path, property_path, optimality_path=optimality_path, constant_str=constants)
    algorithm.load_template_definitions(allowed_path)
    if restrictions:
        algorithm.load_restrictions(restriction_path)
    algorithm.initialise()

    start_time = time.time()
    if partitioning:
        result = algorithm.run_partitioning()
    else:
        result = algorithm.run_feasibility()
    end_time = time.time()

    if partitioning:
        if result is not None:
            above, below = result
            print("Subfamilies above: ")
            print(above)
        else:
            print("Solver finished without returning a result (probably not implemented).")
    else:
        if result is not None:
            sat, solution, optimal_value = result
            if sat:
                print("Satisfiable!")
                if solution is not None:
                    print("using " + ", ".join([str(k) + ": " + str(v) for k,v in solution.items()]))
                if optimal_value is not None:
                    print("and induces a value of {}".format(optimal_value))
                # print(algorithm.build_instance(solution))
            else:
                print("Unsatisfiable!")
        else:
            print("Solver finished without a result provided.")

    logger.info("Finished after {} seconds.".format(end_time - start_time))

    if print_stats:
        algorithm.print_stats()

    description = "-".join([str(x) for x in
                            [project, sketch, allowed, restrictions, optimality, properties, check_prerequisites,
                             backward_cuts, "sat" if result is not None else "unsat"]])
    dump_stats_to_file(stats, algorithm.stats_keyword, constants, description, algorithm.store_in_statistics())

def main():
    setup_logger("dynasty.log")
    dynasty()

if __name__ == "__main__":
    main()