import sys
import click
import os

from . import version

from .sketch.sketch import Sketch
from .synthesizers.synthesizer import *
from .synthesizers.quotient_pomdp import POMDPQuotientContainer
from .synthesizers.synthesizer_pomdp import SynthesizerPOMDP

import logging
# logger = logging.getLogger(__name__)

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
@click.option("--project", required=True, help="project path", )

@click.option("--sketch", default="sketch.templ", show_default=True,
    help="name of the sketch file in the project")
@click.option("--filetype",
    type=click.Choice(['prism', 'jani', 'pomdp', 'drn'], case_sensitive=False),
    default="prism", show_default=True,
    help="input file format")
@click.option("--export",
    type=click.Choice(['prism', 'jani', 'pomdp', 'drn'], case_sensitive=False),
    help="export the model to *.jani/*.pomdp/*.drn and abort")

@click.option("--properties", default="sketch.props", show_default=True,
    help="name of the properties file in the project")
@click.option("--constants", default="", help="constant assignment string", )

@click.option("--method",
    type=click.Choice(['onebyone', 'ar', 'cegis', 'hybrid'], case_sensitive=False),
    default="ar", show_default=True,
    help="synthesis method"
    )
@click.option("--incomplete-search", is_flag=True, default=False,
    help="use incomplete search during the synthesis")
@click.option("--fsc-synthesis", is_flag=True, default=False,
    help="enable incremental synthesis of FSCs for a POMDP")
@click.option("--pomdp-memory-size", default=1,
    help="implicit memory size for POMDP FSCs")
@click.option("--hyperproperty", is_flag=True, default=False,
    help="enable synthesis of an MDP scheduler wrt a hyperproperty")

def paynt(
        project,
        sketch, filetype, export,
        properties, constants,
        method,
        incomplete_search, fsc_synthesis, pomdp_memory_size,
        hyperproperty
):
    logger.info("This is Paynt version {}.".format(version()))

    Sketch.filetype = filetype
    Sketch.export_option = export
    
    Sketch.hyperproperty_synthesis = hyperproperty
    Synthesizer.incomplete_search = incomplete_search
    POMDPQuotientContainer.initial_memory_size = pomdp_memory_size

    # parse sketch
    if not os.path.isdir(project):
        raise ValueError(f"The project folder {project} is not a directory")
    sketch_path = os.path.join(project, sketch)
    properties_path = os.path.join(project, properties)
    sketch = Sketch(sketch_path, properties_path, constants)

    # choose synthesis method and run the corresponding synthesizer
    if sketch.is_pomdp and fsc_synthesis:
        synthesizer = SynthesizerPOMDP(sketch, method)
    elif method == "onebyone":
        synthesizer = Synthesizer1By1(sketch)
    elif method == "cegis":
        synthesizer = SynthesizerCEGIS(sketch)
    elif method == "ar":
        synthesizer = SynthesizerAR(sketch)
    elif method == "hybrid":
        synthesizer = SynthesizerHybrid(sketch)
    else:
        pass
    synthesizer.run()


def main():
    setup_logger()
    paynt()


if __name__ == "__main__":
    main()
