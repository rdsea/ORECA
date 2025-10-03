from pathlib import Path

from rca_methods.classes.graph import parse_dependency_graph


def test_parse_dependency_graph():
    cur_path = Path(__file__).parent
    yaml_file = cur_path / "example_dependency_graph.yaml"

    g = parse_dependency_graph(yaml_file)

    assert set(g.nodes()) == {"A", "B", "C"}

    assert set(g.edges()) == {("A", "B"), ("A", "C"), ("B", "C")}

    # Ensure edges are directional (no reverse edges)
    assert not g.has_edge("B", "A")
    assert not g.has_edge("C", "A")
    assert not g.has_edge("C", "B")
