import time
import os

from paynt.globals import Globals


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
    program_start_time = 0
    program_total_time = 0
    ce_count = None
    timers = None

    @staticmethod
    def get_file_name_for_worker(process_order_number):
        return "paynt/" + Globals.CEGIS_WORKER_PREFIX_FILE_NAME + str(process_order_number) + ".txt"

    @staticmethod
    def initialize():
        Profiler.timers = {}
        Profiler.started_last = None
        Profiler.program_start_time = time.time_ns()

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
        time_total = Profiler.program_total_time
        covered = 0
        for timer_name, timer in Profiler.timers.items():
            t = timer.read()
            covered += t
            print(f'> {timer_name} : {round(t / time_total * 100, 0)}%')
        print(f"> covered {round(covered / time_total * 100, 0)}% of {round(time_total, 1)} sec")

    @staticmethod
    def print_only_time_spent():
        for timer_name, timer in Profiler.timers.items():
            t = timer.read()
            print(f'> {timer_name} : {t}')

    @staticmethod
    def flush_stats_to_the_file(process_order_number):
        # file already exists we have to accumulate metrics

        if os.path.isfile(Profiler.get_file_name_for_worker(process_order_number)):
            f = open(Profiler.get_file_name_for_worker(process_order_number), "r+")

            lines = f.readlines()
            # read and acc timer
            for line in lines:
                key, value = line.split(":")
                # print(f"BEFORE {key} has value:{Profiler.timers.get(key).time}")
                # print(f"Number 1 ({Profiler.timers.get(key).time}) + Number 2 ({value}) = ({Profiler.timers.get(key).time + float(value)})??")
                Profiler.timers.get(key).time += float(value)
                # print(f"AFTER {key} has value:{Profiler.timers.get(key).time}")

            f = open(Profiler.get_file_name_for_worker(process_order_number), "w+")
            # update file
            for timer_name, timer in Profiler.timers.items():
                t = timer.read()
                f.write(f'{timer_name}:{t}\n')
        else:
            # we have to create new file with new values...
            f = open(Profiler.get_file_name_for_worker(process_order_number), "w+")
            # append files
            for timer_name, timer in Profiler.timers.items():
                t = timer.read()
                f.write(f'{timer_name}:{t}\n')

        f.close()

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
    def get_all_data_from_files():
        timers_that_has_to_be_averaged = []
        for file in os.listdir(os.path.dirname(__file__)):
            if file.startswith(Globals.CEGIS_WORKER_PREFIX_FILE_NAME):
                f = open(Globals.CEGIS_WORKER_DIR_NAME + "/" + file, "r+")
                lines = f.readlines()

                timers_that_has_to_be_averaged = [line.split(":")[0] for line in lines]
                # read and acc timer
                for line in lines:
                    key, value = line.split(":")
                    # accumulate for more CPUs...
                    if key in Profiler.timers:
                        # key already exists we are gonna append values
                        Profiler.timers.get(key).time += float(value)
                    else:
                        # key does not exists create new one...
                        Profiler.timers[key] = Timer()
                        Profiler.timers.get(key).time = float(value)
                f.close()


        # average all
        for key in timers_that_has_to_be_averaged:
            # print(f"before average {Profiler.timers.get(key).time}")
            Profiler.timers.get(key).time /= Globals.CEGIS_CPU_COUNT  # this has to be number of CPUs
            # print(f"after average {Profiler.timers.get(key).time}")

    @staticmethod
    def delete_worker_files():
        for file in os.listdir(os.path.dirname(__file__)):
            if file.startswith(Globals.CEGIS_WORKER_PREFIX_FILE_NAME):
                # print(f"Deleting {file} file!")
                os.remove(Globals.CEGIS_WORKER_DIR_NAME + "/" + file)

    @staticmethod
    def print():
        Profiler.stop()
        # program total time in seconds
        Profiler.program_total_time = (time.time_ns()-Profiler.program_start_time)/1000000000
        print("Program execution time:" + str(Profiler.program_total_time) + " (s)")

        Profiler.get_all_data_from_files()

        # Profiler.print_ce()
        Profiler.print_base()
        # Profiler time total for each timer
        Profiler.print_only_time_spent()