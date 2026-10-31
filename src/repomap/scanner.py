"""Walk a repository and build ``directory`` and ``file`` nodes.

Every directory gets a ``contains`` edge to each of its direct children, so the
result is a tree rooted at the node with id ``"."``.

What we skip:

* anything matched by a ``.gitignore`` file (at any depth, like git does),
* folders that are never useful to map (``.git``, ``node_modules``, ...),
* Python virtualenvs, detected by their ``pyvenv.cfg`` file whatever they
  are called.

We never follow symlinks into other folders, so a link pointing back up the
tree can't send us round in circles. A symlink is recorded as a file, which is
also how git stores it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import pathspec

from repomap.graph import Edge, Graph, Node, Reason

ROOT_ID = "."

# Folder names we always skip, whatever .gitignore says.
ALWAYS_SKIP_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        "repomap-out",  # our own output folder
    }
)


@dataclass(frozen=True)
class IgnoreRules:
    """The patterns from one ``.gitignore`` and the folder it lives in.

    A ``.gitignore`` only applies to paths inside its own folder, and its
    patterns are written relative to that folder.
    """

    base: str  # folder id relative to the repo root, "." for the root
    spec: pathspec.GitIgnoreSpec


def scan(root: Path) -> Graph:
    """Scan the directory at ``root`` and return its folder/file tree."""
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    graph = Graph(repo_name=root.name)
    graph.add_node(Node(id=ROOT_ID, kind="directory", label=root.name, path=ROOT_ID))
    _scan_directory(root, ROOT_ID, graph, inherited_rules=[])
    return graph


def _scan_directory(folder: Path, folder_id: str, graph: Graph, inherited_rules: list[IgnoreRules]) -> None:
    """Add every non-ignored child of ``folder`` to ``graph``, recursively."""
    rules = inherited_rules + _load_gitignore(folder, folder_id)

    # Sort by name so the output is the same on every machine and every run.
    with os.scandir(folder) as it:
        entries = sorted(it, key=lambda e: e.name)

    for entry in entries:
        child_id = entry.name if folder_id == ROOT_ID else f"{folder_id}/{entry.name}"
        is_dir = entry.is_dir(follow_symlinks=False)

        if is_dir and _should_skip_dir(Path(entry.path)):
            continue
        if _is_ignored(child_id, is_dir, rules):
            continue
        if not is_dir and not (entry.is_file(follow_symlinks=False) or entry.is_symlink()):
            continue  # sockets, pipes and other special files

        kind = "directory" if is_dir else "file"
        graph.add_node(Node(id=child_id, kind=kind, label=entry.name, path=child_id))
        graph.add_edge(
            Edge(
                id=f"contains:{folder_id}->{child_id}",
                source=folder_id,
                target=child_id,
                kind="contains",
                reason=Reason(
                    file=folder_id,
                    detail=f"{kind} {entry.name!r} is inside directory {folder_id!r}",
                ),
            )
        )

        if is_dir:
            _scan_directory(Path(entry.path), child_id, graph, rules)


def _should_skip_dir(path: Path) -> bool:
    return path.name in ALWAYS_SKIP_DIRS or (path / "pyvenv.cfg").is_file()


def _load_gitignore(folder: Path, folder_id: str) -> list[IgnoreRules]:
    gitignore = folder / ".gitignore"
    if not gitignore.is_file():
        return []
    lines = gitignore.read_text(encoding="utf-8", errors="replace").splitlines()
    return [IgnoreRules(base=folder_id, spec=pathspec.GitIgnoreSpec.from_lines(lines))]


def _is_ignored(path_id: str, is_dir: bool, rules: list[IgnoreRules]) -> bool:
    """Decide whether ``path_id`` is ignored, the way git does.

    Rules are ordered from the root downwards. A deeper ``.gitignore`` can
    override a shallower one (for example ``!keep.log`` re-including a file),
    so the last rule that has an opinion wins.
    """
    ignored = False
    for rule in rules:
        relative = path_id if rule.base == ROOT_ID else path_id.removeprefix(rule.base + "/")
        # gitignore patterns ending in "/" only match folders, and pathspec
        # recognises a folder by a trailing slash.
        if is_dir:
            relative += "/"
        result = rule.spec.check_file(relative)
        if result.include is not None:
            ignored = result.include
    return ignored
