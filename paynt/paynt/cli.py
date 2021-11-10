import sys
import click
import os

from . import version

from .sketch.sketch import Sketch
from .synthesizers.synthesizer import Synthesizer, SynthesizerAR

import logging
# logger = logging.getLogger(__name__)

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


# def dump_stats_to_file(path, keyword, constants, description, *args):
#     logger.debug("Storing stats...")
#     pickle.dump((keyword, constants, description, *args), open(path, "wb"))
#     logger.info("Stored stats at {}".format(path))

@click.command()
@click.option('--project', help="root", required=True)
@click.option('--sketch', help="the sketch", required=False, default="sketch.templ")
@click.option('--properties', help="the properties", required=False, default="sketch.properties")
@click.option("--constants", default="")
@click.option('--short-summary', '-ss', help="Print also short synthesis summary", is_flag=True, default=False)
@click.argument("method", type=click.Choice(
    ['onebyone', 'cegis', 'ar', 'hybrid', 'evo'], case_sensitive=False))
def paynt(
        project, sketch, properties, constants, method, short_summary
):
    print("This is Paynt version {}.".format(version()))

    # parse sketch
    if not os.path.isdir(project):
        raise ValueError(f"The project folder {project} is not a directory")
    sketch_path = os.path.join(project, sketch)
    properties_path = os.path.join(project, properties)
    sketch = Sketch(sketch_path, properties_path, constants)
    # TODO: differentiate between solvers

    # choose synthesis method
    if method == "onebyone":
        algorithm = Synthesizer(sketch)
    elif method == "cegis":
        raise NotImplementedError
    elif method == "ar":
        algorithm = SynthesizerAR(sketch)
    elif method == "hybrid":
        raise NotImplementedError
    else:
        assert None
    
    # synthesize
    algorithm.run()
    algorithm.print_stats(short_summary)


def main():
    setup_logger("paynt.log")
    paynt()


if __name__ == "__main__":
    main()
