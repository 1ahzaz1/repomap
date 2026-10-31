"""The graph data model: nodes, edges and the reason each edge exists.

These dataclasses are what we serialise to ``graph.json``. They are plain data
on purpose, so the file is easy to read and other tools (the viewer, and later
the Go server) can consume it without knowing anything about Python.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Literal

# Bump this when the shape of graph.json changes in a way readers must handle.
SCHEMA_VERSION = 1

NodeKind = Literal[
    "file",
    "directory",
    "service",
    "dockerfile",
    "workflow",
    "k8s-resource",
    "compose-service",
]
EdgeKind = Literal["imports", "contains", "builds", "deploys", "triggers"]


@dataclass(frozen=True)
class Node:
    """Something in the repo: a file, a directory, and later a service etc."""

    id: str
    kind: NodeKind
    label: str
    path: str


@dataclass(frozen=True)
class Reason:
    """Why an edge exists. Every edge must have one (see CLAUDE.md)."""

    file: str
    line: int | None = None
    detail: str = ""


@dataclass(frozen=True)
class Edge:
    """A directed link from ``source`` to ``target`` (both are node ids)."""

    id: str
    source: str
    target: str
    kind: EdgeKind
    reason: Reason


@dataclass
class Graph:
    """A collection of nodes and edges for one repository."""

    repo_name: str
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: dict[str, Edge] = field(default_factory=dict)

    def add_node(self, node: Node) -> None:
        if node.id in self.nodes:
            raise ValueError(f"Duplicate node id: {node.id!r}")
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        if edge.id in self.edges:
            raise ValueError(f"Duplicate edge id: {edge.id!r}")
        for end in (edge.source, edge.target):
            if end not in self.nodes:
                raise ValueError(f"Edge {edge.id!r} points at unknown node {end!r}")
        self.edges[edge.id] = edge

    def to_dict(self, generated_at: datetime | None = None) -> dict:
        """Return the graph as plain dicts/lists, ready for ``json.dumps``.

        Nodes and edges are sorted by id, so the same repo always gives the
        same output. ``generated_at`` is the only field that changes between
        runs; pass a fixed value to make the whole output reproducible.
        """
        when = generated_at or datetime.now(UTC)
        return {
            "version": SCHEMA_VERSION,
            "repo_name": self.repo_name,
            "generated_at": when.isoformat(timespec="seconds"),
            "nodes": [asdict(self.nodes[k]) for k in sorted(self.nodes)],
            "edges": [asdict(self.edges[k]) for k in sorted(self.edges)],
        }

    def to_json(self, generated_at: datetime | None = None) -> str:
        return json.dumps(self.to_dict(generated_at), indent=2)
