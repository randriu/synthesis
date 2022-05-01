
import re
from .utils import *
import logging

logger = logging.getLogger(__name__)


class Conditions:

    conditions = []

    def __init__(self) -> None:
        self.conditions = [
            self.__create_condition("Clear", self.__clear, True, False, False),
            self.__create_condition("Forward", self.__forward),
            self.__create_condition(
                "Backward with loops", self.__backward, synthesize=False),
            self.__create_condition(
                "Backward", self.__self_loops, True, True, True),
            self.__create_condition("One step", self.__self_loops),
            self.__create_condition(
                "Simple circle", self.__simple_circle, True, False, True),
            self.__create_condition(
                "Circle both ways", self.__simple_circle_backward),
            self.__create_condition(
                "Circle both ways with loops", self.__self_loops),
        ]

    def __create_condition(self, name, condition, rewrite=False, restrict=False, synthesize=True):
        return {"name": name, "condition": condition, "rewrite": rewrite, "restrict": restrict, "synthesize": synthesize}

    def __clear(self, _, __, ___):
        return False

    def __forward(self, current, next, max):
        return current + 1 == next or (current == max and next == max)

    def __backward(self, current, next, _):
        return current - 1 == next or (current == 0 and next == 0)

    def __simple_circle(self, current, next, max):
        return (current + 1 == next) or (current == max and next == 0)

    def __simple_circle_backward(self, current, next, max):
        return (current - 1 == next) or (current == 0 and next == max)

    def __self_loops(self, current, next, _):
        return current == next


def set_memory(design_space, mem_size, condition=lambda current, next, _: current > next, rewrite=True, restrict=False, name="Restrict"):

    for hole in design_space:
        assert re.match(
            r"[AM]{1,2}\(\[.*],\d+\)", hole.name), "Cannot use restrict function, hole {} doesn't match".format(hole.name)
        current = get_current_memory(hole.name)

        new_options = [next for next in hole.options if
                       not condition(current, next, mem_size-1)] if restrict else [next for next in range(mem_size) if condition(current, next, mem_size-1)]

        if hole.name[0] == "M":
            if rewrite:
                hole.options = new_options
            else:
                hole.options = hole.options + new_options

        elif hole.name[0] == "A" and hole.name[1] == "M":
            new_options_filtered = [index for (index, i) in enumerate(
                hole.option_labels) if int(re.findall(r"{.*}\+(\d+)", i)[0]) in new_options]

            if rewrite:
                hole.options = new_options_filtered
            else:
                hole.options = hole.options + new_options_filtered

        hole.options = list(set(hole.options))

    logger.info("Condition: " + name.upper() + " " + str(design_space.size))

    return design_space
