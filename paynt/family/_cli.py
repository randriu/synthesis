"""
family-of-environments-synthesis CLI options, composed into paynt.cli.paynt_run via add_options([...]).
"""

import rich_click as click

_PANEL = "Family-of-environments synthesis"

options = [
    click.option(
        "--mdp-discard-unreachable-choices",
        is_flag=True,
        default=False,
        panel=_PANEL,
        help="if set, unreachable choices will be discarded from the splitting scheduler",
    ),
]
