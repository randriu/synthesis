import sys
import click
import os

from . import version

from .sketch.sketch import Sketch
from .synthesizers.synthesizer import *
from .synthesizers.quotient import POMDPQuotientContainer
from .synthesizers.incremental import SynthesizerPOMDPIncremental
from .synthesizers.pomdp import SynthesizerPOMDP

import logging
# logger = logging.getLogger(__name__)


def setup_logger(log_path=None):
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
    ch = logging.StreamHandler(sys.stdout)
    handlers.append(ch)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    for h in handlers:
        root.addHandler(h)
    return handlers


@click.command()
@click.option("--project", required=True, help="root", )
@click.option("--sketch", default="sketch.templ", help="name of the sketch file")
@click.option("--properties", default="sketch.props", help="name of the properties file")
@click.option("--constants", default="", help="constant assignment string", )
@click.argument("method", type=click.Choice(['onebyone', 'cegis', 'ar', 'hybrid'], case_sensitive=False), default="ar")
@click.option("--export-jani", is_flag=True, default=False, help="export JANI model to 'output.jani' and abort")
@click.option("--incomplete-search", is_flag=True, default=False, help="use incomplete search during the synthesis")
@click.option("--fsc-synthesis", is_flag=True, default=False, help="enable incremental synthesis of FSCs for a POMDP")
@click.option("--pomdp-memory-size", default=1, help="implicit memory size for POMDP FSCs")
@click.option("--incremental", nargs=2, default=[0, 0], type=int, help="enable incremental synthesis of FSC for a POMDP within a memory size with applied restrictions")
@click.option("--strategy", type=click.Choice(['full', 'iterative', 'injection']), default="full", help="define strategy")
@click.option("--reset-optimum", is_flag=True, default=False, help="reset the optimality property after each synthesis loop")
@click.option("--hyperproperty", is_flag=True, default=False, help="enable synthesis an MDP scheduler wrt a hyperproperty")
def paynt(
        project, sketch, properties, constants, method, export_jani,
        incomplete_search, fsc_synthesis, pomdp_memory_size,
        incremental, strategy, reset_optimum, hyperproperty
    ):

    logger.info("This is Paynt version {}.".format(version()))

    Sketch.export_jani = export_jani
    Synthesizer.incomplete_search = incomplete_search
    POMDPQuotientContainer.pomdp_memory_size = pomdp_memory_size

    # parse sketch
    if not os.path.isdir(project):
        raise ValueError(f"The project folder {project} is not a directory")
    sketch_path = os.path.join(project, sketch)
    properties_path = os.path.join(project, properties)
    sketch = Sketch(sketch_path, properties_path, constants)

    # choose synthesis method
    if sketch.is_pomdp:
        if incremental != (0, 0):
            synthesizer = SynthesizerPOMDPIncremental(
                sketch, method, min=incremental[0], max=incremental[1], reset_optimum=reset_optimum)
        elif fsc_synthesis:
            synthesizer = SynthesizerPOMDP(sketch, method, strategy)
    elif method == "onebyone":
        synthesizer = Synthesizer1By1(sketch)
    elif method == "cegis":
        synthesizer = SynthesizerCEGIS(sketch)
    elif method == "ar":
        synthesizer = SynthesizerAR(sketch)
    elif method == "hybrid":
        synthesizer = SynthesizerHybrid(sketch)
    elif method == "evo":
        raise NotImplementedError
    else:
        assert None

    # run synthesis
    synthesizer.run()


def main():
    # setup_logger("paynt.log")
    setup_logger()
    paynt()


if __name__ == "__main__":
    main()
