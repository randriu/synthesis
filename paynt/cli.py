from . import version

import paynt.parser.sketch

import paynt.quotient
import paynt.quotient.pomdp
import paynt.quotient.storm_pomdp_control

import paynt.synthesizer.all_in_one
import paynt.synthesizer.synthesizer
import paynt.synthesizer.synthesizer_cegis
import paynt.synthesizer.policy_tree

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
@click.option("--relative-error", type=click.FLOAT, default="0", show_default=True,
    help="relative error for optimal synthesis")
@click.option("--discount-factor", type=click.FLOAT, default="1", show_default=True,
    help="discount factor")
@click.option("--optimum-threshold", type=click.FLOAT,
    help="known optimum bound")

@click.option("--export",
    type=click.Choice(['jani', 'drn', 'pomdp']),
    help="export the model to specified format and abort")

@click.option("--method",
    type=click.Choice(['onebyone', 'ar', 'cegis', 'hybrid', 'ar_multicore']),
    default="ar", show_default=True,
    help="synthesis method"
    )

@click.option("--incomplete-search", is_flag=True, default=False,
    help="use incomplete search during synthesis")
@click.option("--disable-expected-visits", is_flag=True, default=False,
    help="do not compute expected visits for the splitting heuristic")

@click.option("--fsc-synthesis", is_flag=True, default=False,
    help="enable incremental synthesis of FSCs for a POMDP")
@click.option("--pomdp-memory-size", default=1, show_default=True,
    help="implicit memory size for POMDP FSCs")
@click.option("--posterior-aware", is_flag=True, default=False,
    help="unfold MDP taking posterior observation of into account")

@click.option("--storm-pomdp", is_flag=True, default=False,
    help="enable running storm analysis for POMDPs to enhance FSC synthesis (supports AR only for now!)")
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

@click.option("--export-fsc-storm", type=click.Path(), default=None,
    help="path to output file for SAYNT belief FSC")
@click.option("--export-fsc-paynt", type=click.Path(), default=None,
    help="path to output file for SAYNT inductive FSC")
@click.option("--export-evaluation", type=click.Path(), default=None,
    help="base filename to output evaluation result")

@click.option(
    "--all-in-one", type=click.Choice(["sparse", "bdd"]), default=None, show_default=True,
    help="all in one MDP approach",
)

@click.option("--mdp-split-wrt-mdp", is_flag=True, default=False,
    help="# if set, MDP abstraction scheduler will be used for splitting, otherwise game abstraction scheduler will be used")
@click.option("--mdp-discard-unreachable-choices", is_flag=True, default=False,
    help="# if set, unreachable choices will be discarded from the splitting scheduler")
@click.option("--mdp-use-randomized-abstraction", is_flag=True, default=False,
    help="# if set, randomized abstraction guess-and-verify will be used instead of game abstraction;" +
    " MDP abstraction scheduler will be used for splitting"
)

@click.option(
    "--ce-generator", type=click.Choice(["dtmc", "mdp"]), default="dtmc", show_default=True,
    help="counterexample generator",
)
@click.option("--profiling", is_flag=True, default=False,
    help="run profiling")

def paynt_run(
    project, sketch, props, relative_error, discount_factor, optimum_threshold,
    export,
    method,
    incomplete_search, disable_expected_visits,
    fsc_synthesis, pomdp_memory_size, posterior_aware,
    storm_pomdp, iterative_storm, get_storm_result, storm_options, prune_storm,
    use_storm_cutoffs, unfold_strategy_storm,
    export_fsc_storm, export_fsc_paynt, export_evaluation,
    all_in_one,
    mdp_split_wrt_mdp, mdp_discard_unreachable_choices, mdp_use_randomized_abstraction,
    ce_generator,
    profiling
):
    profiler = None
    if profiling:
        profiler = cProfile.Profile()
        profiler.enable()

    logger.info("This is Paynt version {}.".format(version()))

    # set CLI parameters
    paynt.synthesizer.synthesizer.Synthesizer.incomplete_search = incomplete_search
    paynt.quotient.quotient.Quotient.compute_expected_visits = not disable_expected_visits
    paynt.synthesizer.synthesizer_cegis.SynthesizerCEGIS.conflict_generator_type = ce_generator
    paynt.quotient.pomdp.PomdpQuotient.initial_memory_size = pomdp_memory_size
    paynt.quotient.pomdp.PomdpQuotient.posterior_aware = posterior_aware

    paynt.synthesizer.policy_tree.SynthesizerPolicyTree.split_wrt_mdp_scheduler = mdp_split_wrt_mdp
    paynt.synthesizer.policy_tree.SynthesizerPolicyTree.discard_unreachable_choices = mdp_discard_unreachable_choices
    paynt.synthesizer.policy_tree.SynthesizerPolicyTree.use_randomized_abstraction = mdp_use_randomized_abstraction

    storm_control = None
    if storm_pomdp:
        storm_control = paynt.quotient.storm_pomdp_control.StormPOMDPControl()
        storm_control.set_options(
            storm_options, get_storm_result, iterative_storm, use_storm_cutoffs,
            unfold_strategy_storm, prune_storm, export_fsc_storm, export_fsc_paynt
        )

    sketch_path = os.path.join(project, sketch)
    properties_path = os.path.join(project, props)
    if all_in_one is None:
        quotient = paynt.parser.sketch.Sketch.load_sketch(sketch_path,  properties_path, export, relative_error, discount_factor)
        synthesizer = paynt.synthesizer.synthesizer.Synthesizer.choose_synthesizer  (quotient, method, fsc_synthesis, storm_control)
        synthesizer.run(optimum_threshold, export_evaluation)
    else:
        all_in_one_program, specification, family = paynt.parser.sketch.Sketch.load_sketch_as_all_in_one(sketch_path, properties_path)
        all_in_one_analysis = paynt.synthesizer.all_in_one.AllInOne(all_in_one_program, specification, all_in_one, family)
        all_in_one_analysis.run()
    if profiling:
        profiler.disable()
        stats = profiler.create_stats()
        pstats.Stats(profiler).sort_stats('tottime').print_stats(20)


def main():
    setup_logger()
    paynt_run()


if __name__ == "__main__":
    main()
