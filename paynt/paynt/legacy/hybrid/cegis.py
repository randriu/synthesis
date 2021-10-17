import logging

from ..family_checkers.cegis import Synthesiser
from .helpers import readable_assignment
from .statistic import Statistic

logger = logging.getLogger(__name__)


class CEGISChecker(Synthesiser):
    """CEGIS wrapper."""

    def __init__(self, *args):
        super().__init__(*args)
        self.statistic = None

    def run(self, short_summary):
        formulae = [property_obj.raw_formula for property_obj in self._verifier.properties]
        self.statistic = Statistic(
            "CEGIS", formulae, len(self.holes), self._optimality_setting, short_summary=short_summary
        )
        _, assignment, optimal_value = self.run_feasibility()
        assignment = {k: [v] for (k, v) in assignment.items()} if assignment is not None else None
        if assignment is not None:
            logger.info(f"Found satisfying assignment: {readable_assignment(assignment)}")
        self.statistic.finished(
            assignment, (0, self.stats.iterations), optimal_value, self.stats.design_space_size, 0, 0, 0,
            self.verifier_stats.average_model_size,
            self.verifier_stats.qualitative_model_checking_calls + self.verifier_stats.quantitative_model_checking_calls
        )
