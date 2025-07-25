from collections.abc import Callable
from itertools import chain
from typing import Union

import networkx as nx
import numpy as np

from rca_methods.graph_heads import finalize_directed_adj
from rca_methods.utility import dump_json, load_json


def topological_sort(
    nodes: set,
    predecessors: Callable,
    successors: Callable,
) -> list[set]:
    """Sort nodes with predecessors first.

    Args:
        nodes (set): A set of nodes.
        predecessors (Callable): A function that returns the predecessors of a node.
        successors (Callable): A function that returns the successors of a node.

    Returns:
        list[set]: A list of sets, where each set contains nodes at the same topological level.
    """
    graph = {node: set(successors(node)) for node in nodes}
    components = list(nx.strongly_connected_components(nx.DiGraph(graph)))
    node2component = {
        node: index for index, component in enumerate(components) for node in component
    }
    super_graph = {
        index: {node2component[child] for node in component for child in graph[node]}
        - {index}
        for index, component in enumerate(components)
    }
    return [
        set(chain(*[components[index] for index in layer]))
        for layer in nx.topological_generations(nx.DiGraph(super_graph))
    ]


class Node:
    """Represents a node in a graph, consisting of an entity and a metric."""

    def __init__(self, entity: str, metric: str):
        """Initialize a Node object.

        Args:
            entity (str): The entity name.
            metric (str): The metric name.
        """
        self._entity = entity
        self._metric = metric

    @property
    def entity(self) -> str:
        """Entity getter."""
        return self._entity

    @property
    def metric(self) -> str:
        """Metric getter."""
        return self._metric

    def asdict(self) -> dict[str, str]:
        """Serialize the node as a dictionary.

        Returns:
            dict[str, str]: A dictionary representation of the node.
        """
        return {"entity": self._entity, "metric": self._metric}

    def __eq__(self, obj: object) -> bool:
        """Check if two Node objects are equal."""
        if isinstance(obj, Node):
            return self.entity == obj.entity and self.metric == obj.metric
        return False

    def __hash__(self) -> int:
        """Return the hash of the Node object."""
        return hash((self.entity, self.metric))

    def __repr__(self) -> str:
        """Return the string representation of the Node object."""
        return f"Node{(self.entity, self.metric)}"


class LoadingInvalidGraphError(Exception):
    """Exception raised when a Graph tries to load from a broken file."""


class Graph:
    """Abstract base class for graph structures, providing an interface to access relations."""

    def __init__(self):
        """Initialize a Graph object."""
        self._nodes: set[Node] = set()
        self._sorted_nodes: list[set[Node]] = None

    def dump(self, filename: str) -> bool:
        """Dump a graph into the given file.

        Args:
            filename (str): The path to the file.

        Returns:
            bool: True if the operation succeeds, False otherwise.
        """
        return False

    @classmethod
    def load(cls, filename: str) -> Union["Graph", None]:
        """Load a graph from the given file.

        Args:
            filename (str): The path to the file.

        Returns:
            Union["Graph", None]: A graph object if available, None if dump/load is not supported.

        Raises:
            LoadingInvalidGraphError: If the file cannot be parsed.
        """
        return None

    @property
    def nodes(self) -> set[Node]:
        """Get the set of nodes in the graph."""
        return self._nodes

    @property
    def edges(self) -> set[tuple]:
        """Get the set of edges in the graph."""
        return list(self._graph.edges)

    @property
    def str_edges(self) -> set[tuple]:
        """Get the set of edges in string format."""
        try:
            return [
                (f"{i.entity}_{i.metric}", f"{j.entity}_{j.metric}")
                for i, j in self._graph.edges
            ]
        except Exception:
            return self._graph.edges

    @property
    def topological_sort(self) -> list[set[Node]]:
        """Sort nodes with parents first.

        The graph specifies the parents of each node.

        Returns:
            list[set[Node]]: A list of sets, where each set contains nodes at the same topological level.
        """
        if self._sorted_nodes is None:
            self._sorted_nodes = topological_sort(
                nodes=self.nodes, predecessors=self.parents, successors=self.children
            )
        return self._sorted_nodes

    def children(self, node: Node, **kwargs) -> set[Node]:
        """Get the children of the given node in the graph.

        Args:
            node (Node): The node to get children for.

        Returns:
            set[Node]: A set of child nodes.
        """
        raise NotImplementedError

    def parents(self, node: Node, **kwargs) -> set[Node]:
        """Get the parents of the given node in the graph.

        Args:
            node (Node): The node to get parents for.

        Returns:
            set[Node]: A set of parent nodes.
        """
        raise NotImplementedError


class MemoryGraph(Graph):
    """Implementation of Graph with data stored in memory using NetworkX."""

    def __init__(self, graph: nx.DiGraph):
        """Initialize a MemoryGraph object.

        Args:
            graph (nx.DiGraph): The NetworkX directed graph.
        """
        super().__init__()
        self._graph = graph
        self._nodes.update(self._graph.nodes)

    def dump(self, filename: str) -> bool:
        """Dump a graph into the given file.

        Args:
            filename (str): The path to the file.

        Returns:
            bool: True if the operation succeeds, False otherwise.
        """
        nodes: list[Node] = list(self._graph.nodes)
        node_indexes = {node: index for index, node in enumerate(nodes)}
        edges = [
            (node_indexes[cause], node_indexes[effect])
            for cause, effect in self._graph.edges
        ]
        try:
            data = {"nodes": [node.asdict() for node in nodes], "edges": edges}
        except Exception:
            data = {"nodes": list(nodes), "edges": edges}
        dump_json(filename=filename, data=data)
        return True

    @classmethod
    def load(cls, filename: str) -> Union["MemoryGraph", None]:
        """Load a graph from the given file.

        Args:
            filename (str): The path to the file.

        Returns:
            Union["MemoryGraph", None]: A MemoryGraph object if available, None if dump/load is not supported.

        Raises:
            LoadingInvalidGraphError: If the file cannot be parsed.
        """
        data: dict = load_json(filename=filename)
        if "nodes" not in data or "edges" not in data:
            raise LoadingInvalidGraphError(filename)
        try:
            nodes: list[Node] = [Node(**node) for node in data["nodes"]]
        except Exception:
            nodes = list(data["nodes"])

        graph = nx.DiGraph()
        graph.add_nodes_from(nodes)
        graph.add_edges_from(
            (nodes[cause], nodes[effect]) for cause, effect in data["edges"]
        )
        return MemoryGraph(graph)

    @classmethod
    def from_adj(cls, adj: np.ndarray, nodes: list[Node]) -> Union["MemoryGraph", None]:
        """Create a MemoryGraph from an adjacency matrix and a list of nodes.

        Args:
            adj (np.ndarray): The adjacency matrix.
            nodes (list[Node]): A list of nodes corresponding to the adjacency matrix.

        Returns:
            Union["MemoryGraph", None]: A MemoryGraph object.
        """
        graph = nx.DiGraph()
        graph.add_nodes_from(nodes)

        if isinstance(adj, list) and len(adj) == 0:
            return MemoryGraph(graph)

        adj = finalize_directed_adj(adj)

        for i in range(len(adj)):
            for j in range(len(adj)):
                if adj[i, j] == 1:
                    graph.add_edge(nodes[j], nodes[i])

        return MemoryGraph(graph)

    def children(self, node: Node, **kwargs) -> set[Node]:
        """Get the children of the given node in the graph.

        Args:
            node (Node): The node to get children for.

        Returns:
            set[Node]: A set of child nodes.
        """
        if not self._graph.has_node(node):
            return set()
        return set(self._graph.successors(node))

    def parents(self, node: Node, **kwargs) -> set[Node]:
        """Get the parents of the given node in the graph.

        Args:
            node (Node): The node to get parents for.

        Returns:
            set[Node]: A set of parent nodes.
        """
        if not self._graph.has_node(node):
            return set()
        return set(self._graph.predecessors(node))
