from __future__ import annotations

import json
import re
from pathlib import Path

from typer.testing import CliRunner

from repomap.cli import app
from repomap.viewer.render import PLACEHOLDER, render_html


def embedded_json(html: str) -> dict:
    match = re.search(r'<script id="graph-data" type="application/json">(.*?)</script>', html, re.S)
    assert match, "graph data script tag not found"
    return json.loads(match.group(1))


def test_cli_writes_graph_json_and_index_html(tiny_repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"

    result = CliRunner().invoke(app, [str(tiny_repo), "--out", str(out)])

    assert result.exit_code == 0, result.output
    assert "9 files in 5 directories" in result.output

    graph = json.loads((out / "graph.json").read_text())
    assert graph["repo_name"] == "tiny-repo"
    assert {"version", "repo_name", "generated_at", "nodes", "edges"} <= graph.keys()

    html = (out / "index.html").read_text()
    assert PLACEHOLDER not in html
    assert embedded_json(html) == graph


def test_cli_rejects_a_missing_path(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, [str(tmp_path / "nope")])

    assert result.exit_code != 0


def test_file_names_cannot_break_out_of_the_script_tag() -> None:
    sneaky = "</script><script>alert(1)</script>"
    data = {"repo_name": sneaky, "nodes": [{"id": sneaky, "label": "a & b"}], "edges": []}

    html = render_html(data)

    assert sneaky not in html
    assert embedded_json(html) == data
