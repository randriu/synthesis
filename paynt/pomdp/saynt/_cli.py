'''
SAYNT (Storm-guided POMDP synthesis) CLI options, composed into paynt.cli.paynt_run via add_options([...]).
'''

import rich_click as click

_PANEL = "SAYNT (Storm-guided POMDP synthesis)"

options = [
    click.option("--storm-pomdp", is_flag=True, default=False, panel=_PANEL,
        help="enable running belief analysis in STorm to enhance FSC synthesis for POMDPs (AR only)"),
    click.option(
        "--storm-options",
        default="cutoff",
        type=click.Choice(["cutoff", "clip2", "clip4", "small", "refine", "overapp", "2mil", "5mil", "10mil", "20mil", "30mil", "50mil"]),
        show_default=True,
        panel=_PANEL,
        help="run Storm using pre-defined settings and use the result to enhance PAYNT. Can only be used together with --storm-pomdp flag"),
    click.option("--iterative-storm", nargs=3, type=int, show_default=True, default=None, panel=_PANEL,
        help="runs the iterative PAYNT/Storm integration. Arguments timeout, paynt_timeout, storm_timeout. Can only be used together with --storm-pomdp flag"),
    click.option("--get-storm-result", default=None, type=int, panel=_PANEL,
        help="runs PAYNT for given amount of seconds and returns Storm result using FSC at cutoff. If time is 0 returns pure Storm result. Can only be used together with --storm-pomdp flag"),
    click.option("--prune-storm", is_flag=True, default=False, panel=_PANEL,
        help="only explore the main parameter subspace suggested by Storm in each iteration. Can only be used together with --storm-pomdp flag. Can only be used together with --storm-pomdp flag"),
    click.option("--use-storm-cutoffs", is_flag=True, default=False, panel=_PANEL,
        help="use storm randomized scheduler cutoffs are used during the prioritization of families. Can only be used together with --storm-pomdp flag. Can only be used together with --storm-pomdp flag"),
    click.option(
        "--unfold-strategy-storm",
        default="storm",
        type=click.Choice(["storm", "paynt", "cutoff"]),
        show_default=True,
        panel=_PANEL,
        help="specify memory unfold strategy. Can only be used together with --storm-pomdp flag"),
]
