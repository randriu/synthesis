
import re
from .utils import *


class Conditions:
    conditions = {}

    def __init__(self) -> None:
        self.conditions = {
            "original": self.cond0,
            "greater_or_zero": self.cond1,
            "one_step_at_a_time": self.cond2,
            "one_step_circular": self.cond3,
            "circular_one_way": self.cond4,
            "experiment": self.cond5,
            "no_self_loop": self.cond6,
        }

    def cond0(self, *_):
        return False

    def cond1(self, current, next, _):
        return next <= current and next != 0

    def cond2(self, current, next, max):
        return (next - current) != 1 and (current != next) and not (next == 0 and current == max)

    def cond3(self, current, next, _):
        return abs(current - next) > 1

    def cond4(self, current, next, max):
        return not (
            (abs(current - next) <= 1) or
            (current == max and next == 0) or
            (current == 0 and next == max)
        )

    def cond5(self, _, next, __):
        return (next % 2)

    def cond6(self, current, next, _):
        return next == current


def restrict(design_space, condition=lambda current, next, _: current > next, name="Restrict"):

    original_size = design_space.size
    total_options = 0
    removed = 0

    for hole in design_space:
        assert re.match(
            r"[AM]{1,2}\(\[.*],\d\)", hole.name), "Cannot use restrict function, hole {} doesn't match".format(hole.name)

        if hole.name[0] == "M":
            current = int(hole.name[-2])
            max = sorted(hole.options)[-1]
            for option in hole.options.copy():
                total_options += 1
                if condition(current, option, max):
                    hole.options.remove(option)
                    removed += 1
        elif hole.name[0] == "A" and hole.name[1] == "M":
            current = int(hole.name[-2])
            options, max = parse_am_labels(hole)

            for (next, option) in zip(options, hole.options.copy()):
                total_options += 1
                if condition(current, next, max):
                    hole.options.remove(option)
                    removed += 1

    if design_space.size:
        print("[{}]\tReduced to {}%".format(
            name.upper(),
            format((design_space.size/original_size)*100, ".10f")
        ), "of original size")

    if total_options:
        print("[{}]\tRemoved {}%".format(
            name.upper(),
            format((removed/total_options)*100, ".10f")
        ), "of total_options")
    return design_space
