import time

class Timer:
    def __init__(self):
        self.reset()

    def reset(self):
        self.running = False
        self.timer = None        
        self.time = 0

    def timestamp(self):
        return time.process_time()  # cpu time

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
    
    def initialize():
        Profiler.timers = dict()
        Profiler.started_last = None
        Profiler.timer_total = Timer()
        Profiler.timer_total.start()

        Profiler.ce_count = 0
        Profiler.ce_stats = [0 for i in range(5)]

    def stop():
        if Profiler.started_last is None:
            return
        Profiler.started_last.stop()
        Profiler.started_last = None

    def start(timer_name):
        Profiler.stop()
        if timer_name not in Profiler.timers:
            Profiler.timers[timer_name] = Timer()
        Profiler.timers[timer_name].start()
        Profiler.started_last = Profiler.timers[timer_name]

    def add_ce_stats(ce_stats):
        count = Profiler.ce_count
        Profiler.ce_stats[0] += ce_stats[0]
        for i in range(1,len(ce_stats)):
            Profiler.ce_stats[i] = (Profiler.ce_stats[i]*count+ce_stats[i])/(count+1)
        Profiler.ce_count += 1

    def print_base():
        time_total = Profiler.timer_total.read()
        covered = 0
        for timer_name,timer in Profiler.timers.items():
            time = timer.read()
            covered += time
            percentage = time / time_total * 100
            print("> {} : {:g}%".format(timer_name, round(percentage,0)))
        covered = covered / time_total * 100
        print("> covered {:g}% of {} sec".format(round(covered,0),round(time_total,1)))

    def print_ce():
        s = Profiler.ce_stats
        print("> ---")
        print("> storm stats:")

        labels = ["MDP", "DTMC", "sub-DTMC", "CE"]
        for i in range(1,len(s)):
            print("> {}: {}%".format(labels[i-1], round(s[i]*100, 0)))

        covered = 100 * sum([s[i] for i in range(1,len(s))])
        print("> covered {:g}% of {} sec".format(round(covered,0),round(s[0]/1000.0,1)))
        print("> ---")

    def print():
        Profiler.stop()
        Profiler.timer_total.stop()

        Profiler.print_ce()
        Profiler.print_base()