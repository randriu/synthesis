from .ar import ARChecker
from .cegis import CEGISChecker
from .enumeration import EnumerationChecker
from .integrated_checker import IntegratedChecker

STAGE_SCORE_LIMIT = 99999


class Hybrid:
    """Entry point: execution setup."""

    def __init__(
            self, backward_cuts, sketch_path, allowed_path, property_path, optimality_path,
            constants, restrictions, restriction_path, regime, short_summary, ce_quality, ce_maxsat
    ):

        self.sketch_path = sketch_path
        self.allowed_path = allowed_path
        self.property_path = property_path
        self.optimality_path = optimality_path
        self.constants = constants
        self.restrictions = restrictions
        self.restriction_path = restriction_path
        self.short_summary = short_summary
        self.backward_cuts = backward_cuts

        IntegratedChecker.ce_quality = ce_quality
        IntegratedChecker.ce_maxsat = ce_maxsat
        IntegratedChecker.stage_score_limit = STAGE_SCORE_LIMIT
        stats = []

        if regime == 0:
            stats.append(self.run_algorithm(EnumerationChecker))
        elif regime == 1:
            stats.append(self.run_algorithm(CEGISChecker))
        elif regime == 2:
            stats.append(self.run_algorithm(ARChecker))
        elif regime == 3:
            stats.append(self.run_algorithm(IntegratedChecker))
        else:
            assert None

        print("\n")
        for stat in stats:
            print(stat)

    def run_algorithm(self, algorithm_class):
        print("\n\n\n")
        print(algorithm_class.__name__)
        algorithm = algorithm_class()
        algorithm.load_sketch(
            self.sketch_path, self.property_path, optimality_path=self.optimality_path, constant_str=self.constants
        )
        algorithm.load_template_definitions(self.allowed_path)
        if self.restrictions:
            algorithm.load_restrictions(self.restriction_path)
        algorithm.initialise()
        algorithm.run(self.short_summary)
        return algorithm.statistic
