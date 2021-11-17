import time


class Timer:
    def __init__(self):
        self.running = False
        self.timer = None   # last timestamp
        self.time = 0       # total time measured

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

    def read(self):
        if not self.running:
            return self.time
        else:
            return self.time + (self.timestamp() - self.timer)


class Profiler:

    @staticmethod
    def initialize():
        Profiler.running = None
        Profiler.timers = {}
        Profiler.timer_total = Timer()
        Profiler.timer_total.start()

    @staticmethod
    def stop():
        if Profiler.running is None:
            return
        Profiler.running.stop()
        Profiler.running = None

    @staticmethod
    def start(timer_name):
        Profiler.stop()
        Profiler.timers[timer_name] = Profiler.timers.get(timer_name, Timer())
        Profiler.timers[timer_name].start()
        Profiler.running = Profiler.timers[timer_name]

    @staticmethod
    def print_all():
        time_total = Profiler.timer_total.read()
        covered = 0
        for timer_name, timer in Profiler.timers.items():
            t = timer.read()
            covered += t
            print(f'> {timer_name} : {round(t / time_total * 100, 0)}%')
        print(f"> covered {round(covered / time_total * 100, 0)}% of {round(time_total, 1)} sec")

    @staticmethod
    def print():
        Profiler.stop()
        Profiler.timer_total.stop()
        Profiler.print_all()


