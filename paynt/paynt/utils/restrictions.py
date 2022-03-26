
import re
from .utils import *


class Conditions:
    conditions = {}

    def __init__(self) -> None:
        self.conditions = {
            "clear": lambda *_: True,
            # "greater_or_zero": self.cond1,
            # "cond2": self.cond2,
            # "cond3": self.cond3,
            # "cond4": self.cond4,
            # "experiment": self.cond5,
            # "no_self_loop": self.cond6,


            # # row-like
            # "forward_with_loop": lambda current, next, _: current != next and current + 1 != next,
            # "one_step": lambda current, next, _: abs(current - next) != 1,
            # "one_step_with_loop": lambda current, next, _: abs(current - next) > 1,
            "forward": lambda current, next, max: not (current + 1 == next or (current == max and next == max)),
            "backward": lambda current, next, _: not (current - 1 == next or (current == 0 and next == 0)),

            # # circle-like
            "simple_circle": lambda current, next, max: not ((current + 1 == next) or (current == max and next == 0)),
            # "simple_circle_backward": lambda current, next, max: not ((current - 1 == next) or (current == 0 and next == max)),
            # "simple_circle_with_loop": lambda current, next, max: not ((current + 1 == next) or (current == max and next == 0) or (current == next)),
            "two_way_circle": lambda current, next, max: not (abs(current - next) == 1 or ((current == max and next == 0) or (next == max and current == 0))),
            "two_way_circle_with_loops": lambda current, next, max: not (abs(current - next) <= 1 or ((current == max and next == 0) or (next == max and current == 0))),

            # "original": self.cond0,
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
            current = get_current_memory(hole.name)
            max = sorted(hole.options)[-1]
            for option in hole.options.copy():
                total_options += 1
                if condition(current, option, max):
                    hole.options.remove(option)
                    removed += 1
        elif hole.name[0] == "A" and hole.name[1] == "M":
            current = get_current_memory(hole.name)
            options, max = parse_am_labels(hole)

            for (next, option) in zip(options, hole.options.copy()):
                total_options += 1
                if condition(current, next, max):
                    hole.options.remove(option)
                    removed += 1

    if design_space.size:
        print("[{}] Reduced to {}%".format(
            name.upper(),
            format((design_space.size/original_size)*100, ".10f")
        ), "of original size")

    if total_options:
        print("[{}] Removed {}%".format(
            name.upper(),
            format((removed/total_options)*100, ".10f")
        ), "of total_options")

    return design_space


def set_memory(design_space, mem_size, condition=lambda current, next, _: current > next, rewrite=True, name="Restrict"):
    for hole in design_space:
        current = get_current_memory(hole.name)
        new_options = [next for next in range(
            mem_size) if not condition(current, next, mem_size-1)]

        if hole.name[0] == "M":
            if rewrite:
                hole.options = new_options
            else:
                hole.options = hole.options + new_options

        elif hole.name[0] == "A" and hole.name[1] == "M":
            new_options_filtered = [index for (index, i) in enumerate(
                hole.option_labels) if int(re.findall(r"{.*}\+(\d)", i)[0]) in new_options]

            if rewrite:
                hole.options = new_options_filtered
            else:
                hole.options = hole.options + new_options_filtered

        hole.options = list(set(hole.options))

    return design_space
