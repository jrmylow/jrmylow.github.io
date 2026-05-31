# Dev workflow for the Jekyll blog, run through rootless Podman.
# The image carries Ruby+Jekyll and Python+Playwright; the repo is bind-mounted
# at /app, and the Python venv lives in a named volume so `uv add` persists.
#
# Targets:
#   make build   build/refresh the image (run after a lockfile or Gemfile change)
#   make shell   drop into an interactive bash shell in the container
#   make serve   preview the site at http://localhost:4000 (this machine only)
#   make sync    re-sync the venv volume from uv.lock (networked)
#   make test    run the pytest/Playwright suite sealed offline
#
# `make test IT=` disables the TTY flags for CI (no terminal attached).

IMAGE  := jrmylow-dev
VENV   := jrmylow-venv
MOUNTS := -v $(CURDIR):/app -v $(VENV):/opt/venv
IT     := -it

.PHONY: build shell serve sync test

build:
	podman build -t $(IMAGE) .

shell:
	podman run --rm $(IT) $(MOUNTS) $(IMAGE) bash

serve:
	podman run --rm $(IT) -e JEKYLL_ENV=production -p 127.0.0.1:4000:4000 $(MOUNTS) $(IMAGE) \
	  bundle exec jekyll serve --source docs --destination docs/_site \
	  --config docs/_config.yml,docs/_config_dev.yml \
	  --host 0.0.0.0 --port 4000

sync:
	podman run --rm $(IT) $(MOUNTS) $(IMAGE) uv sync

test:
	podman run --rm $(IT) $(MOUNTS) $(IMAGE) uv run pytest
