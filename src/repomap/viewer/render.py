"""Write ``graph.json`` and a standalone ``index.html`` viewer for a graph."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from repomap.graph import Graph

PLACEHOLDER = "__REPOMAP_GRAPH_JSON__"


@dataclass(frozen=True)
class Outputs:
    graph_json: Path
    index_html: Path


def write_outputs(graph: Graph, out_dir: Path) -> Outputs:
    """Write ``graph.json`` and ``index.html`` into ``out_dir``."""
    out_dir.mkdir(parents=True, exist_ok=True)
    data = graph.to_dict()

    graph_json = out_dir / "graph.json"
    graph_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    index_html = out_dir / "index.html"
    index_html.write_text(render_html(data), encoding="utf-8")

    return Outputs(graph_json=graph_json, index_html=index_html)


def render_html(data: dict) -> str:
    """Return the viewer page with ``data`` embedded in it.

    The JSON goes inside a ``<script>`` tag. If a file name contained
    ``</script>``, the browser would end the tag early and treat the rest as
    HTML. To prevent that we escape ``<``, ``>`` and ``&`` as ``\\u003c`` etc.
    Those characters can only appear inside JSON strings, where the escapes
    mean exactly the same thing, so the data is unchanged.
    """
    template = resources.files("repomap.viewer").joinpath("template.html").read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        raise RuntimeError(f"Viewer template is missing the {PLACEHOLDER} placeholder")

    embedded = (
        json.dumps(data, separators=(",", ":"))
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    return template.replace(PLACEHOLDER, embedded)
