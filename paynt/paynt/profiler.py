import time


class Timer:
    def __init__(self):
        self.running = False
        self.timer = None
        self.time = 0

    @staticmethod
    def timestamp():
        return time.process_time()  # cpu time

    def reset(self):
        self.__init__()

    def start(self):
        if self.running:
            return
        self.timer = self.timestamp()
        self.running = True

    def stop(self):
        if not self.running:
            return
        self.time += self.timestamp() - self.timer
        self.timer = None
        self.running = False

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def read(self):
        if not self.running:
            return self.time
        else:
            return self.time + (self.timestamp() - self.timer)


class Profiler:

    labels = []
    ce_stats = []
    timer_total = None
    ce_count = None
    timers = None

    @staticmethod
    def initialize():
        Profiler.timers = {}
        Profiler.started_last = None
        Profiler.timer_total = Timer()
        Profiler.timer_total.start()

        Profiler.labels = ["TODO", "MDP", "DTMC", "sub-DTMC", "CE"]
        Profiler.ce_count = 0
        Profiler.ce_stats = [0] * len(Profiler.labels)

    @staticmethod
    def stop():
        if Profiler.started_last is None:
            return
        Profiler.started_last.stop()
        Profiler.started_last = None

    @staticmethod
    def start(timer_name):
        Profiler.stop()
        Profiler.timers[timer_name] = Profiler.timers.get(timer_name, Timer())
        Profiler.timers[timer_name].start()
        Profiler.started_last = Profiler.timers[timer_name]

    @staticmethod
    def add_ce_stats(ce_stats):
        Profiler.ce_stats[0] += ce_stats[0]
        for i in range(1, len(ce_stats)):
            Profiler.ce_stats[i] = (Profiler.ce_stats[i] * Profiler.ce_count + ce_stats[i]) / (Profiler.ce_count + 1)
        Profiler.ce_count += 1

    @staticmethod
    def print_base():
        time_total = Profiler.timer_total.read()
        covered = 0
        for timer_name, timer in Profiler.timers.items():
            t = timer.read()
            covered += t
            print(f'> {timer_name} : {round(t / time_total * 100, 0)}%')
        print(f"> covered {round(covered / time_total * 100, 0)}% of {round(time_total, 1)} sec")

    @staticmethod
    def print_ce():
        stats = Profiler.ce_stats
        print("> ---")
        print("> storm stats:")

        [print(f"> {Profiler.labels[i]}: {round(stats[i] * 100, 0)}%") for i in range(1, len(stats))]

        covered = 100 * sum([stats[i] for i in range(1, len(stats))])
        print(f"> covered {round(covered, 0):g}% of {round(stats[0] / 1000.0, 1)} sec")
        print("> ---")

    @staticmethod
    def print():
        Profiler.stop()
        Profiler.timer_total.stop()

        # Profiler.print_ce()
        Profiler.print_base()


