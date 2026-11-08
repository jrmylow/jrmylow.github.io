# Development Container

This document captures the rationale behind the design of the development container.

## Objectives

The previous workflow relied on recalling specific commands on jekyll, and ran based off the host machine's ruby and python environment. I picked up `poetry` and then `uv` for my python projects, and felt more comfortable with how it handled virtual environments. The container extends that to the whole site and allows me to experiment e.g. with direct LLM editing of this codebase.

## Implementation details

I wanted to grow my familiarity with containers, and found `podman` as a solution that doesn't use a daemon thread and avoids issues with root access that are a risk for docker.

As to the contents, the goal of the container started with isolating the files from the broader system, but also incorporated a reproducible build and approximation of the Github Pages workflow. The containers also include playwright browsers for functional testing.

Over time, the `Makefile` and container helped land a habitual, simple workflow, with common make commands encoding instructions with sensible defaults and configurations so I don't have to wrangle command line flags each time.

## Image Contents

Defined in `Containerfile`, run through rootless Podman:

- **Base:** `ruby:3.3.4-slim-bookworm`, the exact Ruby that GitHub Pages builds with ([versions.json](https://pages.github.com/versions.json)). The `github-pages` gem pins Jekyll and its plugins, and the Gemfile pins `nokogiri`, which `github-pages` leaves as a range. `BUNDLE_FROZEN` makes the image build fail if `Gemfile.lock` doesn't match the Gemfile, rather than quietly installing something else. When versions.json changes, bump the base tag, `github-pages` and `nokogiri` together. Dependabot ignores the last two for this reason; its Python and Actions PRs don't touch the Pages build and are safe to merge (see `.github/dependabot.yml`).
- **uv 0.9.5** (static binary, copied from its official image) for the Python toolchain.
- **System libraries** for native gem and wheel builds: `build-essential`, `git`, `curl`, `ca-certificates`.
- **Bundler pinned to 2.4.22**, matching `Gemfile.lock`'s `BUNDLED WITH`, so dependency resolution matches the lockfile exactly.

### Layer order

Layers run from least to most likely to change, so a change only rebuilds its own layer and those after it:

1. Base Ruby image
2. System libraries
3. Bundler and gems (`Gemfile`, `Gemfile.lock`)
4. Python interpreter (`.python-version`), then venv (`pyproject.toml`, `uv.lock`)
5. Playwright browsers

Dependency manifests are copied in on their own, before any source, so editing a post or a test never reinstalls gems or wheels. Browsers come last because their build is locked to the installed `playwright` version, so they must be installed after the venv sync that fixes that version.

### Why gems and the venv live outside `/app`

At runtime the repo is bind-mounted over `/app`, which hides whatever the image put there. Gems (`BUNDLE_PATH=/usr/local/bundle`), the venv (`/opt/venv`), the uv-managed Python (`/opt/python`) and the browsers (`/opt/ms-playwright`) therefore live elsewhere. This also keeps installed dependencies out of the working tree.

The venv is also a named volume (`jrmylow-venv`). Podman fills an empty named volume from the image the first time it is mounted, and never again after that. A rebuilt image therefore does not update the venv, which is why `uv.lock` changes need `make sync`.

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
