from . import version

from .parser.sketch import Sketch
from .quotient.quotient_pomdp import POMDPQuotientContainer

from .synthesizer.synthesizer import Synthesizer
from .synthesizer.synthesizer_onebyone import SynthesizerOneByOne
from .synthesizer.synthesizer_ar import SynthesizerAR
from .synthesizer.synthesizer_cegis import SynthesizerCEGIS
from .synthesizer.synthesizer_hybrid import SynthesizerHybrid
from .synthesizer.synthesizer_pomdp import SynthesizerPOMDP
from .synthesizer.synthesizer_multicore_ar import SynthesizerMultiCoreAR

from .quotient.storm_pomdp_control import StormPOMDPControl

from .utils.storm_parallel import ParallelMain
# TODO remove?
from multiprocessing import Manager
from multiprocessing.managers import BaseManager

import click
import sys
import os
import cProfile, pstats

import logging
logger = logging.getLogger(__name__)


def setup_logger(log_path = None):
    ''' Setup routine for logging. '''
    
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    # root.setLevel(logging.INFO)

    # formatter = logging.Formatter('%(asctime)s %(threadName)s - %(name)s - %(levelname)s - %(message)s')
    formatter = logging.Formatter('%(asctime)s - %(filename)s - %(message)s')

    handlers = []
    if log_path is not None:
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        handlers.append(fh)
    sh = logging.StreamHandler(sys.stdout)
    handlers.append(sh)
    sh.setLevel(logging.DEBUG)
    sh.setFormatter(formatter)
    for h in handlers:
        root.addHandler(h)
    return handlers


@click.command()
@click.option("--project", required=True, type=click.Path(exists=True),
    help="project path")
@click.option("--sketch", default="sketch.templ", show_default=True,
    help="name of the sketch file in the project")
@click.option("--props", default="sketch.props", show_default=True,
    help="name of the properties file in the project")
@click.option("--constants", default="", help="constant assignment string")
@click.option("--relative-error", type=click.FLOAT, default="0", show_default=True,
    help="relative error for optimal synthesis")

@click.option("--filetype",
    type=click.Choice(['prism', 'drn', 'pomdp', 'dpomdp']),
    default="prism", show_default=True,
    help="input file format")
@click.option("--export",
    type=click.Choice(['drn', 'pomdp']),
    help="export the model to *.drn/*.pomdp and abort")

@click.option("--method",
    type=click.Choice(['onebyone', 'ar', 'cegis', 'hybrid', 'ar_multicore']),
    default="ar", show_default=True,
    help="synthesis method"
    )

@click.option("--incomplete-search", is_flag=True, default=False,
    help="use incomplete search during synthesis")
@click.option("--fsc-synthesis", is_flag=True, default=False,
    help="enable incremental synthesis of FSCs for a POMDP")
@click.option("--pomdp-memory-size", default=1, show_default=True,
    help="implicit memory size for POMDP FSCs")
@click.option("--fsc-export-result", is_flag=True, default=False,
    help="export the input POMDP as well as the (labeled) optimal DTMC into a .drn format")
@click.option("--hyperproperty", is_flag=True, default=False,
    help="enable synthesis of an MDP scheduler wrt a hyperproperty")
@click.option("--storm-pomdp-analysis", is_flag=True, default=False,
    help="enable running storm analysis for POMDPs to enhance FSC synthesis (supports AR only for now!)")
@click.option("--parallel-storm", is_flag=True, default=False,
    help="run storm analysis in parallel (can only be used together with --storm-pomdp-analysis flag)")
@click.option(
    "--ce-generator",
    default="storm",
    type=click.Choice(["storm", "switss", "mdp"]),
    show_default=True,
    help="counterexample generator",
)
@click.option("--sampling", is_flag=True, default=False,
    help="sample executions")
@click.option("--profiling", is_flag=True, default=False,
    help="run profiling")

def paynt(
        project, sketch, props, constants, relative_error,
        filetype, export,
        method,
        incomplete_search,
        fsc_synthesis, pomdp_memory_size, fsc_export_result,
        hyperproperty, 
        storm_pomdp_analysis, parallel_storm,
        ce_generator,
        sampling,
        profiling
):
    logger.info("This is Paynt version {}.".format(version()))

    # set CLI parameters
    Synthesizer.incomplete_search = incomplete_search
    SynthesizerCEGIS.conflict_generator_type = ce_generator
    POMDPQuotientContainer.initial_memory_size = pomdp_memory_size
    POMDPQuotientContainer.export_optimal_result = fsc_export_result

    # check paths of input files
    sketch_path = os.path.join(project, sketch)
    properties_path = os.path.join(project, props)
    if not os.path.isfile(sketch_path):
        raise ValueError(f"the sketch file {sketch_path} does not exist")
    if not os.path.isfile(properties_path):
        raise ValueError(f"the properties file {properties_path} does not exist")

    quotient = Sketch.load_sketch(sketch_path, filetype, export,
        properties_path, constants, relative_error)

    if storm_pomdp_analysis:
        storm_control = StormPOMDPControl()
    else:
        storm_control = None


    if sampling:
        quotient.sample()
        exit()
        
    # choose the synthesis method and run the corresponding synthesizer
    if isinstance(quotient, POMDPQuotientContainer) and fsc_synthesis:
        synthesizer = SynthesizerPOMDP(quotient, method, storm_control)
    elif method == "onebyone":
        synthesizer = SynthesizerOneByOne(quotient)
    elif method == "ar":
        synthesizer = SynthesizerAR(quotient)
    elif method == "cegis":
        synthesizer = SynthesizerCEGIS(quotient)
    elif method == "hybrid":
        synthesizer = SynthesizerHybrid(quotient)
    elif method == "ar_multicore":
        synthesizer = SynthesizerMultiCoreAR(quotient)
    else:
        pass



    if parallel_storm:
        parallel_main = ParallelMain(synthesizer, storm_control)
        parallel_main.run()
    else:
        if not profiling:
            synthesizer.run()
        else:
            with cProfile.Profile() as pr:
                synthesizer.run()
            stats = pr.create_stats()
            print(stats)
            pstats.Stats(pr).sort_stats('tottime').print_stats(10)


def main():
    setup_logger()
    paynt()


if __name__ == "__main__":
    main()
