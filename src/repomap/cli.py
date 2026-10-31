"""Command-line entry point: ``repomap <path>``."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from repomap import __version__
from repomap.scanner import scan
from repomap.viewer.render import write_outputs

app = typer.Typer(add_completion=False, help="Turn a repository into an interactive map.")


def _print_version(value: bool) -> None:
    if value:
        typer.echo(f"repomap {__version__}")
        raise typer.Exit()


@app.command()
def main(
    path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
            help="The repository folder to map.",
        ),
    ],
    out: Annotated[
        Path,
        typer.Option("--out", "-o", help="Folder to write graph.json and index.html into."),
    ] = Path("repomap-out"),
    version: Annotated[
        bool,
        typer.Option("--version", callback=_print_version, is_eager=True, help="Show the version and exit."),
    ] = False,
) -> None:
    """Scan PATH and write graph.json plus an interactive index.html viewer."""
    graph = scan(path)
    outputs = write_outputs(graph, out)

    files = sum(1 for node in graph.nodes.values() if node.kind == "file")
    dirs = sum(1 for node in graph.nodes.values() if node.kind == "directory")
    typer.echo(f"Scanned {graph.repo_name}: {files} files in {dirs} directories")
    typer.echo(f"  graph:  {outputs.graph_json}")
    typer.echo(f"  viewer: {outputs.index_html}")
