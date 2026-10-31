# repomap

A tool that turns any repository into an interactive map of its code **and** infrastructure: which files depend on which, how each service is built, and how it's deployed.

Point it at a repo and see the full picture: source files → Dockerfiles → CI workflows → Kubernetes deployments, all in one graph.

## Why

Understanding an unfamiliar codebase is slow. Existing visualisers either show only code imports, or use AI to *guess* the architecture from file names and READMEs.

repomap is **deterministic**:
- Every edge in the graph comes from real code or config, so you can always see *why* two things are connected
- The same repo always produces the same map
- Runs fully locally, so your code never leaves your machine
- No AI or external APIs involved

## Install

repomap uses [uv](https://docs.astral.sh/uv/) to manage Python and dependencies.

```sh
brew install uv            # if you don't have it yet
git clone https://github.com/1ahzaz1/repomap.git
cd repomap
uv sync                    # creates .venv/ and installs everything (uv fetches Python 3.12 if needed)
```

## Usage

```sh
uv run repomap path/to/some/repo
open repomap-out/index.html
```

This writes two files into `repomap-out/` (change it with `--out`):

- `graph.json`: the graph data: `{version, repo_name, generated_at, nodes, edges}`. Every edge has a `reason` saying why it exists.
- `index.html`: a standalone interactive viewer. Scroll to zoom, drag to pan, click a node or edge to see its details. Switch between the **Clusters** and **Tree** layouts in the top bar.

The scanner respects `.gitignore` files (at every level, like git) and always skips `.git`, `node_modules`, Python virtualenvs and caches.

> The viewer loads [Cytoscape.js](https://js.cytoscape.org/) from a CDN, so opening `index.html` needs an internet connection. Your repo data stays embedded in the local file and is never sent anywhere.

## Development

```sh
uv run pytest              # run the tests
uv run ruff check .        # lint
uv run ruff format .       # format
```

Project layout:

```
src/repomap/
├── cli.py              # `repomap <path>` entry point
├── graph.py            # Node / Edge / Reason dataclasses + JSON output
├── scanner.py          # walks a repo into directory/file nodes and `contains` edges
└── viewer/
    ├── template.html   # the viewer page (Cytoscape.js)
    └── render.py       # writes graph.json and index.html
tests/                  # pytest tests
examples/tiny-repo/     # small fixture repo used by the tests
```

## Roadmap

### Phase 1 — The map
- [x] Scan a repository and list its files
- [ ] Parse imports to build a file → file dependency graph
- [ ] Parse Dockerfiles, docker-compose, Kubernetes YAML and GitHub Actions workflows
- [ ] Link code → Dockerfile → CI workflow → Kubernetes deployment
- [ ] Interactive web viewer (basic folder/file view done; code and infra views to come)

### Phase 2 — Blast radius
- [ ] Select a file or git diff and highlight everything affected downstream
- [ ] Show which services, CI workflows and deployments a change touches

### Phase 3 — Architecture over time
- [ ] Rebuild the graph across git history
- [ ] Timeline view to watch the architecture evolve
- [ ] Track metrics over time (circular dependencies, coupling)

### Phase 4 — Container insights
- [ ] Image size and layer breakdown per service
- [ ] Rule-based Dockerfile improvement suggestions

## Status

Early development. First test target: [Google's Online Boutique](https://github.com/GoogleCloudPlatform/microservices-demo).

## License

repomap is released under the [MIT License](LICENSE).