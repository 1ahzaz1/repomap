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

## Roadmap

### Phase 1 — The map
- [ ] Scan a repository and list its files
- [ ] Parse imports to build a file → file dependency graph
- [ ] Parse Dockerfiles, docker-compose, Kubernetes YAML and GitHub Actions workflows
- [ ] Link code → Dockerfile → CI workflow → Kubernetes deployment
- [ ] Interactive web viewer

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