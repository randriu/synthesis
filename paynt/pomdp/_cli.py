"""
POMDP-synthesis CLI options, composed into paynt.cli.paynt_run via add_options([...]).
"""

import rich_click as click

_PANEL = "POMDP synthesis"

options = [
    click.option("--posterior-aware", is_flag=True, default=False, panel=_PANEL, help="unfold MDP taking posterior observation of into account"),
]
