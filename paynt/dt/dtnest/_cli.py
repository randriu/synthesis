'''
dtnest-synthesis CLI options, composed into paynt.cli.paynt_run via add_options([...]).
'''

import rich_click as click

_PANEL = "dtnest synthesis"

options = [
    click.option("--dtnest", is_flag=True, default=False, panel=_PANEL,
        help="use dtnest synthesizer for decision tree synthesis"),
    click.option("--dtnest-subtree-depth", default=7, type=int, panel=_PANEL,
        help="dtnest max subtree depth"),
    click.option("--dtnest-error-threshold", default=0.05, type=float, panel=_PANEL,
        help="dtnest error epsilon threshold"),
]
