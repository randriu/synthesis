import re
import pygraphviz as pgv

def parse_hole(name) -> object:
    assert re.match(r"[AM]\(\[.*\],\d\)",
                    name), "Cannot use restrict function, hole name doesn't match"
    hole = {}
    hole["type"] = "Memory" if name[0] == "M" else "Assignment"
    hole["memory"] = int(name[-2])
    hole["observation"] = int(name[5]) if re.match(
        r"[MA]\(\[o=\d\],\d\)", name) else 0

    return hole


class Graph:
    """A class for creating graphs from design space structures.
    """

    def __init__(self) -> None:
        """Initializes an instance of the Graph class.
        """
        self.graph = pgv.AGraph(strict=False, directed=True)

    def parse(self, family) -> None:
        """Parses the design space holes into the nodes dictionary:
                {start_node: {end_node1: [observation1],...}, end_node2: ...}

            family: list of holes
        """
        self.nodes = {}
        for hole in range(family.num_holes):
            tmp = parse_hole(family.hole_name(hole))
            tmp["next"] = list(family.hole_options(hole))

            for next in tmp["next"]:
                if tmp["type"] == "Assignment":
                    continue

                if tmp["memory"] in self.nodes.keys():
                    if next in self.nodes[tmp["memory"]].keys():
                        self.nodes[tmp["memory"]][next].append(
                            tmp["observation"])
                    else:
                        self.nodes[tmp["memory"]][next] = [tmp["observation"]]
                else:
                    self.nodes[tmp["memory"]] = {next: [tmp["observation"]]}

    def create_graph(self, show_labels=False) -> None:
        """Creates a graph from the parsed design space.
        """
        self.graph.clear()
        nodes = list(self.nodes.keys())
        self.graph.add_nodes_from(nodes, fontsize=12, width=0.5, height=0.5)

        for (start, ends) in self.nodes.items():
            for (end, labels) in ends.items():
                if show_labels:
                    self.graph.add_edge(start, end, label=",".join(
                        [str(l) for l in sorted(labels)]), fontsize=12)
                else:
                    self.graph.add_edge(start, end)
        self.graph.layout("circo")

    def print(self, family, file_name="out", show_labels=False, args="-Gsize=5! -Gratio=\"expand\" -Gnodesep=.5") -> None:
        """Prints a graph in .png format.

            family: list of Holes
            file_name: name of file where the graph will be saved without the extention (e.g. file_name=file => file.png)
            args: string with Graphvix arguments to specify the output format
        """
        self.parse(family)
        self.create_graph(show_labels=show_labels)
        self.graph.draw(file_name + ".png", format="png", args=args)

    def __str__(self) -> str:
        return self.graph.string()
