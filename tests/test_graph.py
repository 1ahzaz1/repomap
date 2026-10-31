from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from repomap.graph import SCHEMA_VERSION, Edge, Graph, Node, Reason


def make_graph() -> Graph:
    graph = Graph(repo_name="demo")
    graph.add_node(Node(id=".", kind="directory", label="demo", path="."))
    graph.add_node(Node(id="b.txt", kind="file", label="b.txt", path="b.txt"))
    graph.add_node(Node(id="a.txt", kind="file", label="a.txt", path="a.txt"))
    for target in ("b.txt", "a.txt"):
        graph.add_edge(
            Edge(
                id=f"contains:.->{target}",
                source=".",
                target=target,
                kind="contains",
                reason=Reason(file=".", detail="test"),
            )
        )
    return graph


def test_to_dict_has_the_documented_shape() -> None:
    data = make_graph().to_dict(generated_at=datetime(2026, 1, 1, tzinfo=UTC))

    assert data["version"] == SCHEMA_VERSION
    assert data["repo_name"] == "demo"
    assert data["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert data["nodes"][1] == {"id": "a.txt", "kind": "file", "label": "a.txt", "path": "a.txt"}
    assert data["edges"][0] == {
        "id": "contains:.->a.txt",
        "source": ".",
        "target": "a.txt",
        "kind": "contains",
        "reason": {"file": ".", "line": None, "detail": "test"},
    }


def test_nodes_and_edges_are_sorted_by_id() -> None:
    data = make_graph().to_dict()

    assert [node["id"] for node in data["nodes"]] == [".", "a.txt", "b.txt"]
    assert [edge["id"] for edge in data["edges"]] == ["contains:.->a.txt", "contains:.->b.txt"]


def test_to_json_is_valid_json() -> None:
    assert json.loads(make_graph().to_json())["repo_name"] == "demo"


def test_rejects_duplicate_node_ids() -> None:
    graph = make_graph()
    with pytest.raises(ValueError, match="Duplicate node"):
        graph.add_node(Node(id="a.txt", kind="file", label="a.txt", path="a.txt"))


def test_rejects_edges_to_unknown_nodes() -> None:
    graph = make_graph()
    edge = Edge(id="x", source=".", target="missing", kind="contains", reason=Reason(file="."))
    with pytest.raises(ValueError, match="unknown node"):
        graph.add_edge(edge)
