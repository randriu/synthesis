import time
import psutil
import os


class Timer:

    def __init__(self, time_limit_seconds=None):
        self.running = False
        self.last_timestamp = None
        self.time = 0 # total time measured
        self.time_limit_seconds = time_limit_seconds

    @staticmethod
    def timestamp():
        return time.perf_counter()

    def reset(self):
        self.__init__()

    def start(self):
        if self.running:
            return
        self.last_timestamp = self.timestamp()
        self.running = True

    def stop(self):
        if not self.running:
            return
        self.time += self.timestamp() - self.last_timestamp
        self.last_timestamp = None
        self.running = False

    def read(self):
        if not self.running:
            return self.time
        else:
            return self.time + (self.timestamp() - self.last_timestamp)

    def time_limit_reached(self):
        return self.time_limit_seconds is not None and self.read() > self.time_limit_seconds


class GlobalTimer:

    global_timer = None

    @classmethod
    def start(cls, time_limit_seconds=None):
        cls.global_timer = Timer(time_limit_seconds)
        cls.global_timer.start()

    @classmethod
    def read(cls):
        return cls.global_timer.read()

    @classmethod
    def time_limit_reached(cls):
        return cls.global_timer is not None and cls.global_timer.time_limit_reached()


class GlobalMemoryLimit:

    memory_limit_mb = None

    @classmethod
    def limit_reached(cls):
        process = psutil.Process(os.getpid())
        allocated_mb = process.memory_info().rss / (1024 * 1024)
        return cls.memory_limit_mb is not None and allocated_mb > cls.memory_limit_mb
