from .synthesizer import _run_dtnest
from .task import DtNestTask
from ..result import DtResult
from ..factory import DtColoredMdpFactory


def synthesize(
    cmdp_factory_dt: DtColoredMdpFactory,
    dtnest_task_dt: DtNestTask,
    depth_fine_tuning: bool = True,
    allow_perturbations: bool = True,
    recompute_scheduler_perturbation: bool = True,
) -> DtResult:
    """API function to solve a given DtNestTask and DtColoredMdpFactory using the dtnest synthesizer. Returns paynt_result."""

    # TODO this is a bit hacky, should be refactored eventually so that the specification is passed in a cleaner way
    cmdp_factory_dt.task = dtnest_task_dt

    return _run_dtnest(
        cmdp_factory_dt,
        dtnest_task_dt.error_threshold,
        dtnest_task_dt.tree_depth,
        depth_fine_tuning,
        allow_perturbations,
        recompute_scheduler_perturbation,
        dtnest_task_dt.timeout,
    )
