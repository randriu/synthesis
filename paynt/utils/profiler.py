import time


class Timer:
    def __init__(self):
        self.running = False
        self.timer = None   # last timestamp
        self.time = 0       # total time measured

    @staticmethod
    def timestamp():
        return time.perf_counter()

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

    percentage_filter = 5

    @staticmethod
    def initialize():
        Profiler.timers = {}        # dictionary of all timers
        Profiler.running = None     # currently running timer
        Profiler.paused = []        # stack of paused timers
        
        Profiler.timer_total = Timer()
        Profiler.timer_total.start()


    @staticmethod
    def is_running():
        return Profiler.running is not None

    @staticmethod
    def stop():
        if not Profiler.is_running():
            return
        Profiler.running.stop()
        Profiler.running = None

    @staticmethod
    def pause():
        if not Profiler.is_running():
            return
        Profiler.running.stop()
        Profiler.paused += [Profiler.running]
        Profiler.running = None

    @staticmethod
    def resume():
        Profiler.stop()
        if Profiler.paused:
            Profiler.running = Profiler.paused.pop(-1)
            Profiler.running.start()
    
    @staticmethod
    def start(timer_name = "-"):
        if Profiler.is_running():
            Profiler.pause()
        Profiler.timers[timer_name] = Profiler.timers.get(timer_name, Timer())
        Profiler.timers[timer_name].start()
        Profiler.running = Profiler.timers[timer_name]

    @staticmethod
    def print_all():
        time_total = Profiler.timer_total.read()
        covered = 0
        print("profiling report:")
        for timer_name, timer in Profiler.timers.items():
            t = timer.read()
            covered += t
            percentage = round(t / time_total * 100, 1)
            if percentage > Profiler.percentage_filter:
                print(f'> {timer_name} : {percentage}%')
        print(f"> covered {round(covered / time_total * 100, 0)}% of {round(time_total, 1)} sec")

    @staticmethod
    def print():
        Profiler.stop()
        Profiler.timer_total.stop()
        Profiler.print_all()


