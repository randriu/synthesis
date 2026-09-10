from __future__ import annotations

from typing import Any

from .synthesizer import _choose_solver_for_dt_task, _run_dt_map_scheduler, _run_dtpaynt
from .task import DtTask
from .result import DtResult
from .factory import DtColoredMdpFactory


def synthesize(cmdp_factory_dt: DtColoredMdpFactory, paynt_task_dt: DtTask, use_solver: str | None = None) -> DtResult:
    """API function to solve a given DtTask and DtColoredMdpFactory. Optional use_solver parameter can force
    a specific solver to be used. Returns paynt_result."""

    # TODO this is a bit hacky, should be refactored eventually so that the specification is passed in a cleaner way
    cmdp_factory_dt.task = paynt_task_dt

    if use_solver is None:
        use_solver = _choose_solver_for_dt_task(paynt_task_dt)

    assert use_solver in ["dtmap", "dtpaynt"], f"Invalid solver choice: {use_solver}. Valid options are 'dtmap' and 'dtpaynt'."

    if use_solver == "dtmap":
        return _run_dt_map_scheduler(cmdp_factory_dt, paynt_task_dt.scheduler_to_map, paynt_task_dt.tree_depth)
    return _run_dtpaynt(cmdp_factory_dt, paynt_task_dt.tree_depth, paynt_task_dt.timeout)


def create_task(properties: list[Any], tree_depth: int) -> DtTask:
    """API function to create a DtTask from a list of StormPy properties and a tree depth."""

    raise NotImplementedError("API not yet implemented.")


def create_colored_mdp_factory(model: Any) -> DtColoredMdpFactory:
    """API function to create a DtColoredMdpFactory from a StormPy model."""

    raise NotImplementedError("API not yet implemented.")
