
class SynthetiserStats:
    def __init__(self):
        self.iterations = 0
        self.total_time = None
        self.qualitative_iterations = 0
        self.non_trivial_cex = 0
        self.design_space_size = None
        self.solver_times = []
        self.clause_adding_times = []

    @property
    def total_solver_time(self):
        return self.total_solver_clause_adding_time + self.total_solver_analysis_time

    @property
    def total_solver_analysis_time(self):
        return sum(self.solver_times)

    @property
    def total_solver_clause_adding_time(self):
        return sum(self.clause_adding_times)

class CAStats:
    def __init__(self, cex_stats):
        self.iterations = cex_stats.iterations
        self.setup_time = cex_stats.setup_time.count()/1000
        self.model_checking_time = cex_stats.model_checking_time.count()/1000
        self.analysis_time = cex_stats.analysis_time.count()/1000
        self.solver_time = cex_stats.solver_time.count()/1000
        self.cut_time = cex_stats.cut_time.count()/1000

    @property
    def total_time(self):
        return self.setup_time + self.model_checking_time + self.analysis_time + self.solver_time



class Stats:
    def __init__(self):
        self.conflict_analysis_calls = 0
        self.conflict_analysis_time = 0
        self._property_stats = dict()
        self._optimality_stats = None
        self._conflict_analysis_stats = []
        self._model_building_time = []
        self._model_sizes = []
        self.qualitative_model_checking_calls = 0
        self.qualitative_model_checking_time = 0
        self.quantitative_model_checking_calls = 0
        self.quantitative_model_checking_time = 0

    def report_conflict_analysis_stats(self, ca):
        self._conflict_analysis_stats.append(CAStats(ca))

    def _get_property_stats(self, property):
        if property.name not in self._property_stats:
            return self._optimality_stats
        else:
            return self._property_stats[property.name]

    def initialize_properties_and_holes(self, properties, holes):
        for p in properties:
            self._property_stats[p.property.name] = PropertyStats(holes)
            if p.prerequisite_property:
                self._property_stats[p.prerequisite_property.name] = PropertyStats(holes)
        self._optimality_stats = PropertyStats(holes)

    def report_model_building(self, time, size):
        self._model_building_time.append(time)
        self._model_sizes.append(size)

    def report_conflict_details(self, property, time, conflicts):
        self.conflict_analysis_calls = self.conflict_analysis_calls + 1
        self.conflict_analysis_time = self.conflict_analysis_time + time
        self._get_property_stats(property).report_conflict_details(conflicts, time)

    def report_model_checking(self, property, time, conflict):
        self.quantitative_model_checking_calls += 1
        self.quantitative_model_checking_time += time
        if conflict:
            self._get_property_stats(property).report_conflict(time)
        else:
            self._get_property_stats(property).report_no_conflict(time)

    @property
    def model_building_time(self):
        return sum(self._model_building_time)

    @property
    def model_building_calls(self):
        return len(self._model_sizes)

    @property
    def average_model_building_time(self):
        return self.model_building_time/self.model_building_calls

    @property
    def cumulative_model_size(self):
        return sum(self._model_sizes)

    @property
    def max_model_size(self):
        return max(self._model_sizes)

    @property
    def min_model_size(self):
        return min(self._model_sizes)

    @property
    def average_model_size(self):
        return self.cumulative_model_size/self.model_building_calls

    @property
    def total_conflict_analysis_setup_time(self):
        return sum([cex_generator_stats.setup_time for cex_generator_stats in self._conflict_analysis_stats])

    @property
    def total_conflict_analysis_mc_time(self):
        return sum([cex_generator_stats.model_checking_time for cex_generator_stats in self._conflict_analysis_stats])

    @property
    def total_conflict_analysis_iterations(self):
        return sum([cex_generator_stats.iterations for cex_generator_stats in self._conflict_analysis_stats])

    @property
    def total_conflict_analysis_solver_time(self):
        return sum([cex_generator_stats.solver_time for cex_generator_stats in self._conflict_analysis_stats])

    @property
    def total_conflict_analysis_analysis_time(self):
        return sum([cex_generator_stats.analysis_time for cex_generator_stats in self._conflict_analysis_stats])

    @property
    def total_conflict_analysis_cut_time(self):
        return sum([cex_generator_stats.cut_time for cex_generator_stats in self._conflict_analysis_stats])

    def print_property_stats(self):
        for prop, stats in self._property_stats.items():
            print(prop)
            stats.print()

    @property
    def property_stats(self):
        return self._property_stats.values()


class PropertyStats:
    def __init__(self, holes):
        self._nr_holes = len(holes)
        self._violations = 0
        self._model_checking_times = []
        self._conflict_analysis_times = []
        self._conflict_sizes = []
        self._hole_relevant = dict([(hole, 0) for hole in holes])

    def report_conflict_details(self, conflicts, time):
        print("report {}".format(conflicts))
        self._conflict_sizes.append([])
        for conflict in conflicts:
            self._conflict_sizes[-1].append(len(conflict))

        self._conflict_analysis_times.append(time)
        for conflict in conflicts:
            for hole in conflict:
                self._hole_relevant[hole] = self._hole_relevant[hole] + 1

    def report_no_conflict(self, time):
        self._model_checking_times.append(time)
        self._conflict_size = None
        self._conflict_sizes.append(None)
        self._conflict_analysis_times.append(None)

    def report_conflict(self, time):
        self._violations += 1
        self._model_checking_times.append(time)

    def histogram(self):
        histogram = dict()
        for i in range(self._nr_holes + 1):
            histogram[i] = 0
        for csets in self._conflict_sizes:
            if csets is not None:
                for cs in csets:
                    histogram[cs] += 1
        return histogram

    @property
    def relevant_holes(self):
        return self._hole_relevant

    def print(self):
        print("Violations: {}".format(self._violations))
        histogram = self.histogram()
        print("Violation of size:")
        for i, v in histogram.items():
            print("{}: {}".format(i,v))
        print("Holes relevant")
        for h, v in self._hole_relevant.items():
            print("{}: {}".format(h, v))



    @property
    def average_conflict():
        return sum(self._conflict_sizes) / self._violations