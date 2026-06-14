# Testing

The test philosophy, how the suite is organised, what it covers, the performance
budget, and the red-green-refactor loop. The environment these run in is in
`container.md`.

## Philosophy

End-to-end, behavioural testing with Playwright against a real Jekyll build.
Tests assert what a user can observe — rendered DOM, computed styles, resolved
URLs, HTTP status — not implementation details. This is deliberate: the site has
been through several CSS and template consolidations, and behavioural tests stay
green across refactors that would break tests coupled to selectors-as-structure
or to specific markup.

## Stack and layout

`uv` + `pytest` + `pytest-playwright`. Tests live in `_tests/`.

- **`conftest.py`** provides the session-scoped `jekyll_server` fixture. If a
  server already answers at `JEKYLL_URL` (default `http://localhost:4000`) it is
  reused — this is the container and CI case. Otherwise the fixture starts
  `bundle exec jekyll serve` against `docs/` and tears it down afterward. The
  browser runs headless at 1280x720.
- **`constants.py`** is the single source of shared values: `SELECTORS`, the
  theme colours (`DARK_BG_COLOR`, `LIGHT_BG_COLOR`), `ANIMATION_TIMEOUT`, and the
  `PERF_` budget. Import from here rather than hardcoding, so a UI change is a
  one-line edit.

## Red-green-refactor

Features are built test-first:

1. **Red** — write the smallest failing test for the next slice of behaviour;
   run it; confirm it fails for the expected reason.
2. **Green** — write the minimum code to make it pass.
3. **Refactor** — clean up with the test as a safety net.

This is the working loop for new work, not just a description of past work.

## Test content must not depend on real essays

Real posts come and go, so tests never hardcode their URLs:

- `TEST_PAGE_PATH` and a dedicated fixture page are used for page-level checks
  instead of a real post.
- `test_previews.py` walks the source folders, derives each document's URL the
  way Jekyll does (`YYYY-MM-DD-slug` -> `/YYYY/MM/DD/slug/`, honouring an
  explicit `permalink`), and parametrises over whatever it finds. Previews are
  tested in full; posts are sampled to bound runtime.

## Coverage

By area (`_tests/<file>` -> what it guards):

- `test_navigation` — the sidebar nav is derived from `nav_order` front matter
  and the rendered order matches the derived order.
- `test_theme_toggle`, `test_theme_flash` — the toggle switches and persists the
  theme; the inline script sets the theme before paint (no flash on navigation).
- `test_hamburger` — the sidebar toggle icon renders per theme.
- `test_cards` — card grid presence, required card elements, clickable cards,
  hover styling.
- `test_pagination` — the essays landing (max 5 posts + archive link) and the
  paginated `/essays/all/` archive (page info, prev/next).
- `test_search` — sidebar search, the `/search/` page, and `search-index.json`
  shape/contents.
- `test_analytics` — the GoatCounter script and dynamic noscript fallback (see
  `analytics.md`).
- `test_performance` — the budget below.
- `test_previews` — previews are reachable, carry `noindex`, and are absent from
  the listing, archive, search index, and feed.

Tag and callout suites may also exist depending on what has shipped; check
`_tests/` for the current set.

## Performance budget

Thresholds are derived from Core Web Vitals research and are stricter than field
targets because local runs have no network latency. Metrics come from the
browser Navigation Timing API, averaged over `PERF_ITERATIONS` (10) runs per page
with a p90, across `PERF_TEST_PAGES`. All values live in `constants.py`:

- TTFB: avg < 100 ms, p90 < 200 ms
- DOMContentLoaded: avg < 500 ms, p90 < 800 ms
- Load complete: avg < 1000 ms, p90 < 1500 ms
- Per page: < 20 resources, < 500 KB transferred, < 1500 DOM nodes; no single
  page load over 3000 ms.

## Running the suite

```sh
make test          # canonical: runs sealed offline in the container
make test IT=      # same, for CI (drops the TTY flags; no terminal attached)
```

Without the container, start a server first, then run pytest:

```sh
make serve         # or: bundle exec jekyll serve --source docs --destination docs/_site
uv run pytest
uv run pytest _tests/test_search.py
uv run pytest _tests/test_theme_toggle.py::TestThemeToggle::test_toggle_switches_theme
```

Pre-commit runs `black` and `ruff` over `_tests/` plus a local Jekyll build
check; install it once with `uv run pre-commit install`.

## Fixture / drafts gotcha

The `jekyll_server` fixture serves **without** `--drafts`, so any page a test
navigates to must be reachable in a normal build. That is why the preview test
fixture lives in `docs/_previews/` (committed), not `docs/_drafts/`.

## CI

The harness is CI-ready: point `JEKYLL_URL` at a running build and the fixture
reuses it instead of spawning its own. Pre-commit intentionally defers the Jekyll
build to CI. Verify whether `.github/workflows/` actually contains the workflow
that builds the site and runs the suite — the harness assumes one exists, but the
workflow file should be confirmed in the repo.

## References
- Playwright (Python): <https://playwright.dev/python/docs/intro>
- pytest: <https://docs.pytest.org/>
- Core Web Vitals: <https://web.dev/articles/vitals>
- Navigation Timing: <https://developer.mozilla.org/en-US/docs/Web/API/Performance_API/Navigation_timing>
