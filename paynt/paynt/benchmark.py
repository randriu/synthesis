"""
benchmark.py

Execute several runs of the framework for benchmarking. 
"""

import os
import click

import synt


def _stats_path(prefix, constants):
    cstr = constants.replace(",", "_")
    return os.path.join(prefix, "stats_" + cstr + ".sts")

def _log_path(prefix, constants):
    cstr = constants.replace(",", "_")
    return os.path.join(prefix, "stats_" + cstr + ".log")


def reset_handlers(handlers):
    for h in handlers:
        logging.getLogger().removeHandler(h)

@click.command()
@click.option('--project', help="root")
@click.option('--sketch', help="the sketch")
@click.option('--allowed', help="for each hole the options")
@click.option('--restrictions', help="restrictions")
@click.option('--optimality', help="optimality criterion")
@click.option('--properties', help="the properties")
@click.option('--check-prerequisites', default=False)
@click.option('--add-cuts', default=1, type=int, help="add cuts")
@click.option("--threads", type=int, default=1)
@click.option("--constants", default="")
@click.option("--prefix")
def benchmark(project, sketch, allowed, restrictions, optimality, properties, check_prerequisites, add_cuts, threads, constants, prefix):
    if not os.path.exists(prefix):
        os.makedirs(prefix)
    constants_set = constants.split(";")
    print(constants_set)
    for c in constants_set:
        handlers = synt.setup_logger(_log_path(prefix, c))
        stats_path = _stats_path(prefix, c)
        synt.synthethise(project, sketch, allowed, restrictions, optimality, properties, check_prerequisites, add_cuts, threads, c, stats_path)
        reset_handlers(handlers)


if __name__ == '__main__':
    benchmark()
