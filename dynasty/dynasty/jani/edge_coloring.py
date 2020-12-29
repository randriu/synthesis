class EdgeColoring:

    def __init__(self, hole_options):
        self.hole_options = hole_options

        self.coloring = dict()
        self.reverse_coloring = dict()

    def __len__(self):
        return len(self.reverse_coloring)

    def __str__(self):
        return "EdgeColors BW{0}\nEdgeColors BW{1}".format(
            ";".join([str(k) + ":" + self._hole_assignment_to_string(v) for k, v in self.reverse_coloring.items()]),
            ";".join([self._hole_assignment_to_string(v) + ": " + str(k) for v, k in self.coloring.items()])
        )

    def _hole_assignment_to_string(self, v):
        return "{0}".format(
            ", ".join(["{}: {}".format(x, y) for x, y in zip(self.hole_options.keys(), v) if y is not None])
        )

    def _full_hole_assignment(self, partial_hole_assignment):
        result = []
        for key in self.hole_options:
            result.append(partial_hole_assignment.get(key, None))
        return tuple(self._full_hole_assignment(partial_hole_assignment))

    def get_or_make_color(self, full_hole_assignment):
        _fha = full_hole_assignment  # self._full_hole_assignment(partial_hole_assignment)
        color = self.coloring.get(_fha, len(self.coloring) + 1)
        if color == len(self.coloring) + 1:
            self.coloring[_fha] = color
            self.reverse_coloring[color] = _fha

        # print("{} gets color {}".format(full_hole_assignment, color))
        return color

    def get_hole_assignment(self, color):
        assert color != 0
        return self.reverse_coloring[color]

    def subcolors(self, sub_hole_options):
        assert sub_hole_options.keys() == self.hole_options.keys()
        colors = set()
        for hole_assignment, color in self.coloring.items():
            # print(f"Consider hole_assignment {self._hole_assignment_to_string(hole_assignment)} with color {color}")
            contained = True
            for hole, assignment in zip(sub_hole_options, hole_assignment):
                if assignment is None:
                    continue
                if assignment not in sub_hole_options[hole]:
                    # print(f"Do not add for assignment {assignment} on hole {hole}")
                    contained = False
                    break
            if contained:
                colors.add(color)
        return colors

    def get_hole_assignment_set_colors(self, colors):
        result = dict()
        for color in colors:
            if color == 0:
                continue
            _fha = self.get_hole_assignment(color)
            for hole, assignment in zip(self.hole_options, _fha):
                if assignment is not None:
                    old = result.get(hole, set())
                    old.add(assignment)
                    result[hole] = old

        return result

    def get_hole_assignments(self, lists_colors):
        result = dict()
        for index, colors in enumerate(lists_colors):
            for color in colors:
                if color == 0:
                    continue
                _fha = self.get_hole_assignment(color)
                for hole, assignment in zip(self.hole_options, _fha):
                    if assignment is not None:
                        old = result.get(hole, dict())
                        new_list = old.get(assignment, [])
                        new_list.append(index)
                        old[assignment] = new_list
                        result[hole] = old
        return result

    def violating_colors(self):
        for _, __ in self.coloring.items():
            pass
