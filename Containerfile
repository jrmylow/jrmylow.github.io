# syntax=docker/dockerfile:1
#
# Dev / test / preview image for the Jekyll blog.
# NOT a deployment image: the live site is built by GitHub Pages' built-in
# build, which never uses this. This image only runs `jekyll serve`, pytest,
# and an interactive shell on your machine.
#
# Layer order is stable -> volatile so the build cache invalidates from the
# first changed thing downward:
#   base Ruby  ->  system libs  ->  gems  ->  Python venv  ->  browsers
#
# ---------------------------------------------------------------------------
# Base: official Ruby image. This is a from-source, version-pinned Ruby on a
# Debian Bookworm base, maintained by the Docker official-images team. The repo
# uses the github-pages gem, which pins Jekyll 3.10; keep this tag aligned with
# the Ruby that GitHub Pages builds with. Bump deliberately.
# ---------------------------------------------------------------------------
FROM docker.io/library/ruby:3.3-slim-bookworm

# uv as a static binary, copied from its official image and version-pinned.
COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /uvx /bin/

# --- System libraries (stable layer) --------------------------------------
# build-essential + headers: native gem extensions (sass-embedded, ffi,
# eventmachine, google-protobuf) and any C-extension Python wheels.
# git + curl: general tooling. ca-certificates: TLS for downloads.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Bundler config ---------------------------------------------------------
# Gems install to a fixed path OUTSIDE /app so the runtime bind-mount of the
# repo over /app cannot shadow them. Pin bundler to the Gemfile.lock's
# "BUNDLED WITH" (2.4.22) so resolution matches your lockfile exactly.
ENV BUNDLE_PATH=/usr/local/bundle \
    BUNDLE_JOBS=4 \
    BUNDLE_RETRY=3
RUN gem install bundler -v 2.4.22

# --- Ruby gems (changes when Gemfile/Gemfile.lock change) -------------------
# Copied alone so this layer only rebuilds on a Gemfile change, not on every
# source edit. A bundle cache mount keeps re-resolves fast across rebuilds.
COPY Gemfile Gemfile.lock ./
RUN --mount=type=cache,target=/root/.bundle-cache \
    bundle _2.4.22_ install

# --- Python toolchain via uv -----------------------------------------------
# Venv lives OUTSIDE /app (same bind-mount-shadowing reason as gems).
# uv reads .python-version to fetch the exact interpreter, so Ruby (base image)
# AND Python (uv) are both version-pinned.
# UV_FROZEN: never silently re-resolve; the lockfile is the source of truth.
# (No UV_NO_SYNC here: `uv run` may need to sync into the venv at build time.)
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_LINK_MODE=copy \
    UV_FROZEN=1

COPY .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv python install

# Dependency metadata copied alone so this layer only rebuilds on a lock change.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project

# --- Playwright browsers (most volatile: version-locked to the playwright pkg)
# Installed AFTER the venv so the browser build always matches the just-synced
# playwright version. Both chromium and firefox per the documented test matrix.
# --with-deps pulls the apt system libs each browser needs (Debian-supported).
# Browsers download to a fixed, world-readable path so a non-root exec can use
# them too.
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright
RUN uv run playwright install --with-deps chromium firefox \
    && rm -rf /var/lib/apt/lists/*

# Default to an interactive shell; `make` overrides the command per target.
ENV JEKYLL_URL=http://localhost:4000
EXPOSE 4000
CMD ["bash"]
