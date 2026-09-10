"""
Decision-tree-synthesis CLI options, composed into paynt.cli.paynt_run via add_options([...]).
Kept as a plain list of decorators (not applied here) so importing this module at CLI-startup stays cheap
regardless of whether the loaded sketch actually turns out to be DT-shaped.
"""

import rich_click as click

_PANEL = "Decision tree synthesis"

options = [
    click.option("--tree-depth", default=0, type=int, panel=_PANEL, help="decision tree synthesis: tree depth"),
    click.option(
        "--tree-enumeration",
        is_flag=True,
        default=False,
        panel=_PANEL,
        help="decision tree synthesis: if set, all trees of size at most tree_depth will be enumerated",
    ),
    click.option(
        "--tree-map-scheduler",
        type=click.Path(),
        default=None,
        panel=_PANEL,
        help="decision tree synthesis: path to a scheduler to be mapped to a decision tree",
    ),
    click.option(
        "--add-dont-care-action",
        is_flag=True,
        default=True,
        panel=_PANEL,
        help="decision tree synthesis: # if set, an explicit action executing a random choice of an available action will be added to each state",
    ),
]
