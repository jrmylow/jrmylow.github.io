# Development Container

This document captures the rationale behind the design of the development container.

## Objectives

The previous workflow relied on recalling specific commands on jekyll, and ran based off the host machine's ruby and python environment. I picked up `poetry` and then `uv` for my python projects, and felt more comfortable with how it handled virtual environments. The container extends that to the whole site and allows me to experiment e.g. with direct LLM editing of this codebase.

## Implelmentation details

I wanted to grow my familiarity with containers, and found `podman` as a solution that doesn't use a daemon thread and avoids issues with root access that are a risk for docker.

As to the contents, the goal of the container started with isolating the files from the broader system, but also incorporated a reproducible build and approximation of the Github Pages workflow. The containers also include playwright browsers for functional testing.

Over time, the `Makefile` and container helped land a habitual, simple workflow, with common make commands encoding instructions with sensible defaults and configurations so I don't have to wrangle command line flags each time.

## Image Contents

Defined in `Containerfile`, run through rootless Podman:

- **Base:** `ruby:3.3-slim-bookworm`, pinned to track what GitHub Pages builds with. The `github-pages` gem pins Jekyll 3.10, so bump the base deliberately to keep parity.
- **uv 0.9.5** (static binary, copied from its official image) for the Python toolchain.
- **System libraries** for native gem and wheel builds: `build-essential`, `git`, `curl`, `ca-certificates`.
- **Bundler pinned to 2.4.22**, matching `Gemfile.lock`'s `BUNDLED WITH`, so dependency resolution matches the lockfile exactly.

### Layer order

TODO

### Why gems and the venv live outside `/app`

TODO

## Makefile targets

| Target | Does |
|---|---|
| `make build` | Build/refresh the image. Run after a `Gemfile` or lockfile change. |
| `make shell` | Drop into an interactive bash shell in the container. |
| `make serve` | Serve at `http://127.0.0.1:4000` (this machine only), no drafts. |
| `make preview` | Like `serve`, plus `--drafts` for local WIP (see `workflow.md`). |
| `make sync` | Re-sync the venv volume from `uv.lock` (networked). |
| `make test` | Run the pytest/Playwright suite sealed offline. |

## When to rebuild vs. sync

- `Gemfile` / `Gemfile.lock` changed -> `make build`.
- `uv.lock` changed -> `make sync` (or `make build`).
- Source or content only -> nothing; the bind mount picks it up live.

## References
- Podman: <https://docs.podman.io/>
- GitHub Pages dependency versions: <https://pages.github.com/versions/>
- uv: <https://docs.astral.sh/uv/>
