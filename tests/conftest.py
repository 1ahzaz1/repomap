"""Shared pytest fixtures."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

EXAMPLES = Path(__file__).parent.parent / "examples"

# Files the scanner must skip. We create them at test time rather than
# committing them, because git itself would refuse to commit most of them
# (they match .gitignore rules or are folders like .git and node_modules).
SKIPPED_FILES = [
    ".git/config",  # always skipped
    "node_modules/left-pad/index.js",  # always skipped
    ".venv/pyvenv.cfg",  # always skipped by name
    "my-env/pyvenv.cfg",  # virtualenv with an unusual name, found by pyvenv.cfg
    "my-env/lib/site.py",
    "debug.log",  # root .gitignore: *.log
    "build/output.txt",  # root .gitignore: build/
    "src/notes.log",  # root .gitignore *.log also applies in subfolders
    "src/generated/models.py",  # src/.gitignore: generated/
    "docs/generated/page.md",  # NOT ignored: src/.gitignore doesn't apply to docs/
]


@pytest.fixture
def tiny_repo(tmp_path: Path) -> Path:
    """A copy of examples/tiny-repo with extra files the scanner should skip."""
    repo = tmp_path / "tiny-repo"
    shutil.copytree(EXAMPLES / "tiny-repo", repo)
    for relative in SKIPPED_FILES:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("created by the test fixture\n")
    # Re-included by "!important.log" in src/.gitignore, overriding the root "*.log".
    (repo / "src/important.log").write_text("keep me\n")
    return repo
