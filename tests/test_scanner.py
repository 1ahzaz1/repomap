from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

import pytest

from repomap.scanner import ROOT_ID, scan

EXPECTED_DIRECTORIES = {
    ".",
    "docs",
    "docs/generated",
    "src",
    "src/utils",
}

EXPECTED_FILES = {
    ".gitignore",
    "README.md",
    "keep.log",
    "docs/guide.md",
    "docs/generated/page.md",
    "src/.gitignore",
    "src/app.py",
    "src/important.log",
    "src/utils/helpers.py",
}


def ids_of_kind(graph, kind: str) -> set[str]:
    return {node.id for node in graph.nodes.values() if node.kind == kind}


def test_finds_expected_directories_and_files(tiny_repo: Path) -> None:
    graph = scan(tiny_repo)

    assert ids_of_kind(graph, "directory") == EXPECTED_DIRECTORIES
    assert ids_of_kind(graph, "file") == EXPECTED_FILES


@pytest.mark.parametrize(
    "skipped",
    [
        ".git",
        "node_modules",
        ".venv",
        "my-env",
        "debug.log",
        "build",
        "src/notes.log",
        "src/generated",
    ],
)
def test_skips_ignored_paths(tiny_repo: Path, skipped: str) -> None:
    graph = scan(tiny_repo)

    assert skipped not in graph.nodes
    assert not any(node_id.startswith(skipped + "/") for node_id in graph.nodes)


def test_root_node_is_named_after_the_folder(tiny_repo: Path) -> None:
    root = scan(tiny_repo).nodes[ROOT_ID]

    assert root.kind == "directory"
    assert root.label == "tiny-repo"
    assert root.path == "."


def test_every_node_except_root_has_exactly_one_parent(tiny_repo: Path) -> None:
    graph = scan(tiny_repo)
    parents: dict[str, list[str]] = {}
    for edge in graph.edges.values():
        parents.setdefault(edge.target, []).append(edge.source)

    assert ROOT_ID not in parents
    for node_id in graph.nodes.keys() - {ROOT_ID}:
        assert len(parents[node_id]) == 1, node_id


def test_contains_edges_link_parent_to_child_with_a_reason(tiny_repo: Path) -> None:
    graph = scan(tiny_repo)

    edge = graph.edges["contains:src->src/app.py"]
    assert edge.kind == "contains"
    assert edge.source == "src"
    assert edge.target == "src/app.py"
    assert edge.reason.file == "src"
    assert edge.reason.detail == "file 'app.py' is inside directory 'src'"

    top_level = graph.edges["contains:.->src"]
    assert top_level.source == ROOT_ID
    assert all(edge.kind == "contains" and edge.reason.detail for edge in graph.edges.values())


def test_same_repo_gives_identical_output(tiny_repo: Path) -> None:
    fixed_time = datetime(2026, 1, 1, tzinfo=UTC)

    first = scan(tiny_repo).to_json(generated_at=fixed_time)
    second = scan(tiny_repo).to_json(generated_at=fixed_time)

    assert first == second


def test_does_not_follow_symlinked_directories(tiny_repo: Path) -> None:
    # A link pointing back at the repo root would loop forever if followed.
    os.symlink(tiny_repo, tiny_repo / "src" / "loop")

    graph = scan(tiny_repo)

    assert graph.nodes["src/loop"].kind == "file"
    assert not any(node_id.startswith("src/loop/") for node_id in graph.nodes)


def test_rejects_a_path_that_is_not_a_directory(tiny_repo: Path) -> None:
    with pytest.raises(NotADirectoryError):
        scan(tiny_repo / "README.md")
