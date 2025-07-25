from random import sample

from causallearn.graph.GraphClass import CausalGraph


def random_selection(causal_graph: CausalGraph, n: int) -> list[str]:
    """Randomly selects n nodes from the causal graph.

    Args:
        causal_graph (CausalGraph): The causal graph from which to select nodes.
        n (int): The number of nodes to select.

    Returns:
        list[str]: A list of names of the randomly selected nodes.
    """
    nodes = sample(causal_graph.G.nodes, n)
    return [n.get_name() for n in nodes]
