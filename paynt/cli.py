import paynt.quotient.mdp_family
from . import version

import paynt.utils.timer
import paynt.parser.sketch

import paynt.quotient.quotient
import paynt.quotient.pomdp
import paynt.quotient.decpomdp
import paynt.quotient.posmg
import paynt.quotient.storm_pomdp_control
import paynt.quotient.mdp

import paynt.synthesizer.synthesizer
import paynt.synthesizer.synthesizer_cegis
import paynt.synthesizer.policy_tree
import paynt.synthesizer.decision_tree

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
@click.option("--sketch", default="sketch.templ", show_default=True,
    help="name of the sketch file in the project")
@click.option("--props", default="sketch.props", show_default=True,
    help="name of the properties file in the project")
@click.option("--relative-error", type=click.FLOAT, default="0", show_default=True,
    help="relative error for optimal synthesis")
@click.option("--optimum-threshold", type=click.FLOAT,
    help="known optimum bound")
@click.option("--precision", type=click.FLOAT, default=1e-4,
    help="model checking precision")
@click.option("--exact", is_flag=True, default=False,
    help="use exact synthesis (very limited at the moment)")
@click.option("--timeout", type=int,
    help="timeout (s)")

@click.option("--export",
    type=click.Choice(['jani', 'drn', 'pomdp']),
    help="export the model to specified format and abort")

@click.option("--method",
    type=click.Choice(['onebyone', 'ar', 'cegis', 'hybrid', 'ar_multicore']),
    default="ar", show_default=True,
    help="synthesis method"
    )

@click.option("--disable-expected-visits", is_flag=True, default=False,
    help="do not compute expected visits for the splitting heuristic")

@click.option("--fsc-synthesis", is_flag=True, default=False,
    help="enable incremental synthesis of FSCs for a (Dec-)POMDP")
@click.option("--fsc-memory-size", default=1, show_default=True,
    help="implicit memory size for (Dec-)POMDP FSCs")
@click.option("--posterior-aware", is_flag=True, default=False,
    help="unfold MDP taking posterior observation of into account")

@click.option("--storm-pomdp", is_flag=True, default=False,
    help="enable running belief analysis in STorm to enhance FSC synthesis for POMDPs (AR only)")
@click.option(
    "--storm-options",
    default="cutoff",
    type=click.Choice(["cutoff", "clip2", "clip4", "small", "refine", "overapp", "2mil", "5mil", "10mil", "20mil", "30mil", "50mil"]),
    show_default=True,
    help="run Storm using pre-defined settings and use the result to enhance PAYNT. Can only be used together with --storm-pomdp flag")
@click.option("--iterative-storm", nargs=3, type=int, show_default=True, default=None,
    help="runs the iterative PAYNT/Storm integration. Arguments timeout, paynt_timeout, storm_timeout. Can only be used together with --storm-pomdp flag")
@click.option("--get-storm-result", default=None, type=int,
    help="runs PAYNT for given amount of seconds and returns Storm result using FSC at cutoff. If time is 0 returns pure Storm result. Can only be used together with --storm-pomdp flag")
@click.option("--prune-storm", is_flag=True, default=False,
    help="only explore the main family suggested by Storm in each iteration. Can only be used together with --storm-pomdp flag. Can only be used together with --storm-pomdp flag")
@click.option("--use-storm-cutoffs", is_flag=True, default=False,
    help="use storm randomized scheduler cutoffs are used during the prioritization of families. Can only be used together with --storm-pomdp flag. Can only be used together with --storm-pomdp flag")
@click.option(
    "--unfold-strategy-storm",
    default="storm",
    type=click.Choice(["storm", "paynt", "cutoff"]),
    show_default=True,
    help="specify memory unfold strategy. Can only be used together with --storm-pomdp flag")

@click.option("--export-synthesis", type=click.Path(), default=None,
    help="base filename to output synthesis result")

@click.option("--mdp-discard-unreachable-choices", is_flag=True, default=False,
    help="if set, unreachable choices will be discarded from the splitting scheduler")

@click.option("--tree-depth", default=0, type=int,
    help="decision tree synthesis: tree depth")
@click.option("--tree-enumeration", is_flag=True, default=False,
    help="decision tree synthesis: if set, all trees of size at most tree_depth will be enumerated")
@click.option("--tree-map-scheduler", type=click.Path(), default=None,
    help="decision tree synthesis: path to a scheduler to be mapped to a decision tree")
@click.option("--add-dont-care-action", is_flag=True, default=False,
    help="decision tree synthesis: # if set, an explicit action executing a random choice of an available action will be added to each state")

@click.option(
    "--constraint-bound", type=click.FLOAT, help="bound for creating constrained POMDP for Cassandra models",
)

@click.option(
    "--ce-generator", type=click.Choice(["dtmc", "mdp"]), default="dtmc", show_default=True,
    help="counterexample generator",
)
@click.option("--profiling", is_flag=True, default=False,
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
    ce_generator,
    profiling
):

    profiler = None
    if profiling:
        profiler = cProfile.Profile()
        profiler.enable()
    paynt.utils.timer.GlobalTimer.start(timeout)

    logger.info("This is Paynt version {}.".format(version()))

    # set CLI parameters
    paynt.quotient.quotient.Quotient.disable_expected_visits = disable_expected_visits
    paynt.synthesizer.synthesizer.Synthesizer.export_synthesis_filename_base = export_synthesis
    paynt.synthesizer.synthesizer_cegis.SynthesizerCEGIS.conflict_generator_type = ce_generator
    paynt.quotient.pomdp.PomdpQuotient.initial_memory_size = fsc_memory_size
    paynt.quotient.pomdp.PomdpQuotient.posterior_aware = posterior_aware
    paynt.quotient.decpomdp.DecPomdpQuotient.initial_memory_size = fsc_memory_size
    paynt.quotient.posmg.PosmgQuotient.initial_memory_size = fsc_memory_size

    paynt.quotient.mdp_family.MdpFamilyQuotient.initial_memory_size = fsc_memory_size

    paynt.synthesizer.policy_tree.SynthesizerPolicyTree.discard_unreachable_choices = mdp_discard_unreachable_choices

    paynt.synthesizer.decision_tree.SynthesizerDecisionTree.tree_depth = tree_depth
    paynt.synthesizer.decision_tree.SynthesizerDecisionTree.tree_enumeration = tree_enumeration
    paynt.synthesizer.decision_tree.SynthesizerDecisionTree.scheduler_path = tree_map_scheduler
    paynt.quotient.mdp.MdpQuotient.add_dont_care_action = add_dont_care_action

    storm_control = None
    if storm_pomdp:
        storm_control = paynt.quotient.storm_pomdp_control.StormPOMDPControl()
        storm_control.set_options(
            storm_options, get_storm_result, iterative_storm, use_storm_cutoffs,
            unfold_strategy_storm, prune_storm
        )

    sketch_path = os.path.join(project, sketch)
    properties_path = os.path.join(project, props)
    quotient = paynt.parser.sketch.Sketch.load_sketch(sketch_path, properties_path, export, relative_error, precision, constraint_bound, exact)
    synthesizer = paynt.synthesizer.synthesizer.Synthesizer.choose_synthesizer(quotient, method, fsc_synthesis, storm_control)
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
