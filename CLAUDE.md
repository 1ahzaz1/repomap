# CLAUDE.md

## Project: repomap

A local command-line tool that turns any repository into an interactive map of its **code and infrastructure**: file → file dependencies, plus how each service is built (Dockerfile), built/tested in CI (GitHub Actions), and deployed (Kubernetes / docker-compose).

The roadmap lives in README.md (Phases 1–4). We are at the very start of Phase 1.

## Hard rules

- **No AI/LLM anywhere in the product.** No calls to OpenAI, Anthropic, Gemini or any model API, no embeddings, no "AI summaries". All parsing, linking and analysis is deterministic logic we write. The same repo must always produce the same graph.
- **Fully local.** The tool never sends code or data over the network.
- **Every edge must be explainable.** Each edge in the graph stores *why* it exists (e.g. the file and line of the import, or the YAML key that links two things).
- **Languages and boundaries** (preference order: Python > Go > JavaScript):
  - **Python (majority of the code):** all scanning, parsing, linking and analysis, plus the main CLI.
  - **Go (later, Phase 2):** a small local server, `repomap serve`, in its own `server/` folder. It serves the viewer, watches the target repo for file changes, re-runs the Python analyser, and live-reloads the browser. It also exposes a small HTTP API (e.g. blast radius for a git diff) by calling the Python CLI. Go never re-implements analysis logic.
  - **JavaScript (minimal):** only inside the viewer, for rendering with Cytoscape.js and basic interaction. No framework or build step unless it becomes clearly necessary.
  - The languages talk to each other only through `graph.json` and CLI calls with JSON output. No shared code across languages.
  - Don't add Go until the task calls for it.

## About me / how to work with me

- I'm a graduate/junior engineer working in CD/platform. I'm new to a lot of this, so explain what you're doing and why, briefly and in plain English, especially for new concepts (ASTs, tree-sitter, graph layout, Python packaging).
- I prefer Python. Prefer simple, readable code over clever code. I need to understand and maintain all of it.
- Keep changes small and reviewable: one focused change per branch/PR.
- Work on a feature branch, never directly on `main`.
- Ask before committing, pushing, creating PRs, or adding large dependencies.
- Don't build ahead of the current task. Stop when it's done and suggest the next step.

## Stack

- **Language:** Python 3.12+ with type hints.
- **Project/env management:** `uv` (install with `brew install uv` if missing). Dependencies in `pyproject.toml`.
- **CLI:** `typer` (or `argparse` if simpler).
- **Ignoring files:** `pathspec` to respect `.gitignore`.
- **Graph algorithms:** `networkx` for the in-memory graph (cycle detection, shortest paths, descendants for blast radius). Our own dataclasses are the serialised format; networkx is used for analysis.
- **Later phases:**
  - Code parsing: `tree-sitter` with language grammars (e.g. `tree-sitter-language-pack`).
  - YAML (Kubernetes, compose, GitHub Actions): `PyYAML` or `ruamel.yaml`.
  - Git history (Phase 3): `GitPython` or plain `git` via `subprocess`.
- **Viewer:** the CLI writes a single standalone `index.html` with the graph data embedded as JSON, rendered by Cytoscape.js loaded from a CDN. No build step, no npm, no framework. The HTML template lives in the Python package.
- **Tests:** `pytest`. **Lint/format:** `ruff`.

## Planned structure

```
repomap/
├── src/repomap/
│   ├── __init__.py
│   ├── cli.py          # entry point: `repomap <path>`
│   ├── graph.py        # graph data model (nodes, edges, reasons)
│   ├── scanner.py      # walks a repo, builds file/directory nodes
│   └── viewer/
│       ├── template.html
│       └── render.py   # writes graph.json + standalone index.html
├── server/             # (later, Phase 2) Go local server: `repomap serve`
├── tests/
├── examples/           # small fixture repos for tests
├── pyproject.toml
├── README.md
└── CLAUDE.md
```

## Graph data model (starting point, can evolve)

- Node: `id, kind, label, path` where kind is `file | directory | service | dockerfile | workflow | k8s-resource | compose-service`.
- Edge: `id, source, target, kind, reason` where kind is `imports | contains | builds | deploys | triggers`, and `reason` is `{file, line, detail}`.
- Use dataclasses. Output `graph.json` as `{version, repo_name, generated_at, nodes, edges}`.

## Current task (first code PR): skeleton

1. Set up the Python project with `uv`: `pyproject.toml`, `src/` layout, a `repomap` console command, `pytest` and `ruff`.
2. `graph.py`: define the node/edge dataclasses above and JSON serialisation.
3. `scanner.py`: walk a directory (respecting `.gitignore`, skipping `.git`, `node_modules`, virtualenvs), create `directory` and `file` nodes with `contains` edges.
4. `cli.py` + `viewer/`: `repomap <path>` writes `repomap-out/graph.json` and `repomap-out/index.html`, where the HTML shows the folder/file tree as an interactive Cytoscape.js graph (zoom, pan, click a node to see its path).
5. A few `pytest` tests for the scanner using a small fixture in `examples/`.
6. Update README with how to install and run it.
7. Add `repomap-out/` to `.gitignore`.

**Done when:** `uv run repomap ~/code/test-repos/microservices-demo` produces `graph.json` and an `index.html` that opens in a browser and shows the repo's folder/file structure.

Import parsing, infra parsing and linking come in later PRs, not this one.

## Test target

Google's Online Boutique (microservices-demo), cloned at `~/code/test-repos/microservices-demo`: about 10 services in different languages, each with Dockerfiles, plus Kubernetes manifests, Helm charts and GitHub Actions. It lives outside this repo and must never be committed.
