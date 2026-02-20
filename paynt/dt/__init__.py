__version__ = "unknown"

try:
    from .._version import __version__
except ImportError:
    # We're running in a tree that doesn't have a _version.py, so we don't know what our version is.
    pass

def version():
    return __version__

from .task_dt import TaskDT
from .cmdp_factory_dt import ColoredMdpFactoryDT
from .solvers_dt import SolversDT, _choose_solver_for_dt_task, _run_dt_map_scheduler, _run_dtpaynt

import logging
logger = logging.getLogger(__name__)



def create_task_dt(properties, tree_depth):
    """API function to create a TaskDT from a list of StormPy properties and a tree depth."""

    import paynt.verification.property
    paynt.verification.property.Property.initialize(False)
    properties = [paynt.verification.property.construct_property(p, 0) for p in properties]
    specification = paynt.verification.property.Specification(properties)

    return TaskDT(specification, tree_depth)


def create_colored_mdp_factory_dt(model):
    """API function to create a ColoredMdpFactoryDT from a StormPy model."""

    import paynt.parser.sketch
    paynt.parser.sketch.make_rewards_action_based(model) # needed for quotient MDP initialization
    ColoredMdpFactoryDT.add_dont_care_action = True # TODO this should be made into default bahviour I think

    return ColoredMdpFactoryDT(model)


def solve_dt(cmdp_factory_dt, paynt_task_dt, use_solver=None):
    """API function to solve a given TaskDT and ColoredMdpFactoryDT. Optional use_solver parameter can force a specific solver to be used. Returns paynt_result."""

    cmdp_factory_dt.specification = paynt_task_dt.pctl_task # TODO this is a bit hacky, should be refactored eventually so that the specification is passed in a cleaner way

    if use_solver is None:
        use_solver = _choose_solver_for_dt_task(paynt_task_dt)

    assert use_solver in ["dtmap", "dtpaynt"], f"Invalid solver choice: {use_solver}. Valid options are 'dtmap' and 'dtpaynt'."

    if use_solver == "dtmap":
        return _run_dt_map_scheduler(cmdp_factory_dt, paynt_task_dt.scheduler_to_map, paynt_task_dt.tree_depth)
    elif use_solver == "dtpaynt":
        return _run_dtpaynt(cmdp_factory_dt, paynt_task_dt.tree_depth)

    


