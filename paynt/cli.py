from . import version

import paynt.api
import paynt.utils.timer
import paynt.utils.version_check
import paynt.parser.sketch

import paynt.pomdp
import paynt.dt._cli
import paynt.dt.dtnest._cli
import paynt.pomdp._cli
import paynt.pomdp.saynt._cli
import paynt.family._cli

import rich_click as click
import sys
import os
import cProfile, pstats

import logging
logger = logging.getLogger(__name__)


def add_options(options):
    ''' Standard click idiom for composing a decorator list built elsewhere (here, a feature's own _cli.py)
    onto a command function, applied in the same order as if the decorators had been written inline. '''
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func
    return _add_options


def setup_logger(log_path = None):
    ''' Setup routine for logging. '''

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    # root.setLevel(logging.INFO)

    # formatter = logging.Formatter('%(asctime)s %(threadName)s - %(name)s - %(levelname)s - %(message)s')
    formatter = logging.Formatter('%(asctime)s - %(filename)s:%(lineno)d - %(message)s')

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
@click.argument('project', type=click.Path(exists=True))
@click.option("--sketch", default="sketch.templ", show_default=True, panel="Model & specification loading",
    help="name of the sketch file in the project")
@click.option("--props", default="sketch.props", show_default=True, panel="Model & specification loading",
    help="name of the properties file in the project")
@click.option(
    "--constraint-bound", type=click.FLOAT, panel="Model & specification loading",
    help="bound for creating constrained POMDP for Cassandra models",
)

@click.option("--relative-error", type=click.FLOAT, default="0", show_default=True, panel="Synthesis",
    help="relative error for optimal synthesis")
@click.option("--optimum-threshold", type=click.FLOAT, panel="Synthesis",
    help="known optimum bound")
@click.option("--precision", type=click.FLOAT, default=1e-4, panel="Synthesis",
    help="model checking precision")
@click.option("--exact", is_flag=True, default=False, panel="Synthesis",
    help="use exact synthesis (very limited at the moment)")
@click.option("--timeout", type=int, panel="Synthesis",
    help="timeout (s)")
@click.option("--method",
    type=click.Choice(['onebyone', 'ar', 'cegis', 'hybrid']),
    default="ar", show_default=True, panel="Synthesis",
    help="synthesis method"
    )
@click.option("--disable-expected-visits", is_flag=True, default=False, panel="Synthesis",
    help="do not compute expected visits for the splitting heuristic")
@click.option(
    "--ce-generator", type=click.Choice(["dtmc", "mdp"]), default="dtmc", show_default=True, panel="Synthesis",
    help="counterexample generator",
)

@click.option("--fsc-synthesis", is_flag=True, default=False, panel="FSC synthesis (POMDP / Dec-POMDP / POSMG / family)",
    help="enable incremental synthesis of FSCs for a (Dec-)POMDP")
@click.option("--fsc-memory-size", default=1, show_default=True, panel="FSC synthesis (POMDP / Dec-POMDP / POSMG / family)",
    help="implicit memory size for (Dec-)POMDP FSCs")
@add_options(paynt.pomdp._cli.options)

@add_options(paynt.pomdp.saynt._cli.options)

@add_options(paynt.family._cli.options)

@add_options(paynt.dt._cli.options)

@add_options(paynt.dt.dtnest._cli.options)

@click.option("--export",
    type=click.Choice(['jani', 'drn', 'pomdp']), panel="Output",
    help="export the model to specified format and abort")
@click.option("--export-synthesis", type=click.Path(), default=None, panel="Output",
    help="base filename to output synthesis result")
@click.option("--profiling", is_flag=True, default=False, panel="Output",
    help="run profiling")

def paynt_run(
    project, sketch, props, relative_error, optimum_threshold, precision, exact, timeout,
    export,
    method,
    disable_expected_visits,
    fsc_synthesis, fsc_memory_size, posterior_aware,
    storm_pomdp, iterative_storm, get_storm_result, storm_options, prune_storm,
    use_storm_cutoffs, unfold_strategy_storm,
    export_synthesis,
    mdp_discard_unreachable_choices,
    tree_depth, tree_enumeration, tree_map_scheduler, add_dont_care_action,
    constraint_bound,
    dtnest, dtnest_subtree_depth, dtnest_error_threshold,
    ce_generator,
    profiling
):

    profiler = None
    if profiling:
        profiler = cProfile.Profile()
        profiler.enable()
    paynt.utils.timer.GlobalTimer.start(timeout)

    logger.info("This is Paynt version {}.".format(version()))
    paynt.utils.version_check.check_stormpy_compatibility()

    # Every option below that affects synthesis behavior (as opposed to model loading/parsing) is threaded through as a Task field. 
    # Sketch.load_sketch doesn't know the sketch's feature until it has parsed it, so task_kwargs
    # carries every feature's options at once; whichever Task subclass ends up being constructed picks out
    # only the keys it recognizes (see paynt.task.Task.from_specification).
    task_kwargs = dict(
        export_synthesis_filename_base=export_synthesis,
        conflict_generator_type=ce_generator,
        disable_expected_visits=disable_expected_visits,
        memory_size=fsc_memory_size,
        posterior_aware=posterior_aware,
        discard_unreachable_choices=mdp_discard_unreachable_choices,
        tree_depth=tree_depth,
        tree_enumeration=tree_enumeration,
        scheduler_path=tree_map_scheduler,
        add_dont_care_action=add_dont_care_action,
        max_subtree_depth=dtnest_subtree_depth,
        error_threshold=dtnest_error_threshold,
    )

    storm_control = None
    if storm_pomdp:
        storm_control = paynt.pomdp.saynt.StormPOMDPControl()
        storm_control.set_options(
            storm_options, get_storm_result, iterative_storm, use_storm_cutoffs,
            unfold_strategy_storm, prune_storm
        )

    sketch_path = os.path.join(project, sketch)
    properties_path = os.path.join(project, props)
    colored_mdp_factory, task = paynt.parser.sketch.Sketch.load_sketch(
        sketch_path, properties_path, export, relative_error, precision, constraint_bound, exact, task_kwargs=task_kwargs)
    synthesizer = paynt.api.get_synthesizer(colored_mdp_factory, method, fsc_synthesis, storm_control, dtnest)
    synthesizer.run(optimum_threshold)

    if profiling:
        profiler.disable()
        print_profiler_stats(profiler)

def print_profiler_stats(profiler):
    stats = pstats.Stats(profiler)
    NUM_LINES = 10

    logger.debug("cProfiler info:")
    stats.sort_stats('tottime').print_stats(NUM_LINES)

    logger.debug("percentage breakdown:")
    entries = [ (key,data[2]) for key,data in stats.stats.items()]
    entries = sorted(entries, key=lambda x : x[1], reverse=True)
    entries = entries[:NUM_LINES]
    for key,data in entries:
        module,line,method = key
        if module == "~":
            callee = method
        else:
            callee = f"{module}:{line}({method})"
        percentage = round(data / stats.total_tt * 100,1)
        percentage = str(percentage).ljust(4)
        print(f"{percentage} %  {callee}")

def main():
    setup_logger()
    paynt_run()


if __name__ == "__main__":
    main()
