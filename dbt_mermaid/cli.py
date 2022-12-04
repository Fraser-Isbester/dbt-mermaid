"""Module containing the CLI execution code."""
import argparse
import json
import pickle
from pathlib import Path


def main(argv=None):
    """Main entry point for the CLI."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "dir", type=str, help="directory to dbt artifact (target) folder."
    )
    parser.add_argument(
        "--format",
        type=str,
        default="mermaid",
        choices=["mermaid"],
        help="directory to dbt artifact (target) folder.",
    )
    parser.add_argument(
        "--base-nodes",
        type=int,
        help="Maximum number of base nodes to render.",
    )
    parser.add_argument(
        "-i",
        "--include",
        action="append",
        choices=["model", "source", "seed", "snapshot", "test"],
        help="The node types to include during parsing.",
    )
    args = parser.parse_args(argv)

    artifact_path = Path(args.dir)
    graph_pickle_file = artifact_path / "graph.gpickle"
    run_results_file = artifact_path / "run_results.json"

    if not artifact_path.is_dir():
        raise ValueError(f"Artifact directory {artifact_path} does not exist.")
    if not graph_pickle_file.is_file():
        raise ValueError(f"DBT Graph pickle {graph_pickle_file} does not exist.")
    if not run_results_file.is_file():
        raise ValueError(f"DBT Run Results {run_results_file} does not exist.")

    with graph_pickle_file.open("rb") as file:
        graph = pickle.load(file)

    with run_results_file.open("rb") as file:
        run_results = json.load(file)

    grp = Mermaid()
    nodes = run_results["results"]
    nodes = filter(lambda x: x["unique_id"].startswith(tuple(args.include)), nodes)
    for index, node in enumerate(nodes):
        if args.base_nodes and index > args.base_nodes:
            break

        node_name = node["unique_id"]
        for parent in graph.pred[node_name]:
            if parent.startswith(tuple(args.include)):
                grp.add_edge(parent, node_name)

        for child in graph.adj[node_name]:
            if child.startswith(tuple(args.include)):
                grp.add_edge(node_name, child)

        node_color = "green" if node["status"] == "success" else "red"
        grp.add_style(node_name, node_color)

    grp.print()


class Mermaid:
    """Convience class to represent a mermaid graph."""

    RED_HEX = "#FF5733"
    GREEN_HEX = "#355E3B"
    HEADER = "```mermaid"
    FOOTER = "```"

    def __init__(self, style="graph LR"):
        self.style = style
        self.nodes = list()
        self.lines = set()
        self.styles = set()

    def add_edge(self, from_node, to_node):
        """Add an edge to the graph."""
        from_node = self._validate_transform(from_node)
        to_node = self._validate_transform(to_node)

        line = f"{from_node} --> {to_node}"
        self.lines.add(line)

    def add_style(self, node_id, color):
        """Add a color to a node."""
        if color.lower() == "red":
            color_hex = self.RED_HEX
        elif color.lower() == "green":
            color_hex = self.GREEN_HEX
        else:
            raise ValueError(f"Color {color} not supported.")

        style = f"style {node_id} fill:{color_hex}"
        self.styles.add(style)

    def print(self):
        """Prints the graph to stdout."""
        print(self.HEADER)
        print(self.style)
        for line in self.lines:
            print("\t", line)
        for style in self.styles:
            print("\t", style)
        print(self.FOOTER)

    @staticmethod
    def _validate_transform(model):
        """A place for model validation and transformations"""
        if model.endswith("end"):
            # mermaid nodes can not end with "end"
            model = model + "_"
        return model


if __name__ == "__main__":
    main()
