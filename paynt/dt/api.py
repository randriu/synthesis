

from .synthesizer import _choose_solver_for_dt_task, _run_dt_map_scheduler, _run_dtpaynt
from .task import DtTask
from .result import DtResult
from .factory import DtColoredMdpFactory


def synthesize(cmdp_factory_dt : DtColoredMdpFactory, paynt_task_dt : DtTask, use_solver : str | None = None) -> DtResult:
    """API function to solve a given DtTask and DtColoredMdpFactory. Optional use_solver parameter can force a specific solver to be used. Returns paynt_result."""

    cmdp_factory_dt.specification = paynt_task_dt.pctl_task # TODO this is a bit hacky, should be refactored eventually so that the specification is passed in a cleaner way

    if use_solver is None:
        use_solver = _choose_solver_for_dt_task(paynt_task_dt)

    assert use_solver in ["dtmap", "dtpaynt"], f"Invalid solver choice: {use_solver}. Valid options are 'dtmap' and 'dtpaynt'."

    if use_solver == "dtmap":
        return _run_dt_map_scheduler(cmdp_factory_dt, paynt_task_dt.scheduler_to_map, paynt_task_dt.tree_depth)
    elif use_solver == "dtpaynt":
        return _run_dtpaynt(cmdp_factory_dt, paynt_task_dt.tree_depth)
    

def create_task(properties, tree_depth):
    """API function to create a DtTask from a list of StormPy properties and a tree depth."""

    raise NotImplementedError("API not yet implemented.")


def create_colored_mdp_factory(model):
    """API function to create a DtColoredMdpFactory from a StormPy model."""

    raise NotImplementedError("API not yet implemented.")